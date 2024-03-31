#!/usr/bin/env python3
# coding=utf-8
# date 2023-08-05 08:59:34
# author calllivecn <calllivecn@outlook.com>

import os

from miio.cloud import CloudInterface

username = os.environ["MIROBO_USERNAME"]
password = os.environ["MIROBO_PASSWORD"]

ci = CloudInterface(username=username, password=password)

devs = ci.get_devices()

for did, dev in devs.items():
    print(f"{did=}")
    print(f"{dev=}")


