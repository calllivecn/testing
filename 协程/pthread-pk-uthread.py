#!/usr/bin/env python3
#coding=utf-8



import asyncio
from threading import Thread,Lock
import time

queue = [ 0 for x in range(10000) ]

queue2 = queue.copy()

def uth(sock=1):
    while 1:
        try:
            yield queue.pop()
        except StopIteration :
            return


start = time.time()
u1=uth()
u1.send(None)
for i in range(100):
    d = u1.send('n')
    print('任务',d)
u1.close()
end = time.time()

print('协程用时:',end-start,'秒')




###############################################33

lock = Lock()

#lock.acquire()

Q=''

def pth():
    with lock:
        Q=queue2.pop()
        #time.sleep(0.01)


pth1 = Thread(target=pth)

start = time.time()
pth1.start()
while 1:
    with lock:
        print('线程的Q',Q)
        #time.sleep(0.01)

end = time.time()


print('线程用时:',end-start,'秒')
