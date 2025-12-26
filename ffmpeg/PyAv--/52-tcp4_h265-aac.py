
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
    logger.debug("收到中断信号，准备退出...")
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


def get_nal_type(data):
    """解析 H.265 NAL 单元类型"""

    if len(data) < 5:
        return -1
    # 寻找起始码后的第一个字节
    if data[:4] == b'\x00\x00\x00\x01':
        header_byte = data[4]
    elif data[:3] == b'\x00\x00\x01':
        header_byte = data[3]
    else:
        return -1
    return (header_byte >> 1) & 0x3F

def extract_vss_pps_vps(data):
    """从 Annex-B 中只提取 VPS, SPS, PPS，剔除 SEI 和其他 NALU"""
    import re
    pattern = b'\x00\x00(?:\x00)?\x01'
    positions = [m.start() for m in re.finditer(pattern, data)]
    clean_extradata = bytearray()
    
    for i in range(len(positions)):
        start = positions[i]
        end = positions[i+1] if i+1 < len(positions) else len(data)
        nalu = data[start:end]
        
        # 获取 NAL 类型
        header_pos = 3 if nalu[2] == 1 else 4
        n_type = (nalu[header_pos] >> 1) & 0x3F
        
        # 只保留 32(VPS), 33(SPS), 34(PPS)
        if n_type in [32, 33, 34]:
            clean_extradata.extend(nalu)
            
    return bytes(clean_extradata)

class PacketType(enum.IntEnum):
    VideoNormal = 1
    VideoKeyFrame = 100
    VideoConfig = 101

    AudioNormal = 200
    AudioConfig = 2


