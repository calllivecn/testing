#!/usr/bin/env python3
# coding=utf-8
# date 2023-07-09 13:22:34
# author calllivecn <calllivecn@outlook.com>


import sys
import logging


import log1



logger = logging.getLogger(log1.LOGNAME)

logger.setLevel(logging.DEBUG)


logger.info(f"INFO --> 在log2 中 通过 logname 拿到 log1 中的 logger.")


logger.debug(f"DEBUG --> 在log2 中 通过 logname 拿到 log1 中的 logger.")

def f():
    logger.info(f"INFO --> 在log2 中 通过 logname 拿到 log1 中的 logger.")

print(f"{logger.name=}")


def main():

    if len(sys.argv) == 2 and sys.argv[1] == "--not-logtime":
        log1.set_handler_fmt(log1.stdoutHandler, log1.FMT)
    else:
        f()

    logger.info("重新设置格式后的输出。")

if __name__ == "__main__":
    main()
