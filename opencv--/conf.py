#!/usr/bin/env python3
# coding=utf-8
# date 2023-10-18 01:49:30
# author calllivecn <calllivecn@outlook.com>


import sys
import json
import configparser
from pathlib import Path

__all__ = ("VIDEO")

conf = Path("video-src.conf")

if conf.exists() and conf.is_file():
    cfg = configparser.ConfigParser()
    cfg.read(conf)
    # print(f"{cfg=}")

else:
    print("没有配置视频源地址")
    sys.exit(1)

VIDEO = cfg.get("opencv", "video")

print(f"视频源地址：{VIDEO=}")

if __name__ == "__main__":
    print(VIDEO)
