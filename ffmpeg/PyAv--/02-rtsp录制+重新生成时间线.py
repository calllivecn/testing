

"""
修复，直接从摄像头录制，文件持续时间，和开始播放时间不正确。
并修复"duration: 06:18:33.50, start: 22659.300000" 问题

这个文件不能正常工作

update: 2024-05-25

这个测试有问题，RTSP 会有PTS错误问题。现在使用新的RST协议 。
"""


import sys
import signal
from datetime import (
    datetime,
)

import av
from av.container import Flags

from libcommon import (
    VideoFile,
    ReTimeline,
)

# video = "rtsp://192.168.0.103:5554" # 使用rtsp 还是有问题，在有音频时，还是报退出。

video = sys.argv[1]

options={
    "loglevel": "debug", # 这个没有用呀
    "rtsp_transport": "tcp",
    }


in_v = av.open(video, options=options, buffer_size=8<<20)

print(f"{dir(in_v)=}")
# print(f"{in_v.flags=}")

fps = 30
# 拿到平均帧率
v_s = in_v.streams.video[0]
if v_s.average_rate is None:
    if fps is None:
        raise ValueError("视频流 stream.average_rate为None, 需要手动指定fps.")

print(f"{fps=}")

a_s = in_v.streams.audio[0]

out_v = av.open("test.mkv", mode="w")

out_v_s = out_v.add_stream_from_template(v_s)
out_a_s = out_v.add_stream_from_template(a_s)

time_ = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
out_v.metadata["title"] = "从rtsp录制: {time_}"
out_v.metadata["datetime"] =  time_

EXIT = False

def exit_signal(sig, frame):
    global EXIT
    EXIT = True


signal.signal(signal.SIGINT, exit_signal)

def main():

    retimeline = ReTimeline()

    retimeline.set_video(v_s.time_base, fps)

    retimeline.set_audio(a_s.time_base)

    for packet in in_v.demux():

        if packet.pts is None:
            continue

        print(f"当前流：{packet=} {packet.time_base=}")

        if packet.stream.type == "video":
            retimeline.video(packet)
            packet.stream = out_v_s
        elif packet.stream.type == "audio":
            retimeline.audio(packet)
            packet.stream = out_a_s
        
        else:
            print(f"当前不支持流类型：{packet.stream.type=}")

        if EXIT and packet.is_keyframe:
            break

        out_v.mux(packet)


    print("停止录制，写入数据...")
    in_v.close()


main()
