
import base64

import ollama

MODEL_NAME="gemma4:e4b"
MODEL_NAME="gemma4:12b-it-q8_0"

# --- 第一步：定义工具 (Tools) ---
def calculate_discount(original_price: int, discount_rate: int) -> int:
    """
    计算商品打折后的最终价格。当用户询问总价或折扣时使用。
    args:
        original_price: 商品的原始价格
        discount_rate: 折扣率 (例如 0.8 代表八折)
    """
    return original_price * discount_rate


TOOLS=[
    calculate_discount,
]

system_prompt="""
你是一名桌面行为识别助手，仅基于当前截图分析用户**正在执行的具体操作**。请严格按以下规则输出JSON：
{
  "timestamp": "精确到分钟的时间戳（格式：YYYY-MM-DD HH:MM）",
  "primary_app": "**最显著窗口的软件名称**（如Chrome、VSCode、Excel）",
  "visible_content": "屏幕上**直接可见的关键元素**（限30字内，如'GitHub提交记录页面'、'PPT第5页编辑状态'）",
  "user_action": "用户**当前物理动作**（如'打字'、'滑动鼠标'、'观看视频'）",
  "confidence": "置信度（0-100，若截图模糊或内容不明确需降低）"
}
**禁止**：
- 推测用户意图（如'用户在准备会议'）
- 描述截图外的背景信息
- 输出任何额外解释
这是截图文件名，也是时间点：{screenshot_time}
"""

# --- 第二步：准备图片 ---
# 方法 A: 直接传本地路径 (Ollama Python 库 0.2.0+ 支持)
#image_path = 'product_price.jpg'
image_path = '20260606_232559.png'

# 方法 B: 内存中图片转成Base64
with open(image_path, 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')



# --- 第三步：构建消息 ---
messages = [
    {
        'role': 'user',
        'content': system_prompt + "\n这是截图文件名，也是时间点：{image_path}" ,
        'images': [image_path]  # <--- 关键点：在这里传入图片列表
    }
]

# --- 第四步：发起调用 ---
print("🤖 模型正在看图并思考...")

client = ollama.Client(host="http://10.1.3.20:11434")

response = client.chat(
    model=MODEL_NAME,  # 替换为你的多模态模型
    messages=messages,
    #tools=TOOLS,              # <--- 关键点：在这里传入工具列表
    stream=False
)

# --- 第五步：处理响应 ---
message = response['message']

# 情况 A: 模型直接回答了 (没有调用工具)
if 'content' in message and message['content']:
    print("💬 模型回答:", message['content'])

# 情况 B: 模型决定调用工具
if 'tool_calls' in message:
    print("🛠️ 模型请求调用工具:")
    for tool_call in message['tool_calls']:
        func_name = tool_call['function']['name']
        args = tool_call['function']['arguments']
        
        print(f"   - 函数名: {func_name}")
        print(f"   - 参数: {args}")
        
        # --- 第六步：执行实际逻辑 (Mock) ---
        if func_name == 'calculate_discount':
            price = args.get('original_price')
            rate = args.get('discount_rate')
            final_price = price * rate
            
            print(f"   ✅ 本地执行计算: {price} * {rate} = {final_price}")
            
            # (可选) 如果你想让模型基于计算结果继续回答，需要将结果回传给模型
            # 见下方的 "多轮对话进阶" 部分

    # 接上面的代码...
    
if 'tool_calls' in message:
    # 1. 把模型的请求加入历史消息
    messages.append(message) 
    
    # 2. 执行工具逻辑 (模拟)
    tool_result = 0
    for tc in message['tool_calls']:
        if tc['function']['name'] == 'calculate_discount':
            p = tc['function']['arguments']['original_price']
            r = tc['function']['arguments']['discount_rate']
            tool_result = p * r
    
    # 3. 构造工具返回的消息 (Role 必须是 'tool')
    tool_message = {
        'role': 'tool',
        'content': str(tool_result), # 工具执行的结果
        'tool_call_id': message['tool_calls'][0].get('id', '') # 某些版本需要关联 ID，通常 ollama 会自动处理对应关系，只需 role: tool
    }
    
    # 注意：Ollama 的 tool 响应格式可能因版本略有不同，
    # 最通用的方式是将结果作为 user 或 tool 角色放入 messages
    messages.append({
        'role': 'tool',
        'content': f"计算结果是: {tool_result} 元"
    })

    # 4. 再次调用模型，让它根据结果回答
    print("\n🤖 模型正在根据计算结果生成最终回复...")
    final_response = client.chat(
        model=MODEL_NAME,
        messages=messages,
        tools=TOOLS
    )
    
    print("💬 最终回答:", final_response['message']['content'])

