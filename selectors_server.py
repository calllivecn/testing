#!/usr/bin/env python3
#coding=utf-8


import socket
import selectors

def handler(conn):
	message = conn.recv(1024)
	conn.send(message)
	print(message)

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
				handler(conn)
				selector.unregister(conn)
				#conn.shutdown(socket.SHUT_RDWR)
				conn.close()

	selectot.close()

if __name__ == '__main__':
	try:
		server('0.0.0.0',6789)
	except KeyboardInterrupt:
		pass


