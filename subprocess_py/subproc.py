#!/usr/bin/env python3
#coding=utf-8



from subprocess import Popen,PIPE

from threading import Thread


def out(fd):
    while True:
        data = fd.read()
        print(data.decode())



p = Popen('bash',stdin=PIPE,stdout=PIPE,shell=True,universal_newlines=True)

th = Thread(target=out,args=(p.stdout,),daemon=True)
th.start()

while True:
    cmd = input('--> ')
    if cmd == 'quit':
        break
    p.stdin.write('echo zx \n')
    p.stdin.flush()



