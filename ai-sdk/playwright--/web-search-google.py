

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

        # self.headless = headless
        # self._playwright = None
        # self._browser: Browser = None
        # self._context: BrowserContext = None

        # 工具列表
        self.tools: list[Callable] = [
            self.web_search,
            self.fetch_webpage,
            # self.fetch_webpage_list,
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
            # html = await page.content()
            text = await page.inner_text("body")
            
            return {
                "url": url,
                "title": title,
                # "html_length": len(html),
                "text_length": len(text),
                # "html": html,
                "text": text,
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
                # "html_length": 0,
                "text_length": 0,
                "status": "failed",
                "error": error_msg
            }

        finally:
            await page.close()


    async def fetch_webpage_list(self, urls: list[str]):
        """
        获取多个 list[str:url] 的网页内容
        args:
            urls: URL列表，必须是一个包含 URL 的字符串数组。示例格式：['https://example.com']
        """
        # 创建多个标签页
        pages = [await self._context.new_page() for _ in urls]
        
        # 并行导航并获取内容
        tasks = [self.fetch_webpage_of_page(page, url) for page, url in zip(pages, urls)]
        results = await asyncio.gather(*tasks)
        
        # 统计结果
        success_count = sum(1 for r in results if r["status"] == "success")
        failed_count = len(results) - success_count
        
        print(f"\n{'='*50}")
        print(f"抓取完成：成功 {success_count}/{len(results)}，失败 {failed_count}")
        print(f"{'='*50}\n")
        
        # 打印结果
        for result in results:
            if result["status"] == "success":
                print(f"✅ URL: {result['url']}")
                print(f"   Title: {result['title']}")
                print(f"   Content Length: {result['text_length']}")
                print(f"   Content: {result['text']}")
            else:
                print(f"❌ URL: {result['url']}")
                print(f"   Error: {result.get('error', 'Unknown')}")
            print()
        
        # 关闭pages
        for page in pages:
            await page.close()


    async def web_search(self, query: str) -> list[dict]:
        """
        搜索互联网获取最新信息。
        当用户询问新闻、实时数据、未知事实或需要查证信息时使用。
        无法回答时效性问题或知识盲区时优先调用。这个工具只是返回了搜索的摘要信息。
        当你觉得需要获取详细网页结果时，调用"fetch_webpage"工具'
        args:
            query: 搜索关键词或问题
        """

        page = await self._context.new_page()

        #await page.goto(self.search_engine, wait_until="networkidle")
        await page.goto(self.search_engine)

        # === 新增：如果提供了搜索词，执行搜索 ===
        # 等待搜索框加载 (Google 搜索框的常见选择器)
        # search_box = page.locator('textarea[name="q"], input[name="q"]').first
        # await search_box.wait_for(state="visible")
        
        search_box = page.get_by_role("combobox", name="搜索")

        # 清空并输入搜索内容
        await search_box.fill("")
        await search_box.fill(query)
        
        # 按回车提交搜索
        await search_box.press("Enter")
        
        # 等待搜索结果加载
        
        # await page.wait_for_load_state("networkidle")
        # await asyncio.sleep(5)  # 额外等待确保内容渲染

        # 策略 B: 使用 get_by_role 等待第一个标题出现（更具鲁棒性）
        # Google 的搜索结果通常是 level=3 的 heading
        await page.get_by_role("heading", level=3).first.wait_for()

        # try:
        #     # 等待 <section> 标签出现在页面中，最多等待 30 秒
        #     await page.get_by_role("heading", name="AI 概览").first.wait_for(timeout=3000)
        # except Exception as e:
        #     print(f"等待 AI摘要超时: {e}")

        all_text = await extract_links_fast(page)

        return all_text

async def get_current_time():
    """
    询当前世界日期和时查间
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


TOOLS = [
    get_current_time,
]


class LLM:

    def __init__(self, host: str='http://10.1.3.20:11434'):
        self.client = ollama.AsyncClient(host=host)
        
        self._tools: list[Callable] = []

        self.tools_map: dict[str, Callable] = {}

        self.messages: list[dict] = []

    @property
    def model(self):
        return self._model
    
    @model.setter
    def model(self, name: str):
        self._model = name
    
    @property
    def tools(self):
        return self._tools
    
    @tools.setter
    def tools(self, v: list[Callable]):
        self._tools = v
        for func in self.tools:
            self.tools_map.update(
                {func.__name__: func}
            )

    async def chat(self, content: str):
        message = {
            "role": "user",
            "content": content
        }

        self.messages.append(message)

        max_turns = 5  # 防止死循环
        for _ in range(max_turns):

            response = await self.client.chat(
                model=self._model,
                messages=self.messages,
                tools=self.tools,
                stream=True,
                options={"num_ctx": 8192}
            )


            # 处理流式响应
            full_response = []
            last_chunk: ollama.ChatResponse|None = None  # 保存最后一个 chunk 用于统计
            think = True

            full_tool_calls: list[BaseModel] = []
            # full_tool_calls: list[dict] = []

            async for chunk in response:

                # 检查是否包含统计信息（最后一个 chunk 的特征）
                if 'eval_count' in chunk or 'total_duration' in chunk:
                    last_chunk = chunk

                msg = chunk.message

                # 检查是否存在思考内容 (Thinking)
                if thinking := msg.get('thinking'):
                    print(f"\033[90m{thinking}\033[0m", end="", flush=True)


                if content := msg.get('content'):

                    if not chunk.message.thinking and think:
                        think = False
                        print("\n", "+"*20, "思考结束", "+"*20, "\n")

                    print(content, end='', flush=True)
                    
                    # 把流式回复收集起来
                    full_response.append(content)


                # 记录LLM要调用的工具，之后一直执行。
                if tool_calls := msg.get('tool_calls'):
                    # print(f"{tool_calls[0]=} {type(tool_calls[0])=}")
                    full_tool_calls.extend(tool_calls)

            
            # 模型的回复也要添加到上下文
            if full_response:
                self.messages.append({
                    "role": "assistant",
                    "content": "".join(full_response)
                })

            # 查看 Token 使用情况
            self.calculate_speed(last_chunk)

            # 流式输出处理完后，在处理tool调用
            # 2. 处理工具调用
            if full_tool_calls:
                tool_calls = [t.model_dump() for t in full_tool_calls]

                # 将原始消息加入上下文
                self.messages.append({
                    'role': 'assistant',
                    'tool_calls': tool_calls
                    })

                for tool in tool_calls:
                    f = tool["function"]
                    func_name = f['name']
                    args = f.get('arguments', {}) # 函数可以是没有参数的
                    print(f"\n[调用工具: {func_name}] 参数: {args}")

                    try:
                        # 执行TOOLS中的函数
                        func_result = await self.call_tools(func_name, args)
                    except Exception:
                        func_result = traceback.format_exc(3)
                        print(f"调用函数: {func_name} 异常：{func_result}")

                    # 第一个工具调用
                    func_result_json = json.dumps(func_result, ensure_ascii=False)
                    msg_tool_result = {
                        "role": "tool",
                        "name": func_name,
                        "content": func_result_json,
                    }
                    print(f"\n调用结果: {pprint.pformat(func_result_json)}")

                    self.messages.append(msg_tool_result)
            else:
                # 如果没有工具调用，说明对话已完成
                break

        content_json = f"{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.json"
        print(f"当前上下文保存到：{content_json}")
        # 上下文保存到文件
        with open(content_json, "w") as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=4)


    async def call_tools(self, func_name: str, args: dict):
        if func_name in self.tools_map:

            func = self.tools_map[func_name]
            # print(f"执函数：{func} {args=}")
            result = await func(**args)

        else:
            raise ValueError(f"没有找到 tool 函数：{func_name}")

        return result


    def calculate_speed(self, response: ollama.ChatResponse|None = None):
        if response is None:
            return
        
    # async def calculate_speed(self, response):
        # 提取字段
        prompt_tokens = response.get('prompt_eval_count', 0)
        eval_tokens = response.get('eval_count', 0)

        # 纳秒转秒 (1s = 10^9 ns)
        total_sec = response.get('total_duration', 0) / 1e9
        load_sec = response.get('load_duration', 0) / 1e9
        # eval_duration 是模型实际生成回答所用的时间
        eval_sec = response.get('eval_duration', 0) / 1e9

        # 计算生成速度 (Tokens Per Second)
        # 我们通常使用 eval_count / eval_duration 来衡量模型的推理性能
        tps = eval_tokens / eval_sec if eval_sec > 0 else 0

        print(f"\n--- 性能统计 ---\nPrompt/Output/Total Tokens : {prompt_tokens}/{eval_tokens}/{prompt_tokens + eval_tokens} 👉 生成速度: {tps:.2f} tokens/s ")
        print(f"模型加载耗时: {load_sec:.4f} s 推理生成耗时: {eval_sec:.4f} s 总耗时 (含加载): {total_sec:.4f} s")


async def main(query: str):

    llm = LLM()
    llm.model = "gemma4:e4b"
    # llm.model = "gemma4:31b"
    llm.model = "gemma4-e4b-uncensored:Q8_K_P"

    bs = BrowserSearch("http://localhost:9222", "https://www.google.com")
    await bs.start()

    llm.tools = TOOLS + bs.tools

    # pprint.pprint(llm.tools_map)

    # llm.bs = bs

    # all_text = await bs.web_search(query)
    # pprint.pprint(all_text)

    await llm.chat(query)

    await bs.stop()


if __name__ == "__main__":
    try:
        query = sys.argv[1]
    except Exception:
        query = "什么是ollama"

    asyncio.run(main(query))
