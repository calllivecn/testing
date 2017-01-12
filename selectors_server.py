#!/usr/bin/env python3
#coding=utf-8


import socket
import selectors

def handler(conn,select_key):
	message = conn.recv(1024)
	conn.send(message)
	#select_key
	#conn.close()

def server(host, port):
	listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
	listener.bind((host, port))
	listener.listen(10)

	selector = selectors.DefaultSelector()
	selector.register(listener, selectors.EVENT_READ)

	while True:
		event_list = selector.select()
		for key, events in event_list:
			conn = key.fileobj
			if conn == listener:
				new_conn, addr = conn.accept()
				selector.register(new_conn, selectors.EVENT_READ)
			else:
				handler(conn,key)



if __name__ == '__main__':
	server('0.0.0.0',6789)


