

"""
修复，直接从摄像头录制，文件持续时间，和开始播放时间不正确。
并修复"duration: 06:18:33.50, start: 22659.300000" 问题

这个文件不能正常工作

update: 2024-05-25

这个测试有问题，RTSP 会有PTS错误问题。现在使用新的RST协议 。
"""


import sys
import time
import signal
import pprint
from fractions import Fraction
from datetime import (
    datetime,
    timedelta,
)


import av
from av.container import Flags

from libcommon import (
    VideoFile,
    # ReTimeline,
)

def get_public_attributes(obj):
    """
    获取对象的所有公共属性及其对应的值。
    
    参数:
    obj (object): 要检查的对象
    
    返回:
    dict: 包含对象所有公共属性及其对应值的字典
    """
    attributes = {}
    for attr in dir(obj):
        if not attr.startswith('_'):  # 过滤掉私有属性和特殊方法
            value = getattr(obj, attr)
            if callable(value):  # 过滤掉方法
                attributes[attr] = type(value)
            else:
                attributes[attr] = value
    return attributes

# 新输出容器重新开始时间线
class RTSPReTimeline:

    """
    在rtsp下
    处理 RTSP 这种不可靠时间戳，通常有三种策略：
    方案一：使用“墙上时钟”（Wallclock）重新打标（最推荐）
    原理：完全无视 RTSP 包自带的时间戳，改用你的电脑/服务器接收到包的那一刻的时间作为时间戳。
    """

    def __init__(self):
        pass

    def set_video(self, time_base: Fraction, fps: int):
        self.first_time = True
        # 音频和视频共用，保存同步
        self.first_timestamp = 0
        self.time_base = time_base

        self.last_dts = -1
        # 估算每帧的 DTS 增量
        self.dts_step = int(1 / self.time_base / fps)
        print(f"{self.dts_step=}")

    def set_audio(self, audio_time_base: Fraction, sample_number: int):
        """
        audio_time_base: 就是 Fraction(1, audio_smaple_rate)
        """
        self.first_audio_time = True
        self.first_audio_timestamp = 0
        self.audio_time_base = audio_time_base

        self.last_audio_pts = -1
        self.audio_dts_step = sample_number

        print(f"{self.audio_dts_step=}")

    def video(self, packet: av.Packet) -> av.Packet:
        """
        return: packet
        """

        if self.first_time:
            self.first_time = False
            self.first_timestamp = packet.pts
            
        pts = packet.pts - self.first_timestamp

        packet.pts = pts
        packet.dts = pts # 对于无B帧的情况

        packet.time_base = self.time_base
        # logger.debug(f"处理后 PTS DTS：{packet.pts=} {packet.dts=} {pts=} {running=}")
        return packet


    def audio(self, packet: av.Packet) -> av.Packet:

        if self.first_audio_time:
            self.first_audio_time = False
            self.first_audio_timestamp = packet.pts
        
        pts = packet.pts - self.first_audio_timestamp

        packet.pts = pts
        packet.dts = pts

        packet.time_base = self.audio_time_base

        return packet



# video = "rtsp://192.168.0.103:5554" # 使用rtsp 还是有问题，在有音频时，还是报退出。

video = sys.argv[1]

options={
    # "loglevel": "debug", # 这个没有用呀
    "rtsp_transport": "tcp",
    }


in_v = av.open(video, options=options, buffer_size=8<<20)
# pprint.pprint(f"{get_public_attributes(in_v)}")

fps = Fraction(30, 1)
# 拿到平均帧率
v_s = in_v.streams.video[0]
pprint.pprint(f"视频流：{get_public_attributes(v_s)}")
if v_s.base_rate is None:
    if fps is None:
        raise ValueError("视频流 stream.average_rate为None, 需要手动指定fps.")
else:
    fps = v_s.base_rate

print(f"{fps=}")

a_s = in_v.streams.audio[0]
pprint.pprint(f"音频流：{get_public_attributes(a_s)}")
# 每帧采样数（AAC 通常会返回 1024）
# 注意：有些 RTSP 流在未解码前此值为 0，如果是 0 则默认为 1024
frame_size = a_s.codec_context.frame_size or 1024

codec_context = a_s.codec_context
# 1. 检查 extradata
if not codec_context.extradata:
    print("警告：音频流缺少 extradata，可能无法解码")
else:
    print(f"Extradata 长度: {len(codec_context.extradata)}")

# 2. 显式打开解码器
if not codec_context.is_open:
    codec_context.open()


out_v = av.open("test.mkv", mode="w")

out_v_s = out_v.add_stream_from_template(v_s)
# 告诉输出容器，没有开启B帧
out_v_s.codec_context.max_b_frames = 0

out_a_s = out_v.add_stream_from_template(a_s)

time_ = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
out_v.metadata["title"] = f"从rtsp录制: {time_}"
out_v.metadata["datetime"] =  time_

EXIT = False

def exit_signal(sig, frame):
    global EXIT
    EXIT = True


signal.signal(signal.SIGINT, exit_signal)

def main():

    retimeline = RTSPReTimeline()

    time_base = Fraction(1, 1000)
    retimeline.set_video(time_base, fps)

    # retimeline.set_audio(a_s.time_base, frame_size)

    last_pts = 0
    last_dts = 0

    first_audio = True

    for packet in in_v.demux():

        # print(f"当前流：{packet=} {packet.time_base=}")
        if packet.pts is None:
            print(f"跳过无效时间戳包: {packet.stream.type} {packet.is_keyframe=} {packet=}")

        # 使用接收端的本地时间戳
        packet.pts = int(time.monotonic()*1000)

        if packet.stream.type == "video":

            print(f"视频流：{packet.dts=} {packet.pts=}")

            retimeline.video(packet)

            if last_pts > packet.pts:
                # 实测好像也是没有B帧的
                print(f"有pts倒流的情况: {packet.pts=}")
                last_pts = packet.pts

            if last_dts > packet.dts:
                print(f"有dts倒流的情况: {packet.dts}")
                last_dts = packet.dts

            packet.stream = out_v_s


        elif packet.stream.type == "audio":

            # print(f"视频流：{packet.dts=} {packet.pts=}")

            if bytes(packet) == a_s.codec_context.extradata:
                print("好像首个音频流packet是 extradata!") # 是的
                continue

            # print(f"当前包包含的采样数: {packet.duration}") # 为什么还是0
            if first_audio:
                first_audio = False
                print(f"当前音频流：{get_public_attributes(packet)}")
                for frame in packet.decode():
                    #拿到 samples
                    print(f"{get_public_attributes(frame)}")
                    samples = frame.samples
                    break

                retimeline.set_audio(time_base, samples)

            retimeline.audio(packet)
            packet.stream = out_a_s
        
        else:
            print(f"当前不支持流类型：{packet.stream.type=}")

        if EXIT and packet.is_keyframe:
            break

        out_v.mux(packet)


    print("停止录制，写入数据...")
    in_v.close()


main()
