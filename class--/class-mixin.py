#!/usr/bin/env python3
# coding=utf-8
# date 2021-05-08 16:30:23
# author calllivecn <c-all@qq.com>

"""
要避免使用多重继承。

好像，像下面这样，就能使用多重继承了~！？:
    不行 B 的 __init__() 就没执行。。。
"""

class A:

    def __init__(self, argA):
        self.argA = argA
        print(f"我是: class A")

    def print(self):
        print(f"print() --> 参数为：{self.argA}")

class B:

    def __init__(self, argB):
        self.argB = argB
        print(f"我是: class B")

    def show(self):
        print(f"show() --> 参数为：{self.argB}")



class C(A, B):

    def __init__(self, arga, argb):
        super().__init__(arga)
        self.argB = argb

        # 这样会执行多次 __init__()
        #super(A, self).__init__(arga)
        #super(B, self).__init__(argb)


print(f"MRO: {C.__mro__}")

c = C("argA","argB")

c.print()
c.show()



class D(A, B):
    pass

d = D("argD")

d.print()
d.show()

