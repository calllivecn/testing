#!/bin/bash
# date 2022-12-23 08:27:05
# author calllivecn <c-all@qq.com>



# 录制
ffmpeg -i rtsp://admin:admin@192.168.1.100:554 -vcodec copy out.avi 
ffmpeg -rtsp_transport tcp -i rtsp://admin:admin@192.168.1.100:554 -vcodec copy out.avi 

# 播放

ffplay -i rtsp://admin:admin@192.168.1.100:554
ffplay -rtsp_transport tcp -i rtsp://admin:admin@192.168.1.100:554

