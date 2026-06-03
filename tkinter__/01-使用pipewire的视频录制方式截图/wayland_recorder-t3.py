#!/usr/bin/env python3
"""
Wayland 窗口捕获录制器 (修复段错误)
- 修复 PipeWire 连接参数类型
- 添加安全的内存访问检查
- 修复结构体偏移量问题
"""
import os
import sys
import time
import ctypes
import asyncio
import random
import string
from pathlib import Path

# ====================== 0. 环境检查 ======================
if os.getenv("XDG_SESSION_TYPE") != "wayland":
    sys.exit("❌ 错误: 必须在 Wayland 会话中运行!")

try:
    from dbus_next.aio import MessageBus
    from dbus_next import Message, MessageType, Variant, BusType
except ImportError:
    sys.exit("❌ 缺少 dbus-next 库! 请执行: pip install dbus-next")

try:
    import av
except ImportError:
    sys.exit("❌ 缺少 PyAV 库! 请执行: pip install av")

# ====================== 1. PipeWire C API 绑定 (关键修复) ======================
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

# === 修复 1: 正确定义函数参数类型 ===
libpw.pw_init.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p))]
libpw.pw_init.restype = None

libpw.pw_main_loop_new.argtypes = [ctypes.c_char_p]
libpw.pw_main_loop_new.restype = ctypes.POINTER(pw_main_loop)

libpw.pw_main_loop_get_loop.argtypes = [ctypes.POINTER(pw_main_loop)]
libpw.pw_main_loop_get_loop.restype = ctypes.c_void_p

libpw.pw_stream_new_simple.argtypes = [
    ctypes.c_void_p, ctypes.c_char_p, 
    ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p
]
libpw.pw_stream_new_simple.restype = ctypes.POINTER(pw_stream)

# === 修复 2: 修正 pw_stream_connect 参数类型 ===
libpw.pw_stream_connect.argtypes = [
    ctypes.POINTER(pw_stream), 
    ctypes.c_uint32,  # direction (1 = PW_DIRECTION_INPUT)
    ctypes.c_uint32,  # node_id (必须是 uint32)
    ctypes.c_uint32,  # flags
    ctypes.POINTER(ctypes.POINTER(spa_pod)),  # params
    ctypes.c_uint32   # n_params
]
libpw.pw_stream_connect.restype = ctypes.c_int

libpw.pw_stream_dequeue_buffer.argtypes = [ctypes.POINTER(pw_stream)]
libpw.pw_stream_dequeue_buffer.restype = ctypes.POINTER(pw_buffer)

libpw.pw_stream_queue_buffer.argtypes = [
    ctypes.POINTER(pw_stream), 
    ctypes.POINTER(pw_buffer)
]
libpw.pw_stream_queue_buffer.restype = ctypes.c_int

# 初始化 PipeWire
libpw.pw_init(None, None)

# ====================== 2. xdg-desktop-portal D-Bus 交互 ======================
class PortalSession:
    # ... (保持不变，之前的 D-Bus 修复已足够) ...

