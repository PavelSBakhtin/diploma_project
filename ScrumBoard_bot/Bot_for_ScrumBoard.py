import time
import logging
from aiogram import Bot, Dispatcher, executor, types

# 'UTF-8-sig'
logging.basicConfig(level=logging.INFO, filename="bot_log.csv", filemode="w",
                    format="%(asctime)s: %(levelname)s %(funcName)s-%(lineno)d %(message)s")

with open("info.txt", "r") as f:
    text = f.readline()
TOKEN = str(text)
MSG = "{}, choose an action:"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot)
