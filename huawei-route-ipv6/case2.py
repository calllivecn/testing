#!/usr/bin/env python3
# coding=utf-8
# date 2023-02-11 06:02:29
# author calllivecn <c-all@qq.com>


import os
import time
import traceback
import subprocess
import tempfile
import atexit

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys





def chrome_start_debug(port=9527):
    tmp = tempfile.TemporaryDirectory()
    atexit.register(tmp.cleanup)

    chrome = subprocess.run(f"""google-chrome --remote-debugging-port={port} --user-data-dir={tmp.name}""".split())

    return chrome

# bg_chrome = chrome_start_debug()


# ROUTE_ADDR="http://192.168.8.1/"
ROUTE_ADDR = os.environ.get("ROUTE_ADDR")
PASSWORD = os.environ.get("HUAWEI_ROUTE_PW")
DRIVER = os.environ.get("CHROME_DRVIER")

assert ROUTE_ADDR != None
assert PASSWORD != None
assert DRIVER != None

# chrome = webdriver.Chrome(DRIVER)

# windows 才需要 这样？ 不是， 是需要保留记录才需要。
# options = Options()
# options.add_experimental_option("debuggerAddress", "127.0.0.1:9527")
# chrome = webdriver.Chrome(DRIVER, options=options)

# chrome = webdriver.Chrome(DRIVER)

#chrome.get("http://localhost:6789")


# huawei 操作

class HuaweiRoute:

    def __init__(self):
        service = Service(DRIVER)
        options = Options()
        options.add_argument("--headless")
        self.chrome = webdriver.Chrome(options=options, service=service)


    def close(self):
        self.chrome.close()


    def login(self):
        self.chrome.get(ROUTE_ADDR)

        self.wait_element_click(element=(By.ID, "userpassword_ctrl"))

        login_ctrl = self.chrome.find_element(By.ID, "userpassword_ctrl")
        login_ctrl.send_keys(PASSWORD +  Keys.RETURN)
        # time.sleep(1)

        login_btn = self.chrome.find_element(By.ID, "loginbtn")
        login_btn.click()


    def get_wan_ipv6PD(self):
        # 路由器信息页面
        self.wait_element_click(element=(By.ID, "more"))

        self.wait_element_click(element=(By.ID, "deviceinfoparent_menuId"))

        self.wait_element((By.ID, "deviceinfo_view_data_edit_deviceinfo_ipv6_ipv6prefixlist_label"))
        ipv6pd = self.chrome.find_element(By.ID, "deviceinfo_view_data_edit_deviceinfo_ipv6_ipv6prefixlist_label")
        self.ipv6pd = ipv6pd.text

        self.ipv6_pd, self.ipv6_pd_length = self.ipv6pd.split("/")


    def set_ipv6PD(self):

        self.wait_element_click(element=(By.ID, "netsettingsparent_menuId"))
        time.sleep(1)

        self.wait_element_click(element=(By.ID, "ipv6_menuId"))
        time.sleep(1)

        self.wait_element(element=(By.ID, "ipv6_SLAAC_prefix_ctrl"))
        pd = self.chrome.find_element(By.ID, "ipv6_SLAAC_prefix_ctrl")
        pd.click()
        pd.clear()
        pd.send_keys(self.ipv6_pd)

        pd_length = self.chrome.find_element(By.ID, "ipv6_SLAAC_prefixlength_ctrl")
        pd_length.click()
        pd_length.clear()
        pd_length.send_keys(self.ipv6_pd_length)

        submit_btn = self.chrome.find_element(By.ID, "ipv6_submit_btn")
        submit_btn.click()


    # 等待元素加载完成
    def wait_element(self, element, timeout=10):
        wait = WebDriverWait(self.chrome, timeout)
        wait.until(lambda x: x.find_element(*element))

    def wait_element_click(self, element, timeout=10):
        self.wait_element(element)
        click = self.chrome.find_element(*element)
        click.click()


def start(route):

    route.login()

    cur = []

    while True:
        print("运行中...")
        route.get_wan_ipv6PD()
        print(f"ipv6 PD: {route.ipv6pd}")

        if cur == [route.ipv6_pd, route.ipv6_pd_length]:
            print("ipv6 前缀没有变，sleep(120)")
        else:
            route.set_ipv6PD()
            cur = [route.ipv6_pd, route.ipv6_pd_length]
            print(f"ipv6 前缀变为: {cur}")

        time.sleep(120)
        route.chrome.refresh()


def main():
    route = HuaweiRoute()
    while True:
        try:
            start(route)
        except WebDriverException as e:
            traceback.print_exc(e)
            print("WebDriver 有异常重启服务。")

if __name__ == "__main__":
    main()
