#!/usr/bin/env python3
# coding=utf-8
# date 2019-07-24 10:11:15
# author calllivecn <c-all@qq.com>


from concurrent import futures
from urllib import request

URLS = ['https://www.baidu.com/',
        'https://www.aliyun.com/',
        'https://www.taobao.com/',
        'https://www.google.com/']

# Retrieve a single page and report the URL and contents
def load_url(url, timeout):

    with request.urlopen(url, timeout=timeout) as conn:
        return conn.read()

# We can use a with statement to ensure threads are cleaned up promptly
with futures.ThreadPoolExecutor(max_workers=5) as executor:

    # Start the load operations and mark each future with its URL
    future_to_url = {executor.submit(load_url, url, 60): url for url in URLS}

    print("future :", future_to_url)

    for future in futures.as_completed(future_to_url):

        url = future_to_url[future]
        try:
            data = future.result()
        except Exception as exc:
            print('{} generated an exception: {}'.format(url, exc))
        else:
            print('{} page is {} bytes'.format(url, len(data)))
