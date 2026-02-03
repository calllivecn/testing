import sys
import socket
import signal
import struct
import logging
from fractions import Fraction

import av
from av.video.codeccontext import VideoCodecContext


def get_logger(name=None):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    # logger.setLevel(logging.DEBUG)
    return logger

logger = get_logger(__name__)


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


TCP_HOST = '192.168.1.10'
TCP_HOST = '192.168.114.75'
TCP_PORT = 58888
OUTPUT_FILE = 'output.mkv'
RATE = 30  # 视频帧率


output = av.open(OUTPUT_FILE, mode='w')
stream: av.VideoStream = output.add_stream('hevc', rate=RATE)
# stream: av.VideoStream = output.add_stream('libx265', rate=RATE)

stream.width = 1920
stream.height = 1080
# stream.pix_fmt = 'yuv420p'
# stream.time_base = Fraction(1, RATE) # 设置时间基准

stream.codec_context.options['flags'] = '+global_header'
# stream.codec_context.extradata = extradata
stream.codec_context.options['x265-params'] = 'info=0' # 即使被重算，也要禁掉文本

logger.debug(f"stram: {stream=}, {get_public_attributes(stream)=}")

BUFFER_SIZE = 1 << 15
buffer = bytearray()
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


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((TCP_HOST, TCP_PORT))


def main2():
    codec = av.Codec('hevc', 'r')
    # 强制转换类型或添加标注
    context: VideoCodecContext = av.CodecContext.create(codec)

    # 用于手动计算时间戳的计数器
    frame_count = 0
    stream_time_base = Fraction(1, RATE) # 设置时间基准

    start_pts = 0
    while running:
        pkt_type, pkt_len, pts_us, pkt_data = get_video_packet(sock)

        if pkt_type not in (1, 100, 101):  # 普通帧或关键帧
            logger.debug(f"跳过非视频帧数据包: {pkt_type=}")
            continue

        # 只会解析出，0或 1 个 Packet
        packets = context.parse(pkt_data)
        logger.debug(f"{len(packets)=} {packets=}")

        for packet in packets:
            # print(f"{packet=}")

            if pkt_type == 1:  # 关键帧
                packet.is_keyframe = True
            

            if (not running) and packet.is_keyframe:
                logger.debug("收到退出信号，且当前为关键帧，准备退出循环...")
                break

            # =================================================
            # 动作 C: 手动计算时间戳 (对表)
            # =================================================
            # 裸流 packet 通常没有有效的时间戳，必须手动根据帧率计算
            # 计算公式：PTS = 帧序号 * (流的时间基分母 / 帧率)
            # 例如：MKV 的 time_base 通常是 1/1000 (1ms)
            # 25fps 意味着每帧间隔 40ms (1000/25 = 40)
        
            # 获取每一帧的持续时长（以流的 time_base 为单位）
            # 如果 out_stream.time_base 是 None (初始化时可能还没定)，通常 MKV 默认是 1/1000
            # 我们可以先假定一个通用的逻辑，或者让 PyAV 自动转换
        
            # 简单粗暴且有效的方法：
            # 我们手动把时间戳设置为： frame_count
            # 然后告诉 packet 我们的时间基是 1/fps
            # 最后让 PyAV 自动 rescale 到 output stream 的 time_base
        
            packet.dts = frame_count
            packet.pts = frame_count
            packet.duration = 1
            # 设置这个 packet 原本的“时间单位”是 1/fps (即一帧是一个单位)
            packet.time_base = stream_time_base
            frame_count += 1

            packet.stream = stream
            output.mux(packet)

            # 当 context 收到前面的 SPS/PPS 后，
            # 这里的 decode 遇到第一个 I 帧就能成功产生图像
            # packet.stream.codec_context = context
            try:
                frames = context.decode(packet)
                print(f"{len(frames)=}")
                for frame in frames:
                    pass

            except av.FFmpegError as e:
                # 在没有收到 SPS/PPS 之前，可能会报 "Invalid Data" 错误，这是正常的
                print(f"等待配置包... {e}")
    
    # 善后
    # 刷新 buffer，确保最后几帧写进去
    packets = context.parse() # 传入 None 冲刷解析器
    for packet in packets:
        # 同样的逻辑处理剩余帧...

        packet.dts = frame_count
        packet.pts = frame_count
        packet.duration = 1
        # 设置这个 packet 原本的“时间单位”是 1/fps (即一帧是一个单位)
        packet.time_base = stream_time_base
        frame_count += 1

        packet.stream = stream
        output.mux(packet)

try:
    main2()
finally:
    output.close()
    sock.close()

logger.debug(f"写入完成: {OUTPUT_FILE}")
