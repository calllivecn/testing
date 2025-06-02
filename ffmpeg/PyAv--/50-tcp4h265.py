import sys
import socket
import signal
import struct
from fractions import Fraction

import av

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
TCP_HOST = '192.168.1.11'
TCP_PORT = 58888
OUTPUT_FILE = 'output.mkv'
RATE = 30  # 视频帧率

output = av.open(OUTPUT_FILE, mode='w')
stream = output.add_stream('hevc', rate=RATE)
stream.width = 1920
stream.height = 1080
stream.pix_fmt = 'yuv420p'

print(f"stram: {stream=}, {get_public_attributes(stream)=}")
stream.time_base = Fraction(1, RATE)  # 设置时间基准

BUFFER_SIZE = 1 << 15
buffer = bytearray()
running = True

def signal_handler(sig, frame):
    global running
    print("\n收到中断信号，准备退出...")
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
    pts = 0

    while running:
        # 接收数据，pts_us 是微秒单位的 PTS
        pkt_type, pkt_len, pts_us, pkt_data = get_video_packet(sock)
        # print(f"接收到帧: {pkt_type=}, {pkt_len=}, {pts_us=}, {len(pkt_data)=}") # Debugging

        if pkt_type == 101:  # 参数集 (VPS/SPS/PPS)
            print(f"接收到参数集 {pkt_type=}, size={pkt_len}, {pkt_data=}")
            hevc_extradata = pkt_data
            if stream and hevc_extradata:
                print("设置 stream.codec_context.extradata")
                stream.codec_context.extradata = hevc_extradata
                stream.codec_context.open()  # 显式初始化解码器

        elif pkt_type == 1 or pkt_type == 100:  # 普通视频帧或关键视频帧
            packet = av.Packet(pkt_data)
            packet.stream = stream
            packet.pts = packet.dts = pts
            pts += RATE
            print(f"接收到视频帧: {pkt_type=}, {pkt_len=}, {pts_us=}, len(pkt_data)={len(pkt_data)}")

            packet.is_keyframe = (pkt_type == 100)
            if packet.is_keyframe:
                print(f"处理一个关键帧 (type={pkt_type}): {get_public_attributes(packet)}")
                if hevc_extradata and not stream.codec_context.extradata:
                    print("设置 stream.codec_context.extradata")
                    stream.codec_context.extradata = hevc_extradata
                    stream.codec_context.open()  # 显式初始化解码器

                print("尝试解码关键帧...")
                try:
                    for vframe in packet.decode():
                        print(f"解码帧: {vframe}, {get_public_attributes(vframe)=}")
                except av.error.ValueError as e:
                    print(f"解码失败: {e}")

            output.mux(packet)

        # 如果有音频帧(pkt_type==2)，可在此处理
        # elif pkt_type == 2: # Audio frame
        #    # 处理音频包
        #    pass
        else:
            print(f"忽略未知帧类型: {pkt_type=}")

try:
    main()
finally:
    output.close()
    sock.close()

print(f"写入完成: {OUTPUT_FILE}")
