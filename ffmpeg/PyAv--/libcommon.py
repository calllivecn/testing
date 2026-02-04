

import os
import time
from pathlib import Path
from fractions import Fraction

from typing import (
    Tuple,
    Dict,
)


import cv2
import av
from av.container import Container


class DynamicDetection:
    """
    在记录时间间隔上需要区别是视频文件，还是实时推流。
    当前先处理实时推流。
    """

    # def __init__(self, history_fps: int, threshold: int = 50, areasize :int = 800):
        # self.fps = history_fps

    def __init__(self, threshold: float = 50.0, areasize: float = 800.0):

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

        # if not self.is_detection():
            # return  False

        frame = cv2.cvtColor(frame.to_ndarray() , cv2.COLOR_RGB2BGR)
        #应用背景减法器，检测动态物体
        self.fgmask = self.fgbg.apply(frame)

        # 如果是初始化的第一帧，做初始化，就不用对比了。
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
    
ANDROID_TIMESTAMP_UNIT = 1000000 # 和输入源相同 这里是安卓的 时间戳 单位
# 新输出容器重新开始时间线
class ReTimeline:

    """
    请注意，帧时间戳设置将根据帧速率进行设置
    这些在使用本地摄像头时需要吗？可以调整和不调整
    """

    def __init__(self):
        pass

    def set_video(self, time_base: Fraction, fps: int):
    # def set_video(self, fps: int):

        self.first_time = True
        # 音频和视频共用，保存同步
        self.first_timestamp = 0
        self.time_base = time_base

        self.last_dts = -1
        # 估算每帧的 DTS 增量
        self.dts_step = int(self.time_base / fps)

    def set_audio(self, audio_time_base: Fraction):
        """
        audio_time_base: 就是 Fraction(1, audio_smaple_rate)
        """
        self.first_audio_time = True
        self.first_audio_timestamp = 0
        self.audio_time_base = audio_time_base

        self.last_audio_pts = -1

    def video(self, packet: av.Packet) -> av.Packet:
        """
        return: packet
        """
        # logger.debug(f"时间戳 ：{timestamp=}")
        if packet.pts is None:
            raise ValueError("packet.pts 不能为None")

        # 安卓9. 第一帧输出配置文件时，timestamp会是0
        # 安卓14. 第一帧输出配置文件时，timestamp会是和接下来的视频帧相同。

        if self.first_time and packet.pts != 0:
            self.first_time = False
            self.first_timestamp = packet.pts
        
        # 归零并转换单位
        rel_us = packet.pts - self.first_timestamp
        # 这里的计算公式： us * (time_base.den) / (1,000,000 * time_base.num)
        # 简化后: us * 90000 / 1000000 = us * 0.09
        # pts = int(rel_us * self.time_base.denominator / (ANDROID_TIMESTAMP_UNIT * self.time_base.numerator))
        pts = rel_us

        packet.pts = pts
        packet.dts = pts # 对于无B帧的情况

        calc_dts = self.last_dts + self.dts_step
        
        # 如果计算出的 DTS 居然比 PTS 还大（极少见，除非帧率设定错误或 PTS 回跳严重），需要 Clamp
        if calc_dts > pts:
            # 这种情况下，说明 PTS 跳变了，或者 B 帧间隔很大。
            # 为了安全，尽量保持 DTS 递增，但不能超过 PTS。
            # 如果这行触发，说明可能存在严重的卡顿或时间戳跳变
            calc_dts = pts 
        
        packet.dts = calc_dts
        self.last_dts = calc_dts
        
        # 设置 duration (有助于播放器 seek)
        # packet.duration = self.dts_step

        packet.time_base = self.time_base
        # logger.debug(f"处理后 PTS DTS：{packet.pts=} {packet.dts=} {pts=} {running=}")
        return packet


    def audio(self, packet: av.Packet) -> av.Packet:

        if packet.pts is None:
            raise ValueError("packet.pts 不能为None")

        if self.first_audio_time:
            self.first_audio_time = False
            self.first_audio_timestamp = packet.pts

        pts = packet.pts - self.first_audio_timestamp

        # 4. 修正单调性 (音频虽然没有B帧，但 MediaCodec 有时也会抖动)
        if pts <= self.last_audio_pts:
            pts = self.last_audio_pts + 1  # 强制 +1 (即 1个采样点，影响极小)

        packet.pts = pts
        packet.dts = pts

        self.last_audio_pts = pts

        packet.time_base = self.audio_time_base

        return packet


class Stream_first_time:

    def __init__(self, first_time: bool, first_time_pts: int):
        self.first_time = first_time
        self.first_time_pts = first_time_pts
    
    def __str__(self):
        return f"{type(self)} --> {self.first_time} {self.first_time_pts}"
    

class VideoFile:

    def __init__(self, in_container: Container, videoformat=".mkv"):
        """
        1. 需要处理视频分割，
        2. 处理每帧的时间戳
        """

        self.in_container = in_container

        self.suffix = videoformat

        self.first_time = True
        self.first_time_pts = 0

        self.output: bool = False

        self._stream_id_pts: Dict[int, Stream_first_time] = {}
        for s in self.in_container.streams:
            self._stream_id_pts[s.index] = Stream_first_time(True, 0)


    def is_outputing(self) -> bool:
        return self.output


    def new_output(self, output_filename: Path = None):

        self.first_time = True

        self.output = True

        for s in self.in_container.streams:
            self._stream_id_pts[s.index].first_time = True

        time_ = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())

        if output_filename is not None:
            self.filename = output_filename / f"{time_}{self.suffix}"
        else:
            self.filename = Path(f"{time_}{self.suffix}")
        
        count = 0
        while self.filename.exists():
            self.filename = Path(f"{time_}_{count:04}{self.suffix}")
            count += 1

        self.out_container = av.open(str(self.filename), mode="w")

        self.copy_stream()
    
    # 复制流
    def copy_stream(self):

        for s in self.in_container.streams:
            """
            print(f"stream: {dir(s)=}")
            if s.type == "video":
                self.out_container.add_stream(template=s)
                print(f"video stream: {s}")
            elif s.type == "audio":
                self.out_container.add_stream(template=s)
                print(f"audio stream: {s}")
            else:
                print("当前只添加一个视频流和一个音频流，其他的丢弃：type: {s.stream.type} stream:{s} ")
                print("其他流：type: {s.type} stream:{s} ")
            """

            self.out_container.add_stream(template=s)


    def write(self, packet: av.Packet):
        self.out_container.mux(packet)       


    def write2(self, packet: av.Packet):

        if self.first_time:
            self.first_time = False
            self.first_time_pts = packet.pts

        if packet.dts is not None:
            packet.dts -= self.first_time_pts
        
        if packet.pts is not None:
            packet.pts -= self.first_time_pts

        self.out_container.mux(packet)
    

    def write3(self, packet: av.Packet):

        """
        每个流都需要有自己的 first_time
        """

        if self.first_time:
            self.first_time = False

        s = self._stream_id_pts[packet.stream_index]

        if s.first_time:
            s.first_time = False
            s.first_time_pts = packet.pts

        if packet.dts is not None:
            packet.dts -= s.first_time_pts
        
        if packet.pts is not None:
            packet.pts -= s.first_time_pts


        self.out_container.mux(packet)
    


    def close(self):
        self.first_time = True
        self.output = False
        self.out_container.close()

