"""

方法1 和 方法4 ok
"""

import sys


import av
from av.codec import hwaccel

av.logging.set_level(av.logging.DEBUG)

def validate_Vaapi_decoding(frame):
    # 检查帧格式是否为VAAPI硬件格式
    print(f"帧格式: {frame.format.name}")
    if frame.format.name.startswith("vaapi") or frame.format.name.startswitch("nv12"):
        # print(f"解码器类型: {frame.codec.name}")
        print("是否使用硬件加速: True")
        return True
    else:
        # print(f"解码器类型: {frame.codec.name}")
        print("是否使用硬件加速: False")
        return False


# 可以！
def method1():
    """这是方式一，从容器开始创建，添加硬件加速"""
    hw_vaapi = hwaccel.HWAccel(device_type=hwaccel.HWDeviceType.vaapi, device="/dev/dri/renderD128", allow_software_fallback=False)


    in_container = av.open(video_file, "r", hwaccel=hw_vaapi)

    frame_count = 0
    for packet in in_container.demux():

        if packet.stream.type == "video":
            for frame in packet.decode():
                frame_count += 1
                # 此时frame应为VAAPI硬件帧
                validate_Vaapi_decoding(frame)
                # 可选：如需CPU访问，将硬件帧转换为软件帧
                if frame.format.name.startswith("vaapi"):
                    sw_frame = frame.to_ndarray()  # 自动转换
                elif frame.format.name.startswith("nv12"):
                    print(f"解码出来了帖: {frame_count}")
                    # 或者使用显式转换
                    # sw_frame = frame.reformat(format="nv12").to_ndarray()
                else:
                    print("警告：未使用硬件加速解码")

# 不行
def method2():
    """从编码解码器创建"""
    # 1. 创建HWAccel对象 - 修复设备路径
    hw = hwaccel.HWAccel(
        device_type="vaapi", 
        device="/dev/dri/renderD128",  # 注意这里添加了前导斜杠
        allow_software_fallback=False
    )

    # 2. 创建解码器
    codec = av.Codec("hevc", "r")
    decoder = codec.create()

    # 3. 设置硬件设备上下文
    decoder.hw_device_ctx = hw.device # 没有这个属性

    # 4. 创建容器并开始解码
    container = av.open(video_file)

    for packet in container.demux(video=0):
        for frame in decoder.decode(packet):
            # 此时frame应为VAAPI硬件帧
            # 可选：如需CPU访问，将硬件帧转换为软件帧
            if frame.format.name.startswith("vaapi"):
                sw_frame = frame.to_ndarray()  # 自动转换
                # 或者使用显式转换
                # sw_frame = frame.reformat(format="nv12").to_ndarray()
 
# 不行
def method3():

    # 创建支持VAAPI的HEVC解码器
    decoder = av.Codec("hevc_vaapi", "r").create()

    # 对于较新版本的PyAV，可能需要设置硬件帧上下文
    # 此方法在部分系统上可能有效
    container = av.open(video_file)
    stream = container.streams.video[0]
    stream.codec_context = decoder

    for frame in container.decode(video=0):
        if frame.format.name.startswith("vaapi"):
            print("使用VAAPI硬件加速")

# ok
def method4():
    hw_vaapi = hwaccel.HWAccel(device_type=hwaccel.HWDeviceType.vaapi, device="/dev/dri/renderD128", allow_software_fallback=False)

    ctx = av.VideoCodecContext.create("hevc", "r", hw_vaapi)

    in_container = av.open(video_file, "r")
    v_s = in_container.streams.video[0]
    print(f"{v_s.codec_context.extradata=}")
    ctx.extradata = v_s.codec_context.extradata

    frame_count = 0
    for packet in in_container.demux():
        if packet.stream.type == "video":
            for frame in ctx.decode(packet):
            # for frame in packet.decode():
                frame_count += 1
                print(f"解码出来了帖: {frame_count}")
                if frame.format.name.startswith("vaapi"):
                    sw_frame = frame.to_ndarray()  # 自动转换

video_file = sys.argv[1]


if __name__ == "__main__":
    # method1() # ok
    # method2() # no
    # method3() # no
    method4() # ok