#!/usr/bin/bash

IMAGE="localhost/ffmpeg-pyav:latest"

# ffmpeg 需要是带版本号的
# 从这个报错信息中知道：
# [AVHWDeviceContext @ 0x57245a42dd40] Cannot load libcuda.so.1
# [AVHWDeviceContext @ 0x57245a42dd40] Could not dynamically load CUDA
# [vist#0:0/vp9 @ 0x57245a429e00] [dec:vp9_cuvid @ 0x57245a42e800] Error while opening decoder: Operation not permitted

CUDA0="/usr/lib/x86_64-linux-gnu/libcuda.so.1"
CUDA1="/usr/lib/x86_64-linux-gnu/libnvcuvid.so.1"
CUDA2="/usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1"

  #--security-opt=label=disable \  # 关 SELinux 限制
  #-v /usr/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:ro \
  #-v /usr/lib/x86_64-linux-gnu:/host-driver-libs:ro \
  #-e LD_LIBRARY_PATH=/host-driver-libs \
  #-v /usr/lib/x86_64-linux-gnu/libcuda.so.575.64.03:/usr/lib/x86_64-linux-gnu/libcuda.so.575.64.03:ro \
  #
podman run -itd --name ffmpeg-pyav -v $HOME/data/pyav:/py \
  --device /dev/nvidia0 \
  --device /dev/nvidiactl \
  --device /dev/nvidia-uvm \
  --device /dev/nvidia-uvm-tools \
  -v ${CUDA0}:${CUDA0}:ro \
  -v ${CUDA1}:${CUDA1}:ro \
  -v ${CUDA2}:${CUDA2}:ro \
  "$IMAGE" bash
