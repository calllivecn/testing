apt -y update
apt -y install python3 python3-pip python3-venv pkg-config \
	ffmpeg ca-certificates vim locales \
	libavformat-dev libavcodec-dev libavdevice-dev \
	libavutil-dev libswscale-dev libswresample-dev libavfilter-dev
	

# 启用 zh_CN.UTF-8 locale
sed -i '/zh_CN.UTF-8/s/^# //g' /etc/locale.gen
locale-gen

pip3 config --global set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

pip install --break-system-packages ipython cryptography
pip install --break-system-packages av==16.0.1 --no-binary av
pip cache purge

apt clean
rm -rf /var/lib/apt/lists

