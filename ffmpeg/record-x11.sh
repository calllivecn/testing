#!/bin/bash


#ffmpeg -video_size 1920x1080 -framerate 60 -f x11grab -i :0.0+0,00 output.mp4
#ffmpeg -hide_banner -video_size 3840x2160 -framerate 60 -f x11grab -i ":0.0+0,0" -vcodec hevc output.mp4

# 录制屏幕，需要GPU , hevc_nvenc 才是使用GPU 编码
#ffmpeg -f x11grab -video_size 3840x2160 -r 30 -i :1.0 -vcodec hevc_nvenc -crf 18 outout.mp4


# 无损压缩 H.265 的 -x265-params lossless=1
#ffmpeg -f x11grab -video_size 3840x2160 -r 30 -i :1.0 -vcodec hevc_nvenc -x265-params lossless=1 outout.mp4


# 录屏时录音
ffmpeg -f x11grab -r 30 -i $DISPLAY -f pulse -ac 2 -i default -vcodec hevc_nvenc -profile:v main10 -acodec aac -y output.mp4

