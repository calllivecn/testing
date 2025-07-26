import sys
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
TCP_HOST = '192.168.1.3'
TCP_PORT = 58888
OUTPUT_FILE = 'output.mkv'
RATE = 30  # 视频帧率

output = av.open(OUTPUT_FILE, mode='w')
stream = output.add_stream('hevc', rate=RATE)
stream.width = 1920
stream.height = 1080
stream.pix_fmt = 'yuv420p'

logger.debug(f"stram: {stream=}, {get_public_attributes(stream)=}")
stream.time_base = Fraction(1, RATE)  # 设置时间基准

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

def get_video_packet(sock) -> tuple[int, int, bytes, bytes]:
    """从socket中获取一个视频数据包"""
    HEADER_LEN = 14
    buffer = get_packet(sock, HEADER_LEN)

    pkt_type, data_len, pts = struct.unpack('!HIQ', buffer)  # 确保数据格式正确

    buffer = get_packet(sock, data_len)
    return pkt_type, data_len, pts, buffer


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((TCP_HOST, TCP_PORT))

def main():

    hevc_extradata = None
    extradata_set = False  # 标记extradata是否已设置
    pts = 0

    while running:
        pkt_type, pkt_len, pts_us, pkt_data = get_video_packet(sock)
        logger.debug(f"收到包: pkt_type={pkt_type}, pkt_len={pkt_len}, pts_us={pts_us}")

        if pkt_type == 101:  # 参数集 (VPS/SPS/PPS)
            logger.debug(f"接收到参数集 {pkt_type=}, size={pkt_len}, 前32字节={pkt_data[:32].hex()}")
            # 可选：打印全部参数集内容
            logger.debug(f"参数集完整hex: {pkt_data.hex()}")
            hevc_extradata = pkt_data
            # 只设置一次 extradata
            if stream and hevc_extradata and not extradata_set:
                logger.debug("设置 stream.codec_context.extradata")
                stream.codec_context.extradata = hevc_extradata
                stream.codec_context.open()  # 显式初始化解码器
                extradata_set = True

        elif pkt_type == 1 or pkt_type == 100:  # 普通视频帧或关键视频帧
            packet = av.Packet(pkt_data)
            packet.stream = stream
            # 用 Java 端传来的 pts_us，转换为帧序号
            # 假设 Java 端 pts_us 单调递增，单位为微秒
            packet.pts = packet.dts = int(pts_us * RATE / 1_000_000)
            logger.debug(f"接收到视频帧: {pkt_type=}, {pkt_len=}, {pts_us=}, len(pkt_data)={len(pkt_data)}")

            packet.is_keyframe = (pkt_type == 100)
            if packet.is_keyframe:
                logger.debug(f"处理一个关键帧 (type={pkt_type}): {get_public_attributes(packet)}")
                # 不再重复设置 extradata
                logger.debug("尝试解码关键帧...")
                try:
                    for vframe in packet.decode():
                        logger.debug(f"解码帧: {vframe}, {get_public_attributes(vframe)=}")
                except av.error.ValueError as e:
                    logger.debug(f"解码失败: {e}")
                    raise e

            output.mux(packet)

        else:
            logger.debug(f"忽略未知帧类型: {pkt_type=}")

try:
    main()
finally:
    output.close()
    sock.close()

logger.debug(f"写入完成: {OUTPUT_FILE}")
