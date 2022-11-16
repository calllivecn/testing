#!/bin/bash
# date 2022-07-16 01:54:33
# author calllivecn <c-all@qq.com>



# 可能需要先设置 cap 非常不安全
#sudo setcap cap_sys_admin+ep /usr/bin/ffmpeg

fps="24"
fps="30"
codec="libx265"
codec="h264_vaapi"
codec="hevc_nvenc"
threads="$(nproc)"
threads="4"

video1(){
# 只录屏
ffmpeg -hide_banner -threads $threads \
-f kmsgrab -framerate $fps -t 10 -i - -vf 'hwmap=derive_device=vaapi,scale_vaapi=w=1920:h=1080:format=nv12' -vcodec $codec -r $fps \
"$1"
}


video2(){
# 只录屏
ffmpeg -hide_banner -threads $threads \
-f kmsgrab -framerate $fps -i - -vf 'hwmap=derive_device=vaapi,hwdownload,format=bgr0' -vcodec $codec -r $fps \
"$1"
}

video3(){
# 录屏+录音
ffmpeg -hide_banner -threads $threads \
-f kmsgrab -framerate $fps -ac 1 -i - -vcodec $codec -vf 'hwmap=derive_device=vaapi' -r $fps \
-f alsa -ac 1 -i hw:$1 -c:a aac \
"$2"
}

video3 "$1" 
