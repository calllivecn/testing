#!/usr/bin/env python3
#coding=utf-8

import time


import notify2


notify2.init('python3 notify program')

msg = notify2.Notification('text 1','text2')


msg.set_timeout(3000)

msg.show()
time.sleep(3)
msg.update('title', 'lskadjfiajelkfjsalkdjf ijasdlkfj 中文')

msg.show()
