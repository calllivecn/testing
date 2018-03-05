#!/usr/bin/env python3
#coding=utf-8
# date 2018-03-06 03:12:57
# author calllivecn <c-all@qq.com>


from urllib.request import urlopen


class urlmod:
    def __init__(self,url='http://localhost:8000'):
        self._url = url

    def getUrlMod(self,modname):
        content = urlopen(self._url + '/' + modname + '.py')
        return content.read().decode()




if __name__ == "__main__":
    u = urlmod('https://raw.githubusercontent.com/calllivecn/text2speech/master')

    code = u.getUrlMod('text2speech')
    print(code)
