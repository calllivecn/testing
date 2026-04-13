
import sys
import base64

import ollama

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


MODEL_NAME="qwen3.5:9b"
MODEL_NAME="gemma4:e4b"

client = ollama.Client(host="http://10.1.3.20:11434")

try:
    q = sys.argv[1]
except IndexError:
    q = '介绍下ollama项目'

messages = [
       {'role': 'user', 'content': q},
        ]


#opt = {'num_ctx': 8192}
opt = {'num_ctx': 16384}


stream = client.chat(
    model=MODEL_NAME,
    messages=messages,
    options=opt,
    #think=True,  # ollama中如果模型支持think。默认就是启用的
    stream=True,
)

think = True
last_chunk = None  # 保存最后一个 chunk 用于统计

for chunk in stream:

    # 检查是否包含统计信息（最后一个 chunk 的特征）
    if 'eval_count' in chunk or 'total_duration' in chunk:
        last_chunk = chunk  # 保存完整统计信息

    message = chunk.message

    # 检查是否存在思考内容 (Thinking)
    if thinking := message.get('thinking'):
        print(f"\033[90m{thinking}\033[0m", end="", flush=True)

    if content := message.get('content'):

        if not message.thinking and think:
            think = False
            print("\n", "+"*20, "思考结束", "+"*20, "\n")

        print(content, end='', flush=True)



print("\n", "="*20, "token相关性能指标", "="*20, "\n")
calculate_speed(last_chunk)

