# 测试 gzip、bzip2(bz2)、xz(lzma), zstd(pyzstd)

- tarfile 可以输出到，like file object。

- lzma.compress(data) ，的输出是兼容xz的。

- gzip.compress(data)，也兼容gzip。

- bz2.compress(data) --> bzip2


### 遇到的问题

- ~~从标准输入输出读写，sys.stdout.buffer 会随重定向，和管道的不同而不同。~~ tar-t.py解决了

- ~~tar-t.py 测试tar的安全打包，解包路径。~~ 测试ok


- 需要学习 GUN tar 命令的行为，争取做到一致，或更好。

