
import asyncio
from playwright.async_api import async_playwright
import json


async def run():
    async with async_playwright() as p:
        # 启动浏览器
        #browser = await p.chromium.launch(headless=False)
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        # 在这个已经存在的上下文中打开新标签页
        # 这样它就会出现在你那个看得见的浏览器窗口里，并带有插件和代理
        context = browser.contexts[0]

        page = await context.new_page()

        # 建立 CDP 会话
        client = await context.new_cdp_session(page)

        # 1. 开启相关的 Domain 权限，否则无法接收到对应事件
        #await client.send("Input.enable")
        await client.send("Page.enable")
        # 如果需要监听网络，还需开启 Network.enable
        await client.send("Network.enable")
        await client.send("Runtime.enable")

        print("--- 开始录制 CDP 事件 (请在浏览器窗口进行操作) ---")

        # 2. 定义回调函数，处理捕获到的 CDP 事件
        def on_event(method, params):
            # 过滤掉不感兴趣的移动事件，只看点击和按键
            if method == "Input.dispatchMouseEvent" and params.get("type") == "mousePressed":
                print(f"[点击事件] 坐标: ({params.get('x')}, {params.get('y')}), 按钮: {params.get('button')}")
            
            elif method == "Input.dispatchKeyEvent" and params.get("type") == "keyDown":
                print(f"[按键事件] 键名: {params.get('key')}, 代码: {params.get('windowsVirtualKeyCode')}")

        # 3. 绑定监听器到所有原始 CDP 事件
        # Playwright 的 cdp_session 允许直接监听特定的方法
        client.on("Input.dispatchMouseEvent", lambda p: on_event("Input.dispatchMouseEvent", p))
        client.on("Input.dispatchKeyEvent", lambda p: on_event("Input.dispatchKeyEvent", p))

        # 访问一个目标网页
        await page.goto("https://www.google.com")

        # 保持运行，直到手动关闭浏览器
        try:
            # 模拟持续运行，等待用户操作
            while True:
                await asyncio.sleep(1)
        except Exception as e:
            print(f"\n录制结束: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())

