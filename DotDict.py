#!/usr/bin/env python3
# coding=utf-8
# date 2021-07-22 17:24:22
# author calllivecn <calllivecn@outlook.com>

import time
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

    def __setattr__(self, name, value):
        self.__setitem__(name, value)

    def loads(self, obj, *args, **kwargs):
        self.update(json.loads(obj, *args, **kwargs, object_hook=self.__d2dd))

    def dumps(self, *args, **kwargs):
        return json.dumps(self, *args, **kwargs, default=self.__dd2d)

    def load(self, fp, *args, **kwargs):
        self.update(json.load(fp, *args, **kwargs, object_hook=self.__d2dd))

    def dump(self, fp, *args, **kwargs):
        return json.dump(self, fp, *args, **kwargs, default=self.__dd2d)
    
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
if dd:
    print("init dd:", dd, True)
else:
    print("init dd:", dd, False)

dd.k1 = 1
dd.k2 = 2
print(dd)


print("------------------")
dd2 = DotDict()
dd2.loads('{"name": "zx"}')
print(dd2)


dd2.k1 = "test string"

dd2.name = "zx"

dd2.dep1 = "这是1层深度值"
dd2.dep2 = int(time.time())
print(dd2.dep1)

print(dd2.k1)
print(dd2.k2)
print(dd2.k4)

dd2.k4 = list(range(5))

print(dd2)

print(dd2.dumps(ensure_ascii=False))
