#!/usr/bin/env python3
# coding=utf-8
# date 2023-10-19 07:24:06
# author calllivecn <c-all@qq.com>

import time
import threading

# import numpy as np
import av

video = "120s.mkv"
video_out = "test-split-time.mkv"

options = {
    # "rtsp_transport": "tcp",
    # "stimeout": str(10*(1e6)),
    # "probesize": "128M",
    # "analyzeduration": "0.1",
}

in_container = av.open(video, options=options)

metadata = {
    "title": "这是我的测试视频",
}


out_container = None

def start_container(timestamp):
    global out_container
    filename = "file_" + str(timestamp) + ".mkv"
    print(f"新文件：{filename}")
    out_container = av.open(filename, "w")
    out_container.metadata.update(metadata)

    for s in in_container.streams:
        out_stream = out_container.add_stream(template=s)


def stop_container():
    global out_container
    out_container.close()
    out_container = None



first_packet = True
rescaling_nr = 0
split_time = 30 # 30s
first_frame_timestamp = int(time.time() * 1000)

# 按30s 分割视频
try:

    start = time.time()
    # 直接 -vcodec copy + -acodec copy
    for packet in in_container.demux():

        if not packet.is_keyframe:
            print(f"开始的，不是关键帧，丢掉： {packet=}")
            continue

        cur_timestamp = int(time.time() * 1000)
        # cur_timestamp = time.time()
        if (cur_timestamp - first_frame_timestamp) >= split_time and packet.is_keyframe:
            stop_container()
        
        if out_container is None:
            rescaling_nr = packet.dts
            start_container(int(cur_timestamp))
            first_frame_timestamp = cur_timestamp
        
        # first_frame_timestamp = cur_timestamp

        print(f"{packet.stream.type} {packet.pts=} {packet.dts=}")

        # packet.pts -= rescaling_nr 
        # packet.dts -= rescaling_nr

        out_container.mux(packet)

except KeyboardInterrupt:
    print("结束录制, 写入剩下的数据。")


in_container.close()
# out_container.close()
