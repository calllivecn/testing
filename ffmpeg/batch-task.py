#!/usr/bin/env python3

import sys
import glob
import argparse
import subprocess
from pathlib import Path

from concurrent.futures import ThreadPoolExecutor


def video(cmd):
    print(f"当前执行: {cmd}")
    return subprocess.run(cmd)

def infile(f):
    with open(f) as f:
        tmp = f.readlines()

    return [ l.rstrip("\n") for l in tmp ]

parse = argparse.ArgumentParser()
parse.add_argument("-T", type=int, default=1, help="默认跑1个任务")
#parse.add_argument("--scale", type=int, choices=(2, 3, 4), required=True, help="放大倍率")
parse.add_argument("--out-dir", dest="outdir", type=Path, help="输出目录")

parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)

#group = parse.add_mutually_exclusive_group()
#group.add_argument("-i", "--infile", type=Path, help="从文件读取输入，一行一个文件。")
#group.add_argument("files", nargs="*", help="输入的 *.mp4")

parse.add_argument("files", nargs="*", help="输入的 *.mp4")

args = parse.parse_args()

if args.parse:
    print(args)
    parse.print_help()
    sys.exit(0)


loop = ThreadPoolExecutor(max_workers=args.T)

if args.files:
    files = args.files
elif args.infile:
    files = infile(args.infile)
else:
    print("没有输入文件？？？")
    sys.exit(1)


for v in files:
    # cmd = f'python inference_realesrgan_video.py -n realesr-animevideov3 -s 3 --fp32 --suffix outx3 -i {in_} -o {out_dir}'
    #cmd = ["python", "inference_realesrgan_video.py", "-n", "realesr-animevideov3", "-s", args.scale, "--fp32", "--suffix", f"AIx{args.scale}", "-i", v, "-o", args.outdir]

    # 这样可以在转码时，解码和编码 都使用GPU
    cmd = ["ffmpeg", "-hide_banner", "-vcodec", "h264_cuvid", "-i", v, "-vcodec", "hevc_nvenc", "-acodec", "copy", args.outdir / v]

    print(f"加入任务: {cmd}")
    loop.submit(video, cmd)


loop.shutdown()
