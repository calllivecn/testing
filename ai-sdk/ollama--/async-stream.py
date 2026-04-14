
import asyncio
from ollama import AsyncClient

async def stream_chat():
    message = {'role': 'user', 'content': '写一首关于 Linux 的短诗。'}
    
    # 异步迭代获取每个 token
    async for part in await AsyncClient().chat(model='gemma4:e4b', messages=[message], stream=True):
        print(part['message']['content'], end='', flush=True)

asyncio.run(stream_chat())