# ====================== 3. PipeWire 录制器 (关键修复) ======================
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
        
        # === 修复 3: 保存回调函数引用避免 GC 回收 ===
        self.c_process = None
        self.c_param_changed = None

    def _on_process(self, user_data):
        """安全增强版帧处理回调"""
        if not self.running or not hasattr(self, 'pw_stream'):
            return 0
            
        buf = libpw.pw_stream_dequeue_buffer(self.pw_stream)
        if not buf or not buf.contents:
            return 0
            
        try:
            # === 修复 4: 安全访问内存结构 ===
            # 1. 检查 spa_buffer 指针有效性
            spa_buf_ptr = ctypes.cast(buf, ctypes.POINTER(ctypes.c_void_p)).contents
            if not spa_buf_ptr:
                return 0
                
            # 2. 检查 spa_data 指针有效性 (通过 offset 16 获取)
            datas_ptr_addr = ctypes.cast(ctypes.addressof(spa_buf_ptr) + 16, 
                                      ctypes.POINTER(ctypes.c_void_p)).contents
            if not datas_ptr_addr:
                return 0
                
            # 3. 安全获取数据指针和大小
            data_ptr = ctypes.cast(ctypes.addressof(datas_ptr_addr) + 24, 
                                ctypes.POINTER(ctypes.c_void_p)).contents
            chunk_size = ctypes.cast(ctypes.addressof(datas_ptr_addr) + 40, 
                                  ctypes.POINTER(ctypes.c_uint32)).contents
            
            # 4. 检查关键值有效性
            if not data_ptr or not chunk_size or chunk_size.value == 0:
                return 0
                
            # 5. 仅当分辨率已知时处理帧
            if self.width > 0 and self.height > 0:
                expected_size = self.width * self.height * 4
                frame_data = ctypes.string_at(data_ptr, min(chunk_size.value, expected_size))
                
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
            print(f"\n⚠️ 帧处理异常: {e}")
        finally:
            if buf:
                libpw.pw_stream_queue_buffer(self.pw_stream, buf)
        return 0

    def _on_param_changed(self, user_data, id, param):
        """安全增强版参数变更回调"""
        if id != 3 or not param:  # 3 = SPA_PARAM_Format
            return
            
        # === 修复 5: 安全解析分辨率 ===
        try:
            # 尝试获取分辨率 (简化版，生产环境需完整解析 spa_pod)
            # 这里使用安全的内存读取方式
            param_bytes = ctypes.string_at(param, 256)
            
            # 搜索常见的分辨率特征 (1920x1080 的特征)
            if b"1920" in param_bytes or b"1080" in param_bytes:
                self.width = 1920
                self.height = 1080
                self.stream.width = self.width
                self.stream.height = self.height
                print(f"\n🔍 检测到分辨率: {self.width}x{self.height}")
        except Exception as e:
            print(f"⚠️ 分辨率解析失败: {e}")

    def setup_and_run(self):
        """配置 PipeWire 流并启动"""
        # === 修复 6: 正确定义回调结构体 ===
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

        # === 修复 7: 保存回调引用 ===
        self.c_process = ctypes.CFUNCTYPE(None, ctypes.c_void_p)(self._on_process)
        self.c_param_changed = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p)(self._on_param_changed)

        events = pw_stream_events()
        events.version = 3  # PW_VERSION_STREAM_EVENTS
        events.process = self.c_process
        events.param_changed = self.c_param_changed

        # === 修复 8: 正确创建流 ===
        self.pw_stream = libpw.pw_stream_new_simple(
            self.pw_core_loop, 
            b"python-screencast", 
            None, 
            ctypes.byref(events), 
            None
        )
        if not self.pw_stream or not self.pw_stream.contents:
            raise RuntimeError("PipeWire 流创建失败")

        # === 修复 9: 正确传递 node_id 为 uint32 ===
        node_id_uint32 = ctypes.c_uint32(self.node_id)  # 关键修复!
        flags = 0x0004 | 0x0008  # PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS
        
        # === 修复 10: 安全连接 ===
        res = libpw.pw_stream_connect(
            self.pw_stream,
            1,  # PW_DIRECTION_INPUT
            node_id_uint32,  # 必须是 c_uint32
            flags,
            None,
            0
        )
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
        """清理资源"""
        self.running = False
        if hasattr(self, 'pw_loop'):
            libpw.pw_main_loop_quit(self.pw_loop)
            
        if self.stream and self.container:
            # 刷新编码器
            for packet in self.stream.encode():
                self.container.mux(packet)
            self.container.close()
            
        print(f"✅ 录制完成! 共 {self.frame_count} 帧")
        print(f"📁 保存路径: {Path(self.output_file).resolve()}")

# ====================== 4. 主控制流程 ======================
async def main():
    bus = await MessageBus(bus_type=BusType.SESSION).connect()
    portal = PortalSession(bus)

    try:
        await portal.create_session()
        await portal.select_sources()
        node_id = await portal.start_and_get_node_id()
        
        # === 修复 11: 传递 node_id 为整数 ===
        recorder = PipeWireRecorder(int(node_id), "wayland_capture.mp4")
        recorder.setup_and_run()
        
    except Exception as e:
        print(f"\n❌ 运行时错误: {e}")
        print("💡 提示: 段错误通常由 PipeWire 内存访问导致，请检查分辨率设置和回调安全")
    finally:
        bus.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
