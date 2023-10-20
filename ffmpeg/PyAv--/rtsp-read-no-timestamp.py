#!/usr/bin/env python3
# coding=utf-8
# date 2023-10-19 07:24:06
# author calllivecn <c-all@qq.com>

import time

import numpy as np

import av

video_out = "test-rtsp.mkv"
# video = "test-mpeg4.mp4"
# video = "rtsp://huawei.calllive.top:8554/live"
# video = "rtsp://huawei.calllive.top:8080/h264_opus.sdp"
video = "60s.mkv"

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
    "title": "这是我的测试视频".encode(),
}

out_container = av.open(video_out, mode="w")

# stream = container.add_stream("mpeg4", rate=fps)
# AVDeprecationWarning: VideoStream.framerate is deprecated as it is not always set; please use VideoStream.average_rate.
# stream = out_container.add_stream("mpeg4", rate=in_video_stream.average_rate) 
# stream = out_container.add_stream(template=in_video_stream)

# stream = out_container.add_stream("libx265", rate=in_video_stream.average_rate) 
stream = out_container.add_stream("libx265")
# hevc_nvenc 可能需要从源代编译。
# stream = out_container.add_stream("hevc_nvenc", rate=in_video_stream.average_rate) 

stream.options = {
    "crf": "30",
}
stream.pix_fmt = "gray"

# 添加黑白过滤
vfilter = av.filter.Graph()
# 创建缓冲源滤镜
vf1 = vfilter.add_buffer(template=in_video_stream)

# vf2 = vfilter.add("vfilp")
# 创建灰度滤镜
vf2 = vfilter.add("hue", "s=0")

vf1.link_to(vf2)

# 这个要放在link的最后
sink = vfilter.add('buffersink')

vf2.link_to(sink)

vfilter.configure()

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
    """
    for packet in in_container.demux((in_video_stream, in_audio_stream)):
        out_container.mux(packet)
    """

    # 获取输入流的时间基准
    in_time_base = in_video_stream.time_base
    out_time_base = stream.time_base


    t1 = time.time()
    # for packet in in_container.demux():
    for packet in in_container.demux((in_video_stream, in_audio_stream)):
        print(f"{dir(packet)=}\n{dir(packet.stream)=}\n{packet.stream.type=}")

        # 设置包的时间戳

        # 把视频转为黑白，第一次尝试

        if packet.stream.type == "video":
            for frame in packet.decode():
                # 重置时间戳
                frame.pts = frame.pts * out_time_base / in_time_base
                frame.dts = frame.dts * out_time_base / in_time_base

                vf1.push(frame)
                vfilter_frame = sink.pull()
                # 这个必须有 vfilter_frame.pts = 

                """
                # 把视频转为黑白，第二次尝试 (这种是可转，但是灰度和真正的gray有点不同。)
                # Convert the frame to grayscale
                gray_frame = frame.to_image().convert('L')
                
                # Convert the grayscale image back to a frame
                gray_frame = av.VideoFrame.from_image(gray_frame)
                
                # Copy the frame properties from the original frame
                gray_frame.pts = frame.pts
                gray_frame.time_base = frame.time_base
                """

                for out_packet in stream.encode(vfilter_frame):
                    out_container.mux(out_packet)

        elif packet.stream.type == "audio":
            out_container.mux(packet)
            # print("这是声音packet")
            # for frame in packet.decode():
            #     for out_packet in a_stream.encode(frame):
            #         out_container.mux(out_packet)

        if (time.time() - t1) > 60:
            break

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

