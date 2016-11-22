#!/usr/bin/env python3
#coding=utf-8


import sys


def perm(m):
	global p
	if m == 0:
		print(p)
		#print(p,flush=True)
	else:
		for j in range(n):
			if p[j] == 0:
				p[j]=m
				perm(m-1)
				p[j]=0

def nn(m):
	s=1
	for i in range(1,m+1):
		s*=i
		#print('s : {} i : {}'.format(s,i))
	return s

n=int(sys.argv[1])

for i in range(1,n+1):
	t=nn(i)
	print('{} 的介乘值 {} 所要的二进制位数 : {}'.format(i,t,t.bit_length()))


#p=[ 0 for x in range(n) ];perm(n-1)

