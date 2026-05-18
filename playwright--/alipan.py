


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


class Alipan:
    """
    使用playwright的方式操作阿里去盘网页版本自动上传文件
    """

    def __init__(self, user_dir: Path, netdisk_path: Path, files: list[Path]):
        self.user_dir = user_dir
        self.netdisk_path = netdisk_path
        self.files = files


    async def task_entry(self):

        print("chrome 进程启动了")
        task_chrome = asyncio.create_task(self.start_chrome(Path("/home/zx/chromium-user-dir")))
        await asyncio.sleep(5)

        async with async_playwright() as p:
            await self.connect_chrom_cdp(p)

            await self.login_alipan()
            await self.goto_path(self.netdisk_path)

            await self.upload(self.files)

            await self.wait_upload_done()

        # await task_chrome
        print("cancel task_chrome")
        task_chrome.cancel()


    async def start_chrome(self, user_data_dir: Path, headless: bool = False) -> int:
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


    async def connect_chrom_cdp(self, p: Playwright):
        #browser = await playwright.chromium.launch(headless=False)
        #context = await browser.new_context()
        self.browser = await p.chromium.connect_over_cdp("http://localhost:9222", is_local=True)
        self.context = self.browser.contexts[0]

        self.page: Page = self.context.pages[0] if self.context.pages else await self.context.new_page()


    async def login_alipan(self):
        
        print(f"{self.page.url=}")

        # await self.page.goto("https://www.alipan.com/")
        # link_login = self.page.get_by_role("link", name="登录")

        await self.page.goto("https://www.alipan.com/drive/file/all")
        

        print("正在竞速检测 [主页面元素] vs [嵌套Iframe元素]...")
        if await self.check_login():
            print(">>> 判定：已登录")
        
        else:
            print(">>> 判定：未登录，需扫码")

            # 登录后自动跳转到的home页面
            fileclass = self.page.get_by_text("文件分类").first
            allfile = self.page.get_by_text("全部文件").first

            checkpoint = fileclass.or_(allfile)

            await checkpoint.wait_for(state="visible", timeout=30000)

            if await fileclass.is_visible():
                await self.page.goto("https://www.alipan.com/drive/file/all")
                await self.page.get_by_text("全部文件").wait_for(state="visible")
            
            print("登录成功")


    async def close(self):
        # ---------------------
        await self.context.close()
        await self.browser.close()


    async def check_login(self) -> bool:
        # 1. 定义两个独立的等待任务
        # 任务 A：主页面的“全部文件”
        task_logined = asyncio.create_task(self.page.get_by_text("全部文件").first.wait_for(state="visible"))
        
        # 任务 B：嵌套 iframe 里的“扫码登录”
        # 建议直接用 frame_locator 链式穿透，更稳定
        task_need_login = asyncio.create_task(
            self.page.frame_locator("iframe")
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
        if await self.page.get_by_text("全部文件").first.is_visible():
            return True
        else:
            return False


    # 检测是否向下到底了
    def is_page_scrolled_to_bottom(self):
        return self.page.evaluate("""() => {
            const { scrollY, innerHeight, scrollHeight } = window;
            return scrollY + innerHeight >= scrollHeight - 5;
        }""")


    # 在当前页面查找指定文本，找不到就向下滚动页面
    async def find_by_wheel(self, text: str, timeout_ms: int=30000) -> Locator:

        loop = asyncio.get_event_loop()
        start_time = loop.time()

        while True:
            # 检查元素是否已出现且可见
            locator = self.page.get_by_text(text)
            if await locator.is_visible():
                await locator.scroll_into_view_if_needed()
                return locator
            
            # 检查是否超时
            if (loop.time() - start_time) * 1000 > timeout_ms:
                raise TimeoutError(f"在 {timeout_ms}ms 内未找到文本: {text}")

            # 向下滚动一段距离
            # mouse.wheel 是模拟真实物理滚动最稳健的方法
            await self.page.mouse.wheel(0, 200)
            
            # 等待数据加载的短暂间隔
            # await page.wait_for_timeout(500)

            # 等待网络请求空闲（适用于懒加载）
            await self.page.wait_for_load_state("networkidle")

            if await self.is_page_scrolled_to_bottom():
                raise ValueError("已经到网页底了，说明没有找到当前路径：{text}")


    async def goto_path(self, p: Path):
        """
        按路径一层层找
        """

        for part in p.parts:
            
            if part == Path("/"):
                continue

            loc = await self.find_by_wheel(part)
            await loc.click()


    async def upload(self, filenames: list[Path]):

        # 逻辑：div 且 class 开启于 "button--" 且 class 包含 "adrive-create-button"
        await self.page.locator('div[class^="button--"][class*="adrive-create-button"]').click()

        # 1. 先点击上传按钮
        # 只点击位于菜单里的那个“上传文件”
        upload_button = self.page.get_by_role("menu").get_by_text("上传文件", exact=True)

        # 2. 开启监听，同时点击按钮
        async with self.page.expect_file_chooser() as fc_info:
            await upload_button.click()
        
        # 3. 获取文件选择器对象
        file_chooser = await fc_info.value
        
        # 4. 设置要上传的文件路径
        await file_chooser.set_files(filenames)

        # 5. 后续等待上传完成的逻辑...
        # 注意：阿里网盘上传后通常会弹出一个进度框，建议增加等待
        # await expect(page.get_by_text("正在上传")).to_be_visible()
        # await page.get_by_text("正在上传").click()
        await self.page.locator('div[class^="status-bar-wrapper--"]').click()
        
        print(f"正在上传: {filenames}")
        
    
    async def wait_upload_done(self):

        print("开始轮询上传状态...")
        i = 1
        while True:
            # is_visible 不会报错，它会立即返回 True 或 False
            # 配合 timeout=500 确保检查过程极快
            if await self.page.get_by_text("已上传至", exact=False).is_visible(timeout=500):
                print("上传成功！")
                break
                
            # 可以在这里增加其他逻辑，比如检查是否“上传失败”
            if await self.page.get_by_text("上传失败").is_visible(timeout=500):
                print("检测到上传失败，停止脚本")
                break
            
            i += 1
            print(f"正在等待上传... {i}/s", end="\r")
            await asyncio.sleep(1)



def main():

    parse = argparse.ArgumentParser(
        usage="%(prog)s [option] <file>",
        description="自动上传到阿里网盘",
        )
    
    parse.add_argument("--headless", action="store_true", default=False, help="使用chrome时，是否开启无头模式。")
    parse.add_argument("--user-data-dir", help="指定chrome实例的数据目录。")
    parse.add_argument("--netdisk-path", default="autoupload", help="需要上传到阿里网盘的那个目录，默认值：autoupload")
    parse.add_argument("files", args="+", type=Path, help="要上传的文件")

    args = parse.parse_args()

    if args.parse:
        parse.print_usage()
        sys.exit(0)

    alipan = Alipan(args.user_data_dir, args.netdisk_path, args.files)

    asyncio.run(alipan.task_entry())


if __name__ == "__main__":
    main()
