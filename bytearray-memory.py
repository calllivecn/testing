
import time
import statistics

N = 2000000       # 重复次数（你可以调大）
SIZE = 1 << 16  # 64KB

ba = bytearray(SIZE)
mv = memoryview(ba)

def bench_bytearray_slice():
    a = ba
    for _ in range(N):
        x = a[100:300]   # 会复制 200 bytes
    return x[0]  # 防止优化

def bench_memoryview_slice():
    m = mv
    for _ in range(N):
        x = m[100:300]   # 不复制，创建view
    return x[0]

def bench_bytearray_write():
    a = ba
    for _ in range(N):
        a[100] = 1
    return a[100]

def bench_memoryview_write():
    m = mv
    for _ in range(N):
        m[100] = 1
    return m[100]


def timeit(fn):
    t = []
    for _ in range(5):
        s = time.perf_counter()
        fn()
        t.append(time.perf_counter() - s)
    return statistics.mean(t)


print("bytearray slice :", timeit(bench_bytearray_slice))
print("memoryview slice:", timeit(bench_memoryview_slice))
print("bytearray write :", timeit(bench_bytearray_write))
print("memoryview write:", timeit(bench_memoryview_write))

