#!/usr/bin/env python3
"""
Wayland 窗口捕获录制器 (纯 Python + ctypes + dbus-next + PyAV)
- 修复了 GNOME 下无弹窗问题 (强制环境变量 + 预注册信号监听)
- 严格遵循 xdg-desktop-portal 异步 Request/Response 协议
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

# ====================== 0. 强制校验环境变量 (关键修复) ======================
# 确保 Portal 知道我们在 GNOME 环境下，否则它不会调用 gnome 后端弹窗
current_desktop = os.environ.get('XDG_CURRENT_DESKTOP', '')
if 'GNOME' not in current_desktop.upper() and 'UBUNTU' not in current_desktop.upper():
    print(f"⚠️ 警告: XDG_CURRENT_DESKTOP='{current_desktop}'，强制设置为 'GNOME' 以确保弹窗正常")
    os.environ['XDG_CURRENT_DESKTOP'] = 'GNOME'

# ====================== 1. PipeWire C API 绑定 ======================
class pw_main_loop(ctypes.Structure): pass
class pw_stream(ctypes.Structure): pass
class pw_buffer(ctypes.Structure): pass
class spa_buffer(ctypes.Structure): pass
class spa_data(ctypes.Structure): pass
class spa_pod(ctypes.Structure): pass

try:
    libpw = ctypes.CDLL("libpipewire-0.3.so.0")
except OSError:
    sys.exit("❌ PipeWire 库未找到! 请安装: sudo apt install libpipewire-0.3-dev")

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
libpw.pw_stream_new_simple.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
libpw.pw_stream_new_simple.restype = ctypes.POINTER(pw_stream)
libpw.pw_stream_connect.argtypes = [ctypes.POINTER(pw_stream), ctypes.c_int, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.POINTER(spa_pod)), ctypes.c_uint32]
libpw.pw_stream_connect.restype = ctypes.c_int
libpw.pw_stream_dequeue_buffer.argtypes = [ctypes.POINTER(pw_stream)]
libpw.pw_stream_dequeue_buffer.restype = ctypes.POINTER(pw_buffer)
libpw.pw_stream_queue_buffer.argtypes = [ctypes.POINTER(pw_stream), ctypes.POINTER(pw_buffer)]
libpw.pw_stream_queue_buffer.restype = ctypes.c_int

libpw.pw_init(None, None)

# ====================== 2. xdg-desktop-portal D-Bus 交互 ======================
class PortalSession:
    def __init__(self, bus):
        self.bus = bus
        # 提取 sender name (将 :1.123 转换为 1_123)
        self.sender = self.bus.unique_name.replace('.', '_').replace(':', '_')[1:]
        self.token_counter = 0
        self.session_handle = None

    def _get_unique_token(self):
        """生成合法的 D-Bus 对象路径元素 (必须以字母开头)"""
        self.token_counter += 1
        return f"pytoken{self.token_counter}"

    async def _call_and_wait(self, method, signature, body):
        """
        核心修复：在发送请求【之前】预先注册全局信号监听器，
        彻底解决信号竞态条件和 dbus-next 消息拦截问题。
        """
        token = self._get_unique_token()
        expected_path = f"/org/freedesktop/portal/desktop/request/{self.sender}/{token}"
        
        # 强制注入 handle_token 到 options 字典 (body 的最后一个元素)
        if isinstance(body[-1], dict):
            body[-1]['handle_token'] = Variant('s', token)

        response_event = asyncio.Event()
        response_data = {}

        # 1. 定义全局消息拦截器 (必须在发送请求前注册)
        def signal_handler(msg):
            # 必须显式检查 MessageType.SIGNAL，并返回 False 放行消息
            if msg.message_type != MessageType.SIGNAL:
                return False
                
            # 匹配 Request 接口的 Response 信号
            if (msg.interface == 'org.freedesktop.portal.Request' and 
                msg.member == 'Response' and 
                msg.path == expected_path):
                
                response_code = msg.body[0]
                if response_code == 0:
                    # 成功：提取字典数据
                    response_data.update({k: v.value for k, v in msg.body[1].items()})
                    print(f"   [D-Bus] 收到成功响应: {list(response_data.keys())}")
                else:
                    print(f"   [D-Bus] ⚠️ Portal 返回错误码: {response_code} (用户取消或后端失败)")
                response_event.set()
                
            return False # 关键：返回 False 允许消息继续传递

        # 2. 预先注册监听器
        self.bus.add_message_handler(signal_handler)

        try:
            # 3. 发送方法调用
            print(f"   [D-Bus] 发送 {method} 请求，预期响应路径: {expected_path}")
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
                raise RuntimeError(f"Portal D-Bus 调用被拒绝: {reply.error_name} - {reply.body}")
            
            print(f"   [D-Bus] 请求已受理，等待系统弹窗/信号响应...")

            # 4. 等待信号触发 (超时 120 秒，给用户足够时间点击)
            await asyncio.wait_for(response_event.wait(), timeout=120.0)
            return response_data
            
        except asyncio.TimeoutError:
            raise TimeoutError(f"等待 {method} 响应超时。请检查系统是否弹出了授权窗口，或尝试重启 xdg-desktop-portal 服务。")
        finally:
            # 5. 清理监听器
            self.bus.remove_message_handler(signal_handler)

    async def create_session(self):
        print("🔹 1/3 创建捕获会话...")
        session_token = f"pysession{self.token_counter}"
        options = {
            'session_handle_token': Variant('s', session_token)
        }
        res = await self._call_and_wait('CreateSession', 'a{sv}', [options])
        self.session_handle = res['session_handle']
        print(f"   ✅ 会话已建立: {self.session_handle}")

    async def select_sources(self):
        print("🔹 2/3 选择捕获源 (窗口模式)...")
        options = {
            'types': Variant('u', 1),        # 1 = WINDOW (窗口)
            'cursor_mode': Variant('u', 1),  # 1 = HIDDEN
            'multiple': Variant('b', False)
        }
        await self._call_and_wait('SelectSources', 'oa{sv}', [self.session_handle, options])
        print("   ✅ 捕获源已选择")

    async def start_and_get_node_id(self):
        print("🔹 3/3 启动捕获 (请在弹出的系统窗口中选择目标窗口并点击分享)...")
        options = {}
        res = await self._call_and_wait('Start', 'osa{sv}', [self.session_handle, "", options])
        
        streams = res.get('streams', [])
        if not streams:
            raise RuntimeError("未获取到视频流，用户可能取消了授权或后端未正确返回数据")
            
        node_id = streams[0][0]
        print(f"   ✅ 授权成功! 获取到 PipeWire Node ID: {node_id}")
        return node_id

# ====================== 3. PipeWire 流处理与视频编码 ======================
class PipeWireRecorder:
    def __init__(self, node_id, output_file="output.mp4"):
        self.node_id = node_id
        self.output_file = output_file
        self.running = True
        self.frame_count = 0
        self.width = 0
        self.height = 0
        self.fps = 30
        
        self.container = av.open(self.output_file, mode='w')
        self.stream = self.container.add_stream('h264', rate=self.fps)
        self.stream.pix_fmt = 'yuv420p'
        self.stream.options = {'crf': '23', 'preset': 'veryfast'}
        
        self.pw_loop = libpw.pw_main_loop_new(b"recorder-loop")
        self.pw_core_loop = libpw.pw_main_loop_get_loop(self.pw_loop)

    def _on_process(self, user_data):
        if not self.running:
            return 0
        buf = libpw.pw_stream_dequeue_buffer(self.pw_stream)
        if not buf:
            return 0
        try:
            spa_buf_ptr = ctypes.cast(buf, ctypes.POINTER(ctypes.c_void_p))[0]
            datas_ptr_addr = ctypes.cast(spa_buf_ptr + 16, ctypes.POINTER(ctypes.c_void_p))[0]
            data_ptr = ctypes.cast(datas_ptr_addr + 24, ctypes.POINTER(ctypes.c_void_p))[0]
            chunk_size = ctypes.cast(datas_ptr_addr + 40, ctypes.POINTER(ctypes.c_uint32))[0]
            
            if self.width > 0 and self.height > 0 and data_ptr and chunk_size > 0:
                expected_size = self.width * self.height * 4
                frame_data = ctypes.string_at(data_ptr, min(chunk_size, expected_size))
                if len(frame_data) == expected_size:
                    frame = av.VideoFrame(width=self.width, height=self.height, format='rgba')
                    frame.planes[0].update(frame_data)
                    yuv_frame = frame.reformat(format='yuv420p')
                    yuv_frame.pts = self.frame_count
                    yuv_frame.time_base = self.stream.time_base
                    for packet in self.stream.encode(yuv_frame):
                        self.container.mux(packet)
                    self.frame_count += 1
                    if self.frame_count % 30 == 0:
                        print(f"⏺ 已录制 {self.frame_count} 帧 ({self.width}x{self.height})", end='\r')
        except Exception as e:
            pass
        finally:
            libpw.pw_stream_queue_buffer(self.pw_stream, buf)
        return 0

    def _on_param_changed(self, user_data, id, param):
        if id == 3 and param and self.width == 0:
            print("\n🔍 检测到视频流，设定为 1920x1080")
            self.width = 1920
            self.height = 1080
            self.stream.width = self.width
            self.stream.height = self.height

    def setup_and_run(self):
        class pw_stream_events(ctypes.Structure):
            _fields_ = [
                ("version", ctypes.c_uint32), ("destroy", ctypes.c_void_p),
                ("state_changed", ctypes.c_void_p), ("control_info", ctypes.c_void_p),
                ("io_changed", ctypes.c_void_p),
                ("param_changed", ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p)),
                ("add_buffer", ctypes.c_void_p), ("remove_buffer", ctypes.c_void_p),
                ("process", ctypes.CFUNCTYPE(None, ctypes.c_void_p)),
            ]

        self.c_process = ctypes.CFUNCTYPE(None, ctypes.c_void_p)(self._on_process)
        self.c_param_changed = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p)(self._on_param_changed)

        events = pw_stream_events()
        events.version = 3
        events.process = self.c_process
        events.param_changed = self.c_param_changed

        self.pw_stream = libpw.pw_stream_new_simple(self.pw_core_loop, b"python-screencast", None, ctypes.byref(events), None)
        if not self.pw_stream:
            raise RuntimeError("PipeWire 流创建失败")

        flags = 0x0004 | 0x0008
        res = libpw.pw_stream_connect(self.pw_stream, 1, self.node_id, flags, None, 0)
        if res < 0:
            raise RuntimeError(f"PipeWire 流连接失败 (错误码: {res})")

        print(f"\n▶ 开始录制... (按 Ctrl+C 停止)")
        try:
            libpw.pw_main_loop_run(self.pw_loop)
        except KeyboardInterrupt:
            print("\n\n⏹ 正在停止录制并封装视频...")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        if hasattr(self, 'pw_loop'):
            libpw.pw_main_loop_quit(self.pw_loop)
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

    bus = await MessageBus(bus_type=BusType.SESSION).connect()
    portal = PortalSession(bus)

    try:
        await portal.create_session()
        await portal.select_sources()
        node_id = await portal.start_and_get_node_id()
        
        recorder = PipeWireRecorder(node_id, "wayland_capture.mp4")
        recorder.setup_and_run()
        
    except asyncio.TimeoutError as e:
        print(f"\n❌ 超时错误: {e}")
        print("💡 提示: 如果系统没有弹窗，请尝试在终端执行: systemctl --user restart xdg-desktop-portal xdg-desktop-portal-gnome")
    except Exception as e:
        print(f"\n❌ 运行时错误: {e}")
    finally:
        bus.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
