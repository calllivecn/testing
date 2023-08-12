

import time
import threading




def func(e, name):

    print(f"{name} 等待event事件: {e=}")
    e.wait()
    print(f"{name} event事件通知收到: {e=}")



event = threading.Event()

print(f"{event.is_set()=}")

for i in range(4):

    th = threading.Thread(target=func, args=(event, f"线程{i}"))
    th.start()


time.sleep(1)
event.set()

event.clear()
print(f"{event.is_set()=}")