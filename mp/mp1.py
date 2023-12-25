#!/usr/bin/env python3
# coding=utf-8
# date 2019-03-19 15:18:37
# https://github.com/calllivecn


import os
import time
import random

import multiprocessing as mp

def f(x):
    t = random.randint(1, 4)
    #time.sleep(t)
    c=0

    if x == 80:
        t *= 500000000
    else:
        t *= 50000000

    while c < t:
        c+=1

    return x, t


def items(num):
    c = 0
    while c < num:
        print(f"生成: {c}")
        yield c
        c += 1


# 结果是有序的, 这样是等待100个任务都完成了，才一起把100任务都返回的。
def test1():
    pool = mp.Pool()
    for data in pool.map(f, items(40)):
        print(data)

    pool.close()





# 前面的方式有个问题，就是如果有一个任务执行的时间要比其他99个任务执行的时间长很多，它也会等待它后，才一起返回100任务结果。
# 这期间，就只会有 个 cpu 在工作了。
# 使用batch
def test2():

    pool = mp.Pool()

    #cpucount = pool.pool_size
    batch_size = os.cpu_count()

    tasks = []
    tasks_num = 40
    task = 0
    task_batch = 0
    while task < tasks_num:

        tasks.append(task)
        task += 1

        if task % batch_size == 0:
            print("="*40)
            for data in pool.map(f, tasks):
                print(data)


            task_batch = 0
            tasks = []

    # 处理少于一个batch的。
    print("="*40)
    for data in pool.map(f, tasks):
        print(data)


    pool.close()



if __name__ == "__main__":
    test1()
    # test2()
