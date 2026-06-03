#!/usr/bin/env python3
"""阶段 5: 单进程整合测试 (Portal 授权 + PipeWire 流)"""
import asyncio
import threading
import time
import traceback
from portal_screencast import PortalScreenCast
from _pipewire_cffi import ffi, lib as C

class IntegratedRecorder:
    def __init__(self):
        self.portal = PortalScreenCast()
        self.pw_loop = None
        self.pw_stream = None
        self.frame_count = 0
        self.running = True
        self._keep_alive = []

    def _on_process(self, user_data):
        if not self.running: return
        buf = C.pw_stream_dequeue_buffer(self.pw_stream)
        if buf == ffi.NULL: return
        
        try:
            spa_buf = buf.buffer
            if spa_buf == ffi.NULL or spa_buf.n_datas < 1: return
            
            data_struct = spa_buf.datas[0]
            if data_struct.chunk == ffi.NULL or data_struct.chunk[0].size == 0: return
            
            # 成功拿到数据！
            self.frame_count += 1
            if self.frame_count % 30 == 0:
                print(f"⏺ [帧 #{self.frame_count:04d}] 成功接收到画面数据 ({data_struct.chunk[0].size} bytes)")
        except Exception as e:
            print(f"❌ 回调异常: {e}")
        finally:
            C.pw_stream_queue_buffer(self.pw_stream, buf)

    def _on_state_changed(self, user_data, old, new, err):
        states = {-1:"ERROR", 0:"UNCONNECTED", 1:"CONNECTING", 2:"PAUSED", 3:"STREAMING"}
        print(f"🔄 [PipeWire] 状态: {states.get(old, old)} → {states.get(new, new)}")
        if err != ffi.NULL: print(f"❌ 错误: {ffi.string(err).decode()}")

    def _on_param_changed(self, user_data, id, param):
        if id == 2 and param != ffi.NULL:
            print("🚀 [PipeWire] 格式协商完成，激活流...")
            C.pw_stream_set_active(self.pw_stream, True)

    def _run_pipewire_thread(self, node_id):
        """在后台线程运行 PipeWire C 循环"""
        C.pw_init(ffi.NULL, ffi.NULL)
        self.pw_loop = C.pw_main_loop_new(ffi.NULL)
        loop = C.pw_main_loop_get_loop(self.pw_loop)
        
        events = ffi.new("struct pw_stream_events *")
        events.version = 3
        c_process = ffi.callback("void(void *)", self._on_process, onerror=traceback.print_exc)
        c_state = ffi.callback("void(void *, int, int, const char *)", self._on_state_changed, onerror=traceback.print_exc)
        c_param = ffi.callback("void(void *, uint32_t, const struct spa_pod *)", self._on_param_changed, onerror=traceback.print_exc)
        events.process, events.state_changed, events.param_changed = c_process, c_state, c_param
        self._keep_alive.extend([events, c_process, c_state, c_param])
        
        self.pw_stream = C.pw_stream_new_simple(loop, b"recorder", ffi.NULL, events, ffi.NULL)
        
        # 构建格式
        pod = C.build_video_format_pod(0x42475278, 1920, 1080, 30, 60)
        params = ffi.new("const struct spa_pod *[1]")
        params[0] = pod
        self._keep_alive.extend([params, pod])
        
        # 连接 (0x0004=AUTOCONNECT, 0x0008=MAP_BUFFERS)
        C.pw_stream_connect(self.pw_stream, 1, node_id, 0x0004 | 0x0008, params, 1)
        
        print("▶ [PipeWire] 线程启动，等待数据...")
        C.pw_main_loop_run(self.pw_loop)
        
        # 线程结束时的清理
        if self.pw_stream != ffi.NULL:
            C.pw_stream_destroy(self.pw_stream)
        print("🧹 [PipeWire] 线程已安全退出")

    async def run(self):
        """主异步入口"""
        try:
            # 1. 获取授权 (此时 D-Bus 连接保持活跃)
            node_id = await self.portal.start()
            
            # 2. 启动 PipeWire 线程
            pw_thread = threading.Thread(target=self._run_pipewire_thread, args=(node_id,))
            pw_thread.start()
            
            # 3. 保持主线程存活，让 D-Bus 和 PipeWire 同时运行
            print("\n" + "="*50)
            print("🎥 录制中... (按 Ctrl+C 停止)")
            print("="*50 + "\n")
            
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n⚠️ 收到停止信号...")
        finally:
            self.running = False
            # 停止 PipeWire
            if self.pw_loop:
                C.pw_main_loop_quit(self.pw_loop)
            # 停止 Portal
            await self.portal.stop()
            
            print(f"\n🎉 结束！共捕获 {self.frame_count} 帧。")

if __name__ == "__main__":
    recorder = IntegratedRecorder()
    try:
        asyncio.run(recorder.run())
    except Exception as e:
        print(f"❌ 致命错误: {e}")
        traceback.print_exc()
