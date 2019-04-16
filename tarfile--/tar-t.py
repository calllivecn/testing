#!/usr/bin/env python3
# coding=utf-8
# date 2019-03-20 16:43:36
# https://github.com/calllivecn



import sys

# tarfile 依赖
import tarzx


stdin = sys.stdin.buffer
stdout = sys.stdout.buffer

#def tell():
#    return 0
#
#if hasattr(stdin, "tell"):
#    print("stdin 有tell()")
#else:
#    print("stdin 没有tell()")
#    setattr(stdin, "tell", tell)
#
#sys.exit(0)

#fp = open("my.tar", "wb")

#tar = tarfile.TarFile(mode="w", fileobj=sys.stdout.buffer)

tar = tarzx.TarFile(mode="r", fileobj=stdin)

tar.extractall()

tar.close()

#fp.close()

