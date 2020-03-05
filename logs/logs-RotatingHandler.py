#!/usr/bin/env python3
# coding=utf-8
# date 2020-03-04 14:11:08
# author calllivecn <c-all@qq.com>

import os
from os import path
import logging
from logging import handlers


#from django.conf import settings


__ALL__ = ["logger"]

def __NotExistsMake(logfile):
    dirname, filename = path.split(logfile)
    if not path.exists(dirname):
        os.makedirs(dirname)


BASE_LOG_DIR = path.join("..", "logs") 

info_logfile = path.join(BASE_LOG_DIR, "info.log")
error_logfile = path.join(BASE_LOG_DIR, "error.log")

__NotExistsMake(info_logfile)
__NotExistsMake(info_logfile)

logfmt = logging.Formatter("%(asctime)s.%(msecs)d %(levelname)s %(pathname)s:%(lineno)d %(message)s", datefmt="%H:%M:%S")

infohandle = handlers.TimedRotatingFileHandler(info_logfile, when="midnight", backupCount=7)
errorhandle = handlers.TimedRotatingFileHandler(error_logfile, when="midnight", backupCount=7)


infohandle.setFormatter(logfmt)
errorhandle.setFormatter(logfmt)

infohandle.setLevel(logging.INFO)
errorhandle.setLevel(logging.ERROR)


django_info_handle = handlers.TimedRotatingFileHandler(info_logfile, when="midnight", backupCount=7)
django_info_handle.setLevel(logging.DEBUG)

logger = logging.getLogger("fcAgent")

ENV = os.environ.get("ENV")

if ENV == "DEBUG":
    logger.setLevel(logging.DEBUG)
elif ENV == "INFO":
    logger.setLevel(logging.INFO)
else:
    logger.setLevel(logging.INFO)

logger.addHandler(infohandle)
logger.addHandler(errorhandle)

#logger.info(f"hasHandlers(): {logger.hasHandlers()}") return: False or True

# django 的logger
#django_logger = logging.getLogger()
#django_logger.addHandler(infohandle)
