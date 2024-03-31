#!/usr/bin/env python3
# coding=utf-8
# date 2023-12-03 02:36:23
# author calllivecn <calllivecn@outlook.com>

import apikey


import logging

from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
#logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.WARNING)

logging.getLogger("httpx").setLevel(logging.WARNING)




help_text="""\
可用命令:
/help   发送些帮助信息
/about 关于
/test 测试
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="这是第一个机器人")

async def help_func(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)

async def about(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"""这是我今天(2023-12-03 02:00)创建的机器人""")

async def test(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"""看到这个说明测试成功""")

async def argument(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"""这是参数: {context.args}""")


async def echo(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

async def message_handler_function(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Custom reply to message: '{update.message.text}'")


async def error_handler_function(update, context):
    print(f"Update: {update} caused error: {context.error}")


def main():
    application = ApplicationBuilder().token(apikey.APIKEY).build()
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    application.add_handler(CommandHandler('help', help_func))
    application.add_handler(CommandHandler('about', about))
    application.add_handler(CommandHandler('test', test))
    application.add_handler(CommandHandler('argument', argument))

    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    application.add_handler(echo_handler)

    application.run_polling()


if __name__ == '__main__':
	main()
