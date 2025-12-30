"""
ffmpeg.PyAv--.50-tcp4h265-cuda-decode-ok 的 Docstring

问题：
1. 从摄像头

总结
在摄像头录制场景下，"信任摄像头的时间戳" 是大忌。

核心思路
直接拷贝 (Stream Copy)：不进行 Decode/Encode，直接搬运 Packet。
基准转换 (Rescale)：将时间戳从输入流的时间基（如 1/90000）转换到输出流的时间基（如 1/12800）。
单调性修正 (Monotonicity Fix)：这是解决你报错的关键。如果转换后的时间戳重复或回退，强制让它比上一帧 +1。
零点偏移 (Offset)：网络流进来的第一帧时间戳可能是任意巨大的数字，需要减去起始时间，让 MP4 从 0 秒开始。

"""


import sys
import enum
import socket
import signal
import struct
import logging
import argparse
from fractions import Fraction

import av
from av.codec.hwaccel import HWAccel, hwdevices_available

def get_logger(name=None):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s')
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

        self.first_time = True
        # 音频和视频共用，保存同步
        self.first_timestamp = 0
        self.time_base = time_base

        self.last_dts = -1
        # 估算每帧的 DTS 增量 (90000 / 30 = 3000)
        self.dts_step = int(1 / fps / self.time_base)

    def set_audio(self, sample_rate: int):
        self.first_audio_time = True
        self.first_audio_timestamp = 0
        self.audio_time_base = Fraction(1, sample_rate)

        self.last_audio_pts = -1

    def video(self, packet: av.Packet, timestamp: int) -> av.Packet:
        """
        timestamp: 是原始时间戳 安卓的 纳秒:1000000
        return: packet
        """
        logger.debug(f"时间戳 ：{timestamp=}")

        # 安卓9. 第一帧输出配置文件时，timestamp会是0
        # 安卓14. 第一帧输出配置文件时，timestamp会是和接下来的视频帧相同。

        if self.first_time and timestamp != 0:
            self.first_time = False
            self.first_timestamp = timestamp
        
        # 归零并转换单位
        rel_us = timestamp - self.first_timestamp
        # 这里的计算公式： us * (time_base.den) / (1,000,000 * time_base.num)
        # 简化后: us * 90000 / 1000000 = us * 0.09
        pts = int(rel_us * self.time_base.denominator / (ANDROID_TIMESTAMP_UNIT * self.time_base.numerator))
        
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

        logger.debug(f"处理后 PTS DTS：{packet.pts=} {packet.dts=} {pts=}")
        return packet
    
    def audio(self, packet: av.Packet, timestamp: int) -> av.Packet:

        if self.first_audio_time:
            self.first_audio_time = False
            self.first_audio_timestamp = timestamp

        rel_us = timestamp - self.first_audio_timestamp
        # 【公式差异】视频乘 90000，音频乘 sample_rate (44100)
        # PTS = seconds * time_base.den
        # PTS = (rel_us / 1000000.0) * 44100
        pts = int(rel_us * self.audio_time_base.denominator / ANDROID_TIMESTAMP_UNIT)

        # debug: 出来的需要这处理。1024×(1/44100 / 1/1000)​ ≈23.2199
        # pts = int(rel_us / self.time_base / ANDROID_TIMESTAMP_UNIT)

        # 4. 修正单调性 (音频虽然没有B帧，但 MediaCodec 有时也会抖动)
        if pts <= self.last_audio_pts:
            pts = self.last_audio_pts + 1  # 强制 +1 (即 1个采样点，影响极小)

        packet.pts = pts
        packet.dts = pts

        self.last_audio_pts = pts

        # 【关键】这里不需要手动写 1024 了，直接用解析出来的 duration
        # 注意：Parser 出来的 duration 是基于采样率的 (sample count)
        # 因为我们的 time_base 刚好是 1/sample_rate，所以直接赋值即可
        # packet.duration = 

        return packet


