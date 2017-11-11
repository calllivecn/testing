#!/usr/bin/env python3
#coding=utf-8


import socket
import selectors

def handler(conn,event,sel):
    message = conn.recv(4096)
    conn.send(message)
    sel.unregister(conn)
    conn.close()
    #print(message)

def handler_accept(conn,event,sel):
    sock , addr = conn.accept()
    sel.register(sock,selectors.EVENT_READ,handler)

def server(host, port):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    #listener.setblocking(False)
    listener.bind((host, port))
    listener.listen(128)

    selector = selectors.DefaultSelector()
    selector.register(listener, selectors.EVENT_READ,handler_accept)
    fdmap={}
    while True:
        event_list = selector.select()
        for key, event in event_list:
            conn = key.fileobj
            func = key.data
            func(conn,event,selector)

            '''
            if conn == listener:
                new_conn, addr = conn.accept()
                selector.register(new_conn, selectors.EVENT_READ)
            else:
                handler(conn)
                selector.unregister(conn)
                #conn.shutdown(socket.SHUT_RDWR)
                conn.close()
            '''

    selectot.close()

if __name__ == '__main__':
    try:
        server('0.0.0.0',6789)
    except KeyboardInterrupt:
        pass


