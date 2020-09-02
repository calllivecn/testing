#!/usr/bin/env python3
#coding=utf-8


from functools import partial

from subprocess import Popen,PIPE

from threading import Thread


def out(fd):
    while True:
        data = fd.readline()
        print(data.decode(), end="")



#p = Popen('bash',stdin=PIPE,stdout=PIPE,shell=True,universal_newlines=True)
p = Popen('bash',stdin=PIPE,stdout=PIPE)

th = Thread(target=out,args=(p.stdout,),daemon=True)
th.start()


"""
while True:
    cmd = input('--> ')
    if cmd == 'quit':
        break
    echo = f"echo zx: {cmd}\n".encode()
    p.stdin.write(echo)
    p.stdin.flush()
"""

for cmd in iter(partial(input, "--> "), "quit"):
    echo = f"echo zx: {cmd}\n".encode()
    p.stdin.write(echo)
    p.stdin.flush()



