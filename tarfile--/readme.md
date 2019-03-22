# 测试 gzip、bzip2(bz2)、xz(lzma)

- tarfile 可以输出到，like file object。

- lzma.compress(data) ，的输出是兼容xz的。

- 也许gzip.compress(data)，也兼容gzip。

- 也许bz2.compress(data) --> gzip


- path.py:
	测试tar的安全打包，解包路径。