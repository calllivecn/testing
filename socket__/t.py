#!/usr/bin/env python3
# coding=utf-8
# date 2021-11-10 18:04:20
# author calllivecn <calllivecn@outlook.com>

import io
import time

begin = time.time()
buf = b""
for i in range(0, 50000):
    buf += b"Hello World"
end = time.time()
seconds = end - begin
print("Concat:", seconds)


begin = time.time()
buf = io.BytesIO()
for i in range(0, 50000):
    buf.write(b"Hello World")
end = time.time()
seconds = end - begin
print("BytesIO:", seconds)
