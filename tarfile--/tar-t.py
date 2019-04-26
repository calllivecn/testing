#!/usr/bin/env python3
# coding=utf-8
# date 2019-03-20 16:43:36
# https://github.com/calllivecn



import sys

# tarfile 依赖
#import tarzx
import tarfile


stdin = sys.stdin.buffer
stdout = sys.stdout.buffer

def tell_none():
    print("call tell_none function")
    return 0

setattr(stdin, "tell", tell_none)


stdin.tell()


if stdin is sys.stdin.buffer:
    print("is stdin")
else:
    print("is not stdin")

#exit(0)

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

tar = tarfile.TarFile(mode="w", fileobj=stdin)

#tar = tarzx.TarFile(mode="r", fileobj=stdin)

tar.extractall()

tar.close()

#fp.close()

