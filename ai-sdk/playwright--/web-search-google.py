
import sys
import pprint
import asyncio


from playwright.async_api import (
    Response,
    async_playwright,
    Page,
    Locator,
)

import ollama

MODEL_NAME="gemma4:e4b"

def calculate_speed(response):
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

    print("--- 性能统计 ---")
    print(f"Prompt Tokens: {prompt_tokens}")
    print(f"Output Tokens: {eval_tokens}")
    print(f"模型加载耗时: {load_sec:.4f} s")
    print(f"推理生成耗时: {eval_sec:.4f} s")
    print(f"总耗时 (含加载): {total_sec:.4f} s")
    print(f"👉 生成速度: {tps:.2f} tokens/s")


tools = [
    {
        'type': 'function',
        'function': {
            'name': 'search_web',
            'description': '搜索互联网获取最新信息。当用户询问新闻、实时数据、未知事实或需要查证信息时使用。无法回答时效性问题或知识盲区时优先调用。',
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
        "description": "获取指定网页的完整内容。当搜索结果摘要不足时调用，选择最相关的网页获取详情。",
        "parameters": {
            "type": "object",
            "properties": {
            "urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "候选网页URL列表（来自搜索结果）"
            },
            "max_fetch": {
                "type": "number",
                "description": "最多抓取几个网页，默认 3，复杂问题可设 5",
                "default": 3
            }
            },
            "required": ["urls"]
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


client = ollama.Client(host='http://10.1.3.20:11434')

def chat(content: str):
    # 2. 调用 Ollama 进行分析
    # 注意：这里使用 ollama.chat，不再需要 API Key
    # model 参数填你本地已经拉取好的模型名称（例如 'llama3', 'mistral' 等）
    response = client.chat(
        model=MODEL_NAME,
        messages=[{
            'role': 'user',
            'content': f"请从以下内容中提取内容整理后，以 JSON 格式返回：\n\n{content}"
        }],
        options={"num_ctx": 8192}
    )
    
    # 3. 输出结果
    print("AI 提取结果:", response['message']['content'])

    # 查看 Token 使用情况
    calculate_speed(response)


async def extract_links_fast(page: Page):
    # 方法 2：使用 evaluate 一次性获取（性能更好）
    links = await page.evaluate('''() => {
    const rso = document.getElementById("rso")
    if (!rso) return []

    const result_div = rso.querySelectorAll("[data-snc]")

    const links = []

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



async def fetch_page_content(page: Page, url: str):
    """在单个页面上导航并获取内容"""
    await page.goto(url, wait_until="domcontentloaded")
    
    # 并行获取多种内容
    title = await page.title()
    html = await page.content()
    text = await page.inner_text("body")
    
    return {
        "url": url,
        "title": title,
        "html_length": len(html),
        "text_length": len(text)
    }

async def open_tabs_and_fetch(urls: list[str]):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        
        # 创建多个标签页
        pages = [await context.new_page() for _ in urls]
        
        # 并行导航并获取内容
        tasks = [fetch_page_content(page, url) for page, url in zip(pages, urls)]
        results = await asyncio.gather(*tasks)
        
        # 打印结果
        for result in results:
            print(f"URL: {result['url']}")
            print(f"  Title: {result['title']}")
            print(f"  HTML Length: {result['html_length']}")
            print(f"  Text Length: {result['text_length']}\n")
        
        await browser.close()


async def web_search(url: str, query: str):
    async with async_playwright() as p:

        browser = await p.chromium.connect_over_cdp("http://localhost:9222")

        # 在这个已经存在的上下文中打开新标签页
        # 这样它就会出现在你那个看得见的浏览器窗口里，并带有插件和代理
        context = browser.contexts[0]

        page = await context.new_page()

        #await page.goto(url, wait_until="networkidle")
        await page.goto(url)

        # === 新增：如果提供了搜索词，执行搜索 ===
        # 等待搜索框加载 (Google 搜索框的常见选择器)
        search_box = page.locator('textarea[name="q"], input[name="q"]').first
        await search_box.wait_for(state="visible")
        
        # 清空并输入搜索内容
        await search_box.fill("")
        await search_box.fill(query)
        
        # 按回车提交搜索
        await search_box.press("Enter")
        
        # 等待搜索结果加载
        # await page.wait_for_load_state("networkidle")
        await asyncio.sleep(5)  # 额外等待确保内容渲染


        # loc = page.locator('#center_col')
        loc = page.locator('#rso')
        await loc.wait_for(state="visible")
        all_text = await extract_links_fast(page)

        pprint.pprint(all_text)

        # content = chat(all_text)
        # print(content)
        
        await browser.close()


# 运行前请确保你已经在终端执行了 ollama run llama3
try:
    query = sys.argv[1]
except Exception:
    query = "什么是ollama"

asyncio.run(web_search("https://www.google.com", query))

