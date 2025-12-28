
import sys
import enum
import socket
import signal
import struct
import logging
import argparse

import av
from av.codec.hwaccel import HWAccel, hwdevices_available

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


class PacketType(enum.IntEnum):
    VideoNormal = 1
    VideoKeyFrame = 100
    VideoConfig = 101

    AudioNormal = 200
    AudioConfig = 2


def h264(args: argparse.Namespace):

    enable_video: bool = args.video

    TCP_ADDR: str = args.tcp_addr
    TCP_PORT: int = args.tcp_port
    OUTPUT_FILE: str = args.filename
    CODEC: str = args.codec

    w, h = args.size.split("x")
    width, height = int(w), int(h)
    FPS: int = args.fps  # 视频帧率

    enable_audio: bool = args.audio


    output = av.open(OUTPUT_FILE, mode='w')

    stream: av.VideoStream = output.add_stream(CODEC, rate=FPS)

    stream.width = width
    stream.height = height
    stream.pix_fmt = 'yuv420p'
    stream.time_base = av.time_base  # 通常为1/90000
    # stream.codec_context.flags |= av.codec.context.Flags.global_header
    logger.debug(f"stram: {stream=}, {get_public_attributes(stream)=}")


    astream: av.AudioStream = output.add_stream("aac", rate=44100)
    astream.time_base = stream.time_base # 和视频相同

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((TCP_ADDR, TCP_PORT))

    codec = av.Codec('hevc', 'r')
    # 强制转换类型或添加标注
    # context: av.VideoCodecContext = av.CodecContext.create(codec)
    # 如果硬解支持 启用硬件解码
    if "cuda" in hwdevices_available():
        hwaccel = HWAccel(device_type='cuda', allow_software_fallback=False)
    context: av.VideoCodecContext = av.VideoCodecContext.create(codec, hwaccel)
    

    acodec = av.Codec("aac", "r")
    acontext: av.AudioCodecContext = av.AudioCodecContext.create(acodec)
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
        elif pkt_type == 201:
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


def h265(args: argparse.Namespace):

    enable_video: bool = args.video

    TCP_ADDR: str = args.tcp_addr
    TCP_PORT: int = args.tcp_port
    OUTPUT_FILE: str = args.filename
    CODEC: str = args.codec

    w, h = args.size.split("x")
    width, height = int(w), int(h)
    FPS: int = args.fps  # 视频帧率

    enable_audio: bool = args.audio

    output = av.open(OUTPUT_FILE, mode='w')

    if enable_video:
        stream: av.VideoStream = output.add_stream(CODEC, rate=FPS)
        stream.width = width
        stream.height = height
        stream.pix_fmt = 'yuv420p'
        stream.time_base = av.time_base  # 通常为1/90000
        stream.codec_context.flags |= av.codec.context.Flags.global_header
        logger.debug(f"stram: {stream=}, {get_public_attributes(stream)=}")
    

    if enable_audio:
        astream: av.AudioStream = output.add_stream("aac", rate=44100)
        if enable_video:
            astream.time_base = stream.time_base # 和视频相同
        else:
            astream.time_base = stream.time_base # 和视频相同



    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((TCP_ADDR, TCP_PORT))


    codec = av.Codec('hevc', 'r')
    # 强制转换类型或添加标注
    context: av.VideoCodecContext = av.CodecContext.create(codec)
    context.open()


    acodec = av.Codec("aac", "r")
    acontext: av.CodecContext = av.CodecContext.create(acodec)
    # 音频暂时还不需要解码

    start_pts = 0
    a_start_pts = 0
    safe_exit = True
    while safe_exit:
        pkt_type, pkt_len, pts_us, pkt_data = get_video_packet(sock)
        decode_usage = pkt_data[:]
        # 视频
        if pkt_type in (PacketType.VideoConfig, PacketType.VideoNormal, PacketType.VideoKeyFrame):

            packet = av.Packet(pkt_data)

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

            # 解码后 检测
            frame_sum = 0
            frames = context.decode(packet)
            frame_sum += len(frames)
            for frame in frames:
                print(f"{frame=}")
                print("已经解码到：{frame_sum}帧")

        # 音频配置extradat
        elif pkt_type == 201:
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



def main():
    parse = argparse.ArgumentParser(
        usage="%(prog)s [参数 ...]",
        )
    
    parse.add_argument("--no-video", dest="video", action="store_false", default=True, help="禁用录制视频")
    parse.add_argument("--filename", help="输出视频文件名，当前只支持mkv。(.mkv 后缀可以省略)")
    parse.add_argument("--tcp_addr", help="安卓端tcp地址")
    parse.add_argument("--tcp_port", default=58888, type=int, help="安卓端tcp端口(默认：58888)")
    parse.add_argument("--codec", default="h264", choices=["h264", "h265"], help="视频编码器(h264 or h265) 需要和安卓端配置一致")
    parse.add_argument("--size", default="1280x720", help="视频分辨率默认: 1280x1720 需要和安卓端配置一致")
    parse.add_argument("--fps", default=30, type=int, help="视频帧率 默认: 30 需要和安卓端配置一致")

    parse.add_argument("--no-audio", dest="audio", action="store_false", default=True, help="禁用录制视频")

    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)

    args = parse.parse_args()

    if args.parse:
        print(args)
        sys.exit(0)

    # 处理编码器名称
    encoders = {
        "h264": "libx264", # avc
        "h265": "libx265" # hecv
    }

    if args.filename:
        if not args.filename.endswith(".mkv"):
            args.filename += ".mkv"
    else:
        print("需要指定输出文件")
        sys.exit(1)
    
    if not args.tcp_addr:
        print("需要指定安卓端地址")
        sys.exit(1)

    if args.codec == "h264":
        args.codec = encoders[args.codec]
        h264(args)
    if args.codec == "h265":
        args.codec = encoders[args.codec]
        h265(args)



if __name__ == "__main__":
    main()
