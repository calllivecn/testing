#!/usr/bin/env python3
#coding=utf-8

import sys
import math

import numba as nb
#from numba import vectorize,float32,float64,int8,int32,int64

#from libpy import runtime

#@nb.vectorize(['int8(int32)'])
            #int8(int64),
            #int8(float32),
            #int8(float64)])
@nb.njit
def prime(n):
    if n == 1 :
        return False
    
    for i in range(2, int(math.sqrt(n)) + 1):
        if 0 == n % i:
            return False

    return True

def freema(n):
    return 2**2**n + 1


#@runtime
#@nb.vectorize(['void(int32)'])
@nb.jit(nopython=True)
def main(m):
    for i in range(1,m + 1):
        if prime(i):
            print(i,':是一个素数')


if __name__ == "__main__":
    number = int(sys.argv[1])
    main(number)
    #print(prime(freema(5)))

