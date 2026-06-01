#
# 这是开源库，不支持HECV这种，
# intel-media-va-driver 
# 使用非开源的看的多。
# intel-media-va-driver-non-free
#
# 这是opencv-python 的intel opencl 的支持库。可以安装clinfo包，执行clinfo。查看详细
# apt install ocl-icd-libopencl1 intel-opencl-icd
apt -y update
apt -y install python3 python3-pip python3-venv pkg-config build-essential \
	ca-certificates vim locales \
	ffmpeg vainfo \
	intel-media-va-driver-non-free \
	libavformat-dev libavcodec-dev libavdevice-dev \
	libavutil-dev libswscale-dev libswresample-dev libavfilter-dev


# 启用 zh_CN.UTF-8 locale
sed -i '/zh_CN.UTF-8/s/^# //g' /etc/locale.gen
locale-gen

# 设置时区
ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

pip3 config --global set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

pip install --break-system-packages ipython cryptography
pip install --break-system-packages av==${AV_VERSION} --no-binary av

find ~/.cache/pip/ -type f -iname "*av*.whl" -exec cp -v {} /build/ \;

pip cache purge

apt clean
rm -rf /var/lib/apt/lists

