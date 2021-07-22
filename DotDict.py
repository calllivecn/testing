#!/usr/bin/env python3
# coding=utf-8
# date 2021-07-22 17:24:22
# author calllivecn <c-all@qq.com>

# 网上的实现
class DottableDict(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.__dict__ = self

    def allowDotting(self, state=True):
        if state:
            self.__dict__ = self
        else:
            self.__dict__ = dict()


# 我的实现
class DotDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    def __getattr__(self, name):
        return self.get(name)
    
    def __setattr__(self, name, value):
        self[name] = value

print("------------------")
d1 = {"k1": 1, "k2": 2, "k3": 3}
print(d1)

print("------------------")
dd = DottableDict()
dd.k1 = 1
dd.k2 = 2
print(dd)

print("------------------")
dd2 = DotDict(d1)
print(dd2)

dd2.k1 = "test string"

dd2.name = "zx"

print(dd2.k1)
print(dd2.k2)
print(dd2["k3"])
print(dd2.k4)

dd2.k4 = list(range(5))

print(dd2.k4[3])
