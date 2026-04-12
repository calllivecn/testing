
import asyncio
import datetime

from playwright.async_api import async_playwright
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

    print(f"--- 性能统计 ---")
    print(f"Prompt Tokens: {prompt_tokens}")
    print(f"Output Tokens: {eval_tokens}")
    print(f"模型加载耗时: {load_sec:.4f} s")
    print(f"推理生成耗时: {eval_sec:.4f} s")
    print(f"总耗时 (含加载): {total_sec:.4f} s")
    print(f"👉 生成速度: {tps:.2f} tokens/s")

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
    calculate_speed(response)


def chat2(images: list[bytes]):
    images: list[str] = []
    # 将 bytes 转换为 base64 字符串
    # .decode('utf-8') 是为了将 bytes 格式的 base64 转为 string 格式
    for img in images:
        images.append(base64.b64encode(img).decode('utf-8'))

    # 调用 Ollama 进行分析
    # 注意：这里使用 ollama.chat，不再需要 API Key
    # model 参数填你本地已经拉取好的模型名称（例如 'llama3', 'mistral' 等）
    response = client.chat(
        model=MODEL_NAME, 
        messages=[{
            'role': 'user',
            'content': "请从网页截图中提取内容整理后，以 JSON 格式返回。",
            'images': images
        }],
        options={"num_ctx": 8192},
        #options={"num_ctx": 16384},
    )
    
    # 3. 输出结果
    print("AI 提取结果:", response['message']['content'])
    calculate_speed(response)


async def smart_scrape(url: str):
    async with async_playwright() as p:

        browser = await p.chromium.connect_over_cdp("http://localhost:9222")

        # 在这个已经存在的上下文中打开新标签页
        # 这样它就会出现在你那个看得见的浏览器窗口里，并带有插件和代理
        context = browser.contexts[0]

        page = await context.new_page()

        # 动态设置视口分辨率
        await page.set_viewport_size({"width": 1920, "height": 1080})

        # 强制等待页面重绘（高级用户技巧）
        # 等待 resize 事件触发或等待一小段时间让 CSS 媒体查询生效
        await page.wait_for_timeout(500)

        # 使用 Python 打印浏览器内部真实的渲染指标
        dims = await page.evaluate("""() => {
            return {
                "CSS宽度": window.innerWidth,
                "CSS高度": window.innerHeight,
                "DPR(缩放倍率)": window.devicePixelRatio,
                "物理像素宽": window.innerWidth * window.devicePixelRatio,
                "物理像素高": window.innerHeight * window.devicePixelRatio
            }
        }""")
        print(dims)

        #await page.goto(url, wait_until="networkidle")
        await page.goto(url)

        for i in range(5):
            await asyncio.sleep(1)
            # 模拟按下 PageDown
            await page.keyboard.press("PageDown") 
            # 2. 手动等待网络空闲
            #await page.wait_for_load_state("networkidle")

            
        await asyncio.sleep(3)

        # 1. 提取文本内容
        content = await page.inner_text("body")

        ## 获取 body 元素
        body_element = page.locator("body")
        ## 提取可见文本
        all_text = await body_element.inner_text()

        print(all_text)
        content = chat(all_text)

        # 2. 对当前可视区域截图
        #screenshot_bytes = await page.screenshot(type="png", full_page=True)

        #filename = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S.%f')[:-3]
        #with open(f"{filename}.png", "wb") as f:
        #    f.write(screenshot_bytes)

        #content = chat2([screenshot_bytes])

        print(content)
        
        await browser.close()

# 运行前请确保你已经在终端执行了 ollama run llama3
asyncio.run(smart_scrape("https://www.bilibili.com"))

