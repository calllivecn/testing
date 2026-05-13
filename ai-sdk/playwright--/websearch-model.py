import sys
import json
import pprint
import asyncio
import traceback

from datetime import datetime

from typing import (
    Callable,
    Iterator,
)

from playwright.async_api import (
    Response,
    async_playwright,
    Page,
    Locator,
)

import ollama
from pydantic import BaseModel


async def extract_links_fast(page: Page) -> list[dict]:
    # 方法 2：使用 evaluate 一次性获取（性能更好）
    links = await page.evaluate('''() => {
        const rso = document.getElementById("rso")
        if (!rso) return []

        const links = []

        const result_div = rso.querySelectorAll("[data-snc]")

        for(const a_data_snc of result_div){

            const a = a_data_snc.querySelector("a")
            if (!a) continue

            const url = a.href
            const title = a.querySelector("h3").innerText.trim()

            
            const data_sncf = a_data_snc.querySelector("div[data-sncf]")
            
            let text = ""
            if (data_sncf) {
                for (const span of data_sncf.querySelectorAll("span")) {
                    text += span.innerText.trim()
                }
            }
            
            links.push({
                "url": url,
                "title": title,
                "text": text,
            })
        }

        return links
    }''')
    return links


class BrowserSearch:

    def __init__(self, cdp: str, search_engine: str):
        self.cdp = cdp
        self.search_engine = search_engine

        # 工具列表
        self.tools: list[Callable] = [
            self.web_search,
            self.fetch_webpage,
        ]


    async def start(self):
        """手动启动"""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.connect_over_cdp(self.cdp)

        # 在这个已经存在的上下文中打开新标签页
        # 这样它就会出现在你那个看得见的浏览器窗口里，并带有插件和代理
        self._context = self._browser.contexts[0]


    async def stop(self):
        """手动停止"""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()


    async def fetch_webpage(self, url: str) -> dict:
        """
        获取给定一个 url 的页面内容
        args:
            url: URL示例格式：'https://example.com'
        """
        return await self.fetch_webpage_of_page(await self._context.new_page(), url)


    async def fetch_webpage_of_page(self, page: Page, url: str) -> dict:

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)
            
            # 并行获取多种内容
            title = await page.title()
            html = await page.content() # 获取完整的HTML内容
            text = await page.inner_text("body")
            
            return {
                "url": url,
                "title": title,
                "text_length": len(text),
                "html": html, # 返回HTML内容
                "status": "success"
            }
        except Exception as e:
            error_msg = str(e)
            
            # 给出友好的错误提示
            if "ERR_EMPTY_RESPONSE" in error_msg:
                print(f"\n⚠️  无法访问 {url}")
                print("   原因：服务器没有响应，可能是反爬虫机制或网站暂时不可用")
            elif "timeout" in error_msg.lower():
                print(f"\n⚠️  访问超时 {url}")
                print("   原因：页面加载超过 30 秒，可能是网络慢或页面复杂")
            elif "ERR_NAME_NOT_RESOLVED" in error_msg:
                print(f"\n⚠️  DNS 解析失败 {url}")
                print("   原因：域名无法解析，检查网络连接")
            else:
                print(f"\n⚠️  访问失败 {url}")
                print(f"   原因：{error_msg}")

            return {
                "url": url,
                "title": None,
                "text_length": 0,
                "status": "failed",
                "error": error_msg
            }

        finally:
            await page.close()


    async def fetch_webpage_list(self, urls: list[str]):
        """
// ... existing code ...
        # 关闭pages
        for page in pages:
            await page.close()


    async def web_search(self, query: str, llm_instance: 'LLM') -> list[dict]:
        """
        搜索互联网获取最新信息，并尝试总结结果。
        当用户询问新闻、实时数据、未知事实或需要查证信息时使用。
        """

        page = await self._context.new_page()
        await page.goto(self.search_engine)

        # === 执行搜索 ===
        search_box = page.get_by_role("combobox", name="搜索")
        await search_box.fill("")
        await search_box.fill(query)
        await search_box.press("Enter")
        
        # 等待搜索结果加载
        await page.get_by_role("heading", level=3).first.wait_for()

        all_links_data = await extract_links_fast(page)
        
        print(f"\n✅ 发现 {len(all_links_data)} 个搜索结果链接，开始抓取网页内容并摘要...")

        summary_results = []
        
        # 限制抓取和摘要的网页数量，以控制耗时
        MAX_PAGES_TO_FETCH = 3
        pages_to_process = all_links_data[:min(MAX_PAGES_TO_FETCH, len(all_links_data))]

        # 1. 抓取内容
        webpage_data = []
        for link_data in pages_to_process:
            url_to_fetch = link_data['url']
            result = await self.fetch_webpage(url_to_fetch)
            webpage_data.append(result)

        # 2. 摘要内容
        for page_result in webpage_data:
            if page_result["status"] == "success" and page_result.get("html"):
                
                # 构建给 LLM 的提示词
                summary_prompt = f"""
                请根据以下抓取到的网页内容，生成一份结构化的摘要。
                网页来源：{page_result['title']} ({page_result['url']})
                
                请务必包含以下结构：
                1. 核心摘要（不超过三点，用项目符号）。
                2. 关键引述（摘取 1-2 个最具代表性的短句）。
                3. 网页的原始内容长度信息（原网页文本长度: {page_result['text_length']}）。
                
                请将所有内容用 Markdown 格式清晰展示。
                
                --- 网页 HTML 内容开始 ---
                {page_result['html']}
                --- 网页 HTML 内容结束 ---
                
                请立即开始摘要。
                """
                
                try:
                    # 调用 LLM 进行摘要
                    summary = await llm_instance.chat(summary_prompt)
                    
                    summary_results.append({
                        "source_url": page_result['url'],
                        "summary": summary,
                        "original_title": page_result['title']
                    })
                except Exception as e:
                    summary_results.append({
                        "source_url": page_result['url'],
                        "summary": f"【摘要生成失败】错误: {e}",
                        "original_title": page_result['title']
                    })
            else:
                summary_results.append({
                    "source_url": page_result['url'],
                    "summary": f"【跳过摘要】无法获取内容，状态: {page_result.get('status')}",
                    "original_title": page_result.get('title', 'N/A')
                })
        
        return summary_results

async def get_current_time():
// ... existing code ...