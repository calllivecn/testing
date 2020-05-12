#!/usr/bin/env python3
# coding=utf-8
# date 2020-05-12 14:18:23
# author calllivecn <c-all@qq.com>


from datetime import date

class Person:
    
    ancestor = "亚洲人"

    def __init__(self, name, age):
        self.name = name
        self.age = age

    
    @classmethod
    def fromBirthYear(cls, name, year):
        return cls(name, date.today().year - year)

    @staticmethod
    def isAdult(arg):
        return arg >= 18


person1 = Person("张", 25)
person2 = Person.fromBirthYear("旭", 1994)

print("查看type()")
print(person1)
print(person2)

print("调用静态方法")
print(person1.isAdult(34))

print()
print("test 类属性")
print("关于类属性：")
print()

print("从类引用：", Person.ancestor)
print("从实例引用：", person1.ancestor)
print()

person1.ancestor = "火星人"
print("从实例修改后，从类引用：", Person.ancestor)
print("从实例修改后，从实例引用：", person1.ancestor)
print()

Person.ancestor = "木星人"
print("从类修改后从类引用：", Person.ancestor)
print("从类属性修改后，从实例引用：", person1.ancestor)
print()
