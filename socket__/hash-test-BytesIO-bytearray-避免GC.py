#!/usr/bin/env python3
# coding=utf-8
# date 2021-11-10 16:28:49
# author calllivecn <c-all@qq.com>



import io
import sys
import time
import hashlib



# 1. 使用 hashlib 测试， 性能上看不出来差别。
# 2. 只测试read(), readinto() 的区别。

# 3. 调小 buf 可能会看到性能差别？也没看到，还是 GC 回收会快一点点...
# 4。 BytesIO() 使用姿势不对？


buf_size = 4096

def hash_buf():
    buf = io.BytesIO(bytes(buf_size)).getbuffer()

    #sha256 = hashlib.sha256()

    start = time.time()
    with open(sys.argv[1], "rb") as f, open("/dev/null", "wb") as null:
        while (data_len := f.readinto(buf)) != 0:
            #sha256.update(buf[:data_len])
            null.write(buf[:data_len])# .getvalue())

        #print("sha256:", sha256.hexdigest())
    end = time.time()

    print("耗时：", end - start, "/秒")


def hash_not_buf():

    #sha256 = hashlib.sha256()

    start = time.time()
    with open(sys.argv[1], "rb") as f, open("/dev/null", "wb") as null:
        while (data := f.read(buf_size)) != b"":
            #sha256.update(data)
            null.write(data)

        #print("sha256:", sha256.hexdigest())
    end = time.time()

    print("耗时：", end - start, "/秒")


#hash_buf()
hash_not_buf()

# 分析
#from line_profiler import LineProfiler
#lp = LineProfiler()
#lp_wrapper = lp(hash_buf)
#lp_wrapper = lp.add_function(hash_buf)
#lp.print_stats()
