
# 测试CPU计算速度
import os
import time
import numpy as np
from multiprocessing import Process

ee = int(1e7)
np.random.seed(6)
A = np.random.random(size=[ee, ])
B = np.random.random(size=[ee, ])

start = time.perf_counter()
c1 = np.dot(A, B)
end = time.perf_counter()

print('numpy C :', c1)
print('numpy time : /s', end-start)

def th(count):
    for _ in range(count):
        start = time.perf_counter()
        C = 0
        for i in range(ee):
            C = C + A[i]*B[i]
        end = time.perf_counter()
        print('CPU C :', C)
        print('CPU TIME : /s', end-start)



for _ in range(os.cpu_count()):
    t = Process(target=th, args=(4,))
    t.start()

