#!/usr/bin/env python3
# coding=utf-8
# date 2019-08-21 14:29:39
# author calllivecn <c-all@qq.com>

from ldap3 import Server, Connection, ALL, NTLM

server = Server("ldap://192.168.0.30:389", get_info=ALL)


#con = Connection(server);print(con.bind());exit(0)

con = Connection(server, auto_bind=True, user="b-and-qchina.com\\admin", password="1234qwer", authentication=NTLM)

#print("con.start_tls() -->", con.start_tls()) 
#print(con.bind())

print(server.info)

print(con.extend.standard.who_am_i())

