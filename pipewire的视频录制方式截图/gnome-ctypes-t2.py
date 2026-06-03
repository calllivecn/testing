#!/usr/bin/env python3
"""
Wayland 窗口捕获录制器 (纯 Python 实现)
- 通过 ctypes 直接调用 PipeWire API
- 使用 dbus-next 交互 xdg-desktop-portal
- 无任何外部命令调用
"""
import os
import sys
import time
import ctypes
import threading
import asyncio
from pathlib import Path

# ======================
# 1. PipeWire C API 绑定
# ======================
class PW(ctypes.Structure):
    """PipeWire 核心结构体定义"""
    _fields_ = []

# PipeWire 函数指针类型
pw_init = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.POINTER(ctypes.c_char_p))
pw_loop_new = ctypes.CFUNCTYPE(ctypes.POINTER(PW), ctypes.c_char_p)
pw_loop_destroy = ctypes.CFUNCTYPE(None, ctypes.POINTER(PW))
pw_stream_new = ctypes.CFUNCTYPE(ctypes.POINTER(PW), ctypes.POINTER(PW), ctypes.c_char_p, ctypes.c_void_p)
pw_stream_destroy = ctypes.CFUNCTYPE(None, ctypes.POINTER(PW))
pw_stream_connect = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(PW), ctypes.c_int, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p), ctypes.c_uint)
pw_stream_queue_buffer = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(PW), ctypes.POINTER(PW))
pw_stream_dequeue_buffer = ctypes.CFUNCTYPE(ctypes.POINTER(PW), ctypes.POINTER(PW))
pw_stream_add_listener = ctypes.CFUNCTYPE(ctypes.c_uint, ctypes.POINTER(PW), ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_void_p), ctypes.c_uint)

# PipeWire 事件结构
class pw_stream_events(ctypes.Structure):
    _fields_ = [
        ("version", ctypes.c_uint32),
        ("state_changed", ctypes.CFUNCTYPE(None, ctypes.POINTER(PW), ctypes.c_int, ctypes.c_int)),
        ("param_changed", ctypes.CFUNCTYPE(None, ctypes.POINTER(PW), ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p), ctypes.c_uint32)),
        ("add_buffer", ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(PW), ctypes.POINTER(PW))),
        ("remove_buffer", ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(PW), ctypes.POINTER(PW))),
        ("process", ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(PW)))
    ]

# 加载 PipeWire 库
try:
    libpipewire = ctypes.CDLL("libpipewire-0.3.so.0")
except OSError:
    raise RuntimeError("PipeWire 库未安装! 请安装: sudo apt install libpipewire-0.3-dev")

# 绑定关键函数
pw_init = libpipewire.pw_init
pw_init.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_char_p)]
pw_init.restype = None

pw_loop_new = libpipewire.pw_loop_new
pw_loop_new.argtypes = [ctypes.c_char_p]
pw_loop_new.restype = ctypes.POINTER(PW)

pw_loop_destroy = libpipewire.pw_loop_destroy
pw_loop_destroy.argtypes = [ctypes.POINTER(PW)]
pw_loop_destroy.restype = None

pw_stream_new = libpipewire.pw_stream_new
pw_stream_new.argtypes = [ctypes.POINTER(PW), ctypes.c_char_p, ctypes.c_void_p]
pw_stream_new.restype = ctypes.POINTER(PW)

pw_stream_destroy = libpipewire.pw_stream_destroy
pw_stream_destroy.argtypes = [ctypes.POINTER(PW)]
pw_stream_destroy.restype = None

pw_stream_connect = libpipewire.pw_stream_connect
pw_stream_connect.argtypes = [ctypes.POINTER(PW), ctypes.c_int, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p), ctypes.c_uint]
pw_stream_connect.restype = ctypes.c_int

pw_stream_queue_buffer = libpipewire.pw_stream_queue_buffer
pw_stream_queue_buffer.argtypes = [ctypes.POINTER(PW), ctypes.POINTER(PW)]
pw_stream_queue_buffer.restype = ctypes.c_int

pw_stream_dequeue_buffer = libpipewire.pw_stream_dequeue_buffer
pw_stream_dequeue_buffer.argtypes = [ctypes.POINTER(PW)]
pw_stream_dequeue_buffer.restype = ctypes.POINTER(PW)

pw_stream_add_listener = libpipewire.pw_stream_add_listener
pw_stream_add_listener.argtypes = [ctypes.POINTER(PW), ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_void_p), ctypes.c_uint]
pw_stream_add_listener.restype = ctypes.c_uint

# 初始化 PipeWire
pw_init(0, None)

