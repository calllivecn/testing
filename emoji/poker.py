#!/usr/bin/env python3
# coding=utf-8
# date 2019-08-22 10:46:03
# author calllivecn <c-all@qq.com>

remove=["🂯", "🂰", "🂿", "🃀", "🃐"]

li=[ chr(c) for c in range(ord("🂠"), ord("🃟")) ]

for i in li:
    if i in remove:
        pass
    else:
        print("{} ".format(i), end="")

