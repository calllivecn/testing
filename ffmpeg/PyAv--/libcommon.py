

import os
import time
from pathlib import Path

from typing import (
    Tuple,
    Dict,
)

import av


class Stream_first_time:

    def __init__(self, first_time: bool, first_time_pts: int):
        self.first_time = first_time
        self.first_time_pts = first_time_pts
    
    def __str__(self):
        return f"{type(self)} --> {self.first_time} {self.first_time_pts}"
    

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

        self._stream_id_pts: Dict[int, Stream_first_time] = {}
        for s in self.in_container.streams:
            self._stream_id_pts[s.index] = Stream_first_time(True, 0)


    def is_output(self) -> bool:
        return not self.first_time


    def new_output(self, output_filename: Path = None):

        self.first_time = True

        for s in self.in_container.streams:
            self._stream_id_pts[s.index].first_time = True

        time_ = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
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
            # print(f"stream: {dir(s)=}")
            if s.type == "video":
                # self.out_container.add_stream(template=s)
                print(f"video stream: {s}")
            elif s.type == "audio":
                # self.out_container.add_stream(template=s)
                print(f"audio stream: {s}")
            else:
                # print("当前只添加一个视频流和一个音频流，其他的丢弃：type: {s.stream.type} stream:{s} ")
                print("其他流：type: {s.type} stream:{s} ")


            self.out_container.add_stream(template=s)


    def write(self, packet: av.Packet):
        self.out_container.mux(packet)       


    def write2(self, packet: av.Packet):

        if self.first_time:
            self.first_time = not self.first_time
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

        s = self._stream_id_pts[packet.stream_index]

        if s.first_time:
            s.first_time = not s.first_time
            s.first_time_pts = packet.pts

        if packet.dts is not None:
            packet.dts -= s.first_time_pts
        
        if packet.pts is not None:
            packet.pts -= s.first_time_pts


        self.out_container.mux(packet)
    


    def close(self):
        self.first_time = True
        self.out_container.close()
