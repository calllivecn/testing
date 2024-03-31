#!/usr/bin/env python3
# coding=utf-8
# date 2023-05-08 03:09:51
# author calllivecn <calllivecn@outlook.com>

"""
定义一个可以把多个函数，使用pipeline串连起来的,管理方式！
"""

import os
import heapq
import queue
import threading
import multiprocessing as mp


class PipeLine:

    def __init__(self):
        pass



# 后处理在单核性能不行， 使用 多进程处理。
class StreamingPorcessPool:

    EOF = "EOF"

    def __init__(self, func=None, pool=4, queue_size=16):
        """
        func: 必须是 func(task)
        """

        self._done = False
        self._done_event = threading.Event()
        self._proc_done = False

        self.func = func

        self.pool = pool

        self.pools = []

        self.queue_size = queue_size
        # self.in_queue = mp.JoinableQueue(pool)
        # self.out_queue = mp.JoinableQueue(pool)
        self.in_queue = mp.Queue(pool)
        self.out_queue = mp.Queue(pool)

        self.in_seq = 0
        self.out_seq = 0

        self.stash = []

        if self.func is not None:
            self.submit_func(self.func)


    def submit_func(self, func):
        if self.func is not None:
            raise ValueError("函数已定义")
        self.func = func

        for i in range(self.pool):
            p = mp.Process(target=self.__proc, name="后处理池", daemon=True)
            p.start()
            self.pools.append(p)
        
        th = threading.Thread(target=self.__manager, daemon=True)
        th.start()

    def __manager(self):
        """
        join 队列，等所有任务都完成。
        """
        # with self._done_lock:
        self._done_event.wait()
        for p in self.pools:
            p.join()

        self.out_queue.put(self.EOF)
        self._proc_done = True

    def push(self, *args, **kwargs):
        if self._done:
            raise ValueError("当前pipeline入口已关闭")

        frame = (self.in_seq, (args, kwargs))
        # print(f"push(): {self.in_seq=} {frame=}")

        self.in_queue.put(frame)
        self.in_seq += 1


    def pull(self):
        """
        return: object(EOF), [result] or [result1, result2, ...]
        """
        # 退出条件有  not self.is_done(), self.out_empty(), len(self.stash) == 0

        while True:

            if self.is_done() and self.out_queue.empty():
                return self.EOF

            seq_frame = self.out_queue.get()
            # print(f"pull() 拿到 {seq_frame=}")

            if seq_frame == self.EOF:
                # 这时说明这是最后一次 pull() 了, 需要清空self.stash
                # print("pull() 已经拿到 EOF了")

                while len(self.stash):
                    self.out_queue.put(heapq.heappop(self.stash))

                self._proc_done = True
            else:
                # print(f"debug: {seq_frame=}")
                result = self.next_result(seq_frame)
                # print(f"debug: {seq_frame=} {result=}")
                if len(result) == 0:
                    continue
                return result

    def next_result(self, seq_frame):
        """
        用来保证，任务是有序且连续的进来，和出去的。 self.stash 暂存区
        seq_frames: (seq, task)
        """

        heapq.heappush(self.stash, seq_frame)

        frames = []
        while len(self.stash) > 0 and self.out_seq == self.stash[0][0]:
            _, frame = heapq.heappop(self.stash)
            frames.append(frame)
            self.out_seq += 1

        # [self.pull_queue.put(frame) for frame in frames]
        return frames


    def __proc(self):
        # pid = mp.current_process().pid
        while (seq_frame := self.in_queue.get()) != self.EOF:
            # print(f"Porcess PID:{pid} task: {seq_frame}")
            seq, task = seq_frame
            args, kwargs = task
            result = self.func(*args, **kwargs)

            self.out_queue.put((seq, result))
        

        # 在put 回去， 让其他进程退出。
        self.in_queue.put(self.EOF)


    def done(self):
        self.in_queue.put(self.EOF)
        self._done = True
        # self._done_lock.release()
        self._done_event.set()
    
    def is_done(self):
        _is_done = self._done and self._proc_done
        # print(f"{_is_done=}")
        return _is_done



import time
import random

def task_oreder(task):
    # time.sleep(random.random())
    return task


def pull_task(M_P, count=20):
    for i in range(count):
        M_P.push((f"args {i}", "kwargs"))
        # print("推送的任务：", i)

    for i in range(count):
        M_P.push((f"args {i}", "kwargs"))
        # print("推送的任务：", i)
    
    M_P.done()


spp = StreamingPorcessPool()

th = threading.Thread(target=pull_task, args=(spp,10))
th.start()

spp.submit_func(task_oreder)

results = []
while (result := spp.pull()) != spp.EOF:
    print(f"收到的: {result}")
    results.append(result)



print(f"这是收到的: {results=}")


