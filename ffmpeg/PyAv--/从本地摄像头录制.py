

"""
修复，直接从摄像头录制，文件持续时间，和开始播放时间不正确。
并修复"duration: 06:18:33.50, start: 22659.300000" 问题
"""


import signal

import av


video = "/dev/video0"

in_v = av.open(video)


out_v = av.open("test.mkv", mode="w")

out_v.metadata["title"] = "从本地摄像头录制"


in_v_s = in_v.streams.video[0]

# 能手动配置录制的分辨率么？ ok
in_v_s.width = 1280
in_v_s.height = 720

print(f"stream.type: {in_v_s.type}\n{in_v_s=}")
print(f"{in_v_s.average_rate=}")
out_s = out_v.add_stream("libx265", rate=in_v_s.average_rate)
out_s.width = in_v_s.width
out_s.height = in_v_s.height

# print(f"time_base: {1/in_v_s.average_rate}")

out_s.pix_fmt = "yuv420p"

out_s.options = {
    # "crf": "10",
    # "profile": "main",
    # "profile": "baseline", # libx265 没有baseline, 这是libx264
    # "preset": "ultrafast",
    "preset": "veryfast",
    # "bitrate": "8000",
}


EXIT = False

def exit_signal(sig, frame):
    global EXIT
    EXIT = True
    # print("使用信号退出")
    # print(f"signal: {frame=}")


signal.signal(signal.SIGINT, exit_signal)

def main():

    first_time = True

    for packet in in_v.demux():

        if EXIT and packet_encode.is_keyframe:
            return

        # 请注意，帧时间戳设置将根据帧速率进行设置
        if first_time:
            first_time = False
            first_time_pts = packet.pts
        
        if packet.dts is not None:
            packet.dts -= first_time_pts
        
        if packet.pts is not None:
            packet.pts -= first_time_pts

        # print(f"{packet.pts=} ", end="")

        for frame in packet.decode():
            for packet_encode in out_s.encode(frame):
                # print(f"{packet_encode.pts=} {packet_encode.dts=} {packet_encode.time_base=}")
                out_v.mux(packet_encode)

                    
main()
print("停止录制，写入数据...")

for packet_encode in out_s.encode():
    # print("这里会在结束时执行吗？") # 会执行，还是多次的。
    out_v.mux(packet_encode)

in_v.close()
out_v.close()

