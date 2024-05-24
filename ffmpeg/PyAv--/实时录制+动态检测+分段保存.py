#!/usr/bin/env python3
# coding=utf-8
# date 2023-10-27 00:01:00
# author calllivecn <calllivecn@outlook.com>


import os
import sys
import time
import signal
import argparse
from pathlib import Path


import av
import cv2
import numpy as np



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
        self.fgbg = cv2.createBackgroundSubtractorMOG2(2)

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
    

    def detecion(self, frame):

        if not self.is_detection():
            return 

        frame = self.PIL2CV_IMG(frame)

        self.change = False

        #应用背景减法器，检测动态物体
        self.fgmask = self.fgbg.apply(frame)
        
        # 通过阈值处理二值化图像
        result, binary_image = cv2.threshold(self.fgmask, self.threshold, 255, cv2.THRESH_BINARY)

        # 查找二进制图像中的轮廓
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 绘制边界框
        for contour in contours:
            if cv2.contourArea(contour) > self.areasize:  # 调整面积阈值以过滤小轮廓
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 4)
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
            
            if self.record:
                self.start_record_timestamp = time.time()
            else:
                self.record = True
        else:
            if self.record:
                if (time.time() - self.start_record_timestamp) >= self.stop_record_time:
                    self.record = False


        return self.change
    

    def is_detection(self):
        end = time.time()
        if (end - self.start) > self.detecion_interval:
            self.start = end
            return True
        else:
            return False


    def __bool__(self):
        return self.change
    

    def is_record(self):
        return self.record
    

    def PIL2CV_IMG(self, frame):

        image_array = np.array(frame)

        # 检查颜色空间
        if frame.mode == 'RGBA':
            # 图像使用 RGBA 颜色空间
            image_array = frame.convert('RGB')

        img = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

        return img






class VideoFile:

    def __init__(self, in_container: av.CodecContext, videoformat=".mkv"):
        """
        1. 需要处理视频分割，
        2. 处理每帧的时间戳
        """

        self.in_container = in_container

        self.suffix = videoformat

        self.first_time = True
        self.first_time_pts = 0

        self._is_output = False
    

    def is_output(self) -> bool:
        return self._is_output


    def new_split_output(self):

        self._is_output = True

        self.filename = Path(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()) + self.suffix)
        if self.filename.exists():
            os.remove(self.filename)

        self.out_container = av.open(str(self.filename), mode="w")

        self.copy_stream()
    
    # 复制流
    def copy_stream(self):

        for s in self.in_container.streams:
            # print(f"stream: {dir(s)=}")
            if s.type == "video":
                self.out_container.add_stream(template=s)
            elif s.type == "audio":
                self.out_container.add_stream(template=s)
            else:
                print("当前只添加一个视频流和一个音频流，其他的丢弃：type: {s.stream.type} stream:{s} ")


    def write(self, packet: av.Packet):
        """
        给DTS 或者 PTS 顺序不对的, 比如： rtsp 使用的
        """

        if self.first_time:
            self.first_time_pts = packet.pts

        if packet.dts is not None:
            packet.dts -= self.first_time_pts
        
        if packet.pts is not None:
            packet.pts -= self.first_time_pts

        self.out_container.mux(packet)       
    
    def write2(self, packet: av.Packet):
        self.out_container.mux(packet)       


    def close(self):
        self._is_output = True
        self.out_container.close()




def main():


    parse = argparse.ArgumentParser(usage="%(prog)s --video-src [videofile or protocol_url]")

    parse.add_argument("--video-src", dest="video", required=True, help="视频来源，是参考ffmpeg的.")

    parse.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)
    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)

    args = parse.parse_args()

    if args.parse:
        print(args)
        sys.exit(0)


    in_container = av.open(args.video)

    v_s = in_container.streams.video[0]

    print(f"{dir(v_s)=}\n{v_s=}")

    print(f"{v_s.average_rate=}")
    # fps = round(float(v_s.average_rate), 0)
    # dd = DynamicDetection(fps)
    dd = DynamicDetection()


    vf = VideoFile(in_container)

    for packet in in_container.demux():

        if EXIT:
            break

        for frame in packet.decode():

            if isinstance(frame, av.AudioFrame):
                # print(f"一个音频帧, 跳过")
                continue
        
            
            # print(f"{frame.to_image()=}")
            # <PIL.Image.Image image mode=RGB size=1920x1080 at 0x756D707F1990>

            dd.detecion(frame.to_image())

        if dd.is_record():
            if vf.is_output():
                vf.write2(packet)
            else:
                vf.new_split_output()

        else:
            if vf.is_output():
                vf.close()



if __name__ == "__main__":
    main()