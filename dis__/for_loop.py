#!/usr/bin/env py3
#coding=utf-8
# date 2018-08-20 21:17:29
# author calllivecn <calllivecn@outlook.com>

import time

def runningtime(func):
    def wapper(*args,**kwargs):
        start = time.time()
        result = func(*args,**kwargs)
        end = time.time()
        print(func.__name__,"运行时间：",end - start)
        return result
    
    return wapper

sum=0

#@runningtime
def for_range(count):
    global sum
    for i in range(count):
        sum+=1

    return sum


#@runningtime
def while_loop(count):
    global sum
    i=0
    while i < count:
        sum+=1
        i+=1

    return sum


COUNT=10**8

for_range(COUNT)

while_loop(COUNT)

import dis

print("查看for_range伪汇编代码:")
dis.dis(for_range)
print("查看while_loop伪汇编代码:")
dis.dis(while_loop)
