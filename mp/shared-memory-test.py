#!/usr/bin/env python3
# coding=utf-8
# date 2023-05-07 23:12:51
# author calllivecn <calllivecn@outlook.com>

import os

from multiprocessing import shared_memory


# sm1g = shared_memory.SharedMemory("calllivecn", True, 100*(1<<20))
sm1g = shared_memory.SharedMemory("zx")

print(sm1g.buf[:40].tobytes())


block=1<<20
cur = 0

while cur < sm1g.size:

    sm1g.buf[cur:cur+block] = os.urandom(block)
    cur += block


# sm1g.close()
# sm1g.unlink()

