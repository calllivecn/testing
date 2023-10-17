#!/usr/bin/env python3
# coding=utf-8
# date 2023-10-18 01:49:30
# author calllivecn <c-all@qq.com>


import sys
import json
from pathlib import Path

__all__ = ("VIDEO")

conf = Path("video-src.json")

if conf.exists() and conf.is_file():
    with open(conf, "rb") as f:
        js = json.load(f)

else:
    print("没有配置视频源地址")
    sys.exit(1)

VIDEO = js["video"]

if __name__ == "__main__":
    print(VIDEO)
