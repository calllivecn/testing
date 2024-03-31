#!/usr/bin/env python3
# coding=utf-8
# date 2019-05-15 11:03:09
# author calllivecn <calllivecn@outlook.com>

import sys

for line in sys.stdin:
    fields = line.strip().split()
    for item in fields:
        print("{} {}".format(item, '1'))
