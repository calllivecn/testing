#!/usr/bin/env python3
# coding=utf-8
# date 2021-07-22 17:24:22
# author calllivecn <c-all@qq.com>


import json

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
class DotDict2(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    def __getattr__(self, name):
        return self.get(name)
    
    def __setattr__(self, name, value):
        self[name] = value


# 我的实现 完整点的
class DotDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getattr__(self, name):
        return self.get(name)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def loads(self, *args, **kwargs):
        self.__dict__ = json.loads(*args, **kwargs, object_hook=self.__d2dd)

    def dumps(self, *args, **kwargs):
        return json.dumps(self, *args, **kwargs, default=self.__dd2d)

    def load(self, fp, *args, **kwargs):
        self.__dict__ = json.load(fp, *args, **kwargs, object_hook=self.__d2dd)

    def dump(self, *args, **kwargs):
        return json.dump(self, *args, **kwargs, default=self.__dd2d)
    
    @classmethod
    def __d2dd(cls, obj):
        return cls(obj)

    @classmethod
    def __dd2d(cls, obj):

        if isinstance(obj, cls):
            return obj

        return obj


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

dd2.dep1.dep2.dep3 = "这是3层深度值"

print(dd2.k1)
print(dd2.k2)
print(dd2["k3"])
print(dd2.k4)

dd2.k4 = list(range(5))

print(dd2.k4[3])
