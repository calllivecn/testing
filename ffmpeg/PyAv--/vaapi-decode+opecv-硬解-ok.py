"""

方法1 和 方法4 ok
"""

import sys
import pprint
import time

import cv2
import numpy as np

import av
from av.codec import hwaccel

av.logging.set_level(av.logging.DEBUG)


if cv2.ocl.haveOpenCL():
    print("开启 openCL 加速")
    cv2.ocl.setUseOpenCL(True)
    print(f"当前 OpenCL 设备: {cv2.ocl.Device.getDefault().name()}")

def pyav_frame_to_umat(frame):
    """
    将 PyAV 的 NV12 Frame 高效转换为 OpenCV UMat (BGR)
    """
    # 检查是否为 nv12 (vaapi 解码默认输出通常是这个)
    if frame.format.name != 'nv12':
        # 如果不是 nv12，回退到慢速方法（让 PyAV 用 CPU 转 RGB）
        # print(f"Warning: Frame format is {frame.format.name}, falling back to CPU conversion.")
        return cv2.UMat(frame.to_ndarray(format='bgr24'))

    # --- 步骤 A: 提取 Raw Data (零拷贝或极低拷贝) ---
    # frame.planes[0] 是 Y (Luma), shape=(H, W)
    # frame.planes[1] 是 UV (Chroma), shape=(H/2, W)  <-- 注意这里是交错的
    
    y_plane = frame.planes[0].to_ndarray()
    uv_plane = frame.planes[1].to_ndarray()
    
    h, w = y_plane.shape
    
    # --- 步骤 B: 构建 OpenCV 兼容的 NV12 内存结构 ---
    # OpenCV 的 NV12 格式要求是一个高度为 H * 1.5 的单通道矩阵
    # 前 H 行是 Y，后 H/2 行是 UV
    
    # 创建一个空的容器 (这一步在内存里分配空间)
    # 这里的开销主要是内存分配，对于 UMA 架构非常快
    nv12_array = np.empty((int(h * 1.5), w), dtype=np.uint8)
    
    # 填充数据
    nv12_array[:h, :] = y_plane
    nv12_array[h:, :] = uv_plane # 直接填入 UV 数据
    
    # --- 步骤 C: 转换为 UMat (触发 OpenCL) ---
    # 这一步只是告诉 OpenCV：“嘿，数据在这里，准备用 GPU 跑”
    umat_nv12 = cv2.UMat(nv12_array)
    
    # --- 步骤 D: 在 GPU 上做颜色转换 (NV12 -> BGR) ---
    # 这是计算量最大的一步，完全由核显加速
    umat_bgr = cv2.cvtColor(umat_nv12, cv2.COLOR_YUV2BGR_NV12)
    
    return umat_bgr


def pyav_frame_to_umat2(frame):
    # 1. 直接导出 NV12 格式的 Numpy 数组
    # PyAV 会自动把 Y 和 UV 拼成一个大数组，并处理掉显卡内存里的无效填充数据
    nv12_cpu = frame.to_ndarray(format='nv12')
    
    # 2. 扔给 OpenCV UMat
    umat_nv12 = cv2.UMat(nv12_cpu)
    
    # 3. GPU 上转 BGR
    # 注意：nv12_cpu 的高度已经是 h * 1.5 了，OpenCV 能直接识别
    umat_bgr = cv2.cvtColor(umat_nv12, cv2.COLOR_YUV2BGR_NV12)
    
    return umat_bgr


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

def validate_Vaapi_decoding(frame):
    # 检查帧格式是否为VAAPI硬件格式
    print(f"帧格式: {frame.format.name}")
    if frame.format.name.startswith("vaapi") or frame.format.name.startswith("nv12"):
        # print(f"解码器类型: {frame.codec.name}")
        print("是否使用硬件加速: True")
        return True
    else:
        # print(f"解码器类型: {frame.codec.name}")
        print("是否使用硬件加速: False")
        return False

def method0():
    """使用软件解码，做为加速参数"""
    in_container = av.open(video_file, "r")

    frame_count = 0
    for packet in in_container.demux():
        if packet.stream.type == "video":
            for frame in packet.decode():
                frame_count += 1
    print("CPU 软件解码完成")


# 可以！
def method1():
    """这是方式一，从容器开始创建，添加硬件加速"""
    #如果我没记错的话，除非明确指定 -hwaccel_output_format cuda，否则 FFmpeg CLI 会自动执行硬件到软件的传输（hwdownload），将帧从 VRAM 移动到系统 RAM。
    opt = {
        "hwaccel_output_foramt": "vaapi" # 当前PyAv v16版本, 有效果但不太，它本来就调用效率不高。不如ffmpeg cli
    }
    hw_vaapi = hwaccel.HWAccel(device_type=hwaccel.HWDeviceType.vaapi, device="/dev/dri/renderD128", allow_software_fallback=False, options=opt)


    in_container = av.open(video_file, "r", hwaccel=hw_vaapi)

    frame_count = 0
    for packet in in_container.demux():

        if packet.stream.type == "video":
            for frame in packet.decode():
                frame_count += 1
                # 此时frame应为VAAPI硬件帧
                # validate_Vaapi_decoding(frame)
                # 可选：如需CPU访问，将硬件帧转换为软件帧
                if frame.format.name.startswith("vaapi"):
                    pass
                    # sw_frame = frame.to_ndarray()  # 自动转换
                elif frame.format.name.startswith("nv12"):
                    pass
                    # print(f"解码出来了帖: {frame_count}")
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

    fgbg = cv2.createBackgroundSubtractorMOG2(10)

    hw_vaapi = hwaccel.HWAccel(device_type=hwaccel.HWDeviceType.vaapi, device="/dev/dri/renderD128", allow_software_fallback=False)

    ctx = av.VideoCodecContext.create("hevc", "r", hw_vaapi)

    in_container = av.open(video_file, "r")
    v_s = in_container.streams.video[0]
    # print(f"{v_s.codec_context.extradata=}")
    ctx.extradata = v_s.codec_context.extradata

    frame_count = 0
    for packet in in_container.demux():
        if packet.stream.type == "video":
            if packet.is_keyframe:
                time.sleep(1)
                for frame in ctx.decode(packet):
                # for frame in packet.decode():
                    frame_count += 1
                    # frame_attr = get_public_attributes(frame)
                    # print(f"解码出来了: {frame_count} {frame=}")
                    # pprint.pprint(frame_attr)
                    # print("="*20)

                    img_gpu = pyav_frame_to_umat2(frame)
                    img_bgr = cv2.cvtColor(img_gpu, cv2.COLOR_RGB2BGR)
                    fgmask = fgbg.apply(img_bgr)
                    result, binary_image = cv2.threshold(fgmask, 50.0, 255, cv2.THRESH_BINARY)
                    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    # 绘制边界框
                    change = False
                    for contour in contours:
                        if cv2.contourArea(contour) > 800:  # 调整面积阈值以过滤小轮廓
                            # debug时，可以使用下面的代码画出变化的位置
                            # x, y, w, h = cv2.boundingRect(contour)
                            # cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 4)
                            change = True

video_file = sys.argv[1]

if __name__ == "__main__":
    # method0() # ok
    # method1() # ok
    # method2() # no
    # method3() # no
    method4() # ok