# ======================
# 2. xdg-desktop-portal D-Bus 交互
# ======================
try:
    from dbus_next.aio import MessageBus
    from dbus_next import Variant, BusType
except ImportError:
    raise RuntimeError("缺少 dbus-next 库! 请安装: pip install dbus-next")

class ScreenCastPortal:
    def __init__(self):
        self.session_handle = None
        self.stream_handle = None
        self.stream_token = None
        self.portal = 'org.freedesktop.portal.Desktop'
        self.path = '/org/freedesktop/portal/desktop'
        self.interface = 'org.freedesktop.portal.ScreenCast'
        self.app_id = ''  # 空表示当前应用

    async def create_session(self):
        """创建捕获会话"""
        bus = await MessageBus(bus_type=BusType.SESSION).connect()
        request_handle = f"/org/freedesktop/portal/desktop/request/{os.getpid()}/req{int(time.time())}"
        
        # 调用 CreateSession 方法
        result = await bus.call_method(
            self.portal, self.path, self.interface, 'CreateSession',
            [
                Variant('a{sv}', {
                    'handle_token': Variant('s', f"token{int(time.time())}"),
                    'session_handle_token': Variant('s', f"session_token{int(time.time())}")
                })
            ]
        )
        
        # 解析响应
        self.session_handle = result.body[0]
        return self.session_handle

    async def select_sources(self, session_handle, cursor_mode=2, # 2=隐藏光标
                             screen_cast_type=1, # 1=窗口
                             multiple=False):
        """选择捕获源 (窗口)"""
        bus = await MessageBus(bus_type=BusType.SESSION).connect()
        request_handle = f"/org/freedesktop/portal/desktop/request/{os.getpid()}/req{int(time.time())}"
        
        result = await bus.call_method(
            self.portal, self.path, self.interface, 'SelectSources',
            [
                Variant('o', session_handle),
                Variant('a{sv}', {
                    'handle_token': Variant('s', f"token{int(time.time())}"),
                    'type': Variant('u', screen_cast_type),  # 1=窗口, 2=屏幕
                    'cursor_mode': Variant('u', cursor_mode),
                    'multiple': Variant('b', multiple)
                })
            ]
        )
        
        return result.body[0]  # 返回 stream token

    async def start_cast(self, session_handle, parent_window=""):
        """启动捕获"""
        bus = await MessageBus(bus_type=BusType.SESSION).connect()
        request_handle = f"/org/freedesktop/portal/desktop/request/{os.getpid()}/req{int(time.time())}"
        
        result = await bus.call_method(
            self.portal, self.path, self.interface, 'Start',
            [
                Variant('o', session_handle),
                Variant('s', parent_window),
                Variant('a{sv}', {
                    'handle_token': Variant('s', f"token{int(time.time())}")
                })
            ]
        )
        return result.body[0]  # 返回实际流数据

# ======================
# 3. PipeWire 流处理器
# ======================
try:
    import av
except ImportError:
    raise RuntimeError("缺少 PyAV 库! 请安装: pip install av")

