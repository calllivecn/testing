#!/usr/bin/env python3
# coding=utf-8
# date 2023-02-11 06:02:29
# author calllivecn <c-all@qq.com>


import os
import sys
import time
import traceback
import ipaddress
import argparse
import atexit

import subprocess
import tempfile

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys

from selenium.common.exceptions import (
    WebDriverException,
    NoSuchWindowException
)


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

    def __init__(self, args):
        
        service = Service(DRIVER)
        options = Options()

        if args.headless:
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

        # 找错了。
        # ipv6pd = self.wait_element((By.ID, "deviceinfo_view_data_edit_deviceinfo_ipv6_ipv6prefixlist_label"))

        ipv6 = self.wait_element((By.ID, "deviceinfo_view_data_edit_deviceinfo_ipv6_IPAddress_label"))
        ipv6 = ipaddress.ip_network(ipv6.text, False)
        self.ipv6pd = ipv6.with_prefixlen
        print(f"当前ipv6的PD: {self.ipv6pd}")

        self.ipv6_pd, self.ipv6_pd_length = str(ipv6.network_address), str(ipv6.prefixlen)


    def set_ipv6PD(self):

        self.wait_element_click(element=(By.ID, "netsettingsparent_menuId"))
        time.sleep(1)

        self.wait_element_click(element=(By.ID, "ipv6_menuId"))
        time.sleep(1)

        pd = self.wait_element(element=(By.ID, "ipv6_SLAAC_prefix_ctrl"))

        cur_pd = pd.get_attribute("value")
        print(f"当前设置的PD: {cur_pd}")

        pd_length = self.chrome.find_element(By.ID, "ipv6_SLAAC_prefixlength_ctrl")

        cur_pd_length = pd_length.get_attribute("value")

        if (cur_pd, cur_pd_length) == (self.ipv6_pd, self.ipv6_pd_length):
            print("ipv6 前缀没有变")
            return
        else:
            print(f"ipv6 前缀变为: {self.ipv6pd}")

        pd.click()
        pd.clear()
        pd.send_keys(self.ipv6_pd)

        pd_length.click()
        pd_length.clear()
        pd_length.send_keys(self.ipv6_pd_length)

        submit_btn = self.chrome.find_element(By.ID, "ipv6_submit_btn")
        submit_btn.click()


    # 等待元素加载完成
    def wait_element(self, element, timeout=10):
        wait = WebDriverWait(self.chrome, timeout)
        return wait.until(lambda x: x.find_element(*element))

    def wait_element_click(self, element, timeout=10):
        click = self.wait_element(element)
        click.click()


def start(route, interval=180):

    route.login()

    while True:
        print("运行中...")
        route.get_wan_ipv6PD()
        route.set_ipv6PD()
        print(f"sleep({interval})")
        time.sleep(interval)
        route.chrome.refresh()


def main():

    parse = argparse.ArgumentParser(usage="%(prog)s [option]",
        description="给二级路由器，设置ipv6PD的工具。")
    
    parse.add_argument("--headless", action="store_true", help="使用无头模式")

    parse.add_argument("--interval", action="store", type=int, default=180, help="检测间隔时间单位：s (180)")

    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)

    args = parse.parse_args()

    if args.parse:
        print(args)
        sys.exit(0)


    while True:

        route = HuaweiRoute(args)

        try:
            start(route, args.interval)

        # except NoSuchWindowException as e:
            # traceback.print_exc()
            # time.sleep(5)

        except WebDriverException as e:
            traceback.print_exc()
            print("WebDriver 有异常重启服务。")
            route.chrome.quit()
            time.sleep(5)


if __name__ == "__main__":
    main()
