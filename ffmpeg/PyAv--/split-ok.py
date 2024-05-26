#!/usr/bin/env python3
# coding=utf-8
# date 2023-10-23 16:19:04
# author calllivecn <calllivecn@outlook.com>

"""
按时间长度，切割文件，
并修复"uration: 06:18:33.50, start: 22659.300000" 问题
实验视频分段成功。可以音频被弄的不同步了：2024-05-25

"""

import sys
import time

import av


from libcommon import (
    VideoFile,
)


def main():

    inputContainer = av.open(sys.argv[1], "r")

    try:
         split_time_length = float(sys.argv[2])
    except Exception:
        split_time_length = 60.0 # 要切割的时长, 秒钟

    metadata = {
        "title": "这是测试视频",
    }


    timeline_offset = 0

    vf = VideoFile(inputContainer)
    vf.new_output()

    for packet in inputContainer.demux():

        if packet.pts is None:
            print(f"当前 packet.pts is None: {packet=}")
            continue


        cur_timeline = float(packet.pts * packet.time_base)

        # print(f"cont: {packet.time_base=}, {cur_timeline=}, {packet.stream.type=}, {packet.pos=}, {packet=}")
        
        """
        0. 如果是关键帧，就可以开始或者结束新的录制了。
        1. 当录制时间>= 分段时间时，并且是关键帧时，可以结束旧录制，开始新录制了。
        2. 当前是否在录制中。
        """
        
        if packet.is_keyframe and packet.stream.type == "video":

            if cur_timeline >= (timeline_offset + split_time_length):
                # 在结束这个分段了
                    timeline_offset = cur_timeline
                    # 结束当前文件
                    vf.close()
                    # 同时也是下一个分段的开始
                    vf.new_output()
                    print(f"开始新的写入: {packet.time_base=}, {cur_timeline=}, {packet.stream.type=}, {packet.pos=}, {packet=}")
                    vf.write3(packet)
            else:
                 vf.write3(packet)

        else:
            vf.write3(packet)
        
    
    if vf.is_output():
        vf.close()
            

if __name__ == "__main__":
    main()
