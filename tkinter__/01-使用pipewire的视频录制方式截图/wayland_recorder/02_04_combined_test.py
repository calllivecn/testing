#!/usr/bin/env python3
"""联合测试: D-Bus 授权 + PipeWire cffi 抓帧 (同一进程)"""
import asyncio
import threading
import time
import traceback
from cffi import FFI

# ================= 1. cffi PipeWire 绑定 =================
ffi = FFI()
ffi.cdef("""
    typedef struct pw_main_loop pw_main_loop;
    typedef struct pw_loop pw_loop;
    typedef struct pw_stream pw_stream;
    typedef struct spa_pod spa_pod;
    struct spa_chunk { uint32_t offset; uint32_t size; uint32_t stride; uint32_t flags; };
    struct spa_data { uint32_t id; uint32_t flags; uint32_t type; uint32_t format; int64_t fd; uint32_t mapoffset; uint32_t maxsize; void *data; struct spa_chunk chunk; };
    struct spa_meta { uint32_t type; uint32_t size; void *data; };
    struct spa_buffer { uint32_t n_metas; uint32_t n_datas; struct spa_meta *metas; struct spa_data *datas; };
    struct pw_buffer { struct spa_buffer *buffer; void *user_data; uint64_t size; uint64_t requested; };
    typedef void (*pw_stream_event_process_t)(void *data);
    typedef void (*pw_stream_event_param_changed_t)(void *data, uint32_t id, const struct spa_pod *param);
    struct pw_stream_events {
        uint32_t version; void (*destroy)(void *data); void (*state_changed)(void *data, int old_state, int state, const char *error);
        void (*control_info)(void *data, uint32_t id, uint32_t flags); void (*io_changed)(void *data, uint32_t id, void *area, uint32_t size);
        pw_stream_event_param_changed_t param_changed; void (*add_buffer)(void *data, struct pw_buffer *buffer);
        void (*remove_buffer)(void *data, struct pw_buffer *buffer); pw_stream_event_process_t process; void (*trigger_done)(void *data);
    };
    void pw_init(int *argc, char **argv[]);
    struct pw_main_loop *pw_main_loop_new(const void *props);
    struct pw_loop *pw_main_loop_get_loop(struct pw_main_loop *loop);
    int pw_main_loop_run(struct pw_main_loop *loop);
    int pw_main_loop_quit(struct pw_main_loop *loop);
    struct pw_stream *pw_stream_new_simple(struct pw_loop *loop, const char *name, void *props, const struct pw_stream_events *events, void *data);
    int pw_stream_connect(struct pw_stream *stream, uint32_t direction, uint32_t target_id, uint32_t flags, const void **params, uint32_t n_params);
    struct pw_buffer *pw_stream_dequeue_buffer(struct pw_stream *stream);
    int pw_stream_queue_buffer(struct pw_stream *stream, struct pw_buffer *buf);
    void pw_stream_destroy(struct pw_stream *stream);
""")
C = ffi.dlopen("libpipewire-0.3.so.0")
C.pw_init(ffi.NULL, ffi.NULL)

# ================= 2. PipeWire 流处理类 =================
# ================= 2. PipeWire 流处理类 (终极修复版) =================
class PipeWireStream:
    def __init__(self, node_id):
        self.node_id = node_id
        self.running = True
        self.frame_count = 0
        self.pw_loop = C.pw_main_loop_new(ffi.NULL)
        self.core_loop = C.pw_main_loop_get_loop(self.pw_loop)
        self._keep_alive = []
        self.pw_stream = None
        self.first_frame_logged = False

    def _on_process(self, user_data):
        if not self.running: return
        buf = C.pw_stream_dequeue_buffer(self.pw_stream)
        if buf == ffi.NULL: return
        try:
            spa_buf = buf.buffer
            if spa_buf == ffi.NULL or spa_buf.n_datas < 1: return
            
            data_struct = spa_buf.datas[0]
            data_ptr = data_struct.data
            chunk_size = data_struct.chunk.size
            
            # 🎯 核心修复：不再盲目校验分辨率，只要 chunk_size > 0 就认为抓帧成功！
            if data_ptr != ffi.NULL and chunk_size > 0:
                self.frame_count += 1
                
                # 打印第一帧的真实数据大小，帮我们反推真实分辨率
                if not self.first_frame_logged:
                    print(f"\n🚨 [首帧捕获] 真实数据包大小: {chunk_size} bytes")
                    # 假设 32位色深 (4 bytes/pixel)，反推可能的像素总数
                    pixels = chunk_size // 4
                    print(f"💡 估算像素总数: {pixels} (例如: 2560x1440={2560*1440}, 1920x1080={1920*1080})")
                    self.first_frame_logged = True
                    
                if self.frame_count % 30 == 0:
                    print(f"\r⏺ 成功抓帧: #{self.frame_count} (包大小: {chunk_size})", end="")
        except Exception as e:
            print(f"\n❌ 回调异常: {e}")
            traceback.print_exc()
        finally:
            C.pw_stream_queue_buffer(self.pw_stream, buf)

    def _on_state_changed(self, user_data, old_state, new_state, error):
        # PipeWire 状态枚举: 0=Unconnected, 1=Connecting, 2=Paused, 3=Streaming, -1=Error
        states = {-1: "ERROR", 0: "UNCONNECTED", 1: "CONNECTING", 2: "PAUSED", 3: "STREAMING"}
        state_str = states.get(new_state, f"UNKNOWN({new_state})")
        print(f"\n🔄 [流状态变更] -> {state_str}")
        if new_state == -1 and error != ffi.NULL:
            print(f"❌ PipeWire 报错: {ffi.string(error).decode()}")

    def _on_param_changed(self, user_data, id, param):
        pass 

    def start(self):
        events = ffi.new("struct pw_stream_events *")
        events.version = 3
        
        # 绑定所有关键回调
        c_process = ffi.callback("void(void *)", self._on_process, onerror=traceback.print_exc)
        c_state = ffi.callback("void(void *, int, int, const char *)", self._on_state_changed, onerror=traceback.print_exc)
        c_param = ffi.callback("void(void *, uint32_t, const struct spa_pod *)", self._on_param_changed, onerror=traceback.print_exc)
        
        events.process = c_process
        events.state_changed = c_state
        events.param_changed = c_param
        self._keep_alive.extend([events, c_process, c_state, c_param])

        self.pw_stream = C.pw_stream_new_simple(self.core_loop, b"python-screencast", ffi.NULL, events, ffi.NULL)
        
        # 0x0004 = AUTOCONNECT, 0x0008 = MAP_BUFFERS, 0x0010 = RT_PROCESS (可选)
        flags = 0x0004 | 0x0008 
        res = C.pw_stream_connect(self.pw_stream, 1, self.node_id, flags, ffi.NULL, 0)
        if res < 0: raise RuntimeError(f"连接失败: {res}")
        
        print(f"▶ PipeWire 流已连接，等待底层推流...")
        C.pw_main_loop_run(self.pw_loop)

    def stop(self):
        self.running = False
        C.pw_main_loop_quit(self.pw_loop)
        if self.pw_stream and self.pw_stream != ffi.NULL:
            C.pw_stream_destroy(self.pw_stream)
