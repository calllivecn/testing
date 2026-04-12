#!/usr/bin/env python3
# coding=utf-8
# 基于 chatgpt.py 架构，使用阿里云百炼 API

import os
import copy
import json
import time
import random
import readline
import argparse
from pathlib import Path
from pprint import pprint

from openai import OpenAI


# 初始化客户端
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)


# 可用模型列表
AVAILABLE_MODELS = [
    "qwen3.5-plus-2026-02-15",
    "qwen3.5-flash",
    "qwen3.5-plus",
    "qwen-plus",
    "glm-5",
]

# 默认模型
DEFAULT_MODEL = "qwen-plus"


# 定义工具列表
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "当你想查询指定城市的天气时非常有用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市或县区，比如北京市、杭州市、余杭区等。",
                    }
                },
                "required": ["location"],
            },
        },
    },
]


# 模拟天气查询工具
def get_current_weather(arguments):
    weather_conditions = ["晴天", "多云", "雨天", "阴天", "小雨"]
    random_weather = random.choice(weather_conditions)
    location = arguments.get("location", "未知地区")
    return f"{location}今天是{random_weather}。"


class QwenChat:

    def __init__(self, context_json: Path = Path("default.json")):

        self._debug = False
        self.current_model = DEFAULT_MODEL

        if isinstance(context_json, str):
            self.context_json = Path(context_json)
        
        elif isinstance(context_json, Path):
            self.context_json = context_json

        if self.context_json.exists():
            with open(self.context_json, "r", encoding="utf-8") as f:
                self.messages = json.load(f)
        else:
            self.messages = [{"role": "system", "content": "你是一个乐于助人的助手，可以查询天气信息。"}]

    def list_models(self):
        """列出所有可用模型"""
        print("=" * 20, "可用模型列表", "=" * 20)
        for i, model in enumerate(AVAILABLE_MODELS, 1):
            current_marker = " (当前)" if model == self.current_model else ""
            print(f"{i}. {model}{current_marker}")
        print("=" * 20)

    def set_model(self, model_name):
        """切换模型"""
        if model_name in AVAILABLE_MODELS:
            self.current_model = model_name
            print(f"已切换到模型：{model_name}")
        else:
            print(f"模型 '{model_name}' 不存在。可用模型：")
            self.list_models()

    def get_response(self, messages, use_tools=False, model=None, stream=True):
        """调用阿里云百炼 API 获取响应"""
        use_model = model if model else self.current_model
        
        kwargs = {
            "model": use_model,
            "messages": messages,
        }
        
        if use_tools:
            kwargs["tools"] = TOOLS
        
        if stream:
            kwargs["stream"] = True
            completion = client.chat.completions.create(**kwargs)
            
            # 累积内容
            accumulated_content = ""
            accumulated_tool_calls = []
            reasoning_content = ""
            
            for chunk in completion:
                if not chunk.choices:
                    continue
                
                delta = chunk.choices[0].delta
                
                # 提取推理内容
                reasoning = getattr(delta, 'reasoning_content', None)
                if reasoning:
                    reasoning_content += reasoning
                    if self._debug:
                        print(f"\033[90m{reasoning}\033[0m", end="", flush=True)
                
                # 提取正式回答
                content = getattr(delta, 'content', None)
                if content:
                    accumulated_content += content
                    print(content, end="", flush=True)
                
                # 提取工具调用
                if getattr(delta, 'tool_calls', None):
                    for tc in delta.tool_calls:
                        # 如果是新的工具调用
                        if tc.index >= len(accumulated_tool_calls):
                            accumulated_tool_calls.append({
                                'id': tc.id,
                                'type': tc.type,
                                'function': {
                                    'name': tc.function.name if hasattr(tc.function, 'name') else '',
                                    'arguments': tc.function.arguments if hasattr(tc.function, 'arguments') else ''
                                }
                            })
                        else:
                            # 累积参数
                            accumulated_tool_calls[tc.index]['function']['arguments'] += tc.function.arguments
            
            print()  # 换行
            
            # 构建完整的 message 对象
            class Message:
                def __init__(self, content, tool_calls):
                    self.content = content if content else None
                    self.tool_calls = tool_calls if tool_calls else None
            
            # 转换工具调用格式
            final_tool_calls = None
            if accumulated_tool_calls:
                class ToolCall:
                    def __init__(self, tc):
                        self.id = tc['id']
                        self.type = tc['type']
                        class Function:
                            def __init__(self, name, arguments):
                                self.name = name
                                self.arguments = arguments
                        self.function = Function(tc['function']['name'], tc['function']['arguments'])
                
                final_tool_calls = [ToolCall(tc) for tc in accumulated_tool_calls]
            
            msg = Message(accumulated_content, final_tool_calls)
            return msg
        else:
            kwargs["stream"] = False
            completion = client.chat.completions.create(**kwargs)
            return completion.choices[0].message

    def chat(self, prompt, model=None):
        """处理用户输入并获取回复，支持工具调用"""
        
        # 使用当前设置的模型，或临时指定的模型
        use_model = model if model else self.current_model

        self.messages.append({"role": "user", "content": prompt})

        # 第一次调用模型（流式模式）
        msg = self.get_response(self.messages, use_tools=True, model=use_model, stream=True)

        # 处理 tool_calls
        if msg.tool_calls is not None:
            # 进入工具调用循环
            while msg.tool_calls is not None:
                tool_call = msg.tool_calls[0]
                tool_call_id = tool_call.id
                func_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                if self._debug:
                    print(f"[调试] 正在调用工具 [{func_name}]，参数：{arguments}")
                
                # 执行工具
                if func_name == "get_current_weather":
                    tool_result = get_current_weather(arguments)
                else:
                    tool_result = f"未知工具：{func_name}"
                
                if self._debug:
                    print(f"[调试] 工具返回：{tool_result}")
                
                # 构造工具返回信息
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": tool_result,
                }
                self.messages.append(tool_message)
                
                # 再次调用模型，获取总结后的自然语言回复（非流式，因为工具调用后需要完整响应）
                msg = self.get_response(self.messages, use_tools=False, model=use_model, stream=False)
                
                if msg.content is None:
                    msg.content = ""
        else:
            if msg.content is None:
                msg.content = ""

        # 保存助手回复到上下文
        self.messages.append({"role": "assistant", "content": msg.content})

        return msg.content

    def list_context(self):
        print("=" * 20, "上下文", "=" * 20)
        for msg in self.messages:
            print("=" * 20, msg["role"], "=" * 20)
            print(msg["content"])

    def debug(self):
        if self._debug:
            self._debug = False
            print("调试模式关闭")
        else:
            self._debug = True
            print("调试模式打开")

    def close(self):
        with open(self.context_json, "w", encoding="utf-8") as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=4)


