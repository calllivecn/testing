#!/usr/bin/env python3
# coding=utf-8
# date 2023-06-11 09:34:07
# author calllivecn <c-all@qq.com>


from jnius import autoclass

j_system = autoclass('java.lang.System')
j_system.out.println('Hello world')
Stack = autoclass('java.util.Stack')
stack = Stack()
stack.push('hello')
stack.push('world')
print(stack.pop())
print(stack.pop())
print(f"{dir()=}")
print(f"{locals()=}")
