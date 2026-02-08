#!/usr/bin/bash

# 2026-02-27 测试成功

URL="rtsp://192.168.1.3:5554"

OUT="rtsp3.mkv"

ffmpeg -hide_banner -v info \
    -use_wallclock_as_timestamps 1 \
    -fflags +genpts+igndts+flush_packets \
    -rtsp_transport tcp \
    -i "$URL" \
    -map 0 \
    -c:v copy \
    -c:a aac -af "aresample=async=1" \
    -avoid_negative_ts make_zero \
	"$OUT"

## 1. 报错深度解析
# 
# - Input buffer exhausted before END element found & Error submitting packet to decoder
# 
# 原因：这是音频解码器的报错。说明 Astra Streaming Studio 发出的 AAC 数据包在物理字节上是不完整的，或者不符合标准帧结束标志。
# 
# 影响：录制的文件中，在报错发生的那一瞬间，音频可能会有极轻微的“爆音”或一两帧的静音。
# 
# 结论：影响很小，FFmpeg 已经自动跳过了这些坏包并继续录制了。
# 
# - Timestamps are unset in a packet for stream 0
# 
# 原因：虽然我们用了 genpts，但在 HEVC 流的最开始几个包，或者某些特定的 IDR 帧上，源端完全没有给时间戳。
# 
# 影响：Matroska 容器会尝试补全它。如果报错只出现在刚开始录制时，完全可以忽略。
# 
# 结论：无实质影响。
# 
# - 90000.900fps (mpv 显示)
# 
# 原因：这是因为原始码流没提供 VUI (Video Usability Information) 帧率信息，FFmpeg 默认使用了 90kHz 的时钟基准。
# 
# 影响：播放器可能会在快进、退后时计算进度条不准。

