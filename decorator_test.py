#!/usr/bin/env python3
#coding=utf-8


import asyncio

def test(func):
	def wrapper(*args,**kw):
		print('func 执行前.')
		func(*args,**kw)
		print('func 执行后.')
	return wrapper

@test
def tmp(text):
	print('this tmp function() -->',text)


tmp('execute1')
