# Dockerfile: 编译一个av-xxx.whl包

- 需要挂载一个目录，把编码好的av-xxxx.whl包输出到主机上：
- TMPDIR=$(pwd) podman build -v $(pwd):/build --build-arg AV_VERSION=14.4.0 -t ffmpeg-pyav .


## 要使用 nvidia-gpu 硬件编码的，查看容器中使用cuda的方式。

