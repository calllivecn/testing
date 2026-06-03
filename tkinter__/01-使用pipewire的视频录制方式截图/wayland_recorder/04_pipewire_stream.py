#!/usr/bin/env python3
"""阶段 4: PipeWire 流连接与帧提取 (cffi 安全版)"""
import sys
import time
import threading
from pipewire_bind import ffi, C

class PipeWireStream:
    def __init__(self, node_id):
        self.node_id = node_id
        self.running = True
        self.frame_count = 0
        self.width = 1920  # 简化：假设 1080p，实际应从 param_changed 解析
        self.height = 1080
        self.frame_callback = None
        
        # 创建主循环
        self.pw_loop = C.pw_main_loop_new(ffi.NULL)
        self.core_loop = C.pw_main_loop_get_loop(self.pw_loop)
        
        # 保持回调函数的引用，防止被 Python GC 回收
        self._keep_alive = []

    def _on_process(self, user_data):
        if not self.running:
            return
            
        buf = C.pw_stream_dequeue_buffer(self.pw_stream)
        if buf == ffi.NULL:
            return
            
        try:
            # cffi 允许像 C 一样直接访问 -> 和 . 
            spa_buf = buf.buffer
            if spa_buf.n_datas < 1:
                return
                
            # 安全获取数据指针和大小
            data_struct = spa_buf.datas[0]
            data_ptr = data_struct.data
            chunk_size = data_struct.chunk.size
            
            if data_ptr != ffi.NULL and chunk_size > 0:
                expected_size = self.width * self.height * 4
                # 从 C 指针安全拷贝数据到 Python bytes
                frame_data = ffi.buffer(data_ptr, min(chunk_size, expected_size))[:]
                
                if len(frame_data) == expected_size and self.frame_callback:
                    self.frame_callback(frame_data, self.width, self.height)
                    self.frame_count += 1
        except Exception as e:
            print(f"\n⚠️ 帧处理异常: {e}")
        finally:
            C.pw_stream_queue_buffer(self.pw_stream, buf)

    def _on_param_changed(self, user_data, id, param):
        if id == 3 and param != ffi.NULL:
            print(f"\n🔍 检测到视频流格式变更 (id={id})")
            # 实际生产环境这里需要解析 spa_pod，这里为了测试简化

    def start(self, frame_callback):
        self.frame_callback = frame_callback
        
        # 定义回调结构体
        events = ffi.new("struct pw_stream_events *")
        events.version = 3
        
        # 绑定回调并保持引用
        c_process = ffi.callback("void(void *)", self._on_process)
        c_param_changed = ffi.callback("void(void *, uint32_t, const void *)", self._on_param_changed)
        
        events.process = c_process
        events.param_changed = c_param_changed
        self._keep_alive.extend([events, c_process, c_param_changed])

        # 创建流
        self.pw_stream = C.pw_stream_new_simple(
            self.core_loop, b"python-screencast", ffi.NULL, events, ffi.NULL
        )
        if self.pw_stream == ffi.NULL:
            raise RuntimeError("PipeWire 流创建失败")

        # 连接流 (1 = INPUT, 0x0004|0x0008 = AUTOCONNECT|MAP_BUFFERS)
        flags = 0x0004 | 0x0008
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
    print(f"🔍 阶段 4: PipeWire 流测试 (cffi 版, Node ID: {node_id})")
    print("="*40)
    
    stream = PipeWireStream(node_id)
    
    def on_frame(data, w, h):
        if stream.frame_count % 30 == 0:
            print(f"⏺ 收到帧 #{stream.frame_count} ({w}x{h}, {len(data)} bytes)", end='\r')

    thread = threading.Thread(target=stream.start, args=(on_frame,))
    thread.start()
    
    time.sleep(10) # 测试录制 10 秒
    stream.stop()
    thread.join()
    
    if stream.frame_count > 0:
        print("\n🎉 测试通过！cffi 成功提取帧数据，无段错误！")
    else:
        print("\n⚠️ 未收到帧数据。请检查 Node ID 是否正确，或分辨率是否匹配。")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python 04_pipewire_stream.py <Node_ID>")
        sys.exit(1)
    test_stream(int(sys.argv[1]))
