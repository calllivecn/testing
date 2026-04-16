import asyncio
from playwright.async_api import async_playwright

async def record_async_via_cdp():
    async with async_playwright() as p:
        # 连接到已存在的浏览器
        # 确保你启动 Chrome 时带有 --remote-debugging-port=9222
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        
        # 获取现有的上下文和页面
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        print("--- 异步录制模式已启动 ---")
        print("提示：在弹出的 Inspector 窗口中，确保语言选择为 'Async Python'")

        # 唤起录制/调试面板
        await page.pause()

        await browser.close()

if __name__ == "__main__":
    asyncio.run(record_async_via_cdp())
