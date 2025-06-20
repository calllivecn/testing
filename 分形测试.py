# The Computer Language Benchmarks Game
# https://salsa.debian.org/benchmarksgame-team/benchmarksgame/
#
# contributed by Joerg Baumann

# 输出正方形图的边长大小
# 0. usage: $0 16000 > t.{pbm|ppm}
# 1. convert-img t.pbm t.{webp|jpg}
# 2. 使用图片工具查看

# 添加上 线程池版本（在frethread下测试, ok）

from os import cpu_count
from sys import argv, stdout, stderr
from itertools import islice
from contextlib import closing
from concurrent.futures import (
    ThreadPoolExecutor,
    ProcessPoolExecutor,
)


def pixels(y, n, abs):
    range7 = bytearray(range(7))
    pixel_bits = bytearray(128 >> pos for pos in range(8))
    c1 = 2. / float(n)
    c0 = -1.5 + 1j * y * c1 - 1j
    x = 0
    while True:
        pixel = 0
        c = x * c1 + c0
        for pixel_bit in pixel_bits:
            z = c
            for _ in range7:
                for _ in range7:
                    z = z * z + c
                if abs(z) >= 2.: break
            else:
                pixel += pixel_bit
            c += c1
        yield pixel
        x += 8

def compute_row(p):
    y, n = p

    result = bytearray(islice(pixels(y, n, abs), (n + 7) // 8))
    result[-1] &= 0xff << (8 - n % 8)
    return y, result

def ordered_rows(rows, n):
    order = [None] * n
    i = 0
    j = n
    while i < len(order):
        if j > 0:
            row = next(rows)
            order[row[0]] = row
            j -= 1

        if order[i]:
            yield order[i]
            order[i] = None
            i += 1

def compute_rows(n, f):
    row_jobs = ((y, n) for y in range(n))
    # 添加进程池和线程池。
    #with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
    #with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
    with PoolExecutor(max_workers=cpu_count()) as executor:
        unordered_rows = executor.map(f, row_jobs)
        yield from ordered_rows(unordered_rows, n)

def mandelbrot(n):
    write = stdout.buffer.write

    with closing(compute_rows(n, compute_row)) as rows:
        write("P4\n{0} {0}\n".format(n).encode())
        for row in rows:
            write(row[1])

PoolExecutor = ProcessPoolExecutor

if __name__ == '__main__':
    """
    python $0 1000 > 1000.pbm
    """
    try:
        if argv[2] == "--thread":
            print("使用线程池版本...", file=stderr)
            PoolExecutor = ThreadPoolExecutor
        elif argv[2] == "--process":
            print("使用进程池版本...", file=stderr)
            #PoolExecutor = ProcessPoolExecutor
        else:
            print("使用进程池版本...", file=stderr)

    except IndexError:
        print("使用进程池版本...", file=stderr)

    mandelbrot(int(argv[1]))
