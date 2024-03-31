#!/usr/bin/env py3
#coding=utf-8
# date 2018-11-02 15:24:36
# author calllivecn <calllivecn@outlook.com>

import logging
logger = logging.getLogger() #定义对应的程序模块名name，默认是root
#logger.setLevel(logging.DEBUG) #指定最低的日志级别
ch = logging.StreamHandler() #日志输出到屏幕控制台
ch.setLevel(logging.WARNING) #设置日志等级

fh = logging.FileHandler('access.log')#向文件access.log输出日志信息
fh.setLevel(logging.INFO) #设置输出到文件最低日志级别

#create formatter
formatter = logging.Formatter('%(asctime)s %(name)s- %(levelname)s - %(message)s') #定义日志输出格式

#add formatter to ch and fh
ch.setFormatter(formatter) #选择一个格式
fh.setFormatter(formatter)

logger.addHandler(ch) #增加指定的handler
logger.addHandler(fh)
# 'application' code
logger.debug('debug message')
logger.info('info message')
logger.warn('warn message')
logger.error('error message')
logger.critical('critical message')
