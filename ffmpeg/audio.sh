#!/bin/bash



# 录屏时录音
#ffmpeg -f pulse -ac 1 -i default -ar 16000 -acodec aac -y output.aac
ffmpeg -f pulse -ac 1 -ar 16000 -t 5 -i default -acodec aac -y output.m4a
