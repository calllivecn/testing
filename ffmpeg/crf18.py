#!/usr/bin/env python3
# coding=utf-8
# date 2022-11-26 13:25:56
# author calllivecn <calllivecn@outlook.com>

import sys
from pathlib import Path

import ffmpeg

IN = Path(sys.argv[1])
OUT = Path(sys.argv[2])
print(f"in: {IN} out: {OUT}")

out_encoder="hevc_nvenc"

infile = ffmpeg.input(IN)
                    #format='rawvideo', pix_fmt='bgr24',
                    #s=f'{out_width}x{out_height}',
                    # framerate=fps
                    # vcodec="hevc_cuvid")

out_args = {
    "acodec": "copy",
    "vcodec": out_encoder,
    "crf": 18,
    "profile:v": "main10",
    "loglevel": "info",
}

outfile = ffmpeg.output(
                    infile.video,
                    infile.audio,
                    str(OUT),
                    acodec='copy',
                    # pix_fmt='yuv420p',
                    # vcodec='libx264',
                    vcodec=out_encoder,
                    crf=10,
                    "profile:v"="main10",
                    loglevel='info',
                    )

print(f"run args: {outfile.get_args()}")
exit(0)

outfile.overwrite_output().run()
#.run_async(pipe_stdin=True, pipe_stdout=True)
