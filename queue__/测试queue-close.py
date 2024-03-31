#!/usr/bin/env python3
#coding=utf-8
# date 2023-05-07 01:52:20
# author calllivecn <calllivecn@outlook.com>


import time
import queue
import threading
from multiprocessing import (
    Queue,
    Process,
)




def get_queue(q):
    while True:
        task = q.get()
        if task is None:
            print("拿到了一个None")
            break

        print(task)
    print("结束处理进程")


# q = queue.Queue(5)
q = Queue(100)
# th = threading.Thread(target=get_queue, args=(q,), daemon=True)
th = Process(target=get_queue, args=(q,))
th.start()

for i in range(10):
    q.put(i)

# th.join()
time.sleep(2)
q.close()
print("主进程完成")

"""
q.close() 不会反应到对端。 还是需要 q.put(None)
"""