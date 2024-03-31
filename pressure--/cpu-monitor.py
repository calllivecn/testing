#!/usr/bin/env python3
# coding=utf-8
# date 2023-12-23 15:10:55
# author calllivecn <calllivecn@outlook.com>

import time

def read_cpu_pressure():
    try:
        with open("/proc/pressure/cpu", "r") as file:
            data = file.read()
            return data
    except FileNotFoundError:
        return "Error: /proc/pressure/cpu not found."

def main():
    while True:
        cpu_pressure_data = read_cpu_pressure()
        print(cpu_pressure_data)
        time.sleep(1)  # 每秒读取一次

if __name__ == "__main__":
    main()


