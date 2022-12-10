#!/usr/bin/env python3
# coding=utf-8
# date 2022-12-11 14:41:26
# author calllivecn <c-all@qq.com>


import numpy as np

import av

duration = 256
fps = 10
total_frames = duration * fps
container = av.open('test.mp4', mode='w')
# container = av.open('test.mkv', mode='w')
stream = container.add_stream('mpeg4', rate=fps)
# stream = container.add_stream('hevc', rate=fps)

stream.width = 1920
stream.height = 1080
stream.pix_fmt = 'yuv420p'

codec = av.Codec("hevc", "w")
print(codec)
print(dir(codec))
container.close();exit(1);

stream.thread_type = "AUTO"

img = np.zeros((stream.width, stream.height, 3), dtype=np.uint8)
for r in range(0, 256, 10):
    print("="*40)
    print(f"r:", r)
    for g in range(0, 256, 10):
        print(f"g:", r, g)
        for b in range(0, 256, 10):
            img[:, :, 0] = r
            img[:, :, 1] = g
            img[:, :, 2] = b

            frame = av.VideoFrame.from_ndarray(img, format='rgb24')
            for packet in stream.encode(frame):
               container.mux(packet)
#Flush stream
for packet in stream.encode():
    container.mux(packet)

container.close()