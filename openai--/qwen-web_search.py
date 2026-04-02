

import os
from openai import OpenAI

client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
completion = client.chat.completions.create(
    #model="qwen3.5-plus",
    #model="qwen3.5-flash",
    model="qwen3.5-plus-2026-02-15",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        #{"role": "user", "content": "LLM中的embed，好你是叫这个名。说它是本地记忆？那在LLM的调用中使用它和不使用它。是不是消耗的token会不一样？"},
        {"role": "user", "content": "讲解下openclaw是怎么把skill 和 tool 。还有channel 和 agent model这些角色统一在一起工作的吧。"}
    ],
    extra_body={"enable_search": True,
                "enable_thinking": True
                }
)
print(completion.choices[0].message.content)

