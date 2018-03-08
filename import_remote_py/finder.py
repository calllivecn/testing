#!/usr/bin/env python3
#coding=utf-8
# date 2018-03-06 10:58:43
# author calllivecn <c-all@qq.com>

class urlmodule:                   
     def find_module(self,fullname,path):
         print("Looking for",fullname,path)
         return None



import sys

sys.meta_path.insert(0,urlmodule())
