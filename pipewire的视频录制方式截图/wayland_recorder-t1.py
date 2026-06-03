#!/usr/bin/env python3
"""
Wayland 窗口捕获录制器 (纯 Python + ctypes + dbus-next + PyAV)
- 严格遵循 xdg-desktop-portal 异步 Request/Response 协议
- 通过 ctypes 直接绑定 PipeWire C API 获取视频帧
- 使用 PyAV 进行 H.264 硬件/软件编码
"""
import os
import sys
import time
import ctypes
import asyncio
import random
import string
from pathlib import Path

# ====================== 依赖检查 ======================
try:
    from dbus_next.aio import MessageBus
    from dbus_next import Message, MessageType, Variant, BusType
except ImportError:
    sys.exit("❌ 缺少 dbus-next 库! 请执行: pip install dbus-next")

try:
    import av
except ImportError:
    sys.exit("❌ 缺少 PyAV 库! 请执行: pip install av")

# ====================== 1. PipeWire C API 绑定 ======================
# 定义 PipeWire 核心结构体指针
class pw_main_loop(ctypes.Structure): pass
class pw_stream(ctypes.Structure): pass
class pw_buffer(ctypes.Structure): pass
class spa_buffer(ctypes.Structure): pass
class spa_data(ctypes.Structure): pass
class spa_pod(ctypes.Structure): pass

# 加载 PipeWire 动态库
try:
    libpw = ctypes.CDLL("libpipewire-0.3.so.0")
except OSError:
    sys.exit("❌ PipeWire 库未找到! 请安装: sudo apt install libpipewire-0.3-dev")

# 绑定核心函数
libpw.pw_init.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p))]
libpw.pw_init.restype = None

libpw.pw_main_loop_new.argtypes = [ctypes.c_char_p]
libpw.pw_main_loop_new.restype = ctypes.POINTER(pw_main_loop)

libpw.pw_main_loop_get_loop.argtypes = [ctypes.POINTER(pw_main_loop)]
libpw.pw_main_loop_get_loop.restype = ctypes.c_void_p

libpw.pw_main_loop_run.argtypes = [ctypes.POINTER(pw_main_loop)]
libpw.pw_main_loop_run.restype = ctypes.c_int

libpw.pw_main_loop_quit.argtypes = [ctypes.POINTER(pw_main_loop)]
libpw.pw_main_loop_quit.restype = ctypes.c_int

libpw.pw_stream_new_simple.argtypes = [
    ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
]
libpw.pw_stream_new_simple.restype = ctypes.POINTER(pw_stream)

libpw.pw_stream_connect.argtypes = [
    ctypes.POINTER(pw_stream), ctypes.c_int, ctypes.c_uint32, ctypes.c_uint32, 
    ctypes.POINTER(ctypes.POINTER(spa_pod)), ctypes.c_uint32
]
libpw.pw_stream_connect.restype = ctypes.c_int

libpw.pw_stream_dequeue_buffer.argtypes = [ctypes.POINTER(pw_stream)]
libpw.pw_stream_dequeue_buffer.restype = ctypes.POINTER(pw_buffer)

libpw.pw_stream_queue_buffer.argtypes = [ctypes.POINTER(pw_stream), ctypes.POINTER(pw_buffer)]
libpw.pw_stream_queue_buffer.restype = ctypes.c_int

# 初始化 PipeWire
libpw.pw_init(None, None)

