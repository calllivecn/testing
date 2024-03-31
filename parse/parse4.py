#!/usr/bin/env python3
#coding=utf-8
# date 2018-03-08 21:54:04
# author calllivecn <calllivecn@outlook.com>


import argparse


def _p(args):
    #print(args)
    try:
        int(args)
    except ValueError as e:
        raise argparse.ArgumentTypeError(e)

parse = argparse.ArgumentParser(prog='anynmouse',
                                #formatter_class=argparse.RawDescriptionHelpFormatter,
                                #formatter_class=argparse.RawTextHelpFormatter,
                                #formatter_class=argparse.ArgumentDefaultsHelpFormatter,
description='''Desctioption>>>>>
这什么啊靠～～～
你以为你谁啊，SB''',usage='Using: %(prog)s <none>',
add_help=True)

parse.add_argument('n',type=_p,help='一个数')

parse.add_argument('count',nargs='*',help='anywhere')

parse.add_argument('-t','--text',action='store_true',help='这是一个t选项')
parse.add_argument('-f','--file',nargs='*',dest='file',action='store',help='这是一个f选项')
#args = parse.parse_args(['12','count'])
#parse.print_help()

args = parse.parse_args('a 2 3 count1 count2 count3 -t -f file2 file2'.split())
print(args)
