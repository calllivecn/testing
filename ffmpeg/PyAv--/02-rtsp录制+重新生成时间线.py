

"""
修复，直接从摄像头录制，文件持续时间，和开始播放时间不正确。
并修复"duration: 06:18:33.50, start: 22659.300000" 问题
"""

import signal
from datetime import (
    datetime,
)

import av
from av.container import Flags


# video = "rtsp://192.168.0.103:6789" # 使用rtsp 还是有问题，在有音频时，还是报退出。
video = "srt://192.168.0.103:5000"

options={
    "loglevel": "debug",
    "rtsp_transport": "tcp",
    }

# in_v = av.open(video, options=options, buffer_size=8<<20)
in_v = av.open(video, options=options)

print(f"{dir(in_v)=}")
print(f"{in_v.flags=}")
# in_v.flags |= Flags.IGNDTS
# in_v.flags = Flags.AUTO_BSF
# print(f"{in_v.flags=}")

out_v = av.open("test.mkv", mode="w")

out_v.metadata["title"] = "从rtsp录制"
out_v.metadata["datetime"] =  datetime.now().strftime("%Y-%m-%d %H-%M-%S")


in_v_s = in_v.streams.video[0]
print(f"stream.type: {in_v_s.type} {in_v_s=} {in_v_s.average_rate=}")


out_v_stream = {}
for s in in_v.streams:
    print(f"stream: {s} type:{s.type}")
    out_v_stream[s.type] = out_v.add_stream(template=s)

EXIT = False

def exit_signal(sig, frame):
    global EXIT
    EXIT = True
    # print("使用信号退出")
    # print(f"signal: {frame=}")

# 新输出容器重新开始时间线
class ReTimeline:

    """
    请注意，帧时间戳设置将根据帧速率进行设置
    这些在使用本地摄像头时需要吗？可以调整和不调整

    # 2024-05-24: 好像是第一条流都 要重新生成 time line
    """

    def __init__(self):
        self._pts = 0

        self._first_time = True
    
    def generate(self, packet: av.Packet) -> av.Packet:
        """
        return: packet
        """

        if self._first_time:
            self._first_time = False
            self._first_time_pts = packet.pts
        
        if packet.dts is not None:
            packet.dts -= self._first_time_pts

        if packet.pts is not None:
            packet.pts -= self._first_time_pts

        return packet


signal.signal(signal.SIGINT, exit_signal)

def main():

    v_rtl = ReTimeline()
    a_rtl = ReTimeline()

    for packet in in_v.demux():

        if packet.pts is None:
            continue


        for frame in packet.decode():
            for packet_encode in out_v.encode(frame):

                print(f"当前流：{packet_encode.type=}")

                if packet_encode.type == "video":
                    packet_encode = v_rtl.generate(packet_encode)

                elif packet_encode.type == "audio":
                    packet_encode = a_rtl.generate(packet_encode)


                print(f"{packet_encode.pts=} {packet_encode.dts=} {packet_encode.time_base=}")
                out_v.mux(packet_encode)

        if EXIT:
            break

           
main()
print("停止录制，写入数据...")

# for packet_encode in out_s.encode():
for packet_encode in out_v.encode():
    # print("这里会在结束时执行吗？") # 会执行，还是多次的。
    out_v.mux(packet_encode)

in_v.close()
out_v.close()

