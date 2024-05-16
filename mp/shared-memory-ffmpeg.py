#!/usr/bin/env python3
# coding=utf-8
# date 2023-05-07 23:12:51
# author calllivecn <calllivecn@outlook.com>

import os
import time
import pprint

from multiprocessing import shared_memory

import ffmpeg

size = 500*(1<20)
sm1g = shared_memory.SharedMemory("calllivecn", True, size)

file = "/home/zx/video/鲁路修/R1-01-5m.mp4"

video_info = ffmpeg.probe(file)
# print("video_info: ")
# pprint.pprint(video_info)


reader = (
    ffmpeg.input(file)
    .output("pipe:", format="rawvideo", pix_fmt="rgb24", vcodec="hevc_cuvid")
    .run_async(pipe_stdin=True, pipe_stdout=True)

)



fd = reader.stdout.fileno()

t1 = time.time()
total_n = 0
while (n := os.readv(fd, [sm1g.buf])) != 0:

    total_n += n
    t2 = time.time()
    if (t2 - t1) > 1.0:
        print(f"\n{total_n / (1<<20)}M/s")
        total_n = 0
        t1 = t2

sm1g.close()
sm1g.unlink()