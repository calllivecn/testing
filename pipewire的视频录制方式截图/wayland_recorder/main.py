import asyncio
import signal

import cv2

from portal_screencast import PortalScreenCast
from libpipewire import PipeWireRecorder

class ScreenCaptureApp:
    def __init__(self):
        self.portal = PortalScreenCast()
        self.recorder = PipeWireRecorder()
        self.frame_count = 0
        
    def on_state(self, old, new):
        print(f"🔄 [PipeWire] 状态: {old} → {new}")
        
    def on_format(self, w, h, fmt):
        print(f"📐 [PipeWire] 协商格式: {w}x{h}, fmt={fmt}")
        
    def on_frame(self, img_bgr, w, h):
        """处理每一帧 (业务逻辑：保存图片)"""
        self.frame_count += 1
        filename = f"frame_{self.frame_count:04d}.png"
        cv2.imwrite(filename, img_bgr)
        print(f"✅ [帧 #{self.frame_count:04d}] [大小: {w}x{h}] 成功保存: {filename}")
        
        # 测试：截取 5 帧后触发停止信号
        # if self.frame_count >= 5:
        #     print("🎉 达到测试帧数，准备停止...")
        #     self.recorder.stop_event.set()

    async def run(self):
        # 1. 请求 Portal 授权
        print("🔹 [Portal] 正在请求屏幕共享授权...")
        try:
            node_id = await self.portal.start()
        except Exception as e:
            print(f"❌ Portal 授权失败: {e}")
            return
        print(f"✅ [Portal] 授权成功! Node ID: {node_id}")
        
        # 2. 配置并启动 PipeWire
        self.recorder.set_callbacks(
            on_state=self.on_state,
            on_format=self.on_format,
            on_frame=self.on_frame
        )
        
        print("\n" + "="*50)
        print("🎥 录制中... (按 Ctrl+C 停止)")
        print("="*50 + "\n")
        
        pw_thread = self.recorder.start(node_id)
        
        # 3. 主线程在此等待停止信号
        try:
            while not self.recorder.stop_event.is_set():
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
            
        # 4. 清理资源
        print("🛑 [PipeWire] 正在停止...")
        self.recorder.stop()
        if pw_thread.is_alive():
            pw_thread.join(timeout=2.0)
            
        await self.portal.stop()
        print("🧹 所有资源已清理，再见！")

def main():
    app = ScreenCaptureApp()
    
    # ================= 配置录制参数 =================
    app.recorder.set_target_fps(1)                       # 限制 10 FPS
    app.recorder.set_crop_region(800, 600, 800, 600)      # C层裁剪: x=100, y=100, 宽800, 高600
    # app.recorder.disable_crop()                         # 如果需要全屏，调用此方法
    # =================================================
    
    # 处理 Ctrl+C 优雅退出
    def signal_handler(sig, frame):
        print("\n⚠️ 收到中断信号，正在停止...")
        app.recorder.stop_event.set()
        
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
