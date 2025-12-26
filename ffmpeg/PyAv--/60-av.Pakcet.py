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
stream: av.VideoStream = output.add_stream('libx265', rate=RATE)
stream.width = 1920
stream.height = 1080
stream.pix_fmt = 'yuv420p'
stream.time_base = Fraction(1, RATE) # 设置时间基准
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


"""
pkt = av.packet.Packet(annexb_data)

前提必须同时满足：

annexb_data 是 完整的 HEVC Access Unit

即：一帧

包含该帧所需的所有 slice

Annex-B start code 合法

00 00 01 或 00 00 00 01

VPS / SPS / PPS：

要么已作为 extradata 写入

要么在 IDR 前周期性内联

在这个前提下：

Packet(bytes) = “我手工构造一个已经 demux 好的 packet”


六、一个快速自检方法（强烈推荐你做一次）

把你抓到的一帧丢给 ffprobe：

ffprobe -f hevc -show_frames frame.h265

如果 ffprobe 把它识别成 一帧：

👉 你就可以放心 av.Packet(frame)。

"""

def main2():
    codec = av.Codec('hevc', 'r')
    # 强制转换类型或添加标注
    context: VideoCodecContext = av.CodecContext.create(codec)
 

    # 状态管理
    recording_state = {
        'first_key_found': False,
        'video_pts_us': 0,
        'audio_pts_us': 0,
    }

    pts = 0
    while running:

        pkt_type, pkt_len, pts_us, pkt_data = get_video_packet(sock)

        if pkt_type in (1, 100, 101):
            # --- v16 兼容的时间戳换算 ---
            # (当前us - 起始us) * 90000 / 1000000
            if recording_state["video_pts_us"] == 0:
                recording_state['video_pts_us'] = pts_us
            
            offset = pts_us - recording_state['video_pts_us']
            
            # 正确公式：微秒 * 频率 / 1,000,000
            pts = int(offset * stream.time_base.denominator / 1000000)

            # 每个 TCP 包就是一帧 Annex-B
            packet = av.Packet(pkt_data)
            packet.pts = pts
            packet.dts = pts
            # packet.duration = 1
            packet.stream = stream

            data = bytes(packet)
            # 判断是否为关键帧 (IDR + VPS/SPS/PPS)
            # 这里简单判断：NAL unit type 16~21 是关键帧（VCL IDR）
            # nal_unit_type = data[4] >> 1 & 0x3F  # 假设 4字节 start code
            # if nal_unit_type in (16, 17, 18):  # IDR_W_RADL, IDR_N_LP, CRA_NUT
                # packet.is_keyframe = True
            # else:
                # packet.is_keyframe = False
            
            packet.is_keyframe = (pkt_type == 100)
            if packet.is_keyframe:
                print(f"{packet=} -- packet={data[:20]}")

            output.mux(packet)

            pts += 1
            


try:
    main2()
finally:
    output.close()
    sock.close()

logger.debug(f"写入完成: {OUTPUT_FILE}")
