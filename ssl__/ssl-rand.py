#!/usr/bin/env py3
#coding=utf-8
# date 2018-11-27 12:03:24
# author calllivecn <c-all@qq.com>

import os
import sys
import time
import ssl


block=1<<20  # MB

count = (1<<10) * 50 # 总50GB


def main(datasize):

    with open("test.dd","wb") as f:
        for i in range(datasize):
            f.write(ssl.RAND_bytes(block))
            f.flush()
            #print(i)


def output_stdout():
    fd = sys.stdout.fileno()
    try:
        while True:
            os.write(fd, ssl.RAND_bytes(block))
    except KeyboardInterrupt:
        pass

def speed():
    try:
        start = time.time()
        data_sum = 0
        while True:

            ssl.RAND_bytes(block)

            data_sum += 1

            end = time.time()
            interval = end - start
            if interval >= 1:
                print(round(data_sum / interval, 2),"MB", "interval time: ", round(interval, 3), "秒")
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
