#!/usr/bin/env python3
"""阶段 4: PipeWire 流连接与帧提取 (激活流与线程安全修复版)"""
import sys
import time
import threading
import traceback

from _pipewire_cffi import ffi, lib as C

class PipeWireStream:
    def __init__(self, node_id, width=1920, height=1080):
        self.node_id = node_id
        self.running = True
        self.frame_count = 0
        
        self.width = width
        self.height = height
        self.bpp = 4  
        
        self.frame_callback = None
        self._keep_alive = []  
        
        C.pw_init(ffi.NULL, ffi.NULL)
        print("✅ PipeWire 核心已初始化")
        
        self.pw_loop = C.pw_main_loop_new(ffi.NULL)
        if self.pw_loop == ffi.NULL:
            raise RuntimeError("pw_main_loop_new 失败")
        self.core_loop = C.pw_main_loop_get_loop(self.pw_loop)
        self.pw_stream = ffi.NULL
        self._loop_thread = None

    def _on_process(self, user_data):
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
            
            if data_struct.chunk == ffi.NULL:
                return
                
            chunk_size = data_struct.chunk[0].size
            if chunk_size == 0:
                return
            
            if data_ptr != ffi.NULL and chunk_size > 0:
                expected_size = self.width * self.height * self.bpp
                actual_size = min(chunk_size, expected_size)
                
                frame_data = ffi.buffer(data_ptr, actual_size)[:]
                
                if self.frame_callback:
                    self.frame_callback(frame_data, self.width, self.height)
                    self.frame_count += 1
                    
        except Exception as e:
            print(f"\n❌ [process 回调异常]: {e}")
            traceback.print_exc()
        finally:
            C.pw_stream_queue_buffer(self.pw_stream, buf)

    def _on_state_changed(self, user_data, old_state, new_state, error):
        state_names = {-1: "ERROR", 0: "UNCONNECTED", 1: "CONNECTING", 2: "PAUSED", 3: "STREAMING"}
        print(f"🔄 流状态变更: {state_names.get(old_state, old_state)} → {state_names.get(new_state, new_state)}")
        if error != ffi.NULL:
            print(f"❌ PipeWire 错误: {ffi.string(error).decode()}")

    def _on_param_changed(self, user_data, id, param):
        if param == ffi.NULL:
            return
        print(f"🔍 收到参数变更通知 (Param ID: {id})")
        
        # ✅ 核心修复 1: 当 Format (ID=2) 协商完成后，显式激活流！
        if id == 2:  
            print("🚀 格式协商完成，正在激活流 (set_active)...")
            C.pw_stream_set_active(self.pw_stream, True)

    def _run_loop(self, frame_callback):
        """在子线程中运行主循环，并在退出后安全清理资源"""
        self.frame_callback = frame_callback
        
        events = ffi.new("struct pw_stream_events *")
        events.version = 3
        
        c_process = ffi.callback("void(void *)", self._on_process, onerror=traceback.print_exc)
        c_state_changed = ffi.callback("void(void *, int, int, const char *)", self._on_state_changed, onerror=traceback.print_exc)
        c_param_changed = ffi.callback("void(void *, uint32_t, const struct spa_pod *)", self._on_param_changed, onerror=traceback.print_exc)
        
        events.process = c_process
        events.state_changed = c_state_changed
        events.param_changed = c_param_changed
        
        self._keep_alive.extend([events, c_process, c_state_changed, c_param_changed])
        
        self.pw_stream = C.pw_stream_new_simple(
            self.core_loop, b"python-screencast", ffi.NULL, events, ffi.NULL
        )
        if self.pw_stream == ffi.NULL:
            print("❌ pw_stream_new_simple 失败")
            return
        
        BGRx_FORMAT_ID = 0x42475278 
        format_pod = C.build_video_format_pod(BGRx_FORMAT_ID, self.width, self.height, 30, 60)
        if format_pod == ffi.NULL:
            print("❌ build_video_format_pod 失败")
            return
            
        params = ffi.new("const struct spa_pod *[1]")
        params[0] = format_pod
        self._keep_alive.extend([params, format_pod])
        
        flags = 0x0004 | 0x0008  # AUTOCONNECT | MAP_BUFFERS
        
        print(f"🔌 正在连接 PipeWire 流 (Node ID: {self.node_id})...")
        res = C.pw_stream_connect(self.pw_stream, 1, self.node_id, flags, params, 1)
        if res < 0:
            print(f"❌ pw_stream_connect 失败 (错误码: {res})")
            return
        
        print("▶ 流已连接，开始运行主循环...")
        
        # 阻塞运行
        C.pw_main_loop_run(self.pw_loop)
        
        # ✅ 核心修复 2: 在子线程中（Loop 退出后）安全销毁流
        print("🧹 正在子线程中安全清理 PipeWire 资源...")
        if self.pw_stream != ffi.NULL:
            C.pw_stream_destroy(self.pw_stream)
            self.pw_stream = ffi.NULL

    def start(self, frame_callback):
        """启动子线程运行 Loop"""
        self._loop_thread = threading.Thread(target=self._run_loop, args=(frame_callback,))
        self._loop_thread.daemon = True
        self._loop_thread.start()

    def stop(self):
        """通知主循环退出，并等待子线程完成清理"""
        if not self.running:
            return
        self.running = False
        
        print("\n⚠️ 正在停止主循环...")
        C.pw_main_loop_quit(self.pw_loop)
        
        # 等待子线程执行完 destroy
        if self._loop_thread:
            self._loop_thread.join(timeout=3)
            
        print(f"⏹ PipeWire 流已安全停止，共成功接收 {self.frame_count} 帧")


def test_stream(node_id):
    print("=" * 50)
    print(f"🔍 阶段 4: PipeWire 流测试 (目标 Node ID: {node_id})")
    print("=" * 50)
    
    stream = PipeWireStream(node_id, width=1920, height=1080)
    
    def on_frame_received(data, w, h):
        if stream.frame_count % 30 == 0:  
            print(f"⏺ [帧 #{stream.frame_count:04d}] 分辨率: {w}x{h} | 数据大小: {len(data)} bytes")
    
    stream.start(on_frame_received)
    
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        pass
        
    stream.stop()
    
    print("-" * 50)
    if stream.frame_count > 0:
        fps = stream.frame_count / 10.0
        print(f"🎉 测试通过！成功提取帧数据！ (平均 FPS: {fps:.1f})")
    else:
        print("⚠️ 警告: 10秒内未收到任何帧数据。")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python 04_pipewire_stream.py <Node_ID>")
        sys.exit(1)
    try:
        test_stream(int(sys.argv[1]))
    except Exception as e:
        print(f"❌ 致命错误: {e}")
        traceback.print_exc()
