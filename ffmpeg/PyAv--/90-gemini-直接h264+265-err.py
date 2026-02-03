
"""
这个做法测试完是可以同时录制h265 hevc的。
但是，播放时拖动进度条，会有报错：`[ffmpeg/video] hevc: Could not find ref with POC 28`
一步步debug, 应该是Paketck.VideoConfig 数据没有写入容器。
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

import cv2
import numpy as np



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



class MediaCodecProcessor:
    def __init__(self, output_file, fps=30, opencv_show=False):
        self.opencv_show = opencv_show
        # --- 1. 初始化解码器上下文 (用于 Parse 和 Decode) ---
        # 'h264' 或 'hevc' (h265)
        # self.codec_name = 'h264'
        self.codec_name = 'hevc'
        self.dec_ctx = av.CodecContext.create(self.codec_name, 'r')
        
        # --- 2. 初始化封装器 (用于保存文件) ---
        self.out_container = av.open(output_file, 'w')
        self.out_stream = self.out_container.add_stream(self.codec_name, rate=fps)
        # 在 v12+ 中，flags 被移动到了 context 的属性中
        self.out_stream.codec_context.options['flags'] = '+global_header'

        # 如果可能，先获取流对象
        # self.out_stream.codec_context.extradata = extradata
        self.out_stream.codec_context.options['x265-params'] = 'info=0' # 即使被重算，也要禁掉文本

        self.out_stream.time_base = Fraction(1, 1000) # 强制 H.264 标准 TimeBase
        
        # --- 3. 时间戳管理状态 ---
        self.last_dts = -1
        # 估算每帧的 DTS 增量 (90000 / 30 = 3000)
        self.dts_step = int(1 / fps / self.out_stream.time_base)
        self.first_pts_us = None
    
        # show
        if self.opencv_show:
            cv2.namedWindow('android Camera2 API', cv2.WINDOW_AUTOSIZE)
    
    def set_extradata(self, extradata: bytes):
        """设置解码器和封装器的 extradata (SPS/PPS)"""
        self.dec_ctx.extradata = extradata
        self.out_stream.codec_context.extradata = extradata
        self.extradata_set = True
        logger.debug(f"设置 extradata，长度: {len(extradata)} bytes")

    def process(self, data: bytes, pts_us: int, typ: int):
        """
        处理来自 MediaCodec 的一帧数据
        data: AnnexB 格式的 bytes (含 SPS/PPS 或 I/P/B 帧)
        pts_us: MediaCodec 提供的 presentationTimeUs (可能有非单调的情况)
        """

        # [步骤 1] Parse: 将原始 bytes 解析为 PyAV 的 Packet 对象
        # parse 会自动提取 SPS/PPS 并更新 dec_ctx 的 extradata，也会切分 NALU

        # --- 修正点 1: 无论是不是 Config，都要先给解码器 Parse ---
        # 这一步极其重要！parse 会分析数据中的 SPS/PPS 并存储在 dec_ctx 内部
        packets = self.dec_ctx.parse(data)
        # print(f"解析第一帧时的：{packets=}")

        """
        if typ == PacketType.VideoConfig:
            print(f"捕获到 Config 数据: {len(data)} bytes")
            # 【核心修复】将 Config 数据赋值给输出流的 extradata
            # 这会让 MP4/MKV 在文件头生成 avcC/hvcC 原子
            # 说新版中 直接对 流设置
            self.out_stream.codec_context.extradata = data
            # self.out_stream.extradata = data
            self.extradata_set = True
            return  # Config 帧通常不需要作为 Packet 写入轨道，除非是 In-Band 模式
        """

        # 2. 如果还没有收到过 Config，但来了关键帧 (这种情况比较少见，但在某些流里可能发生)
        # 如果是 HEVC，没有 extradata 基本上没法播放
        if not self.extradata_set and (typ == PacketType.VideoKeyFrame):
            raise ValueError("警告：关键帧来了，但还没有收到 Config 数据！")
        
        if not packets:
            print("没有解析出任何 Packet，跳过此帧")
            return

        # 通常 MediaCodec 一次输出对应一个 Packet，但 parse 返回的是列表，所以要遍历
        for packet in packets:
            # print(f"解析得到的: {packet=}")
            # [步骤 2] 计算 PTS (基于 Microseconds -> 1/90000)
            if self.first_pts_us is None:
                self.first_pts_us = pts_us
            
            # 归零并转换单位
            rel_us = pts_us - self.first_pts_us
            # 这里的计算公式： us * (time_base.den) / (1,000,000 * time_base.num)
            # 简化后: us * 90000 / 1000000 = us * 0.09
            current_pts = int(rel_us * self.out_stream.time_base.denominator / 
                              (1000000 * self.out_stream.time_base.numerator))
            
            packet.pts = current_pts
            
            # [步骤 3] 生成 DTS (关键！处理 B 帧)
            # MediaCodec 输出顺序是 Decode Order (解码顺序)，所以 DTS 必须严格递增。
            # 我们无法预知 B 帧的具体结构，最稳妥的方法是人工生成一个严格递增的 DTS。
            
            # 策略：当前 DTS = 上一帧 DTS + 固定步长
            # 注意：必须满足 DTS <= PTS (解码时间必须早于或等于显示时间)
            
            calc_dts = self.last_dts + self.dts_step
            
            # 如果计算出的 DTS 居然比 PTS 还大（极少见，除非帧率设定错误或 PTS 回跳严重），需要 Clamp
            if calc_dts > current_pts:
                # 这种情况下，说明 PTS 跳变了，或者 B 帧间隔很大。
                # 为了安全，尽量保持 DTS 递增，但不能超过 PTS。
                # 如果这行触发，说明可能存在严重的卡顿或时间戳跳变
                calc_dts = current_pts 
            
            packet.dts = calc_dts
            self.last_dts = calc_dts
            
            # 设置 duration (有助于播放器 seek)
            packet.duration = self.dts_step

            packet.is_keyframe = (typ == PacketType.VideoKeyFrame)

            # [步骤 4] 分流处理
            
            # --- 路 A: 写入文件 (Mux) ---
            # 必须设置 packet 所属的流
            packet.stream = self.out_stream
            
            # 注意：某些只有 config 信息的包 (size=0 或只含 header) 可能不需要 mux，
            # 但 PyAV parse 出来的通常是完整的。如果遇到问题可以加 if packet.size > 0:
            self.out_container.mux(packet)
            
            # --- 路 B: 解码画面 (Decode -> OpenCV) ---
            # 直接使用 parse 出来的 packet 进行解码
            # 注意：decode 会消耗 packet 的数据，但不会修改 timestamp，所以顺序无所谓
            
            # 这里的 packet 已经有了正确的 PTS/DTS，这有助于 dec_ctx 正确排序
            frames = self.dec_ctx.decode(packet)
            # print(f"解码得到的: {len(frames)=}")
            
            for frame in frames:
                # 转换为 OpenCV 格式 (YUV -> BGR)
                if self.opencv_show:
                    img = frame.to_ndarray(format='bgr24')
                    # 在这里做你的 OpenCV 处理
                    cv2.imshow("Preview", img)
                    cv2.waitKey(1)
                

    def close(self):
        # 刷新解码器缓冲 (获取最后几帧 B 帧)
        if self.dec_ctx:
            frames = self.dec_ctx.decode()
            for frame in frames:
                if self.opencv_show:
                    img = frame.to_ndarray(format='bgr24')
                    cv2.imshow("Preview", img)
                    cv2.waitKey(1)
                
        if self.opencv_show:
            cv2.destroyAllWindows()

        # 写入文件尾部
        self.out_container.close()
        print("处理完成")

# 使用示例
# processor = MediaCodecProcessor("output_with_bframes.mp4")
# processor.process(media_codec_bytes, media_codec_pts_us)


def test():
    TCP_ADDR = '192.168.114.75'
    TCP_PORT = 58888
    OUTPUT_FILE = 'output.mkv'
    FPS = 30  # 视频帧率

    sock = socket.create_connection((TCP_ADDR, TCP_PORT))

    MCP = MediaCodecProcessor(OUTPUT_FILE, fps=FPS, opencv_show=False)
    # MCP = MediaCodecProcessor(OUTPUT_FILE, fps=FPS, opencv_show=True)


    safe_exit = True
    while safe_exit:
        pkt_type, pkt_len, pts_us, pkt_data = get_video_packet(sock)

        # print(f"收到数据包: {pkt_type=}, {pkt_len=}, {pts_us=}")

        if pkt_type == PacketType.VideoConfig:
            MCP.set_extradata(pkt_data)
            continue

        # 视频
        if pkt_type in (PacketType.VideoNormal, PacketType.VideoKeyFrame):

            #要在视频帧是关键帧时退出
            if (not running) and PacketType.VideoKeyFrame:
                safe_exit = False
                print("="*20,"正常退出.", "="*20)
                break
            
            MCP.process(pkt_data, pts_us, pkt_type)

    sock.close()
    MCP.close()
    logger.debug(f"写入完成: {OUTPUT_FILE}")



if __name__ == "__main__":
    test()