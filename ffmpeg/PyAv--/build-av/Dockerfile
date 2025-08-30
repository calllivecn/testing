# 需要挂载一个目录，把编码好的av-xxxx.whl包输出到主机上：
# TMPDIR=$(pwd) podman build -v $(pwd):/build --build-arg AV_VERSION=14.4.0 -t pyav .

FROM ubuntu-base:25.04

ARG AV_VERSION

# General dependencies # Library components
RUN apt update \
&& apt install -y build-essential python3-pip python3-dev pkg-config \
libavformat-dev libavcodec-dev libavdevice-dev \
libavutil-dev libswscale-dev libswresample-dev libavfilter-dev


# ubuntu24.04 中的 ffmpeg v6.1.1
RUN pip config --global set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
&& pip install --break-system-packages av==${AV_VERSION} --no-binary av \
&& find ~/.cache/pip/ -type f -iname "*av*.whl" -exec cp -v {} /build/ \;


