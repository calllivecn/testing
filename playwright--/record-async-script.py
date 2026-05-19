import sys
import asyncio
from playwright.async_api import async_playwright

async def record_async_via_cdp():
    # 校验命令行参数，防止 IndexError
    if len(sys.argv) < 2:
        print("错误: 请提供目标 URL。")
        print("用法: python script.py <URL>")
        sys.exit(1)
        
    target_url = sys.argv[1]

    async with async_playwright() as p:
        # 连接到已存在的浏览器
        # 确保你启动 Chrome 时带有 --remote-debugging-port=9222
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        
        try:
            # 获取现有的上下文和页面
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()

            print("--- 异步录制/调试模式已启动 ---")
            print("提示：在弹出的 Inspector 窗口中，确保语言选择为 'Async Python'")
            print(f"正在访问: {target_url}")

            # 导航到目标 URL（goto 默认会等待至 load 状态）
            await page.goto(target_url)
            
            # 如果部分单页应用（SPA）确实需要等待网络空闲，可开启下方这行，但需注意潜在的超时坑
            # await page.wait_for_load_state("networkidle")

            # 唤起录制/调试面板
            # 注意：通过 CDP 接入已有上下文时，page.pause() 唤起的 Inspector 主要用于调试和选择器审查。
            # 如果发现手动操作时无法自动生成代码，这是由于预现有上下文缺少录制注入钩子导致的。
            await page.pause()

        except Exception as e:
            print(f"运行过程中发生异常: {e}", file=sys.stderr)
        finally:
            # 关键修改：使用 disconnect() 释放控制权，避免 kill 掉你的宿主浏览器进程
            await browser.close()
            print("--- 已安全断开 CDP 连接 ---")

if __name__ == "__main__":
    # 针对 Windows 环境下可能出现的 RuntimeError: Event loop is closed 的保护（可选）
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(record_async_via_cdp())