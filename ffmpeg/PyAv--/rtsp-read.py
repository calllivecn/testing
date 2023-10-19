#!/usr/bin/env python3
# coding=utf-8
# date 2023-10-19 07:24:06
# author calllivecn <c-all@qq.com>

import numpy as np

import av

video_out = "test-rtsp.mkv"
# video = "test-mpeg4.mp4"
# video = "rtsp://huawei.calllive.top:8554/live"
video = "rtsp://huawei.calllive.top:8080/h264_opus.sdp"

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

out_container = av.open(video_out, mode="w")
# stream = container.add_stream("mpeg4", rate=fps)
# AVDeprecationWarning: VideoStream.framerate is deprecated as it is not always set; please use VideoStream.average_rate.
# stream = out_container.add_stream("mpeg4", rate=in_video_stream.average_rate) 
# stream = out_container.add_stream("libx265", rate=in_video_stream.average_rate) 
stream = out_container.add_stream(template=in_video_stream)

# a_stream = out_container.add_stream("aac", rate=in_audio_stream.average_rate)
# 复用流，避免重新解码+编码
a_stream = out_container.add_stream(template=in_audio_stream)

# stream.width = in_video_stream.width
# stream.height = in_video_stream.height
# stream.pix_fmt = "yuv420p"

print(f"{dir(stream)=}\n")

# 使用多线程编码? 解码时这么用
# container.streams.video[0].thread_type = "AUTO"

try:

    # 直接 -acodec copy 
    for packet in in_container.demux((in_video_stream, in_audio_stream)):
    # for packet in in_container.demux((in_video_stream,)):
        out_container.mux(packet)


    """
    for packet in in_container.demux():
        # print(f"{dir(packet)=}\n{dir(packet.stream)=}\n{packet.stream.type=}")
        if packet.stream.type == "video":
            for frame in packet.decode():
                frame.pts = None
                frame.time_base = None
                for out_packet in stream.encode(frame):
                    out_container.mux(out_packet)

        elif packet.stream.type == "audio":
            # print("这是声音packet")
            for frame in packet.decode():
                frame.pts = None
                frame.time_base = None

                # out_packet = a_stream.encode(frame)
                for out_packet in a_stream.encode(frame):
                    out_container.mux(out_packet)
    """


    """
    for frame in in_container.decode(in_video_stream):
        frame.pts = None
        frame.time_base = None

        packet = stream.encode(frame)
        out_container.mux(packet)
    """

    """
    # 测试时间戳
    for frame in in_container.decode(in_video_stream):
        print(f"{dir(frame)=}\n{frame.pts=}\n{frame.time_base=}")
        if frame.pts != None:
            timestamp = frame.pts * frame.time_base
            print(f"{timestamp=}")
    """
        
except KeyboardInterrupt:
    print("结束录制, 写入剩下的数据。")


"""
# Flush stream
for out_packet in stream.encode():
    out_container.mux(out_packet)

for out_packet in a_stream.encode():
    out_container.mux(out_packet)
"""

in_container.close()

# Close the file
out_container.close()

