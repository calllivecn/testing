#!/bin/bash
# date 2023-07-09 04:49:26
# author calllivecn <calllivecn@outlook.com>

# 这个是cient 连接到

#ffmpeg -rtsp_transport tcp -i rtsp://zx:huawei.linux@192.168.8.170:8554/live -codec copy rtsp1.mkv

#ffplay -hide_banner -rtsp_transport tcp -i rtsp://zx:huawei.linux@192.168.8.170:8554/live


# 当做服务器等连接拉流
ffmpeg -hide_banner -listen 2 -i rtmp://[::]:8554/live -codec copy rtmp-listen.mkv

