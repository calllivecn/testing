# 测试 gzip、bzip2(bz2)、xz(lzma)

- tarfile 可以输出到，like file object。

- lzma.compress(data) ，的输出是兼容xz的。

- gzip.compress(data)，也兼容gzip。

- bz2.compress(data) --> bzip2


### 遇到的问题

- 从标准输入输出读写，sys.stdout.buffer 会随重定向，和管道的不同而不同。

- 需要学习 GUN tar 命令的行为，争取做到一致，或更好。

- path.py:
测试tar的安全打包，解包路径。

- tarfile.__file__ 1474行， self.offset = sefl.fileobj.tell()，
导致tarfile.TarFile(fileobj=sys.stdin.buffer) 从标准输入中读取tar文件时候异常。
它没有考虑到，从标准输入读取tar文件的情况，这应算该是个BUG。
