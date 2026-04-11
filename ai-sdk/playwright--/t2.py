
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        # 通过 CDP 协议连接到指定的本地或远程端口
        browser = p.chromium.connect_over_cdp("http://localhost:9222")

        # 指定系统中 Chrome 的绝对路径 Linux 常规路径: /usr/bin/google-chrome
        #browser = p.chromium.launch(
        #    executable_path="/usr/bin/google-chrome-stable",
        #    headless=False
        #)
        
        # 获取当前的上下文（如果有已经打开的标签页，可以直接接管）
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        
        page.goto("https://github.com")
        print(page.title())


run()