def h264(args: argparse.Namespace):

    enable_video: bool = args.video

    TCP_ADDR: str = args.tcp_addr
    TCP_PORT: int = args.tcp_port
    OUTPUT_FILE: str = args.filename
    CODEC: str = args.codec

    FPS: int = args.fps  # 视频帧率

    enable_audio: bool = args.audio


    output = av.open(OUTPUT_FILE, mode='w')

    stream: av.VideoStream = output.add_stream(CODEC, rate=FPS)
    stream.time_base = av.time_base  # 如果是MP4容器 通常为1/90000
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
    VCODEC = args.codec

    w, h = args.size.split("x")
    width, height = int(w), int(h)
    FPS: int = args.fps  # 视频帧率
    video_time_base = Fraction(1, 1000)

    enable_audio: bool = args.audio
    ACODEC = "aac"
    sample_rate = int(args.sample_rate)
    audio_time_base = Fraction(1, sample_rate)

    output = av.open(OUTPUT_FILE, mode='w')
    

    if enable_video:
        v_s: av.VideoStream = output.add_stream(VCODEC, rate=FPS)
        v_s.width = width
        v_s.height = height
        v_s.time_base = video_time_base
        logger.debug(f"stram: {v_s=}, {get_public_attributes(v_s)=}")
        # 如果硬解支持 启用硬件解码
        # hw_codec = "cuda" or "vaapi"
        hw_codec = "vaapi"
        if hw_codec in hwdevices_available():
            logger.debug("启用了硬件解码")
            match hw_codec:
                case "cuda":
                    hwaccel = HWAccel(device_type=hw_codec, allow_software_fallback=False)

                case "vaapi":
                    hwaccel = HWAccel(device_type=hw_codec, device="dev/dri/renderD128", allow_software_fallback=False)

                case _:
                    logger.debug("目前只支持了 [cuda vaapi] 硬件解码了。")

            v_ctx: av.VideoCodecContext = av.VideoCodecContext.create(VCODEC, "r", hwaccel)
        else:
            v_ctx: av.VideoCodecContext = av.VideoCodecContext.create("hevc", "r")
    


    if enable_audio:
        # a_s: av.AudioStream = output.add_stream(ACODEC, rate=sample_rate, layout=args.audio_channel)
        a_s: av.AudioStream = output.add_stream(ACODEC, rate=sample_rate, layout="stereo")
        logger.debug(f"配置的音频流：{a_s}")
        a_s.time_base = audio_time_base

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((TCP_ADDR, TCP_PORT))


    if enable_video:
        video_pts = ReTimeline()
        video_pts.set_video(video_time_base, FPS)

    if enable_audio:
        audio_pts = ReTimeline()
        audio_pts.set_audio(sample_rate)

    safe_exit = True
    while safe_exit:
        pkt_type, pkt_len, pts_us, pkt_data = get_video_packet(sock)
        # 视频
        if pkt_type in (PacketType.VideoConfig, PacketType.VideoNormal, PacketType.VideoKeyFrame):

            packet = av.Packet(pkt_data)
            # logger.info(f"packet 的属性：{get_public_attributes(packet)}")
            v_ctx.parse(pkt_data)

            if pkt_type in (PacketType.VideoKeyFrame, PacketType.VideoConfig):
                packet.is_keyframe = True

            #要在视频帧是关键帧时退出
            if (not running) and packet.is_keyframe:
                safe_exit = False
                logger.debug(f"{"="*20} 正常退出. {"="*20}")
                break

            video_pts.video(packet, pts_us)

            # 输出到文件
            packet.stream = v_s
            output.mux(packet)

            # 解码后 检测
            frames = v_ctx.decode(packet)
            for frame in frames:
                logger.debug(f"{frame=}")

        # 音频配置extradat
        elif pkt_type == 201:
            # 每一帧音频里带有 CSD数据 AAC 2字节
            if enable_audio:
                a_s.codec_context.extradata = pkt_data

        # 音频
        elif pkt_type == 2:

            if enable_audio:

                # 以视频的pts为准 视频没有开始时，音频也不要开始
                if video_pts.first_time:
                    logger.debug("视频还没开始! 收到的音频都丢掉。")
                    continue
            
                apacket = av.Packet(pkt_data)
                apacket.is_keyframe = True
                audio_pts.audio(apacket, pts_us)

                # debug: 出来的需要这处理。1024×(1/44100 / 1/1000)​ ≈23.2199
                pts =  apacket.pts * video_pts.time_base.denominator / audio_pts.audio_time_base.denominator
                apacket.pts = pts
                apacket.dts = pts
                apacket.stream = a_s
                output.mux(apacket)
        
        else:
            logger.warning(f"错误的包类型: {pkt_type=} {pkt_len=} {pts_us=} {pkt_data=}")


    output.close()
    sock.close()

    logger.debug(f"写入完成: {OUTPUT_FILE}")



def main():
    parse = argparse.ArgumentParser(
        usage="%(prog)s [参数 ...]",
        )
    
    parse.add_argument("--no-video", dest="video", action="store_false", default=True, help="禁用录制视频")
    parse.add_argument("--filename", help="输出视频文件名，当前只支持mkv。(.mkv 后缀可以省略)")
    parse.add_argument("--tcp-addr", dest="tcp_addr", help="安卓端tcp地址")
    parse.add_argument("--tcp-port", dest="tcp_port", default=58888, type=int, help="安卓端tcp端口(默认：58888)")
    parse.add_argument("--codec", default="h264", choices=["h264", "h265"], help="视频编码器(h264 or h265) 需要和安卓端配置一致, 如果是h264只需要多配置下fps就行。")
    parse.add_argument("--size", help="视频分辨率 [h265]时需要指定 需要和安卓端配置一致")
    parse.add_argument("--fps", default=30, type=int, help="视频帧率 默认: 30 需要和安卓端配置一致")

    parse.add_argument("--no-audio", dest="audio", action="store_false", default=True, help="禁用录制视频")
    parse.add_argument("--audio-sample-rate", dest="sample_rate", default=16000, type=int, help="音频采样率 默认: 16000 需要和安卓端配置一致")
    # parse.add_argument("--audio-channel", dest="audio_channel", default="1", help="音频声道(1 or 2) 默认: 1 单声道 需要和安卓端配置一致")

    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)

    args = parse.parse_args()

    if args.parse:
        print(args)
        sys.exit(0)

    # 处理编码器名称
    encoders = {
        "h264": "h264", # avc
        "h265": "hevc" # hecv
    }
    aencoders = {
        "1": "mono",
        "2": "stereo"
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

    elif args.codec == "h265":
        args.codec = encoders[args.codec]
        h265(args)
    
    # if args.audio_channel == "1":
    #     args.audio_channel = aencoders["1"]
    # elif args.audio_channel == "2":
    #     args.audio_channel = aencoders["2"]



if __name__ == "__main__":
    main()
