#!/usr/bin/env python3
# coding=utf-8

import socket as st
import time

BIND = ('0.0.0.0', 6789)
try:

    S = st.socket(st.AF_INET, st.SOCK_DGRAM)

    S.bind(BIND)

except:
    print('初始化异常！')
    raise

try:
    while True:

        # S.settimeout(5)
        data, address = S.recvfrom(32)
        #data2 = data.decode('utf-8')
        # if data2 == 'quit':
        #	break
        # if data2.split(' ').[0] == 'address :':
        # data2.
        data = 'recv: ' + data.decode('utf-8')
        print('address : ', address, data)
        S.sendto('OK!'.encode('utf-8'), address)
        print('sendto : OK done.')

except KeyboardInterrupt:
    pass

finally:
    S.close()
