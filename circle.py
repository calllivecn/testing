#!/usr/bin/env python3
#coding=utf-8




import math,sys

"""
R = math.sqrt(a^2 + b^2)
"""

R=int(sys.argv[1])

def circle(r):
    for x in range(r,-r,-1):
        #print("x:",x)
        y = math.sqrt(r**2 - (x)**2)
        print("dobule (x,y) : ",x,round(y))


circle(R)


