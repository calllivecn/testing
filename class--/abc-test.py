#!/usr/bin/env python3
# coding=utf-8
# date 2022-12-14 17:11:45
# author calllivecn <calllivecn@outlook.com>

from typing import (
    TypeVar,
    Protocol,
)

T = TypeVar("T")

class ABC(Protocol[T]):

    def func1(self, arg1: str, arg2: str) -> str:
        """
        required: True
        """
        ...

    def func2(self) -> int:
        ...


class A(ABC):
    
    # def func1(self, arg1, arg2) -> str:
    def func1(self, arg1) -> str:
        return arg1 


a = A()
# print(a.func1("str1", "str2"))
print(a.func1("str1"))