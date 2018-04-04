#!/usr/bin/env python3
#coding=utf-8


import math

import numba as nb
#from numba import vectorize,float32,float64,int8,int32,int64

from libpy import runtime

#@nb.vectorize(['int8(int32)'])
            #int8(int64),
            #int8(float32),
            #int8(float64)])
@nb.njit
def prime(n):
    if n <= 2 :
        return True
    
    for i in range(3,int(math.sqrt(n))):
        if 0 == n % i:
            return False

    return True

def freema(n):
    return 2**2**n + 1


@runtime
#@nb.vectorize(['void(int32)'])
@nb.jit(nopython=True)
def main(m):
    for i in range(1,m+1):
        if prime(i) :
            pass
            #print(i,':是一个素数')

    print('i:',i)

if __name__ == "__main__":
    #main(1000000)
    print(prime(freema(5)))

