#!/usr/bin/env python3
# coding=utf-8
# date 2021-05-08 16:30:23
# author calllivecn <calllivecn@outlook.com>

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

    def __init__(self, arga, argb, argc="这是C类的默认参数"):
        #super().__init__(arga)
        #self.argB = argb

        # 这样会执行多次 __init__()
        #super(A, self).__init__(arga)
        #super(B, self).__init__(argb)

        # 由于不能修改 A 和 B 的定义，为了让代码能够运行并清晰地展示，
        # 使用第二种方法：显式调用父类 __init__。
        # 但请记住，如果可以修改父类，让它们支持 **kwargs 并使用 super() 链式调用是更优的。

        # -----------------------------------------------------------
        # 正式推荐的写法 (假设 A 和 B 已修改，可以处理 **kwargs)
        # -----------------------------------------------------------
        # super().__init__(name_a=name_a, name_b=name_b)
        # self.name_c = name_c
        # print(f"初始化 C: {self.name_c}")
        # print(f"C 的 MRO: {C.__mro__}")


        # -----------------------------------------------------------
        # 为了演示目的，且不修改 A, B 的定义，我们使用显式调用方式
        # -----------------------------------------------------------
        A.__init__(self, arga)
        B.__init__(self, argb)
        self.argc = argc
        print(f"初始化 C: {self.argc}")
        print(f"C 的 MRO: {C.__mro__}")


print(f"MRO: {C.__mro__}")

c = C("argA","argB")

c.print()
c.show()



class D(A, B):
    pass

d = D("argD")

d.print()
d.show()


