#!/usr/bin/env python3
# coding=utf-8
# date 2023-07-09 13:23:29
# author calllivecn <c-all@qq.com>


__all__ =(
    "getlogger",
    "logger",
    "set_handler_fmt",
    "remove_add_handler_fmt",
)

import sys
import logging


LOGNAME="ddns"

stdoutHandler = logging.StreamHandler(stream=sys.stdout)

TIME_FMT = logging.Formatter("%(asctime)s %(levelname)s %(filename)s:%(funcName)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")
FMT = logging.Formatter("%(levelname)s %(filename)s:%(funcName)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")


def getlogger(level=logging.INFO):
    logger = logging.getLogger(LOGNAME)

    stdoutHandler.setFormatter(TIME_FMT)

    # stdoutHandler.setLevel(logging.DEBUG)
    logger.addHandler(stdoutHandler)
    logger.setLevel(level)

    return logger


logger = getlogger()


def set_handler_fmt(handler: logging.Handler, fmt: logging.Formatter):
    handler.setFormatter(fmt)

def remove_add_handler_fmt(fmt: logging.Formatter):
    logger.removeHandler(stdoutHandler)
    stdoutHandler.setFormatter(fmt)
    logger.addHandler(stdoutHandler)

