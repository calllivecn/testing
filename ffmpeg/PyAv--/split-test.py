#!/usr/bin/env python3
# coding=utf-8
# date 2023-10-23 16:19:04
# author calllivecn <calllivecn@outlook.com>

"""
按时间长度，切割文件，
并修复"uration: 06:18:33.50, start: 22659.300000" 问题
实验成功。：2023-10-23
"""

import time

import av

inputContainer = av.open("test.mkv", "r")
in_stream = inputContainer.streams.video[0]

av_options = {'avoid_negative_ts': '1'}

frag_length = 20.0 # 要切割的时长, 秒钟

metadata = {
    "title": "这是我的测试视频",
}

out_container = None

def start_container(timestamp):
    global out_container
    filename = "test_out_" + str(timestamp) + ".mkv"
    print(f"新文件：{filename}")
    out_container = av.open(filename, "w")
    out_container.metadata.update(metadata)

    for s in inputContainer.streams:
        out_stream = out_container.add_stream(template=s)


def stop_container():
    global out_container
    out_container.close()
    out_container = None




def main():

    first_pts = True

    for packet in inputContainer.demux():

        if packet.dts is None:
            print(f"开始的packete有空： {packet=}")
            # packet.dts = packet.pts
        
        if packet.size == 0:
            print("转换结束")
            break

        if first_pts:
            first_pts = False
            frag_pts = packet.pts
            frag_offset = float(packet.pts * packet.time_base)


        cur_time = float(packet.pts * packet.time_base)
        orig_pts = packet.pts

        print(f"cont: {orig_pts=}, {packet.time_base=}, {cur_time=}")

        # 开始割切的文件
        if out_container is None:
            start_container(frag_offset)
        
        if cur_time >= frag_offset + frag_length and packet.is_keyframe:
            frag_offset = cur_time
            frag_pts = orig_pts
            # 结束当前文件
            stop_container()
        else:
            if packet.dts is not None:
                packet.dts -= frag_pts
            
            if packet.pts is not None:
                packet.pts -= frag_pts
            
            print(f"{packet.pts=} {packet.dts=}")
            out_container.mux(packet)
            

if __name__ == "__main__":
    main()