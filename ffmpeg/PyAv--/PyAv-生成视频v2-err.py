#!/usr/bin/env python3
# coding=utf-8
# date 2025-08-30 16:38:08
# author calllivecn <calllivecn@outlook.com>

import sys

import numpy as np

import av

# ffmpeg 编码器
try:
    CODEC = sys.argv[1]
except Exception:
    CODEC = "libx265"
    print("默认使用CPU编码: libx265")


duration = 20
fps = 30
total_frames = duration * fps

container = av.open("test.mkv", mode="w")

# 获取元数据字典
metadata = container.metadata

# 设置元数据信息
metadata['title'] = "这是我的测试视频"
metadata['author'] = '我是作者'
metadata['comment'] = 'This is a test'

stream = container.add_stream(CODEC, rate=fps)

stream_width = 1920
stream_height = 1080

stream.width = stream_width
stream.height = stream_height
stream.pix_fmt = "yuv420p"

# 使用多线程编码? 解码时这么用
# container.streams.video[0].thread_type = "AUTO"

def video():

    count = 1
    
    while True:
        # 创建一个 NumPy 数组来保存所有帧的数据
        # 维度: (帧数, 宽度, 高度, 颜色通道)
        # 使用 np.empty 可以避免初始化开销
        imgs = np.empty((total_frames, stream_width, stream_height, 3))
    
        # 构建一个包含所有帧索引的数组，这将是矢量化计算的关键
        # 形状为 (total_frames, 1, 1)，可以利用广播机制
        frame_indices = np.arange(total_frames).reshape(total_frames, 1, 1)
    
        # 矢量化计算：一次性计算所有帧的所有颜色通道
        # 使用广播机制 (broadcasting) 将 frame_indices 应用于整个 imgs 数组
        # 这个操作由底层的多线程库（如 OpenBLAS）并行执行
        base_val = 2 * np.pi * (frame_indices / total_frames)
    
        # 填充红色通道 (0)
        imgs[:, :, :, 0] = 0.5 + 0.5 * np.sin(base_val + 2 * np.pi * (0 / 3))
    
        # 填充绿色通道 (1)
        imgs[:, :, :, 1] = 0.5 + 0.5 * np.sin(base_val + 2 * np.pi * (1 / 3))
    
        # 填充蓝色通道 (2)
        imgs[:, :, :, 2] = 0.5 + 0.5 * np.sin(base_val + 2 * np.pi * (2 / 3))
    
        # 批量转换和裁剪
        # 这两个操作也会由 NumPy 的底层库进行优化
        imgs = np.round(255 * imgs).astype(np.uint8)
        imgs = np.clip(imgs, 0, 255)
    
        # 循环处理所有已经计算好的帧数据
        for frame_i in range(total_frames):
            # 从大的 imgs 数组中取出单帧数据
            img = imgs[frame_i, :, :, :]
            # 从 NumPy 数组转换为 av.VideoFrame
            frame = av.VideoFrame.from_ndarray(img, format="rgb24")
    
            # 这里可以继续你的视频处理逻辑
            # 例如：stream.encode(frame)
            print(f"处理第 {frame_i} 帧...")
            for packet in stream.encode(frame):
                container.mux(packet)
    
        print(f"第 {count} 次循环完成。")
        count += 1


print("CTRL+C 停止生成")
try:
    video()
except KeyboardInterrupt:
    print("停止生成")

# Flush stream
for packet in stream.encode():
    print("最后收尾：`for packte in stream.encode():`")
    container.mux(packet)

container.close()

