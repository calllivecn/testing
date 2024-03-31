#!/usr/bin/env python3
# coding=utf-8
# date 2023-12-03 02:36:23
# author calllivecn <calllivecn@outlook.com>


import time
import asyncio
import logging

from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
#logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.WARNING)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


import apikey


help_text="""\
可用命令:
/help   发送些帮助信息
/about 关于
/test 测试
/argument 测试带参数的命令
/push 测试Bot主动向用户发消息
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="这是第一个机器人")

async def help_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"""这是我今天(2023-12-03 02:00)创建的机器人""")

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"""看到这个说明测试成功""")

async def argument(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"{update.effective_chat.id=}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"""这是参数: {context.args}""")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Custom reply to message: '{update.message.text}'")
    await update.message.reply_text(text=f"echo: '{update.message.text}'")


async def push_task(send_message, chat_id):
    count=10
    for i in range(count):
        await send_message(chat_id=chat_id, text=f"({i}/{count})主动push消息测试: '当前时间:{time.localtime()}'")
        await asyncio.sleep(30)
    
    print("这是完成标志")


async def push(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # update.messge.chat_id
    print(f"{update.effective_user.name=} | {update.effective_user.username=} | {update.effective_user.id=}")

    user = update.effective_user

    if user.username == "calllive":
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"管理员({user.username})，你好")
        asyncio.create_task(push_task(context.bot.send_message, update.effective_chat.id))

    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"你好{user.username}, 你不是管理员")



def main():
    app = ApplicationBuilder().token(apikey.APIKEY).build()
    
    start_handler = CommandHandler('start', start)
    app.add_handler(start_handler)

    app.add_handler(CommandHandler('help', help_func))
    app.add_handler(CommandHandler('about', about))
    app.add_handler(CommandHandler('test', test))
    app.add_handler(CommandHandler('argument', argument))
    app.add_handler(CommandHandler('push', push))

    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    app.add_handler(echo_handler)

    app.run_polling()

    """
    # 这样不行
    try:
        app.run_polling()
    except KeyboardInterrupt:
        app.stop()
    """


if __name__ == '__main__':
	main()
