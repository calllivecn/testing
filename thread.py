#!/usr/bin/python3
#coding=utf-8

import threading
import time
# 为线程定义一个函数
def print_time( threadName, delay):
   count = 0
   while count < 5:
      time.sleep(delay)
      count += 1
      print ("%s: %s" %(threadName,time.ctime(time.time())))


for v in range(2):
# 创建两个线程
    try:
        t = threading.Thread(target=print_time,args=('thread-{} : '.format(v),5))
    except:
        print ("Error: unable to start thread")



    #t.setDaemon(True)
    t.start()

print('Mian exited')
