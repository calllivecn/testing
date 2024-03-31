#!/usr/bin/env python3
# coding=utf-8
# date 2021-08-13 21:32:56
# author calllivecn <calllivecn@outlook.com>

"""
消除 window.navigator.webdriver 特征
只是把 window.navigator.webdriver =true --> =false 不知道这样有用没

1. 打开浏览器
chrome.exe --remote-debugging-port=9527 --user-data-dir=“F:\selenium\AutomationProfile

2. 编写 Python程序获取控制 浏览器

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9527")
browser = webdriver.Chrome(options=options)

"""

import subprocess
import tempfile
import atexit

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


def chrome_start_debug(port=9527):
    tmp = tempfile.TemporaryDirectory()
    atexit.register(tmp.cleanup)

    chrome = subprocess.run(f"""google-chrome --remote-debugging-port={port} --user-data-dir={tmp.name}""".split())

    return chrome

# bg_chrome = chrome_start_debug()

DRIVER="/home/zx/.venv/selenium/chromedriver"
# chrome = webdriver.Chrome(DRIVER)

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9527")
# chrome = webdriver.Chrome(DRIVER, options=options)
chrome = webdriver.Chrome(DRIVER)

#chrome.get("http://localhost:6789")

def login():
    chrome.get("https://aliyundrive.com")

    # 等待元素加载完成
    def wait_element(element, timeout=10):
        return WebDriverWait(chrome, timeout).until(
            EC.presence_of_element_located(element)
        )

    def wait_elements(element, timeout=10):
        return WebDriverWait(chrome, timeout).until(
            EC.presence_of_all_elements_located(element)
        )


    login_web = chrome.find_element_by_xpath('//*[@id="root"]/div/div/div[1]/div[1]/a/span')

    print(dir(login_web))

    login_web.click()

    # iframe entry
    chrome.switch_to_frame(0)
    chrome.switch_to_frame(chrome.find_element_by_id("alibaba-login-box"))

    # 等 二维码登录
    qr_login = wait_element((By.LINK_TEXT, "扫码登录"))

    print(qr_login)

    qr_login.click()

    #退出iframe页面，返回主页面
    chrome.switch_to.default_content()


login()

rootdir = chrome.find_elements_by_xpath('''//p[contains(@class, "text-primary")]''')
# <p class="text-primary--3DHOJ">考研</p>

print("rootdir:", rootdir)

c = None
for e in rootdir:

    if e.text == "net_disk":
        c = e

    print(e.text)


if c:
    c.click()

net_disk = chrome.find_elements_by_xpath('''//p[contains(@class, "text-primary")]''')

for e in net_disk:
    print(e.text)


try:
    print("运行中...")
    input()
except KeyboardInterrupt:
    chrome.quit()
