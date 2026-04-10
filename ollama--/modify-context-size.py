
import base64

import ollama

MODEL_NAME="gemma4:e4b"

messages = [
    {
        'role': 'user',
        'content': '讲解下等差数列和等比数列',
        'num_ctx': 8192,
    }
]

client = ollama.Client(host="http://10.1.3.20:11434")

opt = {
        "num_ctx": 8192
        }

response = client.chat(
    model=MODEL_NAME,  # 替换为你的多模态模型
    messages=messages,
    #tools=tools,              # <--- 关键点：在这里传入工具列表
    options=opt,
    stream=False
)

message = response['message']
print("💬", message['content'])

