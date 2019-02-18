#!/usr/bin/env python3
#coding=utf-8

import sys
import math

from libpy import runtime

def prime(n):
    if n == 1:
        return  False

    for i in range(2,int(math.sqrt(n)) + 1):
        if 0 == n % i:
            return False

    return True

@runtime
def main(m):

    for i in range(1, m + 1):
        if prime(i):
            print(i,"是素数")
    

if __name__ == "__main__":
    main(int(sys.argv[1]))

