
from playwright.sync_api import sync_playwright

def record_via_cdp():
    with sync_playwright() as p:
        # 1. 连接到你已经启动的浏览器 (假设端口为 9222)
        # 注意：启动浏览器时需带上 --remote-debugging-port=9222
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        
        # 2. 获取当前的上下文
        # connect_over_cdp 接入时，通常 context 已经存在
        context = browser.contexts[0]
        
        # 3. 获取或新建页面
        if context.pages:
            page = context.pages[0]
        else:
            page = context.new_page()

        print("--- 已连接到浏览器 ---")
        print("正在启动录制器 (Playwright Inspector)...")

        # 4. 关键步骤：暂停脚本执行并唤起录制面板
        # 这会开启 Playwright Inspector 窗口
        # 你在浏览器里的操作会实时同步到 Inspector 的代码区域
        page.pause()

        # 当你关闭 Inspector 窗口时，脚本会继续向下执行
        browser.close()

if __name__ == "__main__":
    record_via_cdp()
