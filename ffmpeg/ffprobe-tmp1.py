#!/usr/bin/env python3
# coding=utf-8
# date 2022-11-08 08:52:00
# author calllivecn <c-all@qq.com>


import sys
import json
import glob
import pickle
import subprocess

from pathlib import Path
from typing import (
    Literal,
)

def ffprobe(filename: Path):
    cmd = ["ffprobe", "-hide_banner", "-loglevel", "error", "-print_format", "json", "-show_streams", "-show_format", "-i", filename]
    result = subprocess.run(cmd, stdout=subprocess.PIPE)
    return json.loads(result.stdout)


def filter_stream(streams: list, typ: Literal["audio", "subtitle", "video"] = "audio") -> list:
    l = []
    for stream in streams:
        codec_type = stream.get("codec_type")
        if codec_type == typ:
            l.append(stream)
    return l


def jpn_audio(audios):
    for stream in audios:
        tags = stream.get("tags")
        if tags:
            if tags.get("language") == "jpn" and tags.get("title") == "日语":
                return stream.get("index")
        else:
            print(f"没有tags...")
 

def chi_subtitle(subtitles):
    for stream in subtitles:
        tags = stream.get("tags")
        if tags:
            if tags.get("language") == "chi" and tags.get("title") == "简体中文":
                return stream.get("index")
        else:
            print(f"没有tags...")


from pprint import pprint


def main(dir_path):
    ffmpegs = []
    for filename in glob.glob("*", root_dir=dir_path):
        _continue = False
        p = dir_path / filename
        j = ffprobe(p)
        print("-"*40)
        # pprint.pprint(j)

        # mkv title
        mkv_title = p.name.split(".")[0]
        out_name = p.name.split("：")[0].split(" ")[1]

        # pprint(j)
        streams = j["streams"]
        audios = filter_stream(streams, "audio")
        subtitles = filter_stream(streams, "subtitle")

        # jpn_audio
        jpn_audio_index = jpn_audio(audios)
        if not jpn_audio_index:
            _continue = True
            print(p.name, "没有找到audio jpn 日语")

        # chi_ass
        chi_ass_index = chi_subtitle(subtitles)
        if not chi_ass_index:
            _continue = True
            print(p.name, "没有找到 subtitle chi 简体中文")

        if _continue:
            print("继续...")
            print("="*20, "我是分割线", "="*20)
            continue

        # 组装 ffmpeg 命令
        ffmpeg = [
            "ffmepg", "-hide_banner",
            "-i", filename,
            "-map", "0:0", "-vcodec", "libx265", "-metadata", f"title={mkv_title}",
            "-map", f"0:{jpn_audio_index}", "-acodec", "copy", "-disposition:s:a:0", "default",
            "-map", f"0:{chi_ass_index}", "-scodec", "copy", "-disposition:s:s:0", "default",
            f"{out_name}{p.suffix}"
        ]
        print(ffmpeg)
        ffmpegs.append(ffmpeg) 
        print("="*20, "我是分割线", "="*20)

    
    save_file = Path("/tmp/ffprobe-tmp.json")
    print(f"结束时保存下: {save_file}")
    with open(save_file, "w") as f:
        json.dump(ffmpegs, f)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
