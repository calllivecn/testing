#!/usr/bin/env python3
# coding=utf-8
# date 2024-04-28 01:18:05
# author calllivecn <callliveout@outlook.com>

import sys

import av


def test():
    v = "/dev/video0" if len(sys.argv) == 1 else sys.argv[1]
    cap = av.open(v)
    stream = cap.streams[0]

    resolutions = []
    for resolution in stream.codec_info.resolutions:
        width = resolution.width
        height = resolution.height
        resolutions.append((width, height))

    framerates = []
    for framerate in stream.codec_info.framerates:
        framerates.append(framerate)

    print(f"设备：{v}")
    print(f"支持的分辨率：{resolutions}")
    print(f"支持的帧率：{framerates}")

    cap.close()


test()