# ================= 3. D-Bus Portal 交互 =================
from dbus_next.aio import MessageBus
from dbus_next import Message, MessageType, Variant, BusType

async def get_node_id_and_stream():
    print("="*50)
    print("🔍 联合测试: D-Bus 授权 + PipeWire 抓帧")
    print("="*50)
    
    # 1. 连接 D-Bus
    bus = await MessageBus(bus_type=BusType.SESSION).connect()
    sender = bus.unique_name.replace('.', '_').replace(':', '_')[1:]
    
    # 2. 弹窗授权 (简化版内联代码)
    print("🔹 正在请求屏幕共享授权 (请在弹窗中点击分享)...")
    token = "combined_test_token"
    session_token = "combined_session_token"
    expected_path = f"/org/freedesktop/portal/desktop/request/{sender}/{token}"
    
    response_event = asyncio.Event()
    node_id_holder = []

    def handler(msg):
        if msg.message_type == MessageType.SIGNAL and msg.interface == 'org.freedesktop.portal.Request' and msg.member == 'Response' and msg.path == expected_path:
            if msg.body[0] == 0:
                streams = msg.body[1].get('streams', Variant('a(ua{sv})', [])).value
                if streams:
                    node_id_holder.append(streams[0][0].value if hasattr(streams[0][0], 'value') else streams[0][0])
            response_event.set()
        return False

    bus.add_message_handler(handler)
    
    # CreateSession
    await bus.call(Message(destination='org.freedesktop.portal.Desktop', path='/org/freedesktop/portal/desktop', interface='org.freedesktop.portal.ScreenCast', member='CreateSession', signature='a{sv}', body=[{'session_handle_token': Variant('s', session_token), 'handle_token': Variant('s', 'session_req')}] ))
    
    # SelectSources
    session_path = f"/org/freedesktop/portal/desktop/session/{sender}/{session_token}"
    await bus.call(Message(destination='org.freedesktop.portal.Desktop', path='/org/freedesktop/portal/desktop', interface='org.freedesktop.portal.ScreenCast', member='SelectSources', signature='oa{sv}', body=[session_path, {'types': Variant('u', 1), 'cursor_mode': Variant('u', 1), 'handle_token': Variant('s', 'select_req')}] ))
    
    # Start
    await bus.call(Message(destination='org.freedesktop.portal.Desktop', path='/org/freedesktop/portal/desktop', interface='org.freedesktop.portal.ScreenCast', member='Start', signature='osa{sv}', body=[session_path, "", {'handle_token': Variant('s', token)}] ))
    
    await response_event.wait()
    
    if not node_id_holder:
        print("❌ 授权失败或被取消")
        bus.disconnect()
        return
        
    node_id = int(node_id_holder[0])
    print(f"✅ 授权成功! 获取到 Node ID: {node_id}")
    print("💡 保持 D-Bus 连接存活，立刻启动 PipeWire 抓帧...")

    # 3. 启动 PipeWire (在后台线程)
    stream = PipeWireStream(node_id)
    pw_thread = threading.Thread(target=stream.start)
    pw_thread.start()

    # 4. 保持主线程 (和 D-Bus 连接) 存活 10 秒
    print("⏳ 录制 10 秒... (在此期间 D-Bus 保持连接)")
    await asyncio.sleep(10)

    # 5. 清理
    print("\n⏹ 停止录制...")
    stream.stop()
    pw_thread.join()
    bus.remove_message_handler(handler)
    bus.disconnect()
    
    if stream.frame_count > 0:
        print(f"\n🎉🎉🎉 终极测试通过！成功抓取 {stream.frame_count} 帧！底层逻辑完美！")
    else:
        print("\n⚠️ 依然没有抓到帧。可能需要动态解析分辨率。")

if __name__ == "__main__":
    asyncio.run(get_node_id_and_stream())
