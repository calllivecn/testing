#!/usr/bin/env python3
"""阶段 5: PyAV 视频编码测试"""
import av
import numpy as np

def test_encoder():
    print("="*40)
    print("🔍 阶段 5: PyAV 视频编码测试")
    print("="*40)
    
    output_file = "test_output.mp4"
    width, height, fps = 1920, 1080, 30
    
    container = av.open(output_file, mode='w')
    stream = container.add_stream('h264', rate=fps)
    stream.width = width
    stream.height = height
    stream.pix_fmt = 'yuv420p'
    stream.options = {'crf': '23', 'preset': 'veryfast'}
    
    print(f"▶ 正在生成 3 秒的测试视频 ({width}x{height} @ {fps}fps)...")
    
    for i in range(fps * 3): # 3秒视频
        # 生成随机 RGBA 数据 (模拟 PipeWire 传来的数据)
        rgba_data = np.random.randint(0, 256, (height, width, 4), dtype=np.uint8).tobytes()
        
        frame = av.VideoFrame(width=width, height=height, format='rgba')
        frame.planes[0].update(rgba_data)
        
        yuv_frame = frame.reformat(format='yuv420p')
        yuv_frame.pts = i
        yuv_frame.time_base = stream.time_base
        
        for packet in stream.encode(yuv_frame):
            container.mux(packet)
            
    # 刷新缓冲区
    for packet in stream.encode():
        container.mux(packet)
        
    container.close()
    print(f"✅ 视频保存成功: {output_file}")
    print("🎉 编码器测试通过！")

if __name__ == "__main__":
    try:
        import numpy
    except ImportError:
        print("⚠️ 测试需要 numpy，请执行: pip install numpy")
        # 如果没有 numpy，用纯 bytes 替代
        import os
        output_file = "test_output.mp4"
        width, height, fps = 1920, 1080, 30
        container = av.open(output_file, mode='w')
        stream = container.add_stream('h264', rate=fps)
        stream.width = width
        stream.height = height
        stream.pix_fmt = 'yuv420p'
        for i in range(fps * 3):
            rgba_data = os.urandom(width * height * 4)
            frame = av.VideoFrame(width=width, height=height, format='rgba')
            frame.planes[0].update(rgba_data)
            yuv_frame = frame.reformat(format='yuv420p')
            yuv_frame.pts = i
            yuv_frame.time_base = stream.time_base
            for packet in stream.encode(yuv_frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
        container.close()
        print(f"✅ 视频保存成功: {output_file}")
