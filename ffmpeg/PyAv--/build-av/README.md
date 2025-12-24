# Dockerfile-build: 编译一个av-xxx.whl包

- 需要挂载一个目录，把编码好的av-xxxx.whl包输出到主机上：
- TMPDIR=$(pwd) podman build -v $(pwd):/build --build-arg AV_VERSION=14.4.0 -t ffmpeg-pyav .


# Dockerfile: 容器里使用的最新版本PyAv

- 先修改 run.sh 里的 AV\_VERSION变量指定要安装的PyAv版本
- TMPDIR=$(pwd) podman build -t ffmpeg-pyav .


## 要使用 nvidia-gpu 硬件编码的，查看容器中使用cuda的方式。

