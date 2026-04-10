
import base64

import ollama

MODEL_NAME="qwen3.5:9b"
MODEL_NAME="gemma4:e4b"

# --- 第一步：定义工具 (Tools) ---
# 格式必须遵循 JSON Schema 标准
tools = [
    {
        'type': 'function',
        'function': {
            'name': 'calculate_discount',
            'description': '计算商品打折后的最终价格。当用户询问总价或折扣时使用。',
            'parameters': {
                'type': 'object',
                'properties': {
                    'original_price': {
                        'type': 'number',
                        'description': '商品的原始价格'
                    },
                    'discount_rate': {
                        'type': 'number',
                        'description': '折扣率 (例如 0.8 代表八折)'
                    }
                },
                'required': ['original_price', 'discount_rate']
            }
        }
    }
]

# --- 第二步：准备图片 ---
# 方法 A: 直接传本地路径 (Ollama Python 库 0.2.0+ 支持)
image_path = 'product_price.jpg'
image_path = '2026-03-14 17-35-01.png'

# 方法 B: 内存中图片转成Base64
# with open(image_path, 'rb') as f:
#     image_data = base64.b64encode(f.read()).decode('utf-8')

# --- 第三步：构建消息 ---
messages = [
    {
        'role': 'user',
        'content': '请查看这张图片，识别出商品的原始价格。如果原价超过 100 元，请调用 calculate_discount 工具计算打 8 折后的价格。',
        'images': [image_path]  # <--- 关键点：在这里传入图片列表
    }
]

# --- 第四步：发起调用 ---
print("🤖 模型正在看图并思考...")

client = ollama.Client(host="http://10.1.3.20:11434")

response = client.chat(
    model=MODEL_NAME,  # 替换为你的多模态模型
    messages=messages,
    tools=tools,              # <--- 关键点：在这里传入工具列表
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
        tools=tools
    )
    
    print("💬 最终回答:", final_response['message']['content'])

