#!/usr/bin/env python3
"""
main_sync.py
使用 PipeWireRecorder 的同步模式 (Pull/read_frame) 进行屏幕捕获。
适合场景：按需截图、OpenCV 图像处理、AI 推理 (YOLO) 等耗时操作。
"""

import asyncio
import signal
import sys
import time
import cv2

# 假设这两个文件与 main_sync.py 在同一目录下
from portal_screencast import PortalScreenCast
from libpipewire import PipeWireRecorder

# ================= 全局控制标志 =================
running = True

def signal_handler(sig, frame):
    """处理 Ctrl+C 优雅退出"""
    global running
    print("\n⚠️ 收到中断信号 (Ctrl+C)，准备退出...")
    running = False

# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)


async def request_portal_auth():
    """通过 XDG Desktop Portal 请求屏幕共享授权"""
    print("🔹 [Portal] 正在请求屏幕共享授权 (请在弹出的系统窗口中点击'分享')...")
    portal = PortalScreenCast()
    try:
        node_id = await portal.start() 
        print(f"✅ [Portal] 授权成功! 获取到 PipeWire Node ID: {node_id}")
        return node_id, portal
    except Exception as e:
        print(f"❌ [Portal] 授权失败或用户取消: {e}")
        return None, portal


def main():
    global running
    
    # ================= 1. Portal 授权获取 Node ID =================
    try:
        node_id, portal = asyncio.run(request_portal_auth())
    except KeyboardInterrupt:
        print("\n⚠️ 用户强制退出。")
        sys.exit(0)
        
    if node_id is None:
        print("❌ 无法获取 Node ID，程序退出。")
        sys.exit(1)

    # ================= 2. 配置 PipeWireRecorder =================
    recorder = PipeWireRecorder()
    
    # 设置目标 FPS (C层丢帧+时间戳双重限制)
    TARGET_FPS = 15
    recorder.set_target_fps(TARGET_FPS)
    
    # 可选：设置 C 层硬件级裁剪 (x, y, width, height)
    recorder.set_crop_region(100, 200, 800, 600)
    # recorder.disable_crop()  # 默认捕获全屏/全窗口

    # ================= 3. 启动 PipeWire (同步模式) =================
    print(f"\n🚀 [PipeWire] 正在连接 Node {node_id} (同步拉取模式, 目标 {TARGET_FPS} FPS)...")
    try:
        # 【关键】传入 sync_mode=True 启用同步读取
        pw_thread = recorder.start(node_id, sync_mode=True)
    except Exception as e:
        print(f"❌ [PipeWire] 启动失败: {e}")
        sys.exit(1)

    print("✅ [PipeWire] 已进入 STREAMING 状态！")
    print("="*50)
    print("🎥 实时预览中... (按 'q' 或 Ctrl+C 退出)")
    print("="*50)

    # ================= 4. 主循环：同步拉取帧 =================
    frame_count = 0
    fps_start_time = time.time()
    
    cv2.namedWindow("PipeWire Sync Capture", cv2.WINDOW_NORMAL)

    while running:
        # 【关键】阻塞等待最新帧，超时设为 3 秒
        result = recorder.read_frame(timeout=3.0)
        
        if result is None:
            if recorder.stop_event.is_set():
                print("❌ [PipeWire] 流已断开或发生错误。")
                break
            print("⚠️ [PipeWire] 读取超时 (3秒未收到新帧)，继续等待...")
            continue
            
        img_bgr, w, h = result
        frame_count += 1
        
        # ================= 5. 业务逻辑处理 (模拟耗时操作) =================
        
        # 示例 A：模拟耗时的 AI 推理或图像处理 (不会卡死底层 PipeWire)
        # time.sleep(0.1)  # 假设推理耗时 100ms
        
        # 示例 B：在图像上绘制信息
        cv2.putText(img_bgr, f"Frame: {frame_count}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(img_bgr, f"Res: {w}x{h}", (20, 80), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # 示例 C：计算并显示实际拉取帧率
        elapsed = time.time() - fps_start_time
        if elapsed >= 1.0:
            actual_fps = frame_count / elapsed
            cv2.putText(img_bgr, f"Actual FPS: {actual_fps:.1f}", (20, 120), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            # 注意：这里不重置 frame_count，只重置时间，让 FPS 滑动计算
            fps_start_time = time.time()

        # 显示图像 (缩小以适应屏幕)
        display_img = cv2.resize(img_bgr, (w // 2, h // 2))
        cv2.imshow("PipeWire Sync Capture", display_img)
        
        # 按 'q' 退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("🛑 用户按下 'q'，准备退出...")
            running = False

    # ================= 6. 清理资源 =================
    print("\n🧹 正在清理资源...")
    cv2.destroyAllWindows()
    
    # 停止 PipeWire
    recorder.stop()
    if pw_thread.is_alive():
        pw_thread.join(timeout=2.0)
        
    print("👋 程序已优雅退出。再见！")


if __name__ == "__main__":
    main()
