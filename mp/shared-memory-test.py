#!/usr/bin/env python3
# coding=utf-8
# date 2023-05-07 23:12:51
# author calllivecn <calllivecn@outlook.com>

import os

from multiprocessing.shared_memory import SharedMemory



class MultiSharedMemory:

    def __init__(self, max_size: int=-1):
        self.max_size = max_size
        self.cur_size = 0

        self._shared_memory: dict = {}


    
    def create(self, size: int) -> SharedMemory:
        self.sm = SharedMemory(create=True, size=size)
        return self.sm
    
    def 

    def close(self):
        self.sm.close()
    

    def unlink(self):
        self.sm.close()


size = 64

sm1g = SharedMemory("calllivecn", True, size)
# sm1g = SharedMemory("zx")


block=1<<20
cur = 0
while cur < sm1g.size:
    sm1g.buf[cur:cur+block] = os.urandom(size)
    cur += block

print(sm1g.buf[:40].tobytes())

input("回车退出")

print(sm1g.buf[:40].tobytes())

sm1g.close()
sm1g.unlink()

