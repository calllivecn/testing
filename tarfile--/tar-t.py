#!/usr/bin/env python3
# coding=utf-8
# date 2019-03-20 16:43:36
# https://github.com/calllivecn



import sys
import tarfile


stdin = sys.stdin.buffer
stdout = sys.stdout.buffer

#fp = open("my.tar", "wb")

#tar = tarfile.TarFile(mode="w", fileobj=sys.stdout.buffer)

tar = tarfile.TarFile(mode="r", fileobj=stdin)

tar.extractall(path=stdout)

tar.close()

#fp.close()
