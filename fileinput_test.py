#!/usr/bin/env python3
#coding=utf-8


import fileinput as ft
from argparse import ArgumentParser

parse = ArgumentParser()

parse.add_argument('fs',action='append',default='-',help='[files ...]')

args = parse.parse_args()

print(args)

if args.fs != '-':
    input_source = args.fs
else:
    input_source = '-'


with ft.input(files=input_source) as f:
    for data in f:
        print(f.lineno(),data,end='')

        

