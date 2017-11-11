#!/usr/bin/env python3
#coding=utf-8


import math

from libpy import runtime

def prime(n):
    if n <= 2 :
        return True
    
    for i in range(2,int(math.sqrt(n))):
        if 0 == n % i:
            return False

    return True

@runtime
def main(m):
    for i in range(1,m+1):
    #for i in range(1,m+1,2):
        if prime(i):
            pass
            #print(i,"是素数")



if __name__ == "__main__":
    main(100000)

