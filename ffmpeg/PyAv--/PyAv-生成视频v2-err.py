#!/usr/bin/env python3
# coding=utf-8
# date 2025-08-30 16:38:08
# author calllivecn <calllivecn@outlook.com>

import sys

import numpy as np

import av
from av.codec.hwaccel import HWAccel

# ffmpeg 编码器
try:
    CODEC = sys.argv[1]
except IndexError:
    CODEC = "libx265"
    print("默认使用CPU编码: libx265")
try:
    hw = sys.argv[2]
except IndexError:
    hw = None

if hw == "vaapi":
    print("使用硬件编码: VAAPI")
    hw = HWAccel(device_type='vaapi', allow_software_fallback=False)

duration = 20
fps = 30
total_frames = duration * fps

width = 1920
height = 1080

container = av.open("test.mkv", mode="w")

# 获取元数据字典
metadata = container.metadata

# 设置元数据信息
metadata['title'] = "这是我的测试视频"
metadata['author'] = '我是作者'
metadata['comment'] = 'This is a test'

stream = container.add_stream(CODEC, rate=fps)

stream.width = width
stream.height = height
#stream.pix_fmt = "yuv420p"

# stream.codec_context = av.VideoCodecContext.create("hevc", "w", hwaccel=hw) # 不能在这里设置 codec_context了。

# 使用多线程编码? 解码时这么用
# container.streams.video[0].thread_type = "AUTO"

def video():

    count = 1
    while True:

        for frame_i in range(total_frames):

            img = np.empty((width, height, 3))
            img[:, :, 0] = 0.5 + 0.5 * np.sin(2 * np.pi * (0 / 3 + frame_i / total_frames))
            img[:, :, 1] = 0.5 + 0.5 * np.sin(2 * np.pi * (1 / 3 + frame_i / total_frames))
            img[:, :, 2] = 0.5 + 0.5 * np.sin(2 * np.pi * (2 / 3 + frame_i / total_frames))

            img = np.round(255 * img).astype(np.uint8)
            img = np.clip(img, 0, 255)

            frame = av.VideoFrame.from_ndarray(img, format="rgb24")

            for packet in stream.encode(frame):
                container.mux(packet)

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

