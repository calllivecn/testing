#!/usr/bin/env python3
"""阶段 4: PipeWire 流连接与帧提取 (修复回调崩溃)"""
import sys
import time
import threading
import traceback
from pipewire_bind import ffi, C

class PipeWireStream:
    def __init__(self, node_id):
        self.node_id = node_id
        self.running = True
        self.frame_count = 0
        self.width = 1920  # 简化：假设 1080p
        self.height = 1080
        self.frame_callback = None
        
        self.pw_loop = C.pw_main_loop_new(ffi.NULL)
        self.core_loop = C.pw_main_loop_get_loop(self.pw_loop)
        
        # 保持引用防止 GC
        self._keep_alive = []

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
            chunk_size = data_struct.chunk.size
            
            if data_ptr != ffi.NULL and chunk_size > 0:
                expected_size = self.width * self.height * 4
                # 安全拷贝数据
                frame_data = ffi.buffer(data_ptr, min(chunk_size, expected_size))[:]
                
                if len(frame_data) == expected_size and self.frame_callback:
                    self.frame_callback(frame_data, self.width, self.height)
                    self.frame_count += 1
        except Exception as e:
            print(f"\n❌ [process 回调异常]: {e}")
            traceback.print_exc()
        finally:
            C.pw_stream_queue_buffer(self.pw_stream, buf)

    def _on_param_changed(self, user_data, id, param):
        try:
            if id == 3 and param != ffi.NULL:
                print(f"\n🔍 检测到视频流格式变更 (id={id})")
        except Exception as e:
            print(f"\n❌ [param_changed 回调异常]: {e}")
            traceback.print_exc()

    def start(self, frame_callback):
        self.frame_callback = frame_callback
        
        events = ffi.new("struct pw_stream_events *")
        events.version = 3
        
        # 关键修复：添加 onerror 参数，防止异常导致 C 端静默崩溃！
        c_process = ffi.callback("void(void *)", self._on_process, onerror=traceback.print_exc)
        c_param_changed = ffi.callback("void(void *, uint32_t, const struct spa_pod *)", self._on_param_changed, onerror=traceback.print_exc)
        
        events.process = c_process
        events.param_changed = c_param_changed
        self._keep_alive.extend([events, c_process, c_param_changed])

        self.pw_stream = C.pw_stream_new_simple(
            self.core_loop, b"python-screencast", ffi.NULL, events, ffi.NULL
        )
        if self.pw_stream == ffi.NULL:
            raise RuntimeError("PipeWire 流创建失败")

        flags = 0x0004 | 0x0008 # AUTOCONNECT | MAP_BUFFERS
        res = C.pw_stream_connect(
            self.pw_stream, 1, self.node_id, flags, ffi.NULL, 0
        )
        if res < 0:
            raise RuntimeError(f"PipeWire 流连接失败 (错误码: {res})")

        print(f"▶ PipeWire 流已连接 (Node ID: {self.node_id})，开始接收帧...")
        C.pw_main_loop_run(self.pw_loop)

    def stop(self):
        self.running = False
        C.pw_main_loop_quit(self.pw_loop)
        if hasattr(self, 'pw_stream') and self.pw_stream != ffi.NULL:
            C.pw_stream_destroy(self.pw_stream)
        print(f"\n⏹ PipeWire 流已停止，共接收 {self.frame_count} 帧")

def test_stream(node_id):
    print("="*40)
    print(f"🔍 阶段 4: PipeWire 流测试 (Node ID: {node_id})")
    print("="*40)
    
    stream = PipeWireStream(node_id)
    
    def on_frame(data, w, h):
        if stream.frame_count % 30 == 0:
            print(f"⏺ 收到帧 #{stream.frame_count} ({w}x{h}, {len(data)} bytes)", end='\r')

    thread = threading.Thread(target=stream.start, args=(on_frame,))
    thread.start()
    
    time.sleep(10) 
    stream.stop()
    thread.join()
    
    if stream.frame_count > 0:
        print("\n🎉 测试通过！成功提取帧数据！")
    else:
        print("\n⚠️ 未收到帧数据。请检查分辨率是否匹配。")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python 04_pipewire_stream.py <Node_ID>")
        sys.exit(1)
    test_stream(int(sys.argv[1]))
