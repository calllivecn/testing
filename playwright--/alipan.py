


import sys
import asyncio
import argparse
# import subprocess

from pathlib import Path


from playwright.async_api import (
    Playwright,
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
    expect,
    Page,
    Locator,
)


async def start_chrome(user_data_dir: Path, headless: bool = False) -> int:
    args = [
        "google-chrome-stable",
        "--remote-debugging-port=9222",
        f"--user-data-dir={user_data_dir}",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--window-size=1200,800",
    ]
    if headless:
        args.append("--headless")

    print(f"chrome启动参数：{args}")
    p = await asyncio.subprocess.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    try:
        return await p.wait()
    except asyncio.CancelledError:
        # 1. 先发送 SIGTERM（优雅终止）
        p.terminate()
        try:
            # 2. 等待最多 5 秒让子进程自行退出
            return await asyncio.wait_for(p.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            # 3. 超时后强制 SIGKILL
            p.kill()
            return await p.wait()


async def check_login(page: Page) -> bool:
    # 1. 定义两个独立的等待任务
    # 任务 A：主页面的“全部文件”
    task_logined = asyncio.create_task(page.get_by_text("全部文件").first.wait_for(state="visible"))
    
    # 任务 B：嵌套 iframe 里的“扫码登录”
    # 建议直接用 frame_locator 链式穿透，更稳定
    task_need_login = asyncio.create_task(
        page.frame_locator("iframe")
            .frame_locator("#alibaba-login-box")
            .get_by_text("扫码登录")
            .first
            .wait_for(state="visible")
    )

    # 2. 使用 asyncio.wait，设置 return_when=asyncio.FIRST_COMPLETED
    # 这样只要其中一个满足 wait_for，就会立即停止阻塞
    done, pending = await asyncio.wait(
        [task_logined, task_need_login],
        timeout=30,
        return_when=asyncio.FIRST_COMPLETED
    )

    # 3. 取消掉还在等待的任务，避免后台报错
    for task in pending:
        task.cancel()

    # 4. 最后通过 is_visible 判断胜出者
    if await page.get_by_text("全部文件").first.is_visible():
        return True
    else:
        return False


# 在当前页面查找指定文本，找不到就向下滚动页面
async def find_by_wheel(page: Page, text: str, timeout_ms: int=30000) -> Locator:

    loop = asyncio.get_event_loop()
    start_time = loop.time()

    while True:
        # 检查元素是否已出现且可见
        locator = page.get_by_text(text)
        if await locator.is_visible():
            await locator.scroll_into_view_if_needed()
            return locator
        
        # 检查是否超时
        if (loop.time() - start_time) * 1000 > timeout_ms:
            raise TimeoutError(f"在 {timeout_ms}ms 内未找到文本: {text}")

        # 向下滚动一段距离
        # mouse.wheel 是模拟真实物理滚动最稳健的方法
        await page.mouse.wheel(0, 200)
        
        # 等待数据加载的短暂间隔
        # await page.wait_for_timeout(500)

        # 等待网络请求空闲（适用于懒加载）
        await page.wait_for_load_state("networkidle")



try:
    filename = Path(sys.argv[1])
except Exception as e:
    raise e


async def run(p: Playwright) -> None:

    #browser = await playwright.chromium.launch(headless=False)
    #context = await browser.new_context()
    browser = await p.chromium.connect_over_cdp("http://localhost:9222", is_local=True)
    context = browser.contexts[0]

    # context = await p.chromium.launch_persistent_context(
    #     user_data_dir="/home/zx/chromium-user-dir",
    #     executable_path="/usr/bin/google-chrome-stable",  # 直接使用文件名
    #     headless=False,
    #     # 阿里网盘等大文件上传建议增加这个参数，防止因为默认视口太小导致某些按钮点不到
    #     # viewport={'width': 1920, 'height': 1080},
    #     viewport={'width': 1200, 'height': 800},
        
    #     ignore_default_args=[
    #         # 核心设置 1: 显式排除掉 'enable-automation'
    #         "--enable-automation",
    #         # 核心设置 1: 忽略掉 Playwright 默认禁用插件的参数
    #         "--disable-extensions",
    #         "--no-sandbox",
    #         ],
    #     args=[
    #         "--disable-gpu",
    #         "--remote-debugging-port=9222",
    #         # 核心设置 2: 禁用自动化扩展
    #         "--disable-blink-features=AutomationControlled",
    #         ]
    # )

    page = context.pages[0] if context.pages else await context.new_page()
    print(f"{page.url=}")

    # await page.goto("https://www.alipan.com/")
    # link_login = page.get_by_role("link", name="登录")

    await page.goto("https://www.alipan.com/drive/file/all")
    
    """

    # 如果已经是登录的
    logined = page.get_by_text("全部文件").first

    # 如果没有登录会自动跳转到需要登录的页面    
    # login_qr = page.get_by_text("扫码登录").first
    login_qr = page.frame_locator("#alibaba-login-box").get_by_text("扫码登录").first

    # 使用 .or_() 将两者合并为一个“竞速”定位器
    checkpoint = logined.or_(login_qr)

    print("正在检测页面状态...")
    # 3. 等待任意一个目标出现（只要其中一个 visible，等待就结束）
    await checkpoint.wait_for(state="visible", timeout=30000)

    # 4. 分支逻辑判断
    if await logined.is_visible():
        print(">>> 分支确认：当前处于 [已登录] 状态")

    elif await login_qr.is_visible():
        print(">>> 分支确认：当前处于 [未登录] 状态，请准备扫码")

        # 登录后自动跳转到的home页面
        page.get_by_text("文件分类")

        print("登录成功")

        await page.goto("https://www.alipan.com/drive/file/all")
        page.get_by_text("全部文件")
    
        # await page.locator("iframe").content_frame.locator("#alibaba-login-box").content_frame.locator("canvas").click(position={"x":70,"y":52})
        # await page.goto("https://www.alipan.com/drive/home")
        # await page.get_by_text("文件", exact=True).click()
    """

    print("正在竞速检测 [主页面元素] vs [嵌套Iframe元素]...")
    if await check_login(page):
        print(">>> 判定：已登录")
    
    else:
        print(">>> 判定：未登录，需扫码")

        # 登录后自动跳转到的home页面
        fileclass = page.get_by_text("文件分类").first
        allfile = page.get_by_text("全部文件").first

        checkpoint = fileclass.or_(allfile)

        await checkpoint.wait_for(state="visible", timeout=30000)

        if await fileclass.is_visible():
            await page.goto("https://www.alipan.com/drive/file/all")
            await page.get_by_text("全部文件").wait_for(state="visible")
        
        print("登录成功")


    tmp = await find_by_wheel(page, "tmp")
    await tmp.click()

    loc = await find_by_wheel(page, "zx")
    await loc.click()


    # 逻辑：div 且 class 开启于 "button--" 且 class 包含 "adrive-create-button"
    await page.locator('div[class^="button--"][class*="adrive-create-button"]').click()

    # 1. 先点击上传按钮
    # 只点击位于菜单里的那个“上传文件”
    upload_button = page.get_by_role("menu").get_by_text("上传文件", exact=True)

    # 2. 开启监听，同时点击按钮
    async with page.expect_file_chooser() as fc_info:
        await upload_button.click()
    
    # 3. 获取文件选择器对象
    file_chooser = await fc_info.value
    
    # 4. 设置要上传的文件路径
    await file_chooser.set_files(filename)

    # 5. 后续等待上传完成的逻辑...
    # 注意：阿里网盘上传后通常会弹出一个进度框，建议增加等待
    # await expect(page.get_by_text("正在上传")).to_be_visible()
    # await page.get_by_text("正在上传").click()
    await page.locator('div[class^="status-bar-wrapper--"]').click()
    
    print(f"正在上传: {filename}")
    
    print("开始轮询上传状态...")
    i = 1
    while True:
        # is_visible 不会报错，它会立即返回 True 或 False
        # 配合 timeout=500 确保检查过程极快
        if await page.get_by_text("已上传至", exact=False).is_visible(timeout=500):
            print("上传成功！")
            break
            
        # 可以在这里增加其他逻辑，比如检查是否“上传失败”
        if await page.get_by_text("上传失败").is_visible(timeout=500):
            print("检测到上传失败，停止脚本")
            break
        
        i += 1
        print(f"正在等待上传... {i}/s", end="\r")
        await asyncio.sleep(1)

    # ---------------------
    # await context.close()
    await browser.close()


async def playwright_run() -> None:

    print("chrome 进程启动了")
    task_chrome = asyncio.create_task(start_chrome(Path("/home/zx/chromium-user-dir")))
    await asyncio.sleep(5)

    async with async_playwright() as playwright:
        await run(playwright)

    # await task_chrome
    print("cancel task_chrome")
    task_chrome.cancel()


asyncio.run(playwright_run())

