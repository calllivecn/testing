#!/usr/bin/env python3
# coding=utf-8
# date 2023-10-27 00:01:00
# author calllivecn <calllivecn@outlook.com>

"""
在检测到动态后，视频流的前面没有一缓存，回看时体验差一点。
其他项目在改进。
"""


import sys
import time
import signal
import argparse
import traceback
from pathlib import Path


import av

from libcommon import (
    DynamicDetection,
    VideoFile,
)

EXIT = False

def exit_signal(sig, frame):
    global EXIT
    EXIT = True
    # print("使用信号退出")
    # print(f"signal: {frame=}")


# signal.signal(signal.SIGINT, exit_signal)
signal.signal(signal.SIGTERM, exit_signal)




def main():


    parse = argparse.ArgumentParser(usage="%(prog)s --video-url [videofile or protocol_url]")

    parse.add_argument("--video-url", dest="video", required=True, help="视频来源，是参考ffmpeg的.")
    parse.add_argument("--output-dir", dest="dir", type=Path, help="视频保存目录.")

    parse.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)
    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)

    args = parse.parse_args()


    if args.parse:
        print(args)
        sys.exit(0)

    FRAME_CHECK_INTERVAL = 1
    ERROR_WAIT = 30

    # 网络io, 或者ip摄像头没有上线时，sleep(30) 重新尝试连接。
    while True:
        try:

            in_container = av.open(args.video)
        except OSError as e:
            traceback.print_exception(e)
            print(f"可能网络波动，ip摄像头掉线. {ERROR_WAIT}秒后尝试重新连接.")
            time.sleep(ERROR_WAIT)
            continue
    
        try:
    
            # 设置使用多线程
            in_container.streams.video[0].thread_type = "AUTO"
    
            # v_s = in_container.streams.video[0]
            # print(f"{dir(v_s)=}\n{v_s=}")
            # print(f"{v_s.average_rate=}")
            # fps = round(float(v_s.average_rate), 0)
    
            # dd = DynamicDetection(fps)
            dd = DynamicDetection()
    
            vf = VideoFile(in_container)
    
            timeline_offset = 0
    

            for packet in in_container.demux():

                if packet.pts is None:
                    print(f"当前 packet.pts is None: {packet=}")
                    continue

                if packet.is_corrupt:
                    print(f"有数据包损坏: {packet=}")
                    continue

                if packet.is_discard:
                    print(f"当前有个可以丢弃，但不影响视频播放的: {packet=}")


                timeline = float(packet.pts * packet.time_base)

                if packet.stream.type == "video" and packet.is_keyframe and timeline >= (timeline_offset + FRAME_CHECK_INTERVAL):
                    timeline_offset = timeline

                    try:
                        frames = packet.decode()
                        # print(f"当前解码一个packet得到帧数: {len(frames)}")
                        # 在开始的开始也是可能，返回0个帧的。
                        for frame in frames:

                        # for frame in packet.decode():

                            # print(f"{frame.to_image()=}")
                            # <PIL.Image.Image image mode=RGB size=1920x1080 at 0x756D707F1990>

                            dd.detecion(frame)

                    # 也可能不是，试着从一个关键帧才开始decode() 这样可以。就是需要输入端的keyframe之间的时间间隔不要太长。
                    # 好像必须每个packet都decode() 不然，会报，如下：
                    except av.InvalidDataError as e:
                        traceback.print_exception(e)
                        print("decode() 到一个无效数据frame")


                if dd.record:
                    if vf.is_outputing():
                        # print(".", end="", flush=True)
                        vf.write3(packet)
                    else:
                        vf.new_output(args.dir)
                        print(f"开始新输出文件: {vf.filename}")
                        vf.write3(packet)


                else:
                    # 这里是不需要记录的packet
                    if vf.is_outputing():
                        print(f"关闭旧输出文件：{vf.filename}")
                        vf.close()


                if EXIT:
                    print("收尾工作...")
                    break

        except OSError as e:
            traceback.print_exception(e)
            print(f"可能网络波动，ip摄像头掉线. {ERROR_WAIT}秒后尝试重新连接.")
    
        except KeyboardInterrupt:
            print("手动结束工作...")
            break
    
        finally:
            print("收尾工作... done")
            in_container.close()
            if vf.is_outputing():
                vf.close()
    
        time.sleep(ERROR_WAIT)


if __name__ == "__main__":
    main()