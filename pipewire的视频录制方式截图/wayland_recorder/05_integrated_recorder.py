#!/usr/bin/env python3
"""阶段 5: 单进程整合测试 (架构重构版)"""
import asyncio
from portal_screencast import PortalScreenCast
from libpipewire import PipeWireStream

class IntegratedRecorder:
    def __init__(self):
        self.portal = PortalScreenCast()
        self.pw_stream = None
        self.frame_count = 0

    def _handle_state(self, old, new):
        states = {-1:"ERROR", 0:"UNCONNECTED", 1:"CONNECTING", 2:"PAUSED", 3:"STREAMING"}
        print(f"🔄 [PipeWire] 状态: {states.get(old, old)} → {states.get(new, new)}")

    def _handle_format(self, w, h, fmt):
        print(f"✅ [PipeWire] 格式协商成功! 真实分辨率: {w}x{h}, 格式ID: {fmt}")

    def _handle_frame(self, frame_data, w, h, stride):
        self.frame_count += 1
        if self.frame_count % 60 == 0:
            # frame_data 是一个类似 bytes 的内存视图，可以直接传给 numpy 或 ffmpeg
            print(f"⏺ [帧 #{self.frame_count:04d}] 成功接收! 分辨率: {w}x{h} | 大小: {len(frame_data)} bytes")

    async def run(self):
        try:
            print("🔹 [Portal] 正在请求屏幕共享授权...")
            node_id = await self.portal.start()
            print(f"✅ [Portal] 授权成功! Node ID: {node_id}\n")
            
            self.pw_stream = PipeWireStream(node_id)
            self.pw_stream.on_state_changed = self._handle_state
            self.pw_stream.on_format_changed = self._handle_format
            self.pw_stream.on_frame = self._handle_frame
            
            self.pw_stream.start()
            
            print("="*50)
            print("🎥 录制中... (按 Ctrl+C 停止)")
            print("="*50 + "\n")
            
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n⚠️ 收到停止信号...")
        finally:
            if self.pw_stream:
                self.pw_stream.stop()
            await self.portal.stop()
            print(f"\n🎉 结束！共捕获 {self.frame_count} 帧。")

if __name__ == "__main__":
    recorder = IntegratedRecorder()
    try:
        asyncio.run(recorder.run())
    except Exception as e:
        print(f"❌ 致命错误: {e}")
