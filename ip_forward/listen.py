#!/usr/bin/env python3
#coding=utf-8

import socket,argparse,re

parse=argparse.ArgumentParser()

parse.add_argument('-l','--local',action='store',required=True,help='local port')

parse.add_argument('-r','--remote',action='store',required=True)

args=parse.parse_args()


print(args)

sock=args.local.split(':')


print('ip : {} port : {}'.format(sock[0],sock[1]))


listen=socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)

listen.bind((sock[0],sock[1]))

listen.listen(128)

while 1:
	client,address = listen.accept()
	date1 = client.recv()



