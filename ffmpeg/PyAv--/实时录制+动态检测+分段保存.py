#!/usr/bin/env python3
# coding=utf-8
# date 2023-10-27 00:01:00
# author calllivecn <calllivecn@outlook.com>


import os
import sys
import time
import signal
import argparse
import traceback
from pathlib import Path


import av
import cv2
import numpy as np


from libcommon import (
    VideoFile,
)

EXIT = False

def exit_signal(sig, frame):
    global EXIT
    EXIT = True
    # print("使用信号退出")
    # print(f"signal: {frame=}")


signal.signal(signal.SIGINT, exit_signal)
signal.signal(signal.SIGTERM, exit_signal)



class DynamicDetection:
    """
    在记录时间间隔上需要区别是视频文件，还是实时推流。
    当前先处理实时推流。
    """

    # def __init__(self, history_fps: int, threshold: int = 50, areasize :int = 800):
        # self.fps = history_fps

    def __init__(self, threshold: int = 50, areasize :int = 800):

        # 调整阈值以适应场景
        self.threshold = threshold
        # 调整面积阈值以过滤小轮廓
        self.areasize = areasize

        # 创建背景减法器
        # self.fgbg = cv2.createBackgroundSubtractorMOG2(history=round(self.fps))
        self.fgbg = cv2.createBackgroundSubtractorMOG2(10)

        # 是否录制的状态
        self.record = False

        # 画面是否变化（是否检测到运动)
        self.change = False

        self.fgmask = None

        self.detecion_interval = 1
        self.start = time.time()

        # 进入录制状态后，连续N秒钟没有变化才停止录制。
        self.stop_record_time = 10

        self.start_record_timestamp = 0

        self.frist_time = True
    

    def detecion(self, frame: av.VideoFrame) -> bool:
        # frame: av.VideoFrame

        # if not self.is_detection():
            # return  False

        frame = cv2.cvtColor(frame.to_ndarray() , cv2.COLOR_RGB2BGR)


        #应用背景减法器，检测动态物体
        self.fgmask = self.fgbg.apply(frame)

        # 如果是初始化的第一帧，就不用记录了。
        if self.frist_time:
            self.frist_time = False
            return False
        
        # 通过阈值处理二值化图像
        result, binary_image = cv2.threshold(self.fgmask, self.threshold, 255, cv2.THRESH_BINARY)

        # 查找二进制图像中的轮廓
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        self.change = False
        # 绘制边界框
        for contour in contours:
            if cv2.contourArea(contour) > self.areasize:  # 调整面积阈值以过滤小轮廓
                # debug时，可以使用下面的代码画出变化的位置
                # x, y, w, h = cv2.boundingRect(contour)
                # cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 4)
                self.change = True

        """
        这里的动作是：
        1. 如果画面变化，查看是否是录制状态，如果不是录制状态就进入录制状态。
        2. 如果画面没有变化，查看是否是录制状态：
            如果是录制状态，比较录制开始时间戳和当前时间的差，有没有大于 self.stop_record_time 。
                如果大于就停止录制，否则，不操作。
            如果不是录制状态, 不操作。
        """
        if self.change:
            
            self.start_record_timestamp = time.time()

            if self.record:
                pass
            else:
                self.record = True
        else:
            if self.record:
                if (time.time() - self.start_record_timestamp) >= self.stop_record_time:
                    self.record = False


        return self.change
    

    def is_detection(self):

        if self.start == 0:
            self.start = time.time()
            return True

        end = time.time()
        if (end - self.start) > self.detecion_interval:
            self.start = end
            return True
        else:
            return False


    def __bool__(self):
        return self.change
    



def main():


    parse = argparse.ArgumentParser(usage="%(prog)s --video-url [videofile or protocol_url]")

    parse.add_argument("--video-url", dest="video", required=True, help="视频来源，是参考ffmpeg的.")

    parse.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)
    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)

    args = parse.parse_args()


    if args.parse:
        print(args)
        sys.exit(0)

    FRAME_CHECK_INTERVAL = 1

    in_container = av.open(args.video)

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
                vf.new_output()
                print(f"开始新输出文件: {vf.filename}")
                vf.write3(packet)


        else:
            # 这里是不需要记录的packet
            if vf.is_outputing():
                print(f"关闭旧前输出文件：{vf.filename}")
                vf.close()
        

        if EXIT:
            print("收尾工作...")
            break


    if vf.is_outputing():
        vf.close()
    
    print("收尾工作... done")


if __name__ == "__main__":
    main()