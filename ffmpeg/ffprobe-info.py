#!/usr/bin/env python3
# coding=utf-8
# date 2022-11-24 09:26:39
# author calllivecn <calllivecn@outlook.com>

import sys
from pathlib import Path
from pprint import pprint

import ffmpeg


IN = Path(sys.argv[1])

# mp4 duration
if IN.suffix.lower() == ".mp4":
    probe = ffmpeg.probe(IN)
    pprint(probe["streams"])
else:
    probe = ffmpeg.probe(IN)
    pprint(probe)

