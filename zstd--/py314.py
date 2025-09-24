
import sys
import ssl

from compression import zstd
#CompressionParameter

print(f"zstd 版本信息：{zstd.zstd_version_info=}")
print(f"支持压缩等级：{zstd.CompressionParameter.compression_level.bounds()=}")

# 当前还不支持各线程？？？2025-07-15 
# update (py3.14t.rc3) 支持多线程了。
options = {
        zstd.CompressionParameter.compression_level : int(sys.argv[1]),
        zstd.CompressionParameter.nb_workers : int(sys.argv[2]), # 使用8线程压缩
        }

#comp = zstd.ZstdCompressor(level=int(sys.argv[1]), options=options)
comp = zstd.ZstdCompressor(options=options)

SIZE = 8000*(1<<20) # 8000M

com = 0
size = 0
while size < SIZE:
    data = ssl.RAND_bytes((1<<20))
    c = comp.compress(data)
    size += len(data)
    com += len(c)

c = comp.flush()

com += len(c)

print("压缩前大小：", size)
print("压缩后大小：", com)
print("压缩率:", round(com/size, 3))

