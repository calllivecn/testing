import asyncio
import threading
import signal
import sys
import cv2
import numpy as np

# 导入你的 Portal 异步库
from portal_screencast import PortalScreenCast
# 导入我们编译好的 CFFI 模块
from _pipewire_cffi import ffi, lib

class IntegratedRecorder:
    def __init__(self):
        self.portal = PortalScreenCast()
        self.node_id = None
        
        # PipeWire 状态
        self.pw_ctx = None
        self.is_streaming = False
        self.frame_count = 0
        self._c_refs = []  # 防止 CFFI 回调被 GC
        
        # 线程同步信号
        self.stop_event = threading.Event()

    def _setup_pw_callbacks(self):
        """绑定 C 层回调到 Python"""
        @ffi.callback("void(void*, int, int)")
        def on_state(userdata, old, new):
            states = ["UNCONNECTED", "CONNECTING", "PAUSED", "STREAMING", "ERROR"]
            print(f"🔄 [PipeWire] 状态: {states[old]} → {states[new]}")
            if new == 3:  # STREAMING
                self.is_streaming = True
            elif new == 4:  # ERROR
                self.stop_event.set()

        @ffi.callback("void(void*, uint32_t, uint32_t, uint32_t)")
        def on_format(userdata, w, h, fmt):
            print(f"📐 [PipeWire] 协商格式: {w}x{h}, fmt={fmt}")

        @ffi.callback("void(void*, void*, uint32_t, uint32_t, uint32_t, uint32_t)")
        def on_frame(userdata, data_ptr, size, w, h, stride):
            try:
                if not self.is_streaming:
                    return
                
                # 1. 零拷贝获取内存视图
                raw_bytes = np.frombuffer(ffi.buffer(data_ptr, size), dtype=np.uint8)
                
                # 2. 重塑数组 (处理 stride 内存对齐)
                if stride == w * 4:
                    img_array = raw_bytes.reshape((h, w, 4))
                else:
                    img_array = raw_bytes.reshape((h, stride // 4, 4))[:, :w, :]

                # 3. 颜色空间转换 (BGRx -> BGR)
                img_bgr = img_array[:, :, :3]

                # 4. 使用 OpenCV 保存帧
                self.frame_count += 1
                filename = f"frame_{self.frame_count:04d}.png"
                cv2.imwrite(filename, img_bgr)
                print(f"✅ [帧 #{self.frame_count:04d}] 成功保存: {filename}")
                
                # 测试：截取 5 帧后触发停止信号
                if self.frame_count >= 5:
                    print("🎉 达到测试帧数，准备停止...")
                    self.stop_event.set()

            except Exception as e:
                print(f"❌ 帧处理异常: {e}")

        # 保持回调引用
        self._c_refs.extend([on_state, on_format, on_frame])
        lib.set_callbacks(self.pw_ctx, ffi.NULL, on_state, on_format, on_frame)

    def _pw_thread_worker(self):
        """PipeWire 后台线程工作流"""
        try:
            self.pw_ctx = lib.create_recorder()
            if not self.pw_ctx:
                print("❌ 创建 PipeWire 上下文失败！")
                self.stop_event.set()
                return
            
            self._setup_pw_callbacks()
            
            if lib.connect_stream(self.pw_ctx, self.node_id) < 0:
                print("❌ 连接 PipeWire 流失败！")
                self.stop_event.set()
                return

            print("🚀 [PipeWire] 主循环启动 (后台线程)")
            lib.run_loop(self.pw_ctx)  # 阻塞，直到 stop_loop 被调用
            print("🛑 [PipeWire] 主循环已退出")
        except Exception as e:
            print(f"💥 PipeWire 线程异常: {e}")
            self.stop_event.set()

    async def run(self):
        """主异步工作流 (保持 D-Bus 存活)"""
        # 1. 请求 Portal 授权
        print("🔹 [Portal] 正在请求屏幕共享授权...")
        try:
            self.node_id = await self.portal.start()
        except Exception as e:
            print(f"❌ Portal 授权失败: {e}")
            return

        print(f"✅ [Portal] 授权成功! Node ID: {self.node_id}")
        print("\n" + "="*50)
        print("🎥 录制中... (按 Ctrl+C 停止)")
        print("="*50 + "\n")

        # 2. 启动 PipeWire 后台线程
        pw_thread = threading.Thread(target=self._pw_thread_worker, daemon=True)
        pw_thread.start()

        # 3. 主线程在此等待停止信号 (保持 asyncio 事件循环和 D-Bus 存活)
        # 使用 asyncio.sleep 循环检查，以便能响应 KeyboardInterrupt
        try:
            while not self.stop_event.is_set():
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass

        # 4. 清理 PipeWire
        if self.pw_ctx:
            lib.stop_loop(self.pw_ctx)
            pw_thread.join(timeout=2.0)
            lib.destroy_recorder(self.pw_ctx)

        # 5. 清理 Portal 会话
        await self.portal.stop()
        print("🧹 所有资源已清理，再见！")

def main():
    recorder = IntegratedRecorder()
    
    # 处理 Ctrl+C 优雅退出
    def signal_handler(sig, frame):
        print("\n⚠️ 收到中断信号，正在停止...")
        recorder.stop_event.set()
        
    signal.signal(signal.SIGINT, signal_handler)

    try:
        asyncio.run(recorder.run())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
