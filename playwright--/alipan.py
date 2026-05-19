


import sys
import asyncio
import argparse
# import subprocess

from pathlib import Path


from playwright.async_api import (
    Playwright,
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
    # expect,
    Page,
    Locator,
)
from playwright._impl._errors import Error as PlaywrightError

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
        task_chrome = asyncio.create_task(self.start_chrome(self.user_dir))

        async with async_playwright() as p:
            await self.connect_chrom_cdp(p)

            await self.login_alipan()
            await self.goto_path(self.netdisk_path)

            await self.upload(self.files)

            await self.wait_upload_done()

        # await task_chrome
        print("cancel task_chrome")
        task_chrome.cancel()

        await self.close()


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


    async def connect_chrom_cdp(self, p: Playwright, max_retries=5, delay=1.0):

        for attempt in range(1, max_retries + 1):
            try:
                self.browser = await p.chromium.connect_over_cdp("http://localhost:9222", is_local=True)
            except PlaywrightError as e:
                if "connect_over_cdp" in str(e) and attempt < max_retries:
                    print(f"浏览器可能尚未就绪 (尝试 {attempt}/{max_retries})，{delay}秒后重试...")
                    await asyncio.sleep(delay)
                    # 可选：适当增加下一次的延迟
                    delay *= 1.5
                else:
                    # 超过最大重试次数，或者遇到了其他类型的 Playwright 错误，直接抛出
                    raise e

        self.context = self.browser.contexts[0]

        self.page: Page = self.context.pages[0] if self.context.pages else await self.context.new_page()


    async def login_alipan(self):
        
        print(f"{self.page.url=}")

        # await self.page.goto("https://www.alipan.com/")
        # link_login = self.page.get_by_role("link", name="登录", exact=True)

        await self.page.goto("https://www.alipan.com/drive/file/all")
        

        print("正在竞速检测 [主页面元素] vs [嵌套Iframe元素]...")
        if await self.check_login():
            print(">>> 判定：已登录")
        
        else:
            print(">>> 判定：未登录，需扫码")

            # 登录后自动跳转到的home页面
            fileclass = self.page.get_by_text("文件分类", exact=True).first
            allfile = self.page.get_by_text("全部文件", exact=True).first

            checkpoint = fileclass.or_(allfile)

            await checkpoint.wait_for(state="visible", timeout=30000)

            if await fileclass.is_visible():
                await self.page.goto("https://www.alipan.com/drive/file/all")
                await self.page.get_by_text("全部文件", exact=True).wait_for(state="visible")
            
            print("登录成功")


    async def close(self):
        # ---------------------
        # await self.context.close() # 连接到一个已经启动的浏览器，不需要。
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
    async def is_page_scrolled_to_bottom(self) -> bool:

        # 1. 核心判断：先看它到底有没有滚动条
        # has_scrollbar = await scroll_container.evaluate(
        #     "(el) => el.scrollHeight > el.clientHeight"
        # )
        # print(f"当前到底有没有滚动条：{has_scrollbar=}")
        # if not has_scrollbar:
        #     return True


        # 这里的 window; 是整个document的滚动条。但是这里需要的时一个div的滚动条。
        # bottom = await scroll_container.evaluate("""() => {
        #     const { scrollY, innerHeight, scrollHeight } = window;
        #     return scrollY + innerHeight >= scrollHeight - 5;
        # }""")


        bottom = await self.scroll_container.evaluate("""(el) => {
            const { scrollTop, clientHeight, scrollHeight } = el;
            return scrollTop + clientHeight >= scrollHeight - 5;
        }""")

        return bottom


    # 在当前页面查找指定文本，找不到就向下滚动页面
    async def find_by_wheel(self, text: str, timeout_ms: int=30000) -> Locator:

        bool_ = False
        
        while True:

            # 检查元素是否已出现且可见
            locator = self.node_list.get_by_text(text, exact=True)

            # wait_for(state="visible") 会同时确保：
            # 1. AJAX 异步请求已返回（否则没有 DOM 节点）
            # 2. 前端框架已更新 DOM 树并将元素挂载上去（Attached）
            # 3. 浏览器已完成重绘，元素在屏幕上可见（Visible）
            try:
                await locator.wait_for(state="visible", timeout=500)
            except PlaywrightTimeoutError:
                print(f"没找到：{text}，看看是否需要滚动。")


                # 有滚动 条时才需要滚动
                if self.is_scroll:
                    print("滚动页面")
                
                    # 拿到当前div容器的viewport高度
                    clientHeight = await self.scroll_container.evaluate("(el) => el.clientHeight")

                    # 向下滚动一段距离
                    # mouse.wheel 是模拟真实物理滚动最稳健的方法
                    await self.page.mouse.wheel(0, clientHeight//2)
                    
                    # 将滚动条位置设为容器的滚动高度，瞬间回到最底部, 
                    # 
                    # 这样有问题：被称为虚拟滚动（Virtual Scrolling / Infinite Scroll）
                    # 在这种机制下，DOM 树中只保留当前可视区域（Viewport）附近的几项，滚动过去或还没滚动到的元素会被销毁或隐藏。
                    # 因此， 直接瞬间把 scrollTop 设为最大值，会导致中间的所有数据被跳过，无法触发加载，甚至导致你想要寻找的元素因为没有经过渲染而彻底错过。
                    #
                    # await self.scroll_container.evaluate("(el) => el.scrollTop = el.scrollHeight")

                    # 等待网络请求空闲（适用于懒加载）
                    await self.page.wait_for_load_state(state="networkidle", timeout=15000)


                    bool_ = await self.is_page_scrolled_to_bottom()
                    if bool_:
                        # 说明已经找完当前已经加载的内容，没有找到。可以结束
                        break

                else:
                    break

            # 当前名称不能是一个文件名
            if await self.check_is_dir(locator):
                return locator

        if bool_:
            raise ValueError(f"已经到网页底了，说明没有找到当前路径点：{text}")
        
        raise ValueError(f"没有找到目录节点：{text}")


    async def goto_path(self, p: Path):
        """
        按路径一层层找
        """

        p2 = Path("")
        for part in p.parts:
            
            if part == "/":
                continue

            print(f"进入下一级目录：{part}")
            p2 = p2 / part


            await self.page.wait_for_load_state(state="networkidle", timeout=15000)

            # 先定位到文件的div, 如果当前目录为空，可以会没有node-list--容器。就说明没之后的目录了直接创建目录+进入+continue
            self.node_list = self.page.locator('div[class^="node-list--"]')
            try:
                await self.node_list.wait_for(state="visible", timeout=500)
            except PlaywrightTimeoutError:
                print(f"说明当前 路径是空目录，自然也就没有 {part} 目录， 直接创建+进入...")
                await self.mkdir(part)
                loc = await self.find_by_wheel(part)
                await loc.click()
                continue


            # 1. 确保鼠标移动到 div 容器的中心，激活该区域的滚动事件
            box = await self.node_list.bounding_box(timeout=500)
            if not box:
                raise PlaywrightError("无法获取容器的边界，请确保容器在当前 Viewport 内可见。")
            
            center_x = box["x"] + box["width"] // 2
            center_y = box["y"] + box["height"] // 2
            await self.page.mouse.move(center_x, center_y)


            # 精确重定位到这个带滚动条的 div
            # 可以通过它的独有 class，或者结合 style 特征定位
            self.scroll_container = self.node_list.locator('div[class^="grid-scroll--"][style*="overflow"]')

            try:
                await self.scroll_container.wait_for(state="visible", timeout=500)
                print(f"当前位置有滚动条: {p2}")
                self.is_scroll = True
            except PlaywrightTimeoutError:
                # 当前没有滚动条
                self.is_scroll = False

            try:
                loc = await self.find_by_wheel(part)
            except ValueError as e:
                print(f"{e}\n没有找到目录: {p2}，自动创建。")
                await self.mkdir(part)
                loc = await self.find_by_wheel(part)
                # sys.exit(1)

            await loc.click()


    async def mkdir(self, text: str):

        await self.page.locator('div[class^="button--"][class*="adrive-create-button"]').click()

        await self.page.get_by_role("menu").get_by_text("新建文件夹", exact=True).click()

        # 1. 先定位到这个“新建文件夹”的弹窗大容器
        dialog = self.page.get_by_role("dialog", name="新建文件夹", exact=True)
        # 或者如果无障碍语义不够完美，也可以通过类名等锁定弹窗，比如：
        # dialog = page.locator(".modal-container")

        # 2. 在弹窗范围内，精准操作输入框
        # 这样哪怕背景页面有 100 个同名输入框，也绝对不会找错
        folder_input = dialog.get_by_role("textbox", exact=True)
        await folder_input.wait_for(state="visible")

        # 3. 顺手清除默认文字并输入新名字
        await folder_input.fill("")  # 如果原本有文字，先清空
        await folder_input.fill(text)

        # 4. 点击右下角的“确认”按钮
        # confirm_button = dialog.get_by_role("button", name="确认", exact=True)
        # await confirm_button.click()
        await self.page.get_by_role("button", name="确 认", exact=True).click()

        # 找到这个滚动条，返回顶端
        # 将滚动条位置直接设为 0，瞬间回到顶端
        await self.scroll_container.evaluate("(el) => el.scrollTop = 0")


    async def check_is_dir(self, loc: Locator) -> bool:

        # 先向上一层查找
        outer_handle1 = await loc.evaluate_handle(
            '''(el) => el.closest('div[class^="node-card--"]')'''
        )
        # 如果 closest 没找到，JS 会返回 null，Python 端表现为 outer_handle.as_element() 为 None
        if outer_element1 := outer_handle1.as_element():

            # 1. 传入当前的 inner_node，在浏览器内部向上查找最近的符合条件的 div
            outer_handle = await outer_element1.evaluate_handle(
                '''(el) => el.querySelector('div[class^="folder-cover--"]')'''
            )

            if outer_element := outer_handle.as_element():
                # 检查是否真的存在这样一个外层元素
                if await outer_element.is_visible():
                    print("成功定位到指定外层元素为 目录类型")
                    return True
                
                raise ValueError("""找到 div[class^="folder-cover--"] 但是 is_visiable() -> False""")
            
            else:
                # 这里又可能是文件类型
                outer_handle = await outer_element1.evaluate_handle(
                    '''(el) => el.querySelector('div[class^="file-cover--"]')'''
                )

                if outer_element := outer_handle.as_element():
                    if await outer_element.is_visible():
                        print("成功定位到指定外层元素为 文件类型")
                        return False

                raise ValueError("没找到区分当前名称是 文件 还是 文件夹 的class: div[class^='folder-cover--']")
        
        else:
            raise ValueError("没有找到上级div[class^='node-card--']")


    async def upload(self, filenames: list[Path]):

        # 这是上传的div按钮：网页右下角的上传按钮
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
        status_bar_wrapper = self.page.locator('div[class^="status-bar-wrapper--"]')
        await status_bar_wrapper.click()
        
        print(f"正在上传: {filenames}")
        
    
    async def wait_upload_done(self):

        print("开始轮询上传状态...")

        status_bar_wrapper = self.page.locator('div[class^="status-bar-wrapper--"]')
        # 上传小窗口的状态栏
        upload_status_bar = status_bar_wrapper.locator('span[class^="status-bar-title--"]')

        i = 1
        while True:
            # is_visible 不会报错，它会立即返回 True 或 False
            # 配合 timeout=500 确保检查过程极快

            # if await self.page.get_by_text("已上传至", exact=False).is_visible(timeout=500):
            if await upload_status_bar.get_by_text("上传完成", exact=True).is_visible(timeout=500):
                print("上传成功！")
                break
                
            # 可以在这里增加其他逻辑，比如检查是否“上传失败”
            if await self.page.get_by_text("上传失败", exact=True).is_visible(timeout=500):
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
    parse.add_argument("--user-data-dir", required=True, help="指定chrome实例的数据目录。")
    parse.add_argument("--netdisk-path", type=Path, default=Path("autoupload"), help="需要上传到阿里网盘的那个目录，默认值：autoupload")
    parse.add_argument("files", nargs="+", type=Path, help="要上传的文件")

    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)

    args = parse.parse_args()

    if args.parse:
        print(args)
        sys.exit(0)

    alipan = Alipan(args.user_data_dir, args.netdisk_path, args.files)

    asyncio.run(alipan.task_entry())


if __name__ == "__main__":
    main()
