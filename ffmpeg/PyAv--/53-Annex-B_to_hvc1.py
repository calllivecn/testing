"""从安卓通过 TCP 接收 H.264/H.265 + AAC 流并保存为 MKV 文件"""


import sys
import enum
import time
import socket
import signal
import struct
import logging
import argparse
from fractions import Fraction

import cv2
import av
from av.codec.hwaccel import HWAccel, hwdevices_available

def get_logger(name=None):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    # logger.setLevel(logging.DEBUG)
    return logger

logger = get_logger(__name__)

# 开启底层 ffmpeg 的 debug
av.logging.set_level(av.logging.DEBUG)


def cv2_imwrite(img: av.VideoFrame):
    """将 av.VideoFrame 保存为图像文件"""
    array = img.to_ndarray(format='bgr24')
    t = int(time.time()*10)
    filename = f"frame_{t}.png"
    cv2.imwrite(filename, array)

# 这个需要PIL包
def to_png(vf: av.VideoFrame):
    """将 av.VideoFrame 保存为图像文件"""
    img = vf.to_image()
    t = int(time.time()*10)
    filename = f"frame_{t}.png"
    img.save(filename)


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
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
logger.info("按 Ctrl+C 停止录制...")


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
    buffer = get_packet(sock, Header.size)

    pkt_type, data_len, pts = Header.unpack(buffer)

    buffer = get_packet(sock, data_len)
    return pkt_type, data_len, pts, buffer


class PacketType(enum.IntEnum):
    VideoNormal = 1
    VideoKeyFrame = 100
    VideoConfig = 101

    AudioNormal = 2
    AudioConfig = 201


def annexb_to_hvcc(data):
    """
    高性能将 Annex-B (起始码) 转换为 HVCC (长度前缀)
    适用于 PyAV mux 之前的 Packet 数据处理
    # --- 在 PyAV 中使用 ---
    # processed_data = annexb_to_hvcc(your_raw_annexb)
    # packet = av.Packet(processed_data)
    # output_container.mux(packet)
    """
    if not data:
        return data
    
    # 将输入转换为 memoryview 减少内存拷贝
    view = memoryview(data)
    pos = 0
    length = len(view)
    result = bytearray()

    while pos < length:
        # 寻找起始码 00 00 00 01 或 00 00 01
        # 这是一个简化逻辑，实际硬件流中通常是 4 字节起始码
        if view[pos:pos+4] == b'\x00\x00\x00\x01':
            start_code_len = 4
        elif view[pos:pos+3] == b'\x00\x00\x01':
            start_code_len = 3
        else:
            # 这种情况说明数据流起始位置不对，或者已经处理过了
            # 资深用户建议在这里加个异常处理或寻找下一个起始码
            break
            
        pos += start_code_len
        next_start = -1
        
        # 寻找下一个起始码的位置
        # 在 memoryview 中寻找起始码
        # 注意：这里可以使用 view.tobytes().find() 提高搜索速度
        content = view[pos:]
        idx4 = content.tobytes().find(b'\x00\x00\x00\x01')
        idx3 = content.tobytes().find(b'\x00\x00\x01')
        
        # 确定下一个 NAL 的起始位置
        if idx4 != -1 and (idx3 == -1 or idx4 < idx3):
            next_start = idx4
        else:
            next_start = idx3
            
        if next_start == -1:
            # 到达数据末尾
            payload = content
            pos = length
        else:
            payload = content[:next_start]
            pos += next_start
            
        # 核心转换：[4字节大端长度] + [数据]
        result.extend(struct.pack('>I', len(payload)))
        result.extend(payload)
        
    return bytes(result)



