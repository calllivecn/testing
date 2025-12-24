#!/usr/bin/bash

IMAGE="localhost/ffmpeg-pyav:latest"

  #--security-opt=label=disable \  # 关 SELinux 限制
  #-v /usr/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:ro \
  #-v /usr/lib/x86_64-linux-gnu:/host-driver-libs:ro \
  #-e LD_LIBRARY_PATH=/host-driver-libs \
  #-v /usr/lib/x86_64-linux-gnu/libcuda.so.575.64.03:/usr/lib/x86_64-linux-gnu/libcuda.so.575.64.03:ro \
podman run -itd --name ffmpeg-pyav -v $(pwd):/py \
  --device /dev/nvidia0 \
  --device /dev/nvidiactl \
  --device /dev/nvidia-uvm \
  --device /dev/nvidia-uvm-tools \
  -v /usr/lib/x86_64-linux-gnu/libcuda.so:/usr/lib/x86_64-linux-gnu/libcuda.so:ro \
  -v /usr/lib/x86_64-linux-gnu/libcuda.so.1:/usr/lib/x86_64-linux-gnu/libcuda.so.1:ro \
  "$IMAGE" bash
