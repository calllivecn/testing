
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # 启动浏览器，headless=False 表示显示浏览器界面
    #browser = p.chromium.launch(headless=False)
    browser = p.chromium.connect_over_cdp("http://localhost:9222")

    # 2. 关键点：获取已经存在的第一个上下文，而不是让 Playwright 建新的
    # 默认启动的浏览器通常已经有一个 context
    context = browser.contexts[0]
    # 3. 在这个已经存在的上下文中打开新标签页
    # 这样它就会出现在你那个看得见的浏览器窗口里，并带有插件和代理
    page = context.new_page()
    page.goto("https://www.google.com")
    # 打印页面标题
    print(f"页面标题是: {page.title()}")
    browser.close()
