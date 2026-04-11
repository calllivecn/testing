
import base64

import ollama

MODEL_NAME="qwen3.5:9b"
MODEL_NAME="gemma4:e4b"

client = ollama.Client(host="http://10.1.3.20:11434")

stream = client.chat(
    model=MODEL_NAME,
    messages=[{'role': 'user', 'content': '写一篇关于 Linux 内核的长文'}],
    stream=True,
)

for chunk in stream:
    print(chunk['message']['content'], end='', flush=True)

