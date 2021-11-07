
import ssl

import pyzstd

# 这样使用多核
option = {pyzstd.CParameter.compressionLevel : 5, # 压缩等级5
            pyzstd.CParameter.nbWorkers : 8}        # 使用8线程压缩

# compressed_dat = compress(dat, option)

zstd = pyzstd.ZstdCompressor(option)

while True:
    data = ssl.RAND_bytes((1<<20))
    zstd.compress(data)