def main2():
    TCP_HOST = '192.168.131.18'
    TCP_PORT = 58888
    OUTPUT_FILE = 'output.mkv'  # 先只支持mkv容器格式
    
    output = av.open(OUTPUT_FILE, mode='w')
    
    # 1. 优化视频流配置
    # 使用 90kHz 时间基准，能提供微秒级精度，防止 MP4 帧戳重复导致卡死
    VIDEO_TIME_BASE = 9000
    stream = output.add_stream('hevc', rate=30)
    stream.width = 1920
    stream.height = 1080
    stream.pix_fmt = 'yuv420p'
    stream.time_base = Fraction(1, VIDEO_TIME_BASE)
    print(f"视频流的time_base: {stream.time_base=}")
    print(f"视频流的codec_context: {stream.codec_context=}")

    # 告诉 FFmpeg 这个流需要全局头，FFmpeg 内部可能会帮你做一部分 Annex-B 的兼容
    stream.codec_context.flags |= av.codec.context.Flags.global_header #type:ignore

    # stream.add_bitstream_filter("hevc_mp4toannexb")

    astream = output.add_stream("aac", rate=44100)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((TCP_HOST, TCP_PORT))

    codec = av.Codec('hevc', 'r')
    context = av.CodecContext.create(codec)
    print(f"视频流的codec_context: {stream.codec_context=}")


    # 状态管理
    recording_state = {
        'first_key_found': False,
        'video_pts_us': 0,
        'audio_pts_us': 0,
    }

    c = 0
    c_t = True
    safe_exit = True
    while safe_exit:
        pkt_type, pkt_len, pts_us, pkt_data = get_video_packet(sock)

        # A. 视频配置包处理
        if pkt_type == PacketType.VideoConfig:

            print(f"Annex-B SPS/PPS 长度： {pkt_len} 本身: {pkt_data}")
            # 仅更新 extradata，不写入 mux
            print(f"当前：{stream.codec_context.extradata=}")

            # 这个检测 是ok的
            # try:
            #     # 尝试创建一个临时的解码上下文来验证
            #     test_codec = av.CodecContext.create('hevc', 'r')
            #     test_codec.extradata = stream.codec_context.extradata
            #     test_codec.open()
            #     print("✅ 解码器验证成功：extradata 能够被 HEVC 解码器正确解析。")
            #     print(f"{test_codec.extradata=}")
            # except Exception as e:
            #     print(f"❌ 解码器验证失败：{e}")

            # clean_extradata = extract_vss_pps_vps(pkt_data)
            # stream.codec_context.extradata = clean_extradata

            # print(f"收到[VPS] SPS/PPS ctx.parse() 之后：{stream.codec_context.extradata=}")
            stream.codec_context.parse(pkt_data)

        #  视频帧处理
        elif pkt_type in [PacketType.VideoNormal, PacketType.VideoKeyFrame]:
            
            # 不需要拆分，安卓端 CONFIG 就是一个单独的 ~~核心修复：手动拆分复合包~~

                # 寻找最后一个起始码 (Annex-B 格式)
                # last_idx = pkt_data.rfind(b'\x00\x00\x00\x01')
                # print(f"找到 VPS/SPS/PPS: {pkt_data[:last_idx]}")

            is_key = (pkt_type == PacketType.VideoKeyFrame)
            packets = stream.codec_context.parse(pkt_data)
            print(f"{packets=}")
            c += 1
            print(f"经过了几个pkt_data, 才有值的？-> {c=}")

            # print(f"parse() 出来了多少个: {len(packets)}") # 目前看到都是一个, 因为安卓端一次只拿到一个 Annex-B 发送。
            for packet in packets:
                # debug
                # 将 packet 转为 hex 打印前 20 个字节
                # raw_bytes = bytes(packet)
                # header_hex = raw_bytes[:20].hex(' ')
                # print(f"Packet Size: {packet.size}, Header: {header_hex}")

                """
                raw_bytes = bytes(packet)
                startCode_list = raw_bytes.split(b'\x00\x00\x00\x01')
                # print(f"看看是不是有多个startCode: {len(startCode_list)}") # 我去 真的有VPS/SPS/PPS 等信息。
                for i, sc in enumerate(startCode_list):
                    print(f"{i}: {b'\x00\x00\x00\x01'}{sc[:20]=}")

                # 寻找最后一个起始码，跳过冗余配置
                last_start = raw_bytes.rfind(b'\x00\x00\x00\x01')
                if last_start > 0:
                    # print("只保留 IDR 帧及其起始码")
                    packet = av.Packet(raw_bytes[last_start:])

                
                raw_bytes = bytes(packet)
                print(f"拆分过的packet: {raw_bytes[:20]}")
                nal_type = get_nal_type(raw_bytes)

                # 1. 过滤掉重复的配置 NALUs (VPS=32, SPS=33, PPS=34)
                # 这些信息已经通过 VideoConfig 设置给 extradata 了，不应重复 mux 进流
                if nal_type in [32, 33, 34]:
                    print(f"有NAL Unit 数据：{packet=}") # 这里能确认，已经和 PacketType.VideoConfig 包分开了。
                    continue

                # 2. 精准设置关键帧标志 (IDR_W_RADL=19, IDR_N_LP=20)
                # 只有真正的 IRAP 帧才设为关键帧
                if (16 <= nal_type <= 23):
                    packet.is_keyframe = True
                    print(f"是关键帧 通过 NAL_type: {packet=}")

                """

                c += 1
                if c_t and stream.codec_context.extradata:
                    c_t = False
                    print(f"检测是否有值 {stream.codec_context.extradata=}")
                    print(f"{context.extradata=}")

                # 强制同步关键帧状态，解决 MKV 报错
                if is_key:
                    packet.is_keyframe = True
                    print(f"是关键帧 通过 PacketType: {packet=}")
                
                # 安全退出逻辑
                if (not running) and packet.is_keyframe:
                    safe_exit = False
                    break
                
                # --- v16 兼容的时间戳换算 ---
                # (当前us - 起始us) * 90000 / 1000000
                if recording_state["video_pts_us"] == 0:
                    recording_state['video_pts_us'] = pts_us
                
                offset = pts_us - recording_state['video_pts_us']
                
                # 正确公式：微秒 * 频率 / 1,000,000
                pts = int(offset * stream.time_base.denominator / 1000000)
                # print(f"视频 PTS: {pts}")
                packet.pts = pts
                packet.dts = pts
                
                packet.stream = stream
                output.mux(packet)

        # C. 音频处理
        elif pkt_type == 200:
            
            # 假设你的音频数据前 2 字节是 ADTS/Config 信息
            if not astream.codec_context.extradata:
                astream.codec_context.extradata = pkt_data[:2]
            
            apacket = av.Packet(pkt_data[2:])
            apacket.stream = astream

            # 以视频的pts为准 视频没有开始时，音频也不要开始
            if recording_state["video_pts_us"] <= 0:
                print("视频还没开始! 收到的音频都丢掉。")
                continue
            
            # 安卓端 视频编码器和音频编码器 时间戳 值可能不一样。
            # 音频 PTS 换算 (使用音频自身的 time_base 分母，通常是采样率)
            if recording_state["audio_pts_us"] == 0:
                recording_state['audio_pts_us'] = pts_us

            offset = pts_us - recording_state['audio_pts_us']

            pts = int(offset * astream.time_base.denominator / 1000000)
            # print(f"音频PTS: {pts}")
            apacket.pts = pts
            apacket.dts = pts
            
            output.mux(apacket)

    output.close()
    sock.close()


main2()