#!/usr/bin/env python3
# coding=utf-8
# date 2019-03-20 16:43:36
# https://github.com/calllivecn


import os
import sys
import shutil
import tarfile


# def read_tar(archivename):
def read_tar():
    with tarfile.open(mode="r|", fileobj=sys.stdin.buffer) as tar:
        shutil.copyfileobj(tar.fileobj, sys.stdout.buffer)


def extract_tar(target):
    with tarfile.open(mode="r|", fileobj=sys.stdin.buffer) as tar:
        tar.extractall(target)
        # tar.list()

if __name__ == "__main__":
    read_tar() # test ok
    # extract_tar(sys.argv[1]) # test ok