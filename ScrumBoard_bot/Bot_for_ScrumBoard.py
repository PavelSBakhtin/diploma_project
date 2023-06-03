import time
import logging
from aiogram import Bot, Dispatcher, executor, types

# 'UTF-8-sig'
logging.basicConfig(level=logging.INFO, filename="bot_log.csv", filemode="w",
                    format="%(asctime)s: %(levelname)s %(funcName)s-%(lineno)d %(message)s")

with open("key.txt", "r") as f:
    text = f.readline()
TOKEN = str(text)
MSG = "{}, choose an action:"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot)

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    user_full_name = message.from_user.full_name
    user_bot = message.from_user.is_bot
    user_message = message.text
    logging.info(f'{user_id=} {user_bot=} {user_message=}')
    await message.reply(f"Hi, {user_full_name}!")
    time.sleep(1)
    btns = types.ReplyKeyboardMarkup(row_width=2)
    btn_opt = types.KeyboardButton('/options')
    btn_out = types.KeyboardButton('/quit')
    btns.add(btn_opt, btn_out)
    await bot.send_message(user_id, MSG.format(user_name), reply_markup=btns)

@dp.message_handler(commands=['options'])
async def start_handler(message: types.Message):
    await bot.send_message(message.from_user.id, "select an option:")
    if value == "":
        await bot.send_message(message.from_user.id, "", reply_markup=keyboard)
    else:
        await bot.send_message(message.from_user.id, value, reply_markup=keyboard)

@dp.message_handler(commands=['quit'])
async def quit_handler(message: types.Message):
    await bot.send_message(message.from_user.id, 'Goodbye! See you...',
                           reply_markup=types.ReplyKeyboardRemove())

value = ""
old_value = ""
keyboard = types.InlineKeyboardMarkup()
keyboard.row(types.InlineKeyboardButton("tasks", callback_data="tasks"),
             types.InlineKeyboardButton("new task", callback_data="new task"))

@dp.callback_query_handler(lambda c: True)
async def callback_calc(query):

    global value, old_value
    data = query.data

    if data == "tasks":
        value = "your tasks now"
    if data == "new task":
        value = "add a new task"

if __name__ == '__main__':
    executor.start_polling(dp)
