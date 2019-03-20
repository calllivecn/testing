#!/usr/bin/env python3
# coding=utf-8
# date 2019-03-20 17:59:36
# https://github.com/calllivecn



import os
import sys


import multiprocessing as mp
import threading as td

from concurrent.futures import ProcessPoolExecutor as ppe, ThreadPoolExecutor as tpe

import gzip
import bz2
import lzma

def gzipcompress(data):
    data = gzip.compress(data)
    return data

def bz2compress(data):
    data = bz2.compress(data)
    return data

def lzmacompress(data):
    data = lzma.compress(data, preset=9)
    return data


#BUF = 8*(1<<10) # 8K
BUF = 1<<20 # 1M
CPUs = os.cpu_count()

multip = ppe(max_workers=3)

with open(sys.argv[1], 'rb') as inf, open(sys.argv[2],'wb') as outf:
    i = 0
    while True:
        over = False
        mdata = []

        for _ in range(CPUs):
            data = inf.read(BUF)

            if not data:
                over = True
                break

            mdata.append(data)

        i+=1 

        print("计算{}次".format(i))

        #for rdata in multip.map(compress, mdata):
            #print("rdata", rdata)

        outf.writelines(multip.map(bz2compress, mdata))
        
        if over:
            break
    
multip.shutdown()
print("done")
