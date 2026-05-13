
# 更专业的技巧（针对高级用户）
# 由于你是资深用户，处理 Google 页面时建议注意以下几点：

# A. 伪装 User-Agent
# Google 会检测 Playwright 默认的 User-Agent。如果发现被屏蔽，请在启动时设置：

context = await browser.new_context(
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# B. 智能等待 networkidle
# 有时仅仅元素出现是不够的，如果页面有大量的异步加载（如图片或侧边栏），可以使用：

await page.wait_for_load_state("networkidle") # 等待网络请求停止（500ms内无新请求）

# C. 获取摘要的另一种思路
# Google 的摘要文字通常放在一个类名为 VwiC3b 的 div 中。虽然类名会变，但你可以通过父子关系定位：
# 找到 h3 之后，找它同级或下方的第一个描述性容器
summary = await block.locator(".VwiC3b").inner_text()