#!/usr/bin/env python3
# coding=utf-8
# date 2023-04-19 04:54:08
# author calllivecn <c-all@qq.com>

import os
import copy
import json
import time
import readline
import argparse
from pathlib import Path
from pprint import pprint

import openai

openai.api_key = "YOUR_API_KEY"
openai.api_key = os.environ.get("OPENAI_TOKEN")

def generate_text(prompt):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.7,
    )

    message = response.choices[0].text
    return message.strip()


class ChatGPT:

    def __init__(self, context_json: Path =[]):

        self._debug = False

        if isinstance(context_json, str):
            self.context_json = Path(context_json)
        
        elif isinstance(context_json, Path):
            self.context_json = context_json

        if self.context_json.exists():
            with open(self.context_json) as f:
                self.messages = json.load(f)
        else:
            self.messages = []


    def chatgpt35(self, prompt):

        self.messages.append({"role": "user", "content": prompt})

        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=self.messages)

        # print("completion:", type(completion), dir(completion))

        msg = completion.choices[0].message

        self.messages.append(dict(copy.copy(msg)))

        content = msg.get("content")
        # 清理下 messages 为减少调度输出清理下
        msg.content = "clear"

        if self._debug:
            print("-"*20, "调试信息", "-"*20)
            pprint(completion)
            print("-"*20, "调试信息", "-"*20)

        return content
    

    def list_context(self):
        print("="*20, "上下文", "="*20)
        # pprint(self.messages)
        for msg in self.messages:
            print("="*20, msg["role"], "="*20)
            print(msg["content"])
    
    def debug(self):
        if self._debug:
            self._debug = False
            print("调试模式关闭")
        else:
            self._debug = True
            print("调试模式打开")


    def command(self, cmd):
        pass
    

    def close(self):
        with open(self.context_json, "w") as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=4)


def main():

    parse = argparse.ArgumentParser(
        usage="%(prog)s [--context <default.json>]"
    )

    parse.add_argument("--context", action="store", default="default.json", help="指定一个保存上下文的json文件。(default.josn)")
    args = parse.parse_args()

    gpt35 = ChatGPT(args.context)

    while True:
        print("="*20, "请输入新的问题：", "="*20)

        prompt = input("输入: ")

        if prompt.startswith("/"):
            if prompt == "/quit":
                print("退出")
                break

            elif prompt == "/list":
                gpt35.list_context()
                continue
            
            elif prompt == "/debug":
                gpt35.debug()
                continue
            
            else:
                print("未知指令.")
                continue


        elif prompt == "":
            continue

        print("="*20, "回答", "="*20)
        print(gpt35.chatgpt35(prompt))
    

    gpt35.close()


if __name__ == "__main__":
    main()