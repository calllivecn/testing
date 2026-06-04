# pipewire_capture.py
import threading
import traceback
from _pipewire_cffi import ffi, lib as C

# 全局初始化 PipeWire (整个进程只需一次)
C.pw_init(ffi.NULL, ffi.NULL)

# 定义常量 (对应 spa/param/video/format.h 中的枚举值)
SPA_VIDEO_FORMAT_BGRx = 19 

# PipeWire 流方向与标志位常量
PW_DIRECTION_INPUT = 1
PW_STREAM_FLAG_AUTOCONNECT = 0x0004
PW_STREAM_FLAG_MAP_BUFFERS = 0x0008
PW_VERSION_STREAM_EVENTS = 3

class PipeWireCapture:
    def __init__(self, node_id, on_frame=None, on_state_change=None):
        """
        初始化 PipeWire 抓取器
        :param node_id: D-Bus 返回的 PipeWire 节点 ID
        :param on_frame: 帧数据回调函数 on_frame(data_bytes, size, stride, width, height)
        :param on_state_change: 状态变更回调 on_state_change(state_str)
        """
        self.node_id = node_id
        self.on_frame = on_frame
        self.on_state_change = on_state_change
        
        self.running = False
        self.width = 0
        self.height = 0
        self._pw_thread = None
        
        # 创建 PipeWire 主循环和核心 Loop
        self.pw_loop = C.pw_main_loop_new(ffi.NULL)
        self.core_loop = C.pw_main_loop_get_loop(self.pw_loop)
        self.pw_stream = None
        
        # 🎯 核心防坑：保持所有 CFFI 回调和 C 指针的强引用，防止被 Python GC 回收导致段错误
        self._keep_alive = [] 

    def _c_process(self, user_data):
        """底层 C 回调：处理推送过来的视频帧数据"""
        if not self.running: 
            return
            
        buf = C.pw_stream_dequeue_buffer(self.pw_stream)
        if buf == ffi.NULL: 
            return
        
        try:
            spa_buf = buf.buffer
            if spa_buf == ffi.NULL or spa_buf.n_datas < 1: 
                return
            
            data_struct = spa_buf.datas[0]
            data_ptr = data_struct.data
            
            # 🎯 核心修复：chunk 在 struct spa_data 中是一个指针，必须用 [0] 解引用
            if data_struct.chunk == ffi.NULL:
                return
            chunk = data_struct.chunk[0] 
            
            chunk_size = chunk.size
            chunk_stride = chunk.stride 
            
            # 确保数据指针有效且大小合理
            if data_ptr != ffi.NULL and chunk_size > 0:
                # 将 C 内存立即拷贝为 Python bytes，防止底层缓冲区被复用导致数据撕裂
                frame_bytes = ffi.buffer(data_ptr, chunk_size)[:]
                
                if self.on_frame:
                    self.on_frame(frame_bytes, chunk_size, chunk_stride, self.width, self.height)
                    
        except Exception as e:
            print(f"\n❌ PipeWire process 回调异常: {e}")
            traceback.print_exc()
        finally:
            # 无论是否处理成功，都必须将 buffer 归还给 PipeWire
            C.pw_stream_queue_buffer(self.pw_stream, buf)

    def _c_state_changed(self, user_data, old_state, new_state, error):
        """底层 C 回调：处理流状态变更"""
        states = {
            -1: "ERROR", 0: "UNCONNECTED", 1: "CONNECTING", 
            2: "PAUSED", 3: "STREAMING"
        }
        state_str = states.get(new_state, f"UNKNOWN({new_state})")
        
        if self.on_state_change:
            self.on_state_change(state_str)

    def _c_param_changed(self, user_data, param_id, param):
        """底层 C 回调：格式协商完成 (预留接口，目前仅做状态记录)"""
        # SPA_PARAM_Format = 3
        if param_id == 3 and param != ffi.NULL:
            # 这里可以通过 spa_format_parse 解析真实的 width/height，
            # 但为了保持底层代码简洁，我们暂时通过外部或 stride 推算。
            pass 

    def _run_loop(self):
        """在子线程中运行 PipeWire 主循环 (阻塞)"""
        # 1. 配置事件回调结构体
        events = ffi.new("struct pw_stream_events *")
        events.version = PW_VERSION_STREAM_EVENTS
        
        # 绑定 C 回调，并使用 onerror 防止 Python 异常穿透导致 C 层崩溃
        c_process = ffi.callback("void(void *)", self._c_process, onerror=traceback.print_exc)
        c_state = ffi.callback("void(void *, int, int, const char *)", self._c_state_changed, onerror=traceback.print_exc)
        c_param = ffi.callback("void(void *, uint32_t, const struct spa_pod *)", self._c_param_changed, onerror=traceback.print_exc)
        
        events.process = c_process
        events.state_changed = c_state
        events.param_changed = c_param
        
        # 保持强引用
        self._keep_alive.extend([events, c_process, c_state, c_param])

        # 2. 构建 Format POD (16KB 超大缓冲区，防御性编程)
        POD_BUFFER_SIZE = 16384 
        pod_buffer = ffi.new(f"uint8_t[{POD_BUFFER_SIZE}]")
        builder = ffi.new("struct spa_pod_builder *")
        C.spa_pod_builder_init(builder, pod_buffer, POD_BUFFER_SIZE)
        
        pod = C.build_format_pod(builder, SPA_VIDEO_FORMAT_BGRx)
        
        if pod == ffi.NULL:
            print("❌ 致命错误：Format POD 构建失败！")
            return
            
        self._keep_alive.extend([pod_buffer, builder, pod])

        # 🎯 核心修复：严格使用 const struct spa_pod * 数组
        params = ffi.new("const struct spa_pod *[1]")
        params[0] = pod
        self._keep_alive.append(params)

        # 3. 创建并连接 PipeWire 流
        self.pw_stream = C.pw_stream_new_simple(
            self.core_loop, 
            b"python-screencast", 
            ffi.NULL, 
            events, 
            ffi.NULL
        )
        
        if self.pw_stream == ffi.NULL:
            print("❌ 致命错误：无法创建 PipeWire Stream！")
            return
        
        flags = PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS
        res = C.pw_stream_connect(
            self.pw_stream, 
            PW_DIRECTION_INPUT, 
            self.node_id, 
            flags, 
            params, 
            1
        )
        
        if res < 0: 
            print(f"❌ PipeWire 连接失败，错误码: {res}")
            return
        
        # 4. 启动主循环 (阻塞当前线程，直到调用 pw_main_loop_quit)
        self.running = True
        C.pw_main_loop_run(self.pw_loop)

    def start(self):
        """启动抓帧 (非阻塞，在后台线程运行)"""
        if self._pw_thread and self._pw_thread.is_alive(): 
            return
        self._pw_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._pw_thread.start()

    def stop(self):
        """停止抓帧并清理资源"""
        self.running = False
        C.pw_main_loop_quit(self.pw_loop)
        
        if self.pw_stream and self.pw_stream != ffi.NULL:
            C.pw_stream_destroy(self.pw_stream)
            self.pw_stream = None
            
        if self._pw_thread:
            self._pw_thread.join(timeout=2.0)
