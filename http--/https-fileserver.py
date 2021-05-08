#!/usr/bin/env python3
# coding=utf-8
# date 2020-04-18 20:45:13
# author calllivecn <c-all@qq.com>


# taken from https://gist.github.com/dergachev/7028596  
#   
# generate server.xml with the following command:  
#   openssl req -new -x509 -keyout https_svr_key.pem -out https_svr_key.pem -days 3650 -nodes  
# 


import os  
import ssl  
import socket  
from http.server import (
        HTTPServer,
        SimpleHTTPRequestHandler
        )


script_home = os.path.dirname(os.path.abspath(__file__))  

#ip = [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]  
ip = "0.0.0.0"
port = 6789

def main():
    print("simple https server, address: [{}:{}], document root:{}".format(ip, port, script_home))  

    httpd = HTTPServer((ip, port), SimpleHTTPRequestHandler)  

    # 这是旧版的方法，且不支持SNI。
    #httpd.socket = ssl.wrap_socket(httpd.socket, certfile="server.crt", keyfile="server.key", ca_certs="root-ca.crt", server_side=True)

    # 下面是3.7以后的新方法
    sslcontext = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    sslcontext.options |= ssl.OP_NO_TLSv1
    sslcontext.options |= ssl.OP_NO_TLSv1_1

    sslcontext.load_cert_chain(certfile="server.crt", keyfile="server.key")
    httpd.socket = sslcontext.wrap_socket(httpd.socket, server_side=True)

    httpd.serve_forever()

if __name__ == '__main__':  
    #os.chdir(script_home)
    main()