# ====================== 2. xdg-desktop-portal D-Bus 交互 ======================
class PortalSession:
    """处理 xdg-desktop-portal 的异步请求与信号监听"""
    def __init__(self, bus):
        self.bus = bus
        # 生成唯一的 sender name (将 ':' 替换为 '_')
        self.sender = self.bus.unique_name.replace('.', '_').replace(':', '_')[1:]
        self.token = ''.join(random.choices(string.ascii_lowercase, k=8))
        
    def _get_request_path(self):
        """生成当前请求的 D-Bus 对象路径"""
        self.token = ''.join(random.choices(string.ascii_lowercase, k=8))
        return f"/org/freedesktop/portal/desktop/request/{self.sender}/{self.token}"

    async def _call_and_wait(self, method, signature, body):
        """
        核心机制：调用 Portal 方法，并阻塞等待对应的 Response 信号
        """
        request_path = self._get_request_path()
        response_event = asyncio.Event()
        response_data = {}

        # 定义信号回调
        def on_response(msg):
            if msg.path == request_path and msg.member == 'Response':
                response_code = msg.body[0]
                results = msg.body[1]
                if response_code == 0:
                    response_data.update(results)
                response_event.set()

        # 注册信号监听
        match_rule = f"type='signal',sender='org.freedesktop.portal.Desktop',path='{request_path}'"
        await self.bus.call(Message(
            destination='org.freedesktop.DBus',
            path='/org/freedesktop/DBus',
            interface='org.freedesktop.DBus',
            member='AddMatch',
            signature='s',
            body=[match_rule]
        ))
        
        # 添加消息路由
        self.bus.add_message_handler(on_response)

        try:
            # 发送方法调用
            msg = Message(
                destination='org.freedesktop.portal.Desktop',
                path='/org/freedesktop/portal/desktop',
                interface='org.freedesktop.portal.ScreenCast',
                member=method,
                signature=signature,
                body=body
            )
            reply = await self.bus.call(msg)
            if reply.message_type == MessageType.ERROR:
                raise RuntimeError(f"Portal 调用失败: {reply.body[0]}")

            # 等待信号触发 (超时 60 秒，等待用户点击授权)
            await asyncio.wait_for(response_event.wait(), timeout=60.0)
            return response_data
        finally:
            self.bus.remove_message_handler(on_response)

    async def create_session(self):
        print("🔹 1/3 创建捕获会话...")
        session_token = f"session_{self.token}"
        options = {
            'handle_token': Variant('s', self.token),
            'session_handle_token': Variant('s', session_token)
        }
        res = await self._call_and_wait('CreateSession', 'a{sv}', [options])
        self.session_handle = res['session_handle'].value
        print(f"   ✅ 会话已建立: {self.session_handle}")

    async def select_sources(self):
        print("🔹 2/3 选择捕获源 (窗口模式)...")
        options = {
            'handle_token': Variant('s', self.token),
            'types': Variant('u', 1),        # 1 = WINDOW (窗口), 2 = MONITOR (屏幕)
            'cursor_mode': Variant('u', 1),  # 1 = HIDDEN (隐藏光标)
            'multiple': Variant('b', False)
        }
        await self._call_and_wait(
            'SelectSources', 'oa{sv}', 
            [self.session_handle, options]
        )
        print("   ✅ 捕获源已选择")

    async def start_and_get_node_id(self):
        print("🔹 3/3 启动捕获 (请在弹出的系统窗口中选择目标窗口并点击分享)...")
        options = {
            'handle_token': Variant('s', self.token)
        }
        res = await self._call_and_wait(
            'Start', 'osa{sv}', 
            [self.session_handle, "", options]
        )
        
        # 解析 streams 数组获取 PipeWire Node ID
        # 格式: a(ua{sv}) -> array of struct (node_id, properties)
        streams = res['streams'].value
        if not streams:
            raise RuntimeError("未获取到视频流，用户可能取消了授权")
            
        node_id = streams[0][0]  # 取第一个流的 node_id
        print(f"   ✅ 授权成功! 获取到 PipeWire Node ID: {node_id}")
        return node_id

