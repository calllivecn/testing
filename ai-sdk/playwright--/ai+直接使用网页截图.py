
import asyncio
import datetime

from playwright.async_api import async_playwright
import ollama

client = ollama.Client(host='http://10.1.3.20:11434')

def chat(content: str):
    # 2. 调用 Ollama 进行分析
    # 注意：这里使用 ollama.chat，不再需要 API Key
    # model 参数填你本地已经拉取好的模型名称（例如 'llama3', 'mistral' 等）
    response = client.chat(
        model='gemma4:e4b', 
        messages=[{
            'role': 'user',
            'content': f"请从以下内容中提取内容整理后，以 JSON 格式返回：\n\n{content}"
        }],
        options={"num_ctx": 8192}
    )
    
    # 3. 输出结果
    print("AI 提取结果:", response['message']['content'])


def chat2(images: list[bytes]):
    # 2. 调用 Ollama 进行分析
    # 注意：这里使用 ollama.chat，不再需要 API Key
    # model 参数填你本地已经拉取好的模型名称（例如 'llama3', 'mistral' 等）
    response = client.chat(
        model='gemma4:e4b', 
        messages=[{
            'role': 'user',
            'content': "请从网页截图中提取内容整理后，以 JSON 格式返回。",
            'images': images
        }],
        options={"num_ctx": 8192},
    )
    
    # 3. 输出结果
    print("AI 提取结果:", response['message']['content'])


async def smart_scrape(url: str):
    async with async_playwright() as p:

        browser = await p.chromium.connect_over_cdp("http://localhost:9222")

        # 在这个已经存在的上下文中打开新标签页
        # 这样它就会出现在你那个看得见的浏览器窗口里，并带有插件和代理
        context = browser.contexts[0]

        page = await context.new_page()

        #await page.goto(url, wait_until="networkidle")
        await page.goto(url)

        for i in range(5):
            await asyncio.sleep(1)
            # 模拟按下 PageDown
            await page.keyboard.press("PageDown") 
            # 2. 手动等待网络空闲
            #await page.wait_for_load_state("networkidle")

            
        await asyncio.sleep(1)

        # 1. 提取文本内容
        #content = await page.inner_text("body")

        ## 获取 body 元素
        #body_element = page.locator("body")
        ## 提取可见文本
        #all_text = await body_element.inner_text()

        #print(all_text)

        # 2. 对当前可视区域截图
        screenshot_bytes = await page.screenshot(type="png", full_page=True)

        filename = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S.%f')[:-3]
        with open(f"{filename}.png", "wb") as f:
            f.write(screenshot_bytes)

        content = chat2([screenshot_bytes])
        print(content)
        
        await browser.close()

# 运行前请确保你已经在终端执行了 ollama run llama3
asyncio.run(smart_scrape("https://www.bilibili.com"))

