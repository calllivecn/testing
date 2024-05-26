

"""
修复，直接从摄像头录制，文件持续时间，和开始播放时间不正确。
并修复"duration: 06:18:33.50, start: 22659.300000" 问题
直接使用 srt:// 协议就没有这个问题了。
"""

import sys
import time
import signal
import traceback
# from pathlib import Path
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
signal.signal(signal.SIGTERM, exit_signal)

def record(url_srt: str, filename: str):

    options={
        "loglevel": "debug",
        }

    in_v = av.open(url_srt, options=options, buffer_size=8<<20)

    # print(f"{dir(in_v)=}")
    # print(f"{in_v.flags=}")
    # in_v.flags |= Flags.IGNDTS
    # in_v.flags = Flags.AUTO_BSF
    # print(f"{in_v.flags=}")

    out_v = av.open(filename, mode="w")

    time_ = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    out_v.metadata["title"] = f"录制时间：{time_}"
    out_v.metadata["datetime"] = time_


    in_v_s = in_v.streams.video[0]
    print(f"stream.type: {in_v_s.type} {in_v_s=} {in_v_s.average_rate=}")

    out_v_stream = {}
    for s in in_v.streams:
        print(f"stream: {s} type:{s.type}")
        out_v_stream[s.type] = out_v.add_stream(template=s)


    try:
        demuxs = in_v.demux()
        for packet in demuxs:

            if packet.is_corrupt:
                print(f"有数据包损坏: {packet=}")
                continue

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
        raise e

    finally:
        print("停止录制，写入数据...")

        in_v.close()
        out_v.close()

           
def main():

    import argparse

    parse = argparse.ArgumentParser(usage="%(prog)s [--suffix <srt-camera>] --video-url <srt://192.168.1.1:5000>")

    parse.add_argument("--video-url", dest="video", required=True, help="视频来源，参考ffmpeg的demuxer.")
    parse.add_argument("--suffix", help="视频文件名前缀")

    parse.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)
    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)

    args = parse.parse_args()


    if args.parse:
        print(args)
        sys.exit(0)


    while True:
        time_ = datetime.now().strftime("%Y-%m-%d %H-%M-%S")

        if args.suffix:
            filename = f"{args.suffix}_{time_}.mkv"
        else:
            filename = f"{time_}.mkv"
        

        try:
            record(args.video, filename)

        except KeyboardInterrupt:
            break

        except Exception as e:
            traceback.print_exception(e)

        if EXIT:
            break

        print("30s 后尝试重新连接")
        time.sleep(30)


if __name__ == "__main__":
    main()
