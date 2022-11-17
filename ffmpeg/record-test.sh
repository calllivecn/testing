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

# kmsgrab(wayland)有问题
video1(){
# 只录屏
#-f kmsgrab -framerate $fps -t 10 -r $fps -i - -vf 'hwmap=derive_device=vaapi,scale_vaapi=w=1920:h=1080:format=nv12' -vcodec $codec \
ffmpeg -hide_banner -threads $threads \
-f kmsgrab -t 10 -r $fps -i - -vcodec $codec \
"$1"
}


# kmsgrab(wayland)有问题
video2(){
# 只录屏
ffmpeg -hide_banner -threads $threads \
-f kmsgrab -framerate $fps -i - -vf 'hwmap=derive_device=vaapi,hwdownload,format=bgr0' -vcodec $codec -r $fps \
"$1"
}


# ok
video3(){
# 录屏+录音
ffmpeg -hide_banner -threads $threads \
-f kmsgrab -framerate $fps -ac 1 -i - -vcodec $codec -vf 'hwmap=derive_device=vaapi' -r $fps \
-f alsa -ac 1 -i hw:$1 -c:a aac \
"$2"
}

# kmsgrab(wayland)有问题
video4(){
# 从第一个活动平面捕获，将结果下载到正常帧并进行编码。这仅在帧缓冲区既是线性的又是可映射的情况下才有效——否则，结果可能会被扰乱或无法下载。
#ffmpeg -f kmsgrab -i - -vf 'hwdownload,format=bgr0' output.mp4

# 以 60fps 从 CRTC ID 42 捕获，将结果映射到 VAAPI，转换为 NV12 并编码为 H.264。
#ffmpeg -crtc_id 42 -framerate 60 -f kmsgrab -i - -vf 'hwmap=derive_device=vaapi,scale_vaapi=w=1920:h=1080:format=nv12' -c:v h264_vaapi output.mp4

# 要仅捕获平面的一部分，可以裁剪输出 - 这可用于捕获单个窗口，只要它具有已知的绝对位置和大小即可。例如，要捕获和编码 1920x1080 平面的中间四分之一：
ffmpeg -f kmsgrab -i - -vf 'hwmap=derive_device=vaapi,crop=960:540:480:270,scale_vaapi=960:540:nv12' -c:v h264_vaapi output.mp4

}

video1 "$1" 
