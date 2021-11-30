
import sys
import ssl

import pyzstd

# 这样使用多核
option = {pyzstd.CParameter.compressionLevel : int(sys.argv[1]), # 压缩等级5
            pyzstd.CParameter.nbWorkers : int(sys.argv[2])}        # 使用8线程压缩

# compressed_dat = compress(dat, option)

zstd = pyzstd.ZstdCompressor(option)

SIZE = 100*(1<<20) # 100M

com = 0
size = 0
while size < SIZE:
    data = ssl.RAND_bytes((1<<20))
    c = zstd.compress(data)
    size += len(data)
    com += len(c)

c = zstd.flush()

com += len(c)

print("压缩前大小：", size)
print("压缩后大小：", com)
print("压缩率:", round(com/size, 3))
