FROM ubuntu-devel:latest


# General dependencies # Library components
RUN apt update \
&& apt install -y python3-pip python3-dev pkg-config \
libavformat-dev libavcodec-dev libavdevice-dev \
libavutil-dev libswscale-dev libswresample-dev libavfilter-dev


# ubuntu24.04 中的 ffmpeg v6.1.1
RUN pip install --break-system-packages av==13.1.0 --no-binary av


