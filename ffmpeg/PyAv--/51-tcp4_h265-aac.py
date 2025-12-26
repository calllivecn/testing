
import sys
import enum
import socket
import signal
import struct
import logging
from fractions import Fraction

import av


def get_logger(name=None):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # logger.setLevel(logging.INFO)
    logger.setLevel(logging.DEBUG)
    return logger

logger = get_logger(__name__)

# 开启底层 ffmpeg 的 debug
av.logging.set_level(av.logging.DEBUG)

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


running = True
def signal_handler(sig, frame):
    global running
    logger.debug("\n收到中断信号，准备退出...")
    running = False

signal.signal(signal.SIGINT, signal_handler)


Header = struct.Struct('!HIQ')  # 确保数据格式正确

def get_packet(sock: socket.socket, size: int) -> bytes:
    """从socket中读取指定大小的数据包"""
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("连接已关闭")
        data.extend(chunk)
    return bytes(data)

def get_video_packet(sock) -> tuple[int, int, int, bytes]:
    """从socket中获取一个视频数据包"""
    HEADER_LEN = 14
    buffer = get_packet(sock, HEADER_LEN)

    pkt_type, data_len, pts = Header.unpack(buffer)

    buffer = get_packet(sock, data_len)
    return pkt_type, data_len, pts, buffer

# 2. 添加 AAC 流 + extradata
def make_aac_extradata(sr=44100, ch=2):
    sr_idx = {44100: 4, 48000: 3}.get(sr, 4)
    asc = (1 << 11) | (sr_idx << 7) | (ch << 3)
    return asc.to_bytes(2, 'big')


class PacketType(enum.IntEnum):
    VideoNormal = 1
    VideoKeyFrame = 100
    VideoConfig = 101

    AudioNormal = 200
    AudioConfig = 2


def main2():
    TCP_HOST = '192.168.1.10'
    TCP_HOST = '192.168.131.18'
    TCP_PORT = 58888
    OUTPUT_FILE = 'output.mkv'
    RATE = 30  # 视频帧率

    VIDEO_TIME_BASE = 90000
    output = av.open(OUTPUT_FILE, mode='w')
    # stream = output.add_stream('hevc', rate=RATE)
    stream: av.VideoStream = output.add_stream('libx265', rate=RATE)
    stream.width = 1920
    stream.height = 1080
    stream.pix_fmt = 'yuv420p'
    time_base = Fraction(1, VIDEO_TIME_BASE) # 设置时间基准
    stream.time_base = time_base
    logger.debug(f"stram: {stream=}, {get_public_attributes(stream)=}")


    astream: av.AudioStream = output.add_stream("aac", rate=44100)
    a_time_base = Fraction(1, 441000)
    astream.time_base = a_time_base
    # astream.codec_context.extradata = make_aac_extradata(44100, 2)


    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((TCP_HOST, TCP_PORT))


    codec = av.Codec('hevc', 'r')
    # 强制转换类型或添加标注
    context: av.VideoCodecContext = av.CodecContext.create(codec)


    acodec = av.Codec("aac", "r")
    acontext: av.AudioCodecContext = av.CodecContext.create(acodec)
    # 音频暂时还不需要解码

    start_pts = 0
    a_start_pts = 0
    fisrt_audio = True
    safe_exit = True
    while safe_exit:
        pkt_type, pkt_len, pts_us, pkt_data = get_video_packet(sock)
        # 视频
        if pkt_type in (PacketType.VideoConfig, PacketType.VideoNormal, PacketType.VideoKeyFrame):

            packet = av.Packet(pkt_data)

            packet.is_keyframe = (pkt_type == PacketType.VideoKeyFrame)

            #要在视频帧是关键帧时退出
            if (not running) and packet.is_keyframe:
                safe_exit = False
                print("="*20,"正常退出.", "="*20)
                break

            # 1. 换算 PTS (从微秒 us 到 90kHz 单位)
            # 使用 int() 确保是整数，避免播放器解析错误
            # if start_pts == 0:
            #     start_pts = pts_us

            # calculated_pts = int((pts_us - start_pts) * stream.time_base / 1000000)

            # # 2. 赋值给 packet (裸流通常 PTS = DTS)
            # packet.pts = calculated_pts
            # packet.dts = calculated_pts
            # 输出到文件
            packet.pts = start_pts
            packet.dts = start_pts
            packet.time_base = time_base
            packet.duration = 1
            packet.stream = stream
            output.mux(packet)

            start_pts += 1

        # 音频
        elif pkt_type == 200:

            # 每一帧音频里带有 CSD数据
            if fisrt_audio:
                fisrt_audio = False
                astream.codec_context.extradata = pkt_data[:2]
            
            apacket = av.Packet(pkt_data[2:])
            # print(f"音频流：{apacket=}")

            # 音频可以不用？
            # if a_start_pts == 0:
            #     a_start_pts = pts_us
            # pts = calculated_pts = int((pts_us - start_pts) * stream.time_base)
            # apacket.pts = pts
            # apacket.dts = pts

            apacket.pts = a_start_pts
            apacket.dts = a_start_pts
            apacket.time_base = a_time_base
            apacket.duration = 1
            apacket.stream = astream
            apacket.stream = astream

            output.mux(apacket)
            a_start_pts += 1
        
        else:
            print(f"错误的包类型: {pkt_type=} {pkt_len=} {pts_us=} {pkt_data=}")


    output.close()
    sock.close()

    logger.debug(f"写入完成: {OUTPUT_FILE}")


main2()
