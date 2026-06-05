import cffi

ffi = cffi.FFI()

# 读取上限1M大小

BUF = 1<<20

# 1. 定义 C 接口 (给 Python 调用的函数)
with open("_pipewire.h") as f:
    ffi.cdef(f.read(BUF))

# 2. 编写 C 源码 (核心底层逻辑)
with open("_pipewire.c") as f:
    c_source = f.read(BUF)

# 3. 编译 C 代码
if __name__ == "__main__":
    ffi.set_source("_pipewire_cffi", c_source, libraries=['pipewire-0.3'], include_dirs=['/usr/include/pipewire-0.3', '/usr/include/spa-0.2'])
    ffi.compile(verbose=True)
    print("✅ CFFI 编译成功！")
