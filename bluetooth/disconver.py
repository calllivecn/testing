#!/usr/bin/env python3
# coding=utf-8
# date 2019-12-29 19:49:12
# author calllivecn <c-all@qq.com>

import bluetooth

print("Performing inquiry...")

nearby_devices = bluetooth.discover_devices(duration=8,
                                            lookup_names=True,
                                            flush_cache=True, 
                                            lookup_class=False)

print("Found {} devices".format(len(nearby_devices)))

for addr, name in nearby_devices:
    try:
        print("   {} - {}".format(addr, name))
    except UnicodeEncodeError:
        print("   {} - {}".format(addr, name.encode("utf-8", "replace")))