def annexb_payload_generator(data):
    """
    生成器：精准切割 Annex-B 流中的每一个 NAL 单元
    """
    size = len(data)
    pos = 0
    while pos < size:
        # 1. 跳过所有的领先零 (Leading Zeros)
        while pos < size and data[pos] == 0:
            pos += 1
        
        # 2. 检查是否遇到了起始码 0x01
        if pos >= size or data[pos] != 1:
            break
        
        pos += 1 # 越过 0x01
        start = pos # 真正的 NAL 数据开始位置
        
        # 3. 寻找下一个起始码 00 00 01 或 00 00 00 01
        # 我们寻找 00 00 01 序列
        next_start = data.find(b'\x00\x00\x01', pos)
        
        if next_start == -1:
            end = size
        else:
            # 找到起始码了，向前回退所有的 0，直到非零字节
            end = next_start
            while end > start and data[end-1] == 0:
                end -= 1
        
        yield data[start:end]
        pos = next_start if next_start != -1 else size

def convert_to_hvcc_packet(raw_data):
    """
    将一帧（可能含多个 NAL）转换为 MP4 要求的 [len][data][len][data] 格式
    """
    new_data = bytearray()
    for nal in annexb_payload_generator(raw_data):
        if len(nal) == 0:
            continue
        # MP4 规范要求 4 字节长度前缀 (Big-Endian)
        new_data.extend(struct.pack('>I', len(nal)))
        new_data.extend(nal)
    return bytes(new_data)


def debug_full_packet(hvcc_data):
    pos = 0
    size = len(hvcc_data)
    print(f"--- Packet Analysis (Size: {size}) ---")
    while pos + 4 <= size:
        # 读取 4 字节长度前缀
        length = struct.unpack('>I', hvcc_data[pos:pos+4])[0]
        header_pos = pos + 4
        
        if header_pos + length > size:
            print(f"FAILED: NAL at offset {pos} claims length {length}, but only {size-header_pos} left.")
            break
            
        first_byte = hvcc_data[header_pos]
        # HEVC NAL Type: (byte >> 1) & 0x3F
        nal_type = (first_byte >> 1) & 0x3F
        
        status = "✅ OK" if first_byte != 0x00 else "❌ INVALID (0x00)"
        print(f"Offset: {pos:04d} | Len: {length:06d} | Type: {nal_type:02d} | Hex: {first_byte:02x} | {status}")
        
        pos = header_pos + length
    print("---------------------------------------")


import struct

def build_hvcc_extradata(annexb_data):
    """
    将 Annex-B 格式的参数集转换为 MP4/MKV 要求的 hvcC record 格式
    # --- 使用方式 ---
    raw_annexb = bytes.fromhex("0000000140010c01ffff01600000030090000003000003007895980900000001420101016000000300900000030000030078a003c08010e596566924cae68080000003008000000f04000000014401c172b46240")
    codec_context.extradata = build_hvcc_extradata(raw_annexb)
    """
    # 1. 拆分 NAL 单元
    def split_nals(data):
        import re
        return [n for n in re.split(b'\x00\x00(?:\x00)?\x01', data) if n]

    nals = split_nals(annexb_data)
    vps = [n for n in nals if (n[0] >> 1) & 0x3F == 32]
    sps = [n for n in nals if (n[0] >> 1) & 0x3F == 33]
    pps = [n for n in nals if (n[0] >> 1) & 0x3F == 34]

    if not sps:
        return annexb_data # 转换失败则返回原样

    # 2. 从 SPS 中提取 Profile/Level 信息 (简化提取，通常从 SPS 前几个字节获取)
    # SPS header 通常在第 1 字节之后，profile 信息在接下来的几个字节
    sps_data = sps[0]
    profile_idc = sps_data[1] & 0x1F
    
    # 3. 开始构建二进制
    header = bytearray()
    header.append(0x01) # configurationVersion
    
    # 拷贝 Profile/Tier/Level 信息 (来自 SPS 的特定偏移)
    # 这里的 12 字节通常包含 profile_space, tier_flag, profile_idc 等
    # 为稳妥起见，我们从 SPS 中获取这些关键字段，或者使用通用值
    # 下面是标准的 HEVC 配置头布局：
    header.extend(sps_data[1:13]) 
    
    header.extend(struct.pack('>H', 0xF000)) # min_spatial_segmentation_idc (未知设为0)
    header.append(0) # parallelismType
    header.append(0) # chromaFormat
    header.append(0) # bitDepthLumaMinus8
    header.append(0) # bitDepthChromaMinus8
    header.extend(struct.pack('>H', 0)) # avgFrameRate
    header.append(0x03) # constantFrameRate(2bits) + numTemporalLayers(3bits) + temporalIdNested(1bit) + lengthSizeMinusOne(2bits: 3表示4字节)
    
    # 4. 写入 NAL 单元数组
    header.append(3) # numOfArrays (VPS, SPS, PPS)
    
    for nal_group in [vps, sps, pps]:
        if not nal_group: continue
        # array_completeness(1bit) + reserved(1bit) + NAL_unit_type(6bits)
        nal_type = (nal_group[0][0] >> 1) & 0x3F
        header.append(0x80 | nal_type) 
        header.extend(struct.pack('>H', len(nal_group)))
        for nal in nal_group:
            header.extend(struct.pack('>H', len(nal)))
            header.extend(nal)
            
    return bytes(header)



