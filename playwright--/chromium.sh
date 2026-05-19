#!/usr/bin/bash

USER_DATA_DIR="$HOME/chromium-user-dir"

if [ -d "$1" ];then
    USER_DATA_DIR="$1"
fi

  # --remote-debugging-address=10.1.3.20 \ # 这个配置现在chrome也不认，还是只127.0.0.1
  #--headless=new \
# 重新以多页面模式启动
# 安装插件时添加代理：--proxy-server="socks5://10.1.3.1:10004"
  #--proxy-server="socks5://10.1.3.1:10004" \
 
#如果你想使用特定的 Profile（例如你有很多个账号），可以使用： --profile-directory="Default"

  # 这是显示的窗口大小，在非--headless=new模式下
  #--windows-size=1920,1080 \
  #--disable-gpu \

google-chrome-stable \
  --remote-debugging-port=9222 \
  --user-data-dir="$USER_DATA_DIR" \
  --disable-dev-shm-usage \
  --window-size=1200,800
  #--headless
