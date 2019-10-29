#!/usr/bin/env python3
#coding=utf-8
# date 2018-12-16 21:46:48
# author calllivecn <c-all@qq.com>

import os
import sys
import time

block=1<<20  # MB

count = (1<<10) * 50 # 总50GB


def main(datasize):

    with open("test.dd","wb") as f:
        for i in range(datasize):
            f.write(os.urandom(block))
            f.flush()
            #print(i)


def output_stdout():
    fd = sys.stdout.fileno()
    try:
        while True:
            os.write(fd, os.urandom(block))
    except KeyboardInterrupt:
        pass

def speed():
    try:
        start = time.time()
        data_sum = 0
        while True:

            #ssl.RAND_bytes(block)
            os.urandom(block)

            data_sum += 1

            end = time.time()
            interval = end - start
            if interval >= 1:
                print(data_sum / interval,"MB", "interval time: ", interval, "秒")
                data_sum = 0
                start = time.time()
            
    except KeyboardInterrupt:
        pass


def multi_speed():
    import multiprocessing as mp

    cpus = mp.cpu_count()
    for _ in range(cpus):
    
        proc = mp.Process(target=speed)
        proc.start()


if __name__ == "__main__":
    #main(500)
    #output_stdout()
    speed()
    #multi_speed()