# ====================== 3. PipeWire 流处理与视频编码 ======================
class PipeWireRecorder:
    def __init__(self, node_id, output_file="output.mp4"):
        self.node_id = node_id
        self.output_file = output_file
        self.running = True
        self.frame_count = 0
        
        # 视频参数 (将从 PipeWire 动态获取)
        self.width = 0
        self.height = 0
        self.fps = 30
        
        # 初始化 PyAV 容器和编码器
        self.container = av.open(self.output_file, mode='w')
        self.stream = self.container.add_stream('h264', rate=self.fps)
        self.stream.pix_fmt = 'yuv420p'
        self.stream.options = {'crf': '23', 'preset': 'veryfast'}
        
        # 初始化 PipeWire 主循环
        self.pw_loop = libpw.pw_main_loop_new(b"recorder-loop")
        self.pw_core_loop = libpw.pw_main_loop_get_loop(self.pw_loop)

    def _on_process(self, user_data):
        """PipeWire 帧处理回调 (C 函数指针)"""
        if not self.running:
            return 0
            
        # 出队缓冲区
        buf = libpw.pw_stream_dequeue_buffer(self.pw_stream)
        if not buf:
            return 0
            
        try:
            # 解析 spa_buffer 结构 (高度依赖系统 ABI，此处为通用 64位 Linux 偏移)
            # struct pw_buffer { struct spa_buffer *buffer; ... }
            spa_buf_ptr = ctypes.cast(buf, ctypes.POINTER(ctypes.c_void_p))[0]
            
            # struct spa_buffer { uint32_t n_datas; uint32_t n_metas; void *metas; struct spa_data *datas; }
            # 在 64 位系统上，datas 指针通常在偏移 16 字节处 (4+4+8)
            datas_ptr_addr = ctypes.cast(spa_buf_ptr + 16, ctypes.POINTER(ctypes.c_void_p))[0]
            
            # struct spa_data { ... void *data; ... uint32_t chunk_offset; uint32_t chunk_size; ... }
            # data 指针通常在偏移 24 字节处，chunk_size 在偏移 40 字节处 (具体视 spa_data 版本而定)
            # 这里我们假设数据是连续的 RGBA 内存映射
            data_ptr = ctypes.cast(datas_ptr_addr + 24, ctypes.POINTER(ctypes.c_void_p))[0]
            chunk_size = ctypes.cast(datas_ptr_addr + 40, ctypes.POINTER(ctypes.c_uint32))[0]
            
            if self.width > 0 and self.height > 0 and data_ptr and chunk_size > 0:
                # 计算 RGBA 帧大小
                expected_size = self.width * self.height * 4
                
                # 从 C 指针直接拷贝内存到 Python bytes (零拷贝优化可用 memoryview，但为兼容性使用 bytes)
                frame_data = ctypes.string_at(data_ptr, min(chunk_size, expected_size))
                
                if len(frame_data) == expected_size:
                    # 创建 PyAV 视频帧 (RGBA)
                    frame = av.VideoFrame(width=self.width, height=self.height, format='rgba')
                    frame.planes[0].update(frame_data)
                    
                    # 转换为 YUV420P 并编码
                    yuv_frame = frame.reformat(format='yuv420p')
                    yuv_frame.pts = self.frame_count
                    yuv_frame.time_base = self.stream.time_base
                    
                    for packet in self.stream.encode(yuv_frame):
                        self.container.mux(packet)
                        
                    self.frame_count += 1
                    if self.frame_count % 30 == 0:
                        print(f"⏺ 已录制 {self.frame_count} 帧 ({self.width}x{self.height})", end='\r')
        except Exception as e:
            print(f"\n⚠️ 帧处理异常: {e}")
        finally:
            # 重新入队缓冲区
            libpw.pw_stream_queue_buffer(self.pw_stream, buf)
            
        return 0

    def _on_param_changed(self, user_data, id, param):
        """处理流参数变化 (动态获取分辨率)"""
        # id == 3 表示 SPA_PARAM_Format
        if id == 3 and param:
            # 简化的格式解析：尝试从 spa_pod 提取宽高
            # 真实场景应使用 spa_format_video_raw_parse，这里通过内存特征匹配
            try:
                pod_data = ctypes.string_at(param, 256)
                # 搜索常见的分辨率特征 (这是一个 hack，生产环境需完整实现 SPA POD 解析)
                # 这里为了演示，我们假设默认 1920x1080 或从外部获取
                if self.width == 0:
                    print("\n🔍 检测到视频流，默认设定为 1920x1080 (动态解析 SPA POD 需额外 C 绑定)")
                    self.width = 1920
                    self.height = 1080
                    self.stream.width = self.width
                    self.stream.height = self.height
            except:
                pass

    def setup_and_run(self):
        """配置 PipeWire 流并启动主循环"""
        # 定义 pw_stream_events 结构体 (C ABI)
        class pw_stream_events(ctypes.Structure):
            _fields_ = [
                ("version", ctypes.c_uint32),
                ("destroy", ctypes.c_void_p),
                ("state_changed", ctypes.c_void_p),
                ("control_info", ctypes.c_void_p),
                ("io_changed", ctypes.c_void_p),
                ("param_changed", ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p)),
                ("add_buffer", ctypes.c_void_p),
                ("remove_buffer", ctypes.c_void_p),
                ("process", ctypes.CFUNCTYPE(None, ctypes.c_void_p)),
            ]

        # 绑定 C 回调函数 (必须保存引用防止被 GC 回收)
        self.c_process = ctypes.CFUNCTYPE(None, ctypes.c_void_p)(self._on_process)
        self.c_param_changed = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p)(self._on_param_changed)

        events = pw_stream_events()
        events.version = 3  # PW_VERSION_STREAM_EVENTS
        events.process = self.c_process
        events.param_changed = self.c_param_changed

        # 创建流
        self.pw_stream = libpw.pw_stream_new_simple(
            self.pw_core_loop, b"python-screencast", None, 
            ctypes.byref(events), None
        )
        if not self.pw_stream:
            raise RuntimeError("PipeWire 流创建失败")

        # 连接流 (INPUT 方向，AUTOCONNECT | MAP_BUFFERS)
        flags = 0x0004 | 0x0008  # PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS
        res = libpw.pw_stream_connect(
            self.pw_stream, 1, self.node_id, flags, None, 0
        )
        if res < 0:
            raise RuntimeError(f"PipeWire 流连接失败 (错误码: {res})")

        print(f"\n▶ 开始录制... (按 Ctrl+C 停止)")
        try:
            # 阻塞运行 PipeWire 事件循环
            libpw.pw_main_loop_run(self.pw_loop)
        except KeyboardInterrupt:
            print("\n\n⏹ 正在停止录制并封装视频...")
        finally:
            self.stop()

    def stop(self):
        """清理资源并保存视频"""
        self.running = False
        if hasattr(self, 'pw_loop'):
            libpw.pw_main_loop_quit(self.pw_loop)
            
        # 刷新编码器缓冲
        if self.stream and self.container:
            for packet in self.stream.encode():
                self.container.mux(packet)
            self.container.close()
            
        print(f"✅ 录制完成! 共 {self.frame_count} 帧")
        print(f"📁 保存路径: {Path(self.output_file).resolve()}")

