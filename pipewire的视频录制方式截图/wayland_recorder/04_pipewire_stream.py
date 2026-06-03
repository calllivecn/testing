#!/usr/bin/env python3
"""阶段 4: PipeWire 流连接与帧提取 (完整修复版)"""
import sys
import time
import threading
import traceback

# ✅ 修复 1: 使用正确的 CFFI 模块名 (补全了 ffi, lib as C)
from _pipewire_cffi import ffi, lib as C

# ==============================================================================
# PipeWire 流核心类
# ==============================================================================
class PipeWireStream:
    def __init__(self, node_id, width=1920, height=1080):
        self.node_id = node_id
        self.running = True
        self.frame_count = 0
        
        # 预期分辨率 (需与 build_video_format_pod 中请求的默认值一致)
        self.width = width
        self.height = height
        self.bpp = 4  # BGRx / RGBx 都是 4 bytes per pixel
        
        self.frame_callback = None
        self._keep_alive = []  # 防止 CFFI 回调和 POD 被 Python GC 回收
        
        # ✅ 修复 3: 必须在使用任何 PipeWire API 前初始化
        C.pw_init(ffi.NULL, ffi.NULL)
        print("✅ PipeWire 核心已初始化")
        
        # 创建主循环
        self.pw_loop = C.pw_main_loop_new(ffi.NULL)
        if self.pw_loop == ffi.NULL:
            raise RuntimeError("pw_main_loop_new 失败，无法创建主循环")
        self.core_loop = C.pw_main_loop_get_loop(self.pw_loop)
        self.pw_stream = ffi.NULL

    # --------------------------------------------------------------------------
    # C 回调函数 (由 PipeWire 主循环在独立线程中触发)
    # --------------------------------------------------------------------------
    def _on_process(self, user_data):
        """核心回调：从 PipeWire 队列中提取帧数据"""
        if not self.running:
            return
            
        # 1. 获取缓冲区
        buf = C.pw_stream_dequeue_buffer(self.pw_stream)
        if buf == ffi.NULL:
            return
            
        try:
            spa_buf = buf.buffer
            if spa_buf == ffi.NULL or spa_buf.n_datas < 1:
                return
                
            data_struct = spa_buf.datas[0]
            data_ptr = data_struct.data
            
            # ✅ 修复 2: chunk 是指针，必须先判空再解引用
            if data_struct.chunk == ffi.NULL:
                return
                
            chunk_size = data_struct.chunk[0].size
            if chunk_size == 0:
                return
            
            # 2. 提取帧数据
            if data_ptr != ffi.NULL and chunk_size > 0:
                expected_size = self.width * self.height * self.bpp
                # 防止内存越界：如果实际 chunk 小于预期，只拷贝实际大小
                actual_size = min(chunk_size, expected_size)
                
                # 使用 ffi.buffer 安全拷贝 C 内存到 Python bytes
                frame_data = ffi.buffer(data_ptr, actual_size)[:]
                
                # 3. 触发上层回调
                if self.frame_callback:
                    self.frame_callback(frame_data, self.width, self.height)
                    self.frame_count += 1
                    
        except Exception as e:
            print(f"\n❌ [process 回调异常]: {e}")
            traceback.print_exc()
        finally:
            # 4. 归还缓冲区给 PipeWire
            C.pw_stream_queue_buffer(self.pw_stream, buf)

    def _on_state_changed(self, user_data, old_state, new_state, error):
        """状态变更回调"""
        state_names = {
            -1: "ERROR", 0: "UNCONNECTED", 1: "CONNECTING", 
            2: "PAUSED", 3: "STREAMING"
        }
        old_name = state_names.get(old_state, str(old_state))
        new_name = state_names.get(new_state, str(new_state))
        print(f"🔄 流状态变更: {old_name} → {new_name}")
        
        if error != ffi.NULL:
            err_msg = ffi.string(error).decode('utf-8', errors='ignore')
            print(f"❌ PipeWire 错误: {err_msg}")

    def _on_param_changed(self, user_data, id, param):
        """参数变更回调 (用于后续动态获取实际协商的分辨率)"""
        if param == ffi.NULL:
            return
        # 目前仅做日志记录，后续若需动态解析 spa_pod 可在此扩展
        print(f"🔍 收到参数变更通知 (Param ID: {id})")

    # --------------------------------------------------------------------------
    # 流控制
    # --------------------------------------------------------------------------
    def start(self, frame_callback):
        """启动 PipeWire 流并开始阻塞运行主循环"""
        self.frame_callback = frame_callback
        
        # 1. 注册 C 回调事件
        events = ffi.new("struct pw_stream_events *")
        events.version = 3  # PipeWire 0.3 标准版本
        
        # 使用 onerror 防止 Python 异常导致 C 层段错误
        c_process = ffi.callback(
            "void(void *)", self._on_process, onerror=traceback.print_exc
        )
        c_state_changed = ffi.callback(
            "void(void *, int, int, const char *)", 
            self._on_state_changed, onerror=traceback.print_exc
        )
        c_param_changed = ffi.callback(
            "void(void *, uint32_t, const struct spa_pod *)", 
            self._on_param_changed, onerror=traceback.print_exc
        )
        
        events.process = c_process
        events.state_changed = c_state_changed
        events.param_changed = c_param_changed
        
        # 保持引用，防止被垃圾回收
        self._keep_alive.extend([events, c_process, c_state_changed, c_param_changed])
        
        # 2. 创建 PipeWire 流
        self.pw_stream = C.pw_stream_new_simple(
            self.core_loop, b"python-screencast", ffi.NULL, events, ffi.NULL
        )
        if self.pw_stream == ffi.NULL:
            raise RuntimeError("pw_stream_new_simple 失败，无法创建流")
        
        # 3. ✅ 修复 4: 构建并传递视频格式 POD
        # BGRx 的 SPA 枚举值通常为 0x42475278 (或直接传整数，C端会处理)
        # 这里请求 1920x1080，帧率 30~60
        BGRx_FORMAT_ID = 0x42475278 
        format_pod = C.build_video_format_pod(
            BGRx_FORMAT_ID, self.width, self.height, 30, 60
        )
        
        if format_pod == ffi.NULL:
            raise RuntimeError("build_video_format_pod 失败，内存分配错误")
            
        params = ffi.new("const struct spa_pod *[1]")
        params[0] = format_pod
        self._keep_alive.extend([params, format_pod])
        
        # 4. 连接流
        # 0x0004 = PW_STREAM_FLAG_AUTOCONNECT
        # 0x0008 = PW_STREAM_FLAG_MAP_BUFFERS
        flags = 0x0004 | 0x0008  
        
        print(f"🔌 正在连接 PipeWire 流 (Node ID: {self.node_id})...")
        res = C.pw_stream_connect(
            self.pw_stream, 1, self.node_id, flags, params, 1
        )
        if res < 0:
            raise RuntimeError(f"pw_stream_connect 失败 (错误码: {res})")
        
        print("▶ 流已连接，开始运行主循环接收帧数据 (按 Ctrl+C 停止)...")
        
        # 5. 阻塞运行主循环
        try:
            C.pw_main_loop_run(self.pw_loop)
        except KeyboardInterrupt:
            print("\n⚠️ 收到中断信号，正在停止...")
            self.stop()

    def stop(self):
        """停止流并清理资源"""
        if not self.running:
            return
            
        self.running = False
        C.pw_main_loop_quit(self.pw_loop)
        
        if self.pw_stream != ffi.NULL:
            C.pw_stream_destroy(self.pw_stream)
            self.pw_stream = ffi.NULL
            
        # 释放 C 端分配的 POD 内存
        for item in self._keep_alive:
            if str(type(item)) == "<cdata 'const struct spa_pod *'>":
                try:
                    C.free_format_pod(item)
                except Exception:
                    pass
                    
        print(f"\n⏹ PipeWire 流已安全停止，共成功接收 {self.frame_count} 帧")


