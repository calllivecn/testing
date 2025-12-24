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
    # logger.setLevel(logging.INFO)
    logger.setLevel(logging.DEBUG)
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
TCP_HOST = '192.168.131.18'
TCP_PORT = 58888
OUTPUT_FILE = 'output.mkv'
RATE = 30  # 视频帧率

output = av.open(OUTPUT_FILE, mode='w')
# stream = output.add_stream('hevc', rate=RATE)
stream = output.add_stream('libx265')
# stream.width = 1920
# stream.height = 1080
# stream.pix_fmt = 'yuv420p'

logger.debug(f"stram: {stream=}, {get_public_attributes(stream)=}")
stream.time_base = Fraction(1, RATE) # 设置时间基准

BUFFER_SIZE = 1 << 15
buffer = bytearray()
running = True

def signal_handler(sig, frame):
    global running
    logger.debug("\n收到中断信号，准备退出...")
    running = False

signal.signal(signal.SIGINT, signal_handler)

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

    pkt_type, data_len, pts = struct.unpack('!HIQ', buffer)  # 确保数据格式正确

    buffer = get_packet(sock, data_len)
    return pkt_type, data_len, pts, buffer


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((TCP_HOST, TCP_PORT))


def main2():
    codec = av.Codec('hevc', 'r')
    # 强制转换类型或添加标注
    context: VideoCodecContext = av.CodecContext.create(codec)

    start_pts = 0
    while running:
        pkt_type, pkt_len, pts_us, pkt_data = get_video_packet(sock)
        packets = context.parse(pkt_data)
        print(f"{packets=}")
        for packet in packets:
            # print(f"{stream.time_base=}")
            # print(f"{packet=}")

            # 1. 换算 PTS (从微秒 us 到 90kHz 单位)
            # 使用 int() 确保是整数，避免播放器解析错误
            if start_pts == 0:
                start_pts = pts_us

            calculated_pts = int((pts_us - start_pts) * stream.time_base)

            # 2. 赋值给 packet (裸流通常 PTS = DTS)
            packet.pts = calculated_pts
            packet.dts = calculated_pts
            # 输出到文件
            packet.stream = stream
            output.mux(packet)

            # 当 context 收到前面的 SPS/PPS 后，
            # 这里的 decode 遇到第一个 I 帧就能成功产生图像
            # packet.stream.codec_context = context
            try:
                frames = context.decode(packet)
                for frame in frames:
                    print(f"{frame=}")

            except av.FFmpegError as e:
                # 在没有收到 SPS/PPS 之前，可能会报 "Invalid Data" 错误，这是正常的
                print(f"等待配置包... {e}")

try:
    main2()
finally:
    output.close()
    sock.close()

logger.debug(f"写入完成: {OUTPUT_FILE}")
