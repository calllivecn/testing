#!/usr/bin/env python3
# coding=utf-8
# date 2023-12-23 17:23:59
# author calllivecn <c-all@qq.com>

import os

with open('/proc/pressure/memory', 'w') as f:
    os.write(f.fileno(), b'some 150000 1000000')



