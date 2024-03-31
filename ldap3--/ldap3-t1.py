#!/usr/bin/env python3
# coding=utf-8
# date 2019-08-21 14:29:39
# author calllivecn <calllivecn@outlook.com>

from ldap3 import Server, Connection, ALL, NTLM

server = Server("ldap://192.168.0.30:389", get_info=ALL)


#con = Connection(server);print(con.bind());exit(0)

con = Connection(server, user="cn=xu.zhang, dc=b-and-qchain, dc=com", password="zx4@1597530.x") #, authentication=NTLM)

#print("con.start_tls() -->", con.start_tls()) 
con.open()
print(con.bind())

print(con.result)

print(server.info)

#print(con.extend.standard.who_am_i())