ANDROID_TIMESTAMP_UNIT = 1000000 # 和输入源相同 这里是安卓的 时间戳 单位
# 新输出容器重新开始时间线
class ReTimeline:

    """
    请注意，帧时间戳设置将根据帧速率进行设置
    这些在使用本地摄像头时需要吗？可以调整和不调整
    """

    def __init__(self):
        pass

    # def set_video(self, time_base: Fraction, fps: int):
    def set_video(self, fps: int):

        self.first_time = True
        # 音频和视频共用，保存同步
        self.first_timestamp = 0
        # self.time_base = time_base
        # 这是安卓的 时间基
        self.time_base = Fraction(1, ANDROID_TIMESTAMP_UNIT)

        self.last_dts = -1
        # 估算每帧的 DTS 增量
        self.dts_step = int(1 / self.time_base / fps)
        logger.debug(f"{self.dts_step=}")

    # def set_audio(self, sample_rate: int):
    def set_audio(self):
        self.first_audio_time = True
        self.first_audio_timestamp = 0
        # self.audio_time_base = Fraction(1, sample_rate)

        self.last_audio_pts = -1

    def video(self, packet: av.Packet, timestamp: int) -> av.Packet:
        """
        timestamp: 是原始时间戳 安卓的 纳秒:1000000
        return: packet
        """
        # logger.debug(f"时间戳 ：{timestamp=}")

        # 安卓9. 第一帧输出配置文件时，timestamp会是0
        # 安卓14. 第一帧输出配置文件时，timestamp会是和接下来的视频帧相同。

        if self.first_time and timestamp != 0:
            self.first_time = False
            self.first_timestamp = timestamp
        
        # 归零并转换单位
        pts = timestamp - self.first_timestamp

        packet.pts = pts
        # packet.dts = pts # 对于无B帧的情况

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
        logger.debug(f"这里查看：{self.dts_step=} {calc_dts=} 处理之后的: {packet=}")

        packet.time_base = self.time_base
        # logger.debug(f"处理后 PTS DTS：{packet.pts=} {packet.dts=} {pts=} {running=}")
        return packet
    
    def audio(self, packet: av.Packet, timestamp: int) -> av.Packet:

        if self.first_audio_time:
            self.first_audio_time = False
            self.first_audio_timestamp = timestamp

        pts = timestamp - self.first_audio_timestamp

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

        packet.time_base = self.time_base

        return packet


