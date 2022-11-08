#!/usr/bin/env python3
# coding=utf-8
# date 2022-11-08 08:52:00
# author calllivecn <c-all@qq.com>


import sys
import json
import subprocess

from pathlib import Path

def ffprobe(filename: Path):
    cmd = ["ffprobe", "-hide_banner", "-i", filename, "-print_format", "json", "-show_streams"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE)
    return json.loads(result.stdout)


def check_chi(streams):

    for stream in streams:

        if stream.get("codec_type") == "audio":
            tags = stream.get("tags")
            if tags:
                if tags.get("language") == "chi":
                    return stream.get("index")
                    

def check_jpn(streams):

    for stream in streams:

        if stream.get("codec_type") == "audio":
            tags = stream.get("tags")
            if tags:
                if tags.get("language") == "jpn":
                    return stream.get("index")
 

# import pprint

# for f in sys.argv[1:]:

def main(f):
    p = Path(f)
    j = ffprobe(p)
    print("-"*40)
    # pprint.pprint(j)
    index = check_jpn(j["streams"])
    if index != 2:
        print(f"{p.name} -- jpn音轨不是:2, 是: {index}")
    elif index is None:
        print(f"{p.name} -- 没有找到音轨类型.")

    print("="*20, "我是分割线", "="*20)


if __name__ == "__main__":
    main(sys.argv[1])