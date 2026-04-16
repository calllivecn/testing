

import sys
import json
import pprint
import asyncio
import traceback

from datetime import datetime

from typing import (
    Iterator,
)

from playwright.async_api import (
    Response,
    async_playwright,
    Page,
    Locator,
)

import ollama


TOOLS = [
    {
        'type': 'function',
        'function': {
            'name': 'get_current_time',
            'description': '查询当前世界日期和时间',
            'parameters': {
                'type': 'object',
                'properties': {}
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'web_search',
            'description': '搜索互联网获取最新信息。当用户询问新闻、实时数据、未知事实或需要查证信息时使用。无法回答时效性问题或知识盲区时优先调用。这个工具只是返回了搜索的摘要信息。当你觉得需要获取详细网页结果时，调用"fetch_webpage"工具',
            'parameters': {
                'type': 'object',
                'properties': {
                    'query': {
                        'type': 'string',
                        'description': '搜索关键词或问题'
                    },
                },
                'required': ['query']
            }
        }
    },
    {
        "name": "fetch_webpage",
        "description": "获取指定网页的完整内容。当搜索结果的摘要不足时调用，选择最相关的网页获取详情。",
        "parameters": {
            "type": "object",
            "properties": {
            "url": {
                "type": "array",
                "items": {"type": "string"},
                "description": "候选网页URL列表，必须是一个包含 URL 的字符串数组。示例格式：['https://example.com']"
            },
            # "max_fetch": {
            #     "type": "number",
            #     "description": "最多抓取几个网页，默认 3，复杂问题可设 5",
            #     "default": 3
            # }
            },
            "required": ["url"]
        }
    }
]


# fetch_webpage 返回
# [
#     {
#         "url": "https://...",
#         "content": "完整网页内容...",
#         "title": "网页标题"
#     }
# ]


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


    async def start(self):
        """手动启动"""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.connect_over_cdp(self.cdp)
        # self._context = await self._browser.new_context()

        # 在这个已经存在的上下文中打开新标签页
        # 这样它就会出现在你那个看得见的浏览器窗口里，并带有插件和代理
        self._context = self._browser.contexts[0]


    async def stop(self):
        """手动停止"""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def fetch_page_content(self, page: Page, url: str):
        """在单个页面上导航并获取内容"""
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # 并行获取多种内容
            title = await page.title()
            html = await page.content()
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

    async def open_tabs_and_fetch(self, urls: list[str]):
            
        # 创建多个标签页
        pages = [await self._context.new_page() for _ in urls]
        
        # 并行导航并获取内容
        tasks = [self.fetch_page_content(page, url) for page, url in zip(pages, urls)]
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


class LLM:

    def __init__(self, host: str='http://10.1.3.20:11434'):
        self.client = ollama.AsyncClient(host=host)
        
        self.tools = TOOLS

#         self.messages: list[dict] = [{
#                 'role': 'system',
#                 'content': """这是从搜索引擎获取的查询结果摘要: json格式的: {"url": str, "title": str, "text": str}（url+标题+片段）。
# 请按以下步骤处理：
# 1. 先判断摘要信息是否足够回答问题
# 2. 如果足够，直接整理信息回答用户
# 3. 如果不足，调用 fetch_webpage 获取 3-5 个最相关网页的详细内容
# 4. 基于完整内容给出准确回答

# 注意：不要编造信息，不确定的内容要说明。"""
#             }]
        self.messages: list[dict] = []

    @property
    def model(self):
        return self._model
    
    @model.setter
    def model(self, name: str):
        self._model = name

    @property
    def bs(self):
        return self._bs
    
    @bs.setter
    def bs(self, bs: BrowserSearch):
        self._bs = bs

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
                tools=TOOLS,
                stream=True,
                options={"num_ctx": 8192}
            )


            # 处理流式响应
            full_response = []
            tool_calls = []
            last_chunk = None  # 保存最后一个 chunk 用于统计
            think = True

            full_tool_calls = []

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
                    full_tool_calls.extend(tool_calls)

            
            # 模型的回复也要添加到上下文
            if full_response:
                self.messages.append({
                    "role": "assistant",
                    "content": "".join(full_response)
                })

            # 查看 Token 使用情况
            await self.calculate_speed(last_chunk)

            # 流式输出处理完后，在处理tool调用
            # 2. 处理工具调用
            if full_tool_calls:
                # 将原始消息加入上下文
                self.messages.append({'role': 'assistant', 'tool_calls': full_tool_calls})

                for tool in full_tool_calls:
                    func_name = tool['function']['name']
                    args = tool['function'].get('arguments', {}) # 函数可以是没有参数的
                    print(f"\n[调用工具: {func_name}] 参数: {args}")

                    try:
                        # 执行TOOLS中的函数
                        func_result = await self.call_tools(func_name, args)
                    except Exception:
                        func_result = traceback.format_exc(3)
                        print(f"调用函数: {func_name} 异常：{func_result}")

                    # 第一个工具调用
                    msg_tool_result = {
                        "role": "tool",
                        "name": func_name,
                        "content": json.dumps(func_result, ensure_ascii=False),
                    }

                    self.messages.append(msg_tool_result)
            else:
                # 如果没有工具调用，说明对话已完成
                break

        pprint.pprint(self.messages)

    async def call_tools(self, func_name: str, args: dict):
        if func_name == "web_search":
            result = await self.bs.web_search(args["query"])
        
        elif func_name == "fetch_webpage":

            if isinstance(args["url"], str):
                a = [args["url"]]
            elif isinstance(args["url"], list):
                a = args["url"]
            else:
                raise ValueError("参数类型不对，应该是：str:url 或者 list[str:url]")
            result = await self.bs.open_tabs_and_fetch(a)
        
        elif func_name == "get_current_time":
            result = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        else:
            raise ValueError(f"没有找到 tool 函数：{func_name}")

        return result


    # def calculate_speed(self, response: ollama.ChatResponse):
    async def calculate_speed(self, response):
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

    bs = BrowserSearch("http://localhost:9222", "https://www.google.com")
    await bs.start()

    llm.bs = bs

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