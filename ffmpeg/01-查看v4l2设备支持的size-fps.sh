
# 
ffmpeg -f video4linux2 -list_formats all -i /dev/video0 

# 查看当前设备的音频输入
# ALSA 标识符的语法如下：
# 	hw:CARD[,DEV[,SUBDEV]]
# 	三个参数（按顺序：CARD、DEV、SUBDEV）指定卡号或标识符、设备号和子设备号（-1 表示任意）。
# 	要查看系统当前识别的卡列表，请检查文件 /proc/asound/cards 和 /proc/asound/devices 。
# 
# 
# 	sample_rate
# 	Set the sample rate in Hz. Default is 48000.
# 	设置采样率（以 Hz 为单位）。默认值为 48000。
# 
# 	channels
# 	Set the number of channels. Default is 2.
# 	设置通道数。默认值为 2。

# cmd
#ffmpeg -f alsa -i hw:0 alsaout.wav
#ffmpeg -f alsa -i hw:0 -acodec libmp3lame alsaout.mp3