def main():

    parse = argparse.ArgumentParser(
        usage="%(prog)s [--context <default.json>]"
    )

    parse.add_argument("--context", action="store", default="qwen_context.json", 
                       help="指定一个保存上下文的 json 文件。(qwen_context.json)")
    args = parse.parse_args()

    qwen_chat = QwenChat(args.context)

    print("=" * 20, "Qwen 聊天助手", "=" * 20)
    print("可用命令：/quit (退出), /list (查看上下文), /debug (调试模式), /clear (清空上下文), /model (切换模型)")
    print("=" * 20)

    while True:
        print("=" * 20, "请输入新的问题：", "=" * 20)

        prompt = input("输入：")

        if prompt.startswith("/"):
            if prompt == "/quit":
                print("退出")
                break

            elif prompt == "/list":
                qwen_chat.list_context()
                continue
            
            elif prompt == "/debug":
                qwen_chat.debug()
                continue
            
            elif prompt == "/clear":
                qwen_chat.messages = [{"role": "system", "content": "你是一个乐于助人的助手，可以查询天气信息。"}]
                print("上下文已清空")
                continue
            
            elif prompt == "/model":
                qwen_chat.list_models()
                print("使用方法：/model <模型名称>  或  /model <序号>")
                continue
            
            elif prompt.startswith("/model "):
                model_arg = prompt[7:].strip()
                # 支持通过序号切换
                if model_arg.isdigit():
                    idx = int(model_arg) - 1
                    if 0 <= idx < len(AVAILABLE_MODELS):
                        qwen_chat.set_model(AVAILABLE_MODELS[idx])
                    else:
                        print(f"无效序号，请输入 1-{len(AVAILABLE_MODELS)}")
                else:
                    qwen_chat.set_model(model_arg)
                continue
            
            else:
                print("未知指令。可用命令：/quit, /list, /debug, /clear, /model")
                continue

        elif prompt == "":
            continue

        print("=" * 20, "回答", "=" * 20)
        print(qwen_chat.chat(prompt))

    qwen_chat.close()


if __name__ == "__main__":
    main()
