#!/usr/bin/env python3
"""阶段 5: 单进程整合测试 (终极修复版：注册监听器 + 动态获取分辨率)"""
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
        
        # 动态获取的真实视频参数
        self.actual_width = 0
        self.actual_height = 0
        self.actual_format = 0

    def _on_process(self, user_data):
        if not self.running: return
        buf = C.pw_stream_dequeue_buffer(self.pw_stream)
        if buf == ffi.NULL: return
        
        try:
            spa_buf = buf.buffer
            if spa_buf == ffi.NULL or spa_buf.n_datas < 1: return
            
            data_struct = spa_buf.datas[0]
            if data_struct.chunk == ffi.NULL or data_struct.chunk[0].size == 0: return
            
            self.frame_count += 1
            if self.frame_count % 30 == 0:
                print(f"⏺ [帧 #{self.frame_count:04d}] 成功接收! 分辨率: {self.actual_width}x{self.actual_height} | 大小: {data_struct.chunk[0].size} bytes")
        except Exception as e:
            print(f"❌ 回调异常: {e}")
        finally:
            C.pw_stream_queue_buffer(self.pw_stream, buf)

    def _on_state_changed(self, user_data, old, new, err):
        states = {-1:"ERROR", 0:"UNCONNECTED", 1:"CONNECTING", 2:"PAUSED", 3:"STREAMING"}
        print(f"🔄 [PipeWire] 状态: {states.get(old, old)} → {states.get(new, new)}")
        if err != ffi.NULL: print(f"❌ 错误: {ffi.string(err).decode()}")

    def _on_param_changed(self, user_data, id, param):
        if param == ffi.NULL: return
        
        # ID 2 = SPA_PARAM_Format
        if id == 2:
            fmt_ptr = ffi.new("uint32_t *")
            w_ptr = ffi.new("uint32_t *")
            h_ptr = ffi.new("uint32_t *")
            
            if C.parse_video_format(param, fmt_ptr, w_ptr, h_ptr) == 0:
                self.actual_format = fmt_ptr[0]
                self.actual_width = w_ptr[0]
                self.actual_height = h_ptr[0]
                print(f"✅ [PipeWire] 格式协商成功! 真实分辨率: {self.actual_width}x{self.actual_height}")
                
                # ✅ 核心修复：格式协商完成后，必须更新 Buffers 参数并激活流
                buffers_pod = C.build_buffers_pod()
                self._keep_alive.append(buffers_pod)
                C.pw_stream_update_params(self.pw_stream, ffi.new("const struct spa_pod *[1]", [buffers_pod]), 1)
                
                print("🚀 [PipeWire] 激活流 (set_active)...")
                C.pw_stream_set_active(self.pw_stream, True)

    def _run_pipewire_thread(self, node_id):
        C.pw_init(ffi.NULL, ffi.NULL)
        self.pw_loop = C.pw_main_loop_new(ffi.NULL)
        loop = C.pw_main_loop_get_loop(self.pw_loop)
        
        events = ffi.new("struct pw_stream_events *")
        events.version = 3  # PW_VERSION_STREAM_EVENTS
        
        c_process = ffi.callback("void(void *)", self._on_process, onerror=traceback.print_exc)
        c_state = ffi.callback("void(void *, int, int, const char *)", self._on_state_changed, onerror=traceback.print_exc)
        c_param = ffi.callback("void(void *, uint32_t, const struct spa_pod *)", self._on_param_changed, onerror=traceback.print_exc)
        
        events.process = c_process
        events.state_changed = c_state
        events.param_changed = c_param
        self._keep_alive.extend([events, c_process, c_state, c_param])
        
        self.pw_stream = C.pw_stream_new_simple(loop, b"recorder", ffi.NULL, events, ffi.NULL)
        
        # ✅ 核心修复：必须显式注册监听器！
        listener = ffi.new("struct spa_hook *")
        C.pw_stream_add_listener(self.pw_stream, listener, events, ffi.NULL)
        self._keep_alive.append(listener)
        
        # 构建初始参数 (Format)
        pod = C.build_video_format_pod(1920, 1080)
        params = ffi.new("const struct spa_pod *[1]")
        params[0] = pod
        self._keep_alive.extend([params, pod])
        
        flags = 0x0004 | 0x0008  # AUTOCONNECT | MAP_BUFFERS
        
        print("▶ [PipeWire] 线程启动，等待数据...")
        res = C.pw_stream_connect(self.pw_stream, 1, node_id, flags, params, 1)
        if res < 0:
            print(f"❌ PipeWire 连接失败，错误码: {res}")
            
        C.pw_main_loop_run(self.pw_loop)
        
        if self.pw_stream != ffi.NULL:
            C.pw_stream_destroy(self.pw_stream)
        print("🧹 [PipeWire] 线程已安全退出")

    async def run(self):
        try:
            node_id = await self.portal.start()
            pw_thread = threading.Thread(target=self._run_pipewire_thread, args=(node_id,))
            pw_thread.start()
            
            print("\n" + "="*50)
            print("🎥 录制中... (按 Ctrl+C 停止)")
            print("="*50 + "\n")
            
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n⚠️ 收到停止信号...")
        finally:
            self.running = False
            if self.pw_loop:
                C.pw_main_loop_quit(self.pw_loop)
            await self.portal.stop()
            print(f"\n🎉 结束！共捕获 {self.frame_count} 帧。")

if __name__ == "__main__":
    recorder = IntegratedRecorder()
    try:
        asyncio.run(recorder.run())
    except Exception as e:
        print(f"❌ 致命错误: {e}")
        traceback.print_exc()
