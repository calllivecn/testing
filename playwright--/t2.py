"""
在自动化爬取或测试时，面对这种可能存在、也可能不存在滚动条的局部容器，完美的健壮代码应该这样写：
"""

import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("你的目标网页URL")

        # 定位器（注意：使用了修正后的正确 CSS 选择器）
        scroll_container = page.locator("div[class^='grid-scroll--']")
        await scroll_container.wait_for(state="visible")

        # 1. 核心判断：先看它到底有没有滚动条
        has_scrollbar = await scroll_container.evaluate(
            "(el) => el.scrollHeight > el.clientHeight"
        )

        if not has_scrollbar:
            print("【状态】内容已全部放下，当前无滚动条。无需滚动，直接提取数据！")
            # 在这里直接执行你的数据抓取逻辑...
        else:
            print("【状态】检测到滚动条，开启循环向下滚动逻辑...")

            # 2. 如果有滚动条，则循环滚动直到触底
            while True:
                # 判断是否已经抵达底部
                is_bottom = await scroll_container.evaluate(
                    "(el) => (el.scrollTop + el.clientHeight) >= (el.scrollHeight - 1)"
                )

                if is_bottom:
                    print("已经滚动到最底部了！")
                    break

                # 没到底就继续往下滚 400 像素
                await scroll_container.evaluate("(el) => el.scrollTop += 400")
                await page.wait_for_timeout(500)  # 给懒加载留出渲染时间

            print("【结束】滚动流处理完毕。")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
