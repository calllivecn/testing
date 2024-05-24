

"""
修复，直接从摄像头录制，文件持续时间，和开始播放时间不正确。
并修复"duration: 06:18:33.50, start: 22659.300000" 问题
"""

import sys
import signal
import traceback
from datetime import (
    datetime,
)

import av



EXIT = False

def exit_signal(sig, frame):
    global EXIT
    EXIT = True
    # print("使用信号退出")
    # print(f"signal: {frame=}")


signal.signal(signal.SIGINT, exit_signal)

def main2():


    # video = "srt://192.168.0.103:5000"

    try:
        video = sys.argv[1]
        filename = sys.argv[2]
    except IndexError:
        print("使用方法：{sys.argv[0]} <srt://server:port> <output.mkv>")
        sys.exit(1)

    options={
        "loglevel": "debug",
        }

    in_v = av.open(video, options=options, buffer_size=8<<20)

    print(f"{dir(in_v)=}")
    print(f"{in_v.flags=}")
    # in_v.flags |= Flags.IGNDTS
    # in_v.flags = Flags.AUTO_BSF
    # print(f"{in_v.flags=}")

    out_v = av.open(filename, mode="w")

    out_v.metadata["title"] = "从srt录制"
    out_v.metadata["datetime"] =  datetime.now().strftime("%Y-%m-%d %H-%M-%S")


    in_v_s = in_v.streams.video[0]
    print(f"stream.type: {in_v_s.type} {in_v_s=} {in_v_s.average_rate=}")

    out_v_stream = {}
    for s in in_v.streams:
        print(f"stream: {s} type:{s.type}")
        out_v_stream[s.type] = out_v.add_stream(template=s)



    try:
        demuxs = in_v.demux()
        for packet in demuxs:

            if packet.is_keyframe:
                # print(f"{packet=}, 是is_keyframe")
                pass
            else:
                # print(f"{packet=}")
                pass

            out_v.mux(packet)

            if EXIT:
                break

    except OSError as e:
        traceback.print_exception(e)

    finally:
        print("停止录制，写入数据...")

        in_v.close()
        out_v.close()

           
# main()
main2()
