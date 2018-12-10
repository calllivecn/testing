#!/usr/bin/env py3
#coding=utf-8
# date 2018-12-10 15:35:40
# author calllivecn <c-all@qq.com>

import sys


def bit_64(number):
    if number > sys.maxsize and number < 0:
        print("太大 请输入小于{}大于0的数".format(sys.maxsize))
        return False

    #print("第一次的变量：",locals())
    num = 0
    while number:
        b = (number - 1) 
        number &= b
        num += 1
        print("变量：",locals())

    print("一共有{}位bit为1".format(num))


if __name__ == "__main__":
    num = input("请输入一个小于{}的数: ".format(sys.maxsize))
    s = int(num)
    bit_64(s)
