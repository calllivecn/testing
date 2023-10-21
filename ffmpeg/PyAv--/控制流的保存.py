#!/usr/bin/env python3
# coding=utf-8
# date 2023-10-19 07:24:06
# author calllivecn <c-all@qq.com>

import time

import numpy as np

import av

# video = "test-mpeg4.mp4"
video = "60s.mkv"

video_out = "test.mkv"

options = {
    "rtsp_transport": "tcp",
    # "stimeout": str(10*(1e6)),
    # "probesize": "128M",
    # "analyzeduration": "0.1",
}

in_container = av.open(video, options=options)
in_video_stream = in_container.streams.video[0]
in_audio_stream = in_container.streams.audio[0]
# print(f"{dir(in_audio_stream)=}\n{in_audio_stream.average_rate=}")

opt = {
    "title": "这是我的测试视频",
}

out_container = av.open(video_out, mode="w")

# stream = container.add_stream("mpeg4", rate=fps)
# AVDeprecationWarning: VideoStream.framerate is deprecated as it is not always set; please use VideoStream.average_rate.
# stream = out_container.add_stream("mpeg4", rate=in_video_stream.average_rate) 
stream = out_container.add_stream(template=in_video_stream)

# stream = out_container.add_stream("libx265", rate=in_video_stream.average_rate) 
# stream = out_container.add_stream("libx265")

# stream.options = {
#     "crf": "30",
# }
# stream.pix_fmt = "gray"

# a_stream = out_container.add_stream("aac", rate=in_audio_stream.average_rate)
# 复用流，避免重新解码+编码
a_stream = out_container.add_stream(template=in_audio_stream)

stream.width = in_video_stream.width
stream.height = in_video_stream.height
# stream.pix_fmt = "yuv420p"

# print(f"{dir(stream)=}\n")

# 使用多线程编码? 解码时这么用
# container.streams.video[0].thread_type = "AUTO"

try:

    # 直接 -vcodec copy + -acodec copy
    for packet in in_container.demux((in_video_stream, in_audio_stream)):

        out_container.mux(packet)

except KeyboardInterrupt:
    print("结束录制, 写入剩下的数据。")


# Flush stream
for out_packet in stream.encode():
    out_container.mux(out_packet)

# for out_packet in a_stream.encode():
    # out_container.mux(out_packet)

in_container.close()

# Close the file
out_container.close()

