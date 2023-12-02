#!/usr/bin/env python3
# coding=utf-8
# date 2023-12-03 01:23:42
# author calllivecn <c-all@qq.com>

from setuptools import setup

setup(
    ...
    setup_requires=["cffi>=1.0.0"],
    cffi_modules=["piapprox_build:ffibuilder"], # "filename:global"
    install_requires=["cffi>=1.0.0"],
)
