#!/usr/bin/env python3
# coding=utf-8
# date 2019-03-20 17:59:36
# https://github.com/calllivecn



import os
import sys


import multiprocessing as mp
import threading as td

from concurrent.futures import ProcessPoolExecutor as ppe, ThreadPoolExecutor as tpe

import lzma


def multicore(data):
    
    return lzma.compress(data)


BUF = 8*(1<<10) # 8k
CPUs = os.cpu_count()

multip = ppe()

with open(sys.argv[1], 'rb') as inf, open(sys.argv[2],'wb') as outf:
    i = 0
    while True:
        over = False
        mdata = []

        for _ in range(CPUs):
            data = inf.read(BUF)
            if not data:
                over = True
        i+=1 
        print("计算{}次".format(i))
        rdata = multip.map(multicore, mdata)
        print(rdata)
        outf.writelines(rdata)
        
        if over:
            break
    

multip.shutdown()