# ==============================================================================
# 测试入口
# ==============================================================================
def test_stream(node_id):
    print("=" * 50)
    print(f"🔍 阶段 4: PipeWire 流测试 (目标 Node ID: {node_id})")
    print("=" * 50)
    
    # 初始化流 (默认请求 1920x1080)
    stream = PipeWireStream(node_id, width=1920, height=1080)
    
    # 定义收到帧时的处理逻辑
    def on_frame_received(data, w, h):
        if stream.frame_count % 30 == 0:  # 每 30 帧打印一次，避免刷屏
            print(f"⏺ [帧 #{stream.frame_count:04d}] 分辨率: {w}x{h} | 数据大小: {len(data)} bytes")
            
        # TODO: 在这里将 data 传递给 05_video_encoder.py 进行编码
    
    # 在独立线程中运行，方便主线程控制超时
    thread = threading.Thread(target=stream.start, args=(on_frame_received,))
    thread.daemon = True
    thread.start()
    
    # 测试运行 10 秒
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        pass
        
    stream.stop()
    thread.join(timeout=3)
    
    print("-" * 50)
    if stream.frame_count > 0:
        fps = stream.frame_count / 10.0
        print(f"🎉 测试通过！成功提取帧数据！ (平均 FPS: {fps:.1f})")
        print("💡 下一步: 可以将 on_frame_received 中的 data 接入 PyAV 编码器。")
    else:
        print("⚠️ 警告: 10秒内未收到任何帧数据。")
        print("   排查建议: ")
        print("   1. 确认 02_portal_dbus.py 获取的 Node ID 是否仍然有效 (Portal 会话可能已过期)。")
        print("   2. 确认屏幕共享弹窗中是否点击了 '共享/Share' 按钮。")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python 04_pipewire_stream.py <Node_ID>")
        print("提示: Node ID 可从 02_portal_dbus.py 获取")
        sys.exit(1)
        
    try:
        target_node_id = int(sys.argv[1])
        test_stream(target_node_id)
    except ValueError:
        print("❌ 错误: Node ID 必须是整数")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 发生未捕获的致命错误: {e}")
        traceback.print_exc()
        sys.exit(1)
