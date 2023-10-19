#!/usr/bin/env python3
# coding=utf-8
# date 2022-12-11 14:41:26
# author calllivecn <c-all@qq.com>


import numpy as np

import av

duration = 10
fps = 30
total_frames = duration * fps

container = av.open('test.mp4', mode='w')

stream = container.add_stream('mpeg4', rate=fps)
# stream = container.add_stream('hevc', rate=fps)

stream.width = 1920
stream.height = 1080
stream.pix_fmt = 'yuv420p'

codec = av.Codec("hevc", "w")

print(codec)
print(dir(codec))
#container.close();exit(1);

#stream.thread_type = "AUTO"

img = np.zeros((stream.width, stream.height, 3), dtype=np.uint8)
for frame_i in range(total_frames):
    img = np.empty((stream.width, stream.height, 3))
    img[:, :, 0] = 0.5 + 0.5 * np.sin(2 * np.pi * (0 / 3 + frame_i / total_frames))
    img[:, :, 1] = 0.5 + 0.5 * np.sin(2 * np.pi * (1 / 3 + frame_i / total_frames))
    img[:, :, 2] = 0.5 + 0.5 * np.sin(2 * np.pi * (2 / 3 + frame_i / total_frames))

    img = np.round(255 * img).astype(np.uint8)
    img = np.clip(img, 0, 255)

    frame = av.VideoFrame.from_ndarray(img, format='rgb24')
    for packet in stream.encode(frame):
       container.mux(packet)

#Flush stream
for packet in stream.encode():
    container.mux(packet)

container.close()