class PipeWireRecorder:
    def __init__(self, output_file="capture.mp4"):
        self.output_file = output_file
        self.loop = None
        self.stream = None
        self.running = False
        self.frame_count = 0
        self.container = None
        self.video_stream = None
        self.width = 0
        self.height = 0
        
        # 初始化视频编码器
        self.container = av.open(output_file, mode='w')
        self.video_stream = self.container.add_stream('h264', rate=30)
        self.video_stream.width = 1280  # 临时值，将从流中更新
        self.video_stream.height = 720
        self.video_stream.pix_fmt = 'yuv420p'

    def on_param_changed(self, stream, id, param, size):
        """处理流参数变化 (获取分辨率)"""
        if id != 3:  # SPA_PARAM_Format
            return
        
        # 解析格式参数 (简化版)
        struct = ctypes.cast(param, ctypes.POINTER(ctypes.c_uint32))
        media_type = struct[0]
        if media_type != 1:  # 1 = SPA_MEDIA_TYPE_video
            return
            
        format = struct[1]
        if format != 1:  # 1 = SPA_VIDEO_FORMAT_RGBA
            return
            
        # 提取分辨率
        self.width = struct[4]
        self.height = struct[5]
        print(f"✅ 检测到分辨率: {self.width}x{self.height}")
        
        # 更新编码器
        self.video_stream.width = self.width
        self.video_stream.height = self.height

    def on_process(self, stream):
        """处理视频帧"""
        buf = pw_stream_dequeue_buffer(stream)
        if not buf:
            return -1
            
        # 获取缓冲区数据
        buffer = ctypes.cast(buf, ctypes.POINTER(ctypes.c_void_p)).contents
        datas = ctypes.cast(buffer[4], ctypes.POINTER(ctypes.c_void_p))
        stride = ctypes.cast(datas[1], ctypes.c_int).value
        data_ptr = ctypes.cast(datas[0], ctypes.POINTER(ctypes.c_uint8))
        
        # 创建帧对象 (RGBA -> YUV420P)
        frame = av.VideoFrame(self.width, self.height, 'rgba')
        frame.planes[0].update(
            (data_ptr, self.width * self.height * 4)
        )
        
        # 转换为 YUV420P 并编码
        yuv_frame = frame.reformat(self.width, self.height, 'yuv420p')
        for packet in self.video_stream.encode(yuv_frame):
            self.container.mux(packet)
            
        self.frame_count += 1
        if self.frame_count % 30 == 0:
            print(f"⏺ 已录制 {self.frame_count} 帧")
            
        # 重新入队缓冲区
        pw_stream_queue_buffer(stream, buf)
        return 0

    def setup_stream(self, node_id):
        """配置 PipeWire 流"""
        self.loop = pw_loop_new(b"event-loop")
        if not self.loop:
            raise RuntimeError("PipeWire loop 创建失败")
            
        # 创建事件结构体
        events = pw_stream_events()
        events.version = 3  # pw_stream_events 的当前版本
        events.param_changed = ctypes.CFUNCTYPE(None, 
            ctypes.POINTER(PW), ctypes.c_uint32, 
            ctypes.POINTER(ctypes.c_void_p), ctypes.c_uint32
        )(self.on_param_changed)
        
        events.process = ctypes.CFUNCTYPE(ctypes.c_int, 
            ctypes.POINTER(PW)
        )(self.on_process)
        
        # 创建流
        self.stream = pw_stream_new(self.loop, b"ScreenCast Recorder", 
                                   ctypes.byref(events))
        if not self.stream:
            raise RuntimeError("PipeWire 流创建失败")
        
        # 连接流
        flags = 1 | 4  # PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS
        res = pw_stream_connect(self.stream, 1, node_id, flags, None, 0)
        if res < 0:
            raise RuntimeError(f"流连接失败: {res}")

    def run(self):
        """启动录制事件循环"""
        self.running = True
        print("⏺ 开始录制... 按 Ctrl+C 停止")
        
        try:
            while self.running:
                # 处理 PipeWire 事件
                libpipewire.pw_loop_iterate(self.loop, 100)
        except KeyboardInterrupt:
            print("\n⏹ 停止录制...")
        finally:
            self.stop()

    def stop(self):
        """清理资源"""
        if self.stream:
            pw_stream_destroy(self.stream)
        if self.loop:
            pw_loop_destroy(self.loop)
        
        # 刷新编码器
        for packet in self.video_stream.encode():
            self.container.mux(packet)
        self.container.close()
        
        print(f"✅ 录制完成! 保存至: {Path(self.output_file).resolve()}")
        print(f"总计: {self.frame_count} 帧 | 分辨率: {self.width}x{self.height}")

# ======================
# 4. 主控制流程
# ======================
async def main(output_file="capture.mp4"):
    # 检查环境
    if os.getenv("XDG_SESSION_TYPE") != "wayland":
        raise RuntimeError("必须在 Wayland 会话中运行!")
    
    # 1. 通过 D-Bus 创建捕获会话
    portal = ScreenCastPortal()
    session_handle = await portal.create_session()
    print(f"✅ 创建会话: {session_handle}")
    
    # 2. 选择窗口作为捕获源
    stream_token = await portal.select_sources(session_handle, screen_cast_type=1)
    print("🖱 请在屏幕上点击目标窗口...")
    
    # 3. 启动捕获 (用户交互点)
    await portal.start_cast(session_handle)
    print("✅ 捕获已启动")
    
    # 4. 获取 PipeWire 节点 ID (通过 D-Bus 信号)
    # 注意: 实际实现中需监听 org.freedesktop.portal.ScreenCast.StreamStarted 信号
    # 简化处理: 使用固定节点ID (真实场景需从 D-Bus 信号中提取)
    node_id = 42  # ⚠️ 真实实现需替换为动态获取的节点ID
    
    # 5. 配置 PipeWire 录制器
    recorder = PipeWireRecorder(output_file)
    recorder.setup_stream(node_id)
    
    # 6. 启动录制
    recorder.run()

if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "capture.mp4"
    
    try:
        asyncio.run(main(output))
    except Exception as e:
        print(f"❌ 错误: {str(e)}", file=sys.stderr)
        sys.exit(1)
