#!/usr/bin/env python3
#conding=utf-8


class Person:
    def __init__(self,name,job=None,pay=0):
        self.name=name
        self.job=job
        self.pay=pay

    def __str__(self):
        return "{} {} {}".format(self.name,self.job,self.pay)

if __name__ == '__main__':
		bob=Person('Bob Smith')
		sue=Person('Sue Jones',job='dev',pay=4500)
		print(bob)
		print(sue)

