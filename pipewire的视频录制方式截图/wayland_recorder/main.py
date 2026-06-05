
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

class PipewireRecorder:
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
        
        self.enable_crop = False  # 是否启用裁剪开关
        # 新增：保存裁剪和 FPS 参数
        self.target_fps = 5
        self.crop_x, self.crop_y, self.crop_w, self.crop_h = 0, 0, 0, 0


    def set_crop_frame(self, x: int, y: int, w: int, h: int):
        # 裁剪参数配置 (可根据需要修改)
        self.crop_x = x
        self.crop_y = y
        self.crop_w = w  # 裁剪宽度
        self.crop_h = h  # 裁剪高度
        self.enable_crop = True

    def set_target_fps(self, fps: int):
        self.target_fps = fps

    def crop_frame(self, img, x, y, w, h):
        """从图像中裁剪出指定位置和大小的区域"""
        img_h, img_w = img.shape[:2]
        
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(img_w, x + w)
        y2 = min(img_h, y + h)
        
        if x1 >= x2 or y1 >= y2:
            raise ValueError(f"裁剪区域无效或超出范围: 请求({x},{y},{w},{h}), 原图({img_w}x{img_h})")
            
        return img[y1:y2, x1:x2]

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
                
                """
                # 4. 执行裁剪 (如果启用)
                final_img = img_bgr
                if self.enable_crop:
                    try:
                        final_img = self.crop_frame(img_bgr, self.crop_x, self.crop_y, self.crop_w, self.crop_h)
                    except ValueError as e:
                        print(f"⚠️ 裁剪警告: {e}")
                """

                # 5. 使用 OpenCV 保存帧
                self.frame_count += 1
                filename = f"frame_{self.frame_count:04d}.png"
                cv2.imwrite(filename, img_bgr)
                print(f"✅ [帧 #{self.frame_count:04d}] 成功保存: {filename}")
                
                # 测试：截取 5 帧后触发停止信号
                #if self.frame_count >= 5:
                #    print("🎉 达到测试帧数，准备停止...")
                #    self.stop_event.set()
                    
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


            # ================= 新增：在 connect 之前配置 C 层参数 =================
            # 1. 设置目标 FPS
            lib.set_target_fps(self.pw_ctx, self.target_fps)
            
            # 2. 设置裁剪区域 (如果启用了裁剪)
            if self.enable_crop:
                lib.set_crop_region(self.pw_ctx, 1, self.crop_x, self.crop_y, self.crop_w, self.crop_h)
            else:
                lib.set_crop_region(self.pw_ctx, 0, 0, 0, 0, 0) # 禁用裁剪
            # =====================================================================
            
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

        # 3. 主线程在此等待停止信号
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

    recorder = PipewireRecorder()
    
    # ================= 配置裁剪参数 =================
    # 如果您需要裁剪，请取消下方注释并修改参数
    recorder.set_target_fps(10)                       # 限制 15 FPS
    recorder.set_crop_frame(100, 100, 800, 600)       # 裁剪区域: x=100, y=100, 宽800, 高600
    # ================================================
    
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
