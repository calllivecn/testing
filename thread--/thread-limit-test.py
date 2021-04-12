
import time
import threading


def sleep(s=500):
    time.sleep(s)


def test_thread_count():
    c =0 
    for i in range(1, 10000000 +1):
    
        if c > 1000:
            print("当前线程数:", i)
            c = 0
        else:
            c +=1
    
        th = threading.Thread(target=sleep, daemon=True)
        th.start()


def add():
    c = 0
    while True:
        c += 1

        if c >= 100000000:
            print("我还在:", threading.current_thread())
            c = 0

def start_thread(count):
    for _ in range(count):
        th = threading.Thread(target=add, daemon=True)
        th.start()

def compute_count():
    while True:
        num = threading.active_count()
        s = input(f"当前线程数：{num} 添加线程数：")

        if s == "quit":
            break
        elif s == "":
            print("退出请输入quit")
            continue

        th = int(s)

        start_thread(th)


compute_count()
