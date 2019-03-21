# tar 
- tarfile 可以输出到，like file object。
- lzma.compress(data) ，的输出是兼容xz的。
- 也许gzip.compress(data)，也兼容gzip。
- 也许bz2.compress(data) --> gzip




### 遇到的问题
- 从标准输入输出读写，sys.stdout.buffer 会随重定向，和管道的不同而不同。
- 需要学习 GUN tar 命令的行为，争取做到一致，或更好。
