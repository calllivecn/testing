


import av


in_v = av.open("/dev/video0")

out_v = av.open("test.mkv", mode="w")

out_v.metadata["title"] = "从本地摄像头录制"


in_v_s = in_v.streams.video[0]

"""
# 和滤镜无关，还是会视频时长不准确
vfilter = av.filter.Graph()
# 创建缓冲源滤镜
vf1 = vfilter.add_buffer(template=in_v_s)
vf2 = vfilter.add("setpts")
vf1.link_to(vf2)
sink = vfilter.add('buffersink')
vf2.link_to(sink)
vfilter.configure()
"""



try:
    print(f"stream.type: {in_v_s.type}\n{in_v_s=}")
    print(f"{in_v_s.average_rate=}")
    out_s = out_v.add_stream("libx265", rate=in_v_s.average_rate)
    out_s.width = in_v_s.width
    out_s.height = in_v_s.height
    out_s.pix_fmt = "yuv420p"
    out_s.options = {
        # "crf": "10",
        # "profile": "main",
        # "preset": "ultrafast",
        "preset": "fast",
        # "bitrate": "8000",
    }


    first_time_pts = None
    first_time_dts = None

    for packet in in_v.demux(in_v_s):

        # print(f"{packet}\n{dir(packet)=}")

        for frame in packet.decode():

            # print(f"{frame=}\n{dir(frame)=}")

            # vf1.push(frame)
            # frame = vf2.pull()

            
            for packet_encode in out_s.encode(frame):
                
                """
                # 如果使用了这种方式，就有这个警告信息：播放时也不对。
                # “Timestamps are unset in a packet for stream 0. This is deprecated and will stop working in the future. Fix your code to set the timestamps properly
                # Encoder did not produce proper pts, making some up.”
                packet_encode.pts = None
                packet_encode.dts = None
                """

                """
                # 如果  pts < dts 就丢掉
                if packet_encode.pts < packet_encode.dts:
                    print(f"丢弃{packet_encode=}")
                    continue
                

                if first_time_pts is None:
                    first_time_pts = packet_encode.pts
                    packet_encode.pts = 0
                    first_time_dts = packet_encode.dts
                    packet_encode.dts = 0
                else:
                    packet_encode.pts -= first_time_pts
                    packet_encode.dts -= first_time_dts
                """
                
                print(f"{dir(packet_encode)=}\n{packet_encode.pts=} {packet_encode.dts=} {packet_encode.time_base=}")

                out_v.mux(packet_encode)

except KeyboardInterrupt:
    print("停止录制，写入数据...")

for packet_encode in out_s.encode():
    """
    packet_encode.pts = None
    packet_encode.dts = None

    packet_encode.pts -= first_time_pts
    packet_encode.dts -= first_time_dts
    """
    out_v.mux(packet_encode)

in_v.close()
out_v.close()

