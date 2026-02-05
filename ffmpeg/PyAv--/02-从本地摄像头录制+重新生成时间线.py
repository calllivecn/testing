

"""
修复，直接从摄像头录制，文件持续时间，和开始播放时间不正确。
并修复"duration: 06:18:33.50, start: 22659.300000" 问题
"""

import sys
import signal
from datetime import (
    datetime,
)

import av
from av.codec import hwaccel


video = "/dev/video0" if len(sys.argv) == 1 else sys.argv[1]

input_options = {
        'video_size': '640x480',
        'framerate': '30',
        'input_format': 'mjpeg'  # 如果摄像头支持 MJPEG，通常带宽占用更低
}

# 开启底层 ffmpeg 的 debug
av.logging.set_level(av.logging.DEBUG)

#in_container = av.open(video, format='v4l2', options=input_options, buffer_size=8<<20) # ok
in_container = av.open(video, buffer_size=8<<20) # ok

out_container = av.open("local-dev-video.mkv", mode="w")

out_container.metadata["title"] = "从本地摄像头录制"
out_container.metadata["datetime"] =  datetime.now().strftime("%Y-%m-%d %H-%M-%S %z")

in_s = in_container.streams.video[0]
#out_s = out_container.add_stream("libx265", rate=in_s.average_rate) # ok
out_s = out_container.add_stream("hevc_qsv", rate=in_s.average_rate)
out_s.width = 640
out_s.height = 480
#out_s.pix_fmt = "yuv420p" # 转换像素格式以获得更好的兼容性
out_s.pix_fmt = "nv12"

opt = {
    "hwaccel_output_foramt": "vaapi" # 当前PyAv v16版本, 有效果但不太，它本来就调用效率不高。不如ffmpeg cli
}
hw_vaapi = hwaccel.HWAccel(device_type=hwaccel.HWDeviceType.vaapi, device="/dev/dri/renderD128", allow_software_fallback=False, options=opt)

print(f"{dir(out_s)=}")

print(f"stream.type: {in_s.type}\n{in_s=}")
print(f"{in_s.average_rate=}")
print(f"{out_s.codec_context=}")

# 默认使用的CPU
# 测试使用vaapi硬件加速
#out_s.codec_context = av.VideoCodecContext.create("hevc", "w", hw_vaapi)

# print(f"time_base: {1/in_s.average_rate}")

options = {
    "crf": "20",
    # "profile": "main",
    # "profile": "baseline", # libx265 没有baseline, 这是libx264
    # "preset": "ultrafast",
    # "preset": "veryfast",
    # "bitrate": "8000",
}
out_s.options = options

EXIT = False

def exit_signal(sig, frame):
    global EXIT
    EXIT = True
    # print("使用信号退出")
    # print(f"signal: {frame=}")


# 新输出容器重新开始时间线
class ReTimeline:

    """
    请注意，帧时间戳设置将根据帧速率进行设置
    这些在使用本地摄像头时需要吗？可以调整和不调整
    """

    def __init__(self):
        self._pts = 0

        self._first_time = True
    
    def generate(self, packet: av.Packet) -> av.Packet:
        """
        return: packet
        """

        if self._first_time:
            self._first_time = False
            self._first_time_pts = packet.pts
        
        if packet.dts is not None:
            packet.dts -= self._first_time_pts

        if packet.pts is not None:
            packet.pts -= self._first_time_pts

        return packet


signal.signal(signal.SIGINT, exit_signal)

def main():

    rtl = ReTimeline()

    for packet in in_container.demux(in_s):

        if packet.pts is None:
            continue

        packet = rtl.generate(packet)

        for frame in packet.decode():
            for packet_encode in out_s.encode(frame):
            #for packet_encode in codec_context.encode(frame):
                #print(f"{packet_encode.pts=} {packet_encode.dts=} {packet_encode.time_base=}")
                out_container.mux(packet_encode)

        if EXIT:
            break

           
main()
print("停止录制，写入数据...")

for packet_encode in out_s.encode():
#for packet_encode in codec_context.encode():
    # print("这里会在结束时执行吗？") # 会执行，还是多次的。
    out_container.mux(packet_encode)

in_container.close()
out_container.close()

