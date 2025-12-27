
import sys
import enum
import socket
import signal
import struct
import logging

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


def h264():
    TCP_HOST = '192.168.131.18'
    TCP_PORT = 58888
    OUTPUT_FILE = 'output.mkv'
    RATE = 30  # 视频帧率

    output = av.open(OUTPUT_FILE, mode='w')
    stream: av.VideoStream = output.add_stream('libx264', rate=RATE)
    stream.width = 1920
    stream.height = 1080
    stream.pix_fmt = 'yuv420p'
    stream.time_base = av.time_base  # 通常为1/90000
    # stream.codec_context.flags |= av.codec.context.Flags.global_header
    logger.debug(f"stram: {stream=}, {get_public_attributes(stream)=}")


    astream: av.AudioStream = output.add_stream("aac", rate=44100)
    astream.time_base = stream.time_base # 和视频相同


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
    safe_exit = True
    sps_pps_data = b""
    while safe_exit:
        pkt_type, pkt_len, pts_us, pkt_data = get_video_packet(sock)
        # 视频
        if pkt_type == PacketType.VideoConfig:
            sps_pps_data = pkt_data

        elif pkt_type in (PacketType.VideoNormal, PacketType.VideoKeyFrame):

            if pkt_type == PacketType.VideoKeyFrame:
                if sps_pps_data:
                    pkt_data = sps_pps_data + pkt_data
                    sps_pps_data = b'' # 写入后清空（或者不清空，取决于你是否想让每个关键帧都带参数）

                print(f"{pts_us}: PacketType 判断是一个关键帧")
                packet = av.Packet(pkt_data)
                packet.is_keyframe = True

            else:

                packet = av.Packet(pkt_data)

            #要在视频帧是关键帧时退出
            if (not running) and packet.is_keyframe:
                safe_exit = False
                print("="*20,"正常退出.", "="*20)
                break

            # 1. 换算 PTS (从微秒 us 到 90kHz 单位)
            # 使用 int() 确保是整数，避免播放器解析错误
            if start_pts == 0:
                start_pts = pts_us

            calculated_pts = (pts_us - start_pts) * stream.time_base
            print(f"视频PTS: {calculated_pts}")

            # # 2. 赋值给 packet (裸流通常 PTS = DTS)
            packet.pts = calculated_pts
            packet.dts = calculated_pts
            # 输出到文件
      
            packet.stream = stream
            output.mux(packet)

        # 音频配置extradat
        elif pkt_type == 200:
            # 每一帧音频里带有 CSD数据 AAC 2字节
            astream.codec_context.extradata = pkt_data

        # 音频
        elif pkt_type == 2:

            # 以视频的pts为准 视频没有开始时，音频也不要开始
            if start_pts == 0:
                print("视频还没开始! 收到的音频都丢掉。")
                continue
            
            apacket = av.Packet(pkt_data)
            # print(f"音频流：{apacket=}")
            apacket.is_keyframe = True

            # 音频可以不用？
            if a_start_pts == 0:
                a_start_pts = start_pts

            pts = (pts_us - a_start_pts) * stream.time_base
            print(f"音频PTS: {pts}")
            apacket.pts = pts
            apacket.dts = pts

            apacket.stream = astream
            output.mux(apacket)
        
        else:
            print(f"错误的包类型: {pkt_type=} {pkt_len=} {pts_us=} {pkt_data=}")


    output.close()
    sock.close()

    logger.debug(f"写入完成: {OUTPUT_FILE}")


def h265():

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
    stream.time_base = av.time_base  # 通常为1/90000
    stream.codec_context.flags |= av.codec.context.Flags.global_header
    logger.debug(f"stram: {stream=}, {get_public_attributes(stream)=}")


    astream: av.AudioStream = output.add_stream("aac", rate=44100)
    astream.time_base = stream.time_base # 和视频相同


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
    safe_exit = True
    sps_pps_data = b""
    while safe_exit:
        pkt_type, pkt_len, pts_us, pkt_data = get_video_packet(sock)
        # 视频
        if pkt_type in (PacketType.VideoConfig, PacketType.VideoNormal, PacketType.VideoKeyFrame):

            packet = av.Packet(pkt_data)

            # 判断是否为关键帧 (IDR + VPS/SPS/PPS)
            # 这里简单判断：NAL unit type 16~21 是关键帧（VCL IDR）
            # data = bytes(packet)
            # nal_unit_type = data[4] >> 1 & 0x3F  # 假设 4字节 start code
            # if nal_unit_type in (16, 17, 18):  # IDR_W_RADL, IDR_N_LP, CRA_NUT
            #     is_keyframe = True
            #     print(f"{pts_us}: nal_unit_type 判断是一个关键帧")
            # else:
            #     is_keyframe = False

            if pkt_type in (PacketType.VideoKeyFrame, PacketType.VideoConfig):
                print(f"{pts_us}: PacketType 判断是一个关键帧")
                # is_keyframe = True
                packet.is_keyframe = True


            #要在视频帧是关键帧时退出
            if (not running) and packet.is_keyframe:
                safe_exit = False
                print("="*20,"正常退出.", "="*20)
                break

            # 1. 换算 PTS (从微秒 us 到 90kHz 单位)
            # 使用 int() 确保是整数，避免播放器解析错误
            if start_pts == 0:
                start_pts = pts_us

            calculated_pts = (pts_us - start_pts) * stream.time_base
            print(f"视频PTS: {calculated_pts}")

            # # 2. 赋值给 packet (裸流通常 PTS = DTS)
            packet.pts = calculated_pts
            packet.dts = calculated_pts
            # 输出到文件
      
            packet.stream = stream
            output.mux(packet)

        # 音频配置extradat
        elif pkt_type == 200:
            # 每一帧音频里带有 CSD数据 AAC 2字节
            astream.codec_context.extradata = pkt_data

        # 音频
        elif pkt_type == 2:

            # 以视频的pts为准 视频没有开始时，音频也不要开始
            if start_pts == 0:
                print("视频还没开始! 收到的音频都丢掉。")
                continue
            
            apacket = av.Packet(pkt_data)
            # print(f"音频流：{apacket=}")
            apacket.is_keyframe = True

            # 音频可以不用？
            if a_start_pts == 0:
                a_start_pts = start_pts

            pts = (pts_us - a_start_pts) * stream.time_base
            print(f"音频PTS: {pts}")
            apacket.pts = pts
            apacket.dts = pts

            apacket.stream = astream
            output.mux(apacket)
        
        else:
            print(f"错误的包类型: {pkt_type=} {pkt_len=} {pts_us=} {pkt_data=}")


    output.close()
    sock.close()

    logger.debug(f"写入完成: {OUTPUT_FILE}")


if __name__ == "__main__":
    h264()
    # h265()
