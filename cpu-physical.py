#!/usr/bin/env python3
# coding=utf-8
# date 2022-08-19 00:46:36
# author calllivecn <c-all@qq.com>




def cpu_physical():
    with open("/proc/cpuinfo") as f:
        while (line := f.readline()) != "":
            if "cpu cores" in line:
                count = line.strip("\n")
                break

    _, cores = count.split(":")
    return int(cores.strip())

number = cpu_physical()
print(type(number), number)