# ====================== 4. 主控制流程 ======================
async def main():
    if os.getenv("XDG_SESSION_TYPE") != "wayland":
        sys.exit("❌ 错误: 必须在 Wayland 会话中运行!")

    # 1. 连接 D-Bus 会话总线
    bus = await MessageBus(bus_type=BusType.SESSION).connect()
    portal = PortalSession(bus)

    try:
        # 2. 执行 Portal 交互流程 (创建会话 -> 选择源 -> 启动并获取 Node ID)
        await portal.create_session()
        await portal.select_sources()
        node_id = await portal.start_and_get_node_id()
        
        # 3. 将 Node ID 传递给 PipeWire 录制器
        recorder = PipeWireRecorder(node_id, "wayland_capture.mp4")
        
        # 4. 启动 PipeWire 事件循环 (此处会阻塞直到 Ctrl+C)
        # 注意：由于 pw_main_loop_run 是 C 级别的阻塞，会接管线程
        # 在纯 Python 中，我们直接调用它，Ctrl+C 会触发 KeyboardInterrupt
        recorder.setup_and_run()
        
    except asyncio.TimeoutError:
        print("\n❌ 等待用户授权超时 (60秒)")
    except Exception as e:
        print(f"\n❌ 运行时错误: {e}")
    finally:
        bus.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
