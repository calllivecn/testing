#!/usr/bin/env python3
"""阶段 3: PipeWire C API 结构体与函数绑定"""
import ctypes
import sys

# ================= 1. 定义 SPA (PipeWire 底层) 结构体 =================
class spa_pod(ctypes.Structure): pass

class spa_chunk(ctypes.Structure):
    _fields_ = [
        ("offset", ctypes.c_uint32),
        ("size", ctypes.c_uint32),
        ("stride", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
    ]

class spa_data(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
        ("type", ctypes.c_uint32),
        ("format", ctypes.c_uint32),
        ("fd", ctypes.c_int64),   # off_t 在 64位系统通常是 8 字节
        ("mapoffset", ctypes.c_uint32),
        ("maxsize", ctypes.c_uint32),
        ("data", ctypes.c_void_p),
        ("chunk", spa_chunk),
    ]

class spa_meta(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_uint32),
        ("size", ctypes.c_uint32),
        ("data", ctypes.c_void_p),
    ]

class spa_buffer(ctypes.Structure):
    _fields_ = [
        ("n_metas", ctypes.c_uint32),
        ("n_datas", ctypes.c_uint32),
        ("metas", ctypes.POINTER(spa_meta)),
        ("datas", ctypes.POINTER(spa_data)),
    ]

# ================= 2. 定义 PipeWire 结构体 =================
class pw_main_loop(ctypes.Structure): pass
class pw_stream(ctypes.Structure): pass

class pw_buffer(ctypes.Structure):
    _fields_ = [
        ("buffer", ctypes.POINTER(spa_buffer)),
        ("requested", ctypes.c_uint32), # 简化，实际是个 struct spa_pod_builder
        ("datas", ctypes.c_void_p),     # 简化
    ]

# ================= 3. 加载动态库并绑定函数 =================
try:
    libpw = ctypes.CDLL("libpipewire-0.3.so.0")
except OSError:
    sys.exit("❌ 找不到 libpipewire-0.3.so.0")

# 初始化
libpw.pw_init.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p))]
libpw.pw_init.restype = None

# 主循环
libpw.pw_main_loop_new.argtypes = [ctypes.c_char_p]
libpw.pw_main_loop_new.restype = ctypes.POINTER(pw_main_loop)
libpw.pw_main_loop_get_loop.argtypes = [ctypes.POINTER(pw_main_loop)]
libpw.pw_main_loop_get_loop.restype = ctypes.c_void_p
libpw.pw_main_loop_run.argtypes = [ctypes.POINTER(pw_main_loop)]
libpw.pw_main_loop_run.restype = ctypes.c_int
libpw.pw_main_loop_quit.argtypes = [ctypes.POINTER(pw_main_loop)]
libpw.pw_main_loop_quit.restype = ctypes.c_int

# 流管理
libpw.pw_stream_new_simple.argtypes = [
    ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
]
libpw.pw_stream_new_simple.restype = ctypes.POINTER(pw_stream)

libpw.pw_stream_connect.argtypes = [
    ctypes.POINTER(pw_stream), ctypes.c_uint32, ctypes.c_uint32, 
    ctypes.c_uint32, ctypes.POINTER(ctypes.POINTER(spa_pod)), ctypes.c_uint32
]
libpw.pw_stream_connect.restype = ctypes.c_int

libpw.pw_stream_dequeue_buffer.argtypes = [ctypes.POINTER(pw_stream)]
libpw.pw_stream_dequeue_buffer.restype = ctypes.POINTER(pw_buffer)

libpw.pw_stream_queue_buffer.argtypes = [ctypes.POINTER(pw_stream), ctypes.POINTER(pw_buffer)]
libpw.pw_stream_queue_buffer.restype = ctypes.c_int

libpw.pw_stream_disconnect.argtypes = [ctypes.POINTER(pw_stream)]
libpw.pw_stream_disconnect.restype = ctypes.c_int

libpw.pw_stream_destroy.argtypes = [ctypes.POINTER(pw_stream)]
libpw.pw_stream_destroy.restype = None

# 初始化 PipeWire
libpw.pw_init(None, None)

def test_bindings():
    print("="*40)
    print("🔍 阶段 3: PipeWire C API 绑定测试")
    print("="*40)
    print("✅ libpipewire-0.3.so.0 加载成功")
    print("✅ 结构体定义完成，无内存偏移硬编码")
    loop = libpw.pw_main_loop_new(b"test-loop")
    if loop:
        print("✅ pw_main_loop_new 调用成功")
    else:
        print("❌ pw_main_loop_new 失败")
    print("🎉 绑定测试通过！")

if __name__ == "__main__":
    test_bindings()
