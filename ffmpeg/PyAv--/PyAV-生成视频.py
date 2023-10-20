#!/usr/bin/env python3
# coding=utf-8
# date 2023-10-19 07:24:06
# author calllivecn <c-all@qq.com>

import numpy as np

import av


duration = 10
fps = 30
total_frames = duration * fps

container = av.open("test.mkv", mode="w")
container.title = "这是我的测试视频"

# stream = container.add_stream("mpeg4", rate=fps)
stream = container.add_stream("libx265", rate=fps)

# ~~stream = container.add_stream("hevc_nvenc", rate=fps)~~

#stream.width = 480
#stream.height = 320

stream.width = 1920
stream.height = 1080
stream.pix_fmt = "yuv420p"

# 使用多线程编码? 解码时这么用
# container.streams.video[0].thread_type = "AUTO"


print("CTRL+C 停止生成")
try:
    count = 1
    while True:
        for frame_i in range(total_frames):

            img = np.empty((stream.width, stream.height, 3))
            img[:, :, 0] = 0.5 + 0.5 * np.sin(2 * np.pi * (0 / 3 + frame_i / total_frames))
            img[:, :, 1] = 0.5 + 0.5 * np.sin(2 * np.pi * (1 / 3 + frame_i / total_frames))
            img[:, :, 2] = 0.5 + 0.5 * np.sin(2 * np.pi * (2 / 3 + frame_i / total_frames))

            img = np.round(255 * img).astype(np.uint8)
            img = np.clip(img, 0, 255)

            frame = av.VideoFrame.from_ndarray(img, format="rgb24")

            # for packet in stream.encode(frame):
                # container.mux(packet)

            packet = stream.encode(frame)
            container.mux(packet)


except KeyboardInterrupt:
    print(f"{container.streams.video[0].thread_type=}")
    print("停止生成")


# Flush stream
for packet in stream.encode():
    container.mux(packet)

# Close the file
container.close()