def h264_h265(args: argparse.Namespace):

    enable_video: bool = args.video

    TCP_ADDR: str = args.tcp_addr
    TCP_PORT: int = args.tcp_port
    OUTPUT_FILE: str = args.filename
    VCODEC = args.codec

    w, h = args.size.split("x")
    width, height = int(w), int(h)
    FPS: int = args.fps  # 视频帧率

    enable_audio: bool = args.audio
    ACODEC = "aac"
    sample_rate = int(args.sample_rate)
    audio_time_base = Fraction(1, sample_rate)

    output = av.open(OUTPUT_FILE, mode='w')

    if enable_video:
        v_s: av.VideoStream = output.add_stream(VCODEC, rate=FPS)

        # 在 v12+ 中，flags 被移动到了 context 的属性中，但部分版本通过这种方式设置：
        v_s.codec_context.options['flags'] = '+global_header'

        # 如果可能，先获取流对象
        # v_s.codec_context.extradata = extradata
        v_s.codec_context.options['x265-params'] = 'info=0' # 即使被重算，也要禁掉文本

        # 尝试 hvc1 强制标签（如果是 MP4 容器）。
        v_s.codec_context.codec_tag = 'hvc1'

        v_s.width = width
        v_s.height = height
        logger.debug(f"stram: {v_s=}, {get_public_attributes(v_s)=}")
        # 如果硬解支持 启用硬件解码
        # hw_codec = "cuda" or "vaapi"
        hw_codec = "vaapi"
        if hw_codec in hwdevices_available():
            logger.debug("启用了硬件解码")
            match hw_codec:
                case "cuda":
                    hw = HWAccel(device_type=hw_codec, allow_software_fallback=False)

                case "vaapi":
                    hw = HWAccel(device_type=hw_codec, device="/dev/dri/renderD128", allow_software_fallback=False)

                case _:
                    raise ValueError("目前只支持了 [cuda vaapi] 硬件解码了。")
                    logger.debug("目前只支持了 [cuda vaapi] 硬件解码了。")

            v_ctx: av.VideoCodecContext = av.VideoCodecContext.create(VCODEC, "r", hw)
        else:
            v_ctx: av.VideoCodecContext = av.VideoCodecContext.create("hevc", "r")



    if enable_audio:
        # a_s: av.AudioStream = output.add_stream(ACODEC, rate=sample_rate, layout=args.audio_channel)
        a_s: av.AudioStream = output.add_stream(ACODEC, rate=sample_rate, layout="stereo")
        logger.debug(f"配置的音频流：{a_s}")
        a_s.time_base = audio_time_base

    sock = socket.create_connection((TCP_ADDR, TCP_PORT))

    if enable_video:
        video_pts = ReTimeline()
        # video_pts.set_video(video_time_base, FPS)
        video_pts.set_video(FPS)

    if enable_audio:
        video_pts.set_audio()

    # 兼容h.264
    sps_pps_data = b""

    safe_exit = True
    while safe_exit:
        logger.info("这是从socket拿数据的开始")
        pkt_type, pkt_len, pts_us, pkt_data = get_video_packet(sock)
        # 视频
        if pkt_type in (PacketType.VideoNormal, PacketType.VideoKeyFrame):

            if VCODEC == "h264" and pkt_type == PacketType.VideoKeyFrame:
                if sps_pps_data:
                    pkt_data = sps_pps_data + pkt_data
                    sps_pps_data = b'' # 写入后清空（或者不清空，取决于你是否想让每个关键帧都带参数）

                packet = av.Packet(annexb_to_hvcc(pkt_data))
                packet.is_keyframe = True

            else:
                # packet = av.Packet(annexb_to_hvcc(pkt_data))
                hvcc_data = convert_to_hvcc_packet(pkt_data)
                # HEVC NAL Header 第一个字节的 bit 0 必须为 0
                # Type 位在第一个字节的 bit 1~6
                first_byte = hvcc_data[4] # 跳过 4 字节长度
                nal_type = (first_byte >> 1) & 0x3F
                print(f"First NAL Type in packet: {nal_type}, First Byte: {hex(first_byte)}")

                if first_byte == 0x00:
                    print("❌ 核心错误：转换后的第一个字节依然是 0，说明起始码没切干净！")

                packet = av.Packet(hvcc_data)

            # logger.info(f"packet 的属性：{get_public_attributes(packet)}")

            if pkt_type == PacketType.VideoKeyFrame:
                logger.debug(f"{packet=}: PacketType 判断是一个关键帧")
                packet.is_keyframe = True

            #要在视频帧是关键帧时退出
            if (not running) and packet.is_keyframe:
                safe_exit = False
                logger.info(f"{"="*20} 正常退出. {"="*20}")
                break

            if enable_video:
                video_pts.video(packet, pts_us)

            # 输出到文件
            packet.stream = v_s

            # 测试只解码关键帧 测试是ok的
            if packet.is_keyframe:
                # frames = v_ctx.decode(packet)
                frames = v_ctx.decode(av.Packet(pkt_data))
                logger.debug(f"# 测试只解码关键帧: {len(frames)=}")
                for frame in frames:
                    logger.debug(f"解码成功: 格式={frame.format.name} 尺寸={frame.width}x{frame.height} PTS={frame.pts}")
                    # cv2_imwrite(frame)

            if packet.is_keyframe:
                logger.info(f"output.mux()前 {packet=}: 一个关键帧")
            

            # 在 mux 之前执行
            # debug_full_packet(hvcc_data)

            # 需要先解码，在mux()
            output.mux(packet)

            print(f"codec_context.parse() 后 extradata: {v_s.codec_context.extradata.hex()}")

        # 音频
        elif pkt_type == PacketType.AudioNormal:

            if enable_audio:

                # 以视频的pts为准 视频没有开始时，音频也不要开始
                if video_pts.first_time:
                    logger.debug("视频还没开始! 收到的音频都丢掉。")
                    continue
            
                apacket = av.Packet(pkt_data)
                apacket.is_keyframe = True
                video_pts.audio(apacket, pts_us)

                logger.debug(f"音频流：{apacket=}")
                apacket.stream = a_s
                output.mux(apacket)
        
        
        elif pkt_type == PacketType.VideoConfig:
            logger.info("收到 视频 配置包")

            if VCODEC == "h264":
                logger.info("视频编码器是 H264")
                sps_pps_data = pkt_data

            elif VCODEC == "hevc":
                logger.info("视频编码器是 H265")

                # 【动作 1】给 Muxer (写在文件头)
                # v_s.codec_context.extradata = pkt_data
                # v_s.codec_context.parse(pkt_data) # 不行
                v_s.codec_context.extradata = build_hvcc_extradata(pkt_data)
                print(f"extradata: {pkt_data.hex()}")
        
                # 【动作 2】给 Decoder (让解码器初始化)
                # 这一步至关重要！没有它，解码器解不出第一个关键帧。
                v_ctx.extradata = pkt_data
        
                """
                packet = av.Packet(pkt_data)
                video_pts.video(packet, pts_us)
                packet.stream = v_s
                output.mux(packet)
                """

            else:
                # logger.warning(f"未知的视频编码器类型: {VCODEC}")
                raise ValueError(f"未知的视频编码器类型: {VCODEC}")

        # 音频配置extradat
        elif pkt_type == PacketType.AudioConfig:
            logger.info("收到 音频 配置包")
            # 每一帧音频里带有 CSD数据 AAC 2字节
            if enable_audio:
                a_s.codec_context.extradata = pkt_data

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
    parse.add_argument("--filename", required=True, help="输出视频文件名，当前只支持 mp4 和 mkv。")
    parse.add_argument("--tcp-addr", dest="tcp_addr", required=True, help="安卓端tcp地址")
    parse.add_argument("--tcp-port", dest="tcp_port", default=58888, type=int, help="安卓端tcp端口(默认：58888)")
    parse.add_argument("--codec", default="hevc", choices=["h264", "h265","hevc"], help="视频编码器(h264 or h265) 需要和安卓端配置一致, 如果是h264只需要多配置下fps就行。")
    parse.add_argument("--size", default="1920x1080", help="视频分辨率 [h265]时需要指定 需要和安卓端配置一致")
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
        "h264": "h264",
        "h265": "hevc"
    }
    aencoders = {
        "1": "mono",
        "2": "stereo"
    }

    if args.filename:
        if not args.filename.endswith(".mkv") and not args.filename.endswith(".mp4"):
            raise ValueError(f"输出文件错误：{args.filename} 需要是 *.mp4 or *.mkv")

    else:
        print("需要指定输出文件")
        sys.exit(1)
    
    if not args.tcp_addr:
        print("需要指定安卓端地址")
        sys.exit(1)

    args.codec = encoders.get(args.codec, "hevc")
    h264_h265(args)
    
    # if args.audio_channel == "1":
    #     args.audio_channel = aencoders["1"]
    # elif args.audio_channel == "2":
    #     args.audio_channel = aencoders["2"]



if __name__ == "__main__":
    main()
