import logging
import bot_markups as mks
from bot_db import Database
from aiogram import Bot, Dispatcher, executor
from aiogram.types import ReplyKeyboardRemove, Message, CallbackQuery
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext


logging.basicConfig(level=logging.INFO, filename='bot_log.csv', filemode='a',
                    format='%(asctime)s: %(levelname)s %(funcName)s-%(lineno)d %(message)s')

with open('key.txt', 'r') as f:
    text = f.readline()
TOKEN = str(text)
MSG = '{}, choose an action'

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot, storage=MemoryStorage())
db = Database('users_db.csv')
login_status = False
start_status = False
lgn = ''


@dp.message_handler(commands=['start'])
async def start_handler(message: Message):
    global start_status
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    user_full_name = message.from_user.full_name
    user_bot = message.from_user.is_bot
    user_message = message.text
    logging.info(f'{user_id=} {user_bot=} {user_message=}')
    await message.reply(f'Hi, {user_full_name}!')
    start_status = True
    await bot.send_message(user_id, MSG.format(user_name), reply_markup=mks.button)


class Form(StatesGroup):
    login_user = State()
    password_user = State()


@dp.message_handler(commands=['login'])
async def login_handler(message: Message):
    global start_status
    if start_status == True:
        user_id = message.from_user.id
        await Form.login_user.set()
        await bot.send_message(user_id, 'enter login:')


@dp.message_handler(state=Form.login_user)
async def login_text(message: Message, state: FSMContext):
    user_id = message.from_user.id
    async with state.proxy() as data:
        data['login_user'] = message.text
    await Form.next()
    await bot.send_message(user_id, 'enter password:')


@dp.message_handler(state=Form.password_user)
async def password_text(message: Message, state: FSMContext):
    global lgn
    global login_status
    user_name = message.from_user.first_name
    user_id = message.from_user.id
    async with state.proxy() as data:
        data['password_user'] = message.text
    # await bot.send_message(user_id, data['login_user'])
    # await bot.send_message(user_id, data['password_user'])
    lgn = data['login_user']
    pswd = data['password_user']
    await state.finish()
    # await bot.send_message(user_id, f'{lgn}, {pswd}')
    if db.user_logining(lgn, pswd) == True:
        login_status = True
        await bot.send_message(user_id, MSG.format(user_name), reply_markup=mks.buttons)
    else:
        await bot.send_message(
            user_id, 'The login or password is entered incorrectly,\nor such user does not exist')


@dp.message_handler(commands=['options'])
async def options_handler(message: Message):
    global login_status
    if login_status == True:
        await bot.send_message(message.from_user.id, 'select an option:', reply_markup=mks.keyboard)


@dp.message_handler(commands=['quit'])
async def quit_handler(message: Message):
    global login_status
    global start_status
    await bot.send_message(message.from_user.id, 'Goodbye! See you...',
                           reply_markup=ReplyKeyboardRemove())
    login_status = False
    start_status = False
    await bot.delete_webhook(drop_pending_updates=True)


@dp.message_handler()
async def data_handler(message: Message, data):
    # text = *data
    await bot.send_message(message.from_user.id, data)


value = ""
old_value = ""


@dp.callback_query_handler(lambda call: True)
async def callback_options(query: CallbackQuery):

    global value, old_value
    data = query.data
    global lgn

    if data == 'tasks':
        value = 'your tasks now'
        await bot.edit_message_text(chat_id=query.message.chat.id,
                                    message_id=query.message.message_id,
                                    text=value, reply_markup=mks.keyboard_next)
        old_value = value
        value = ""

    elif data == 'new task':
        value = 'add a new task'
        await bot.edit_message_text(chat_id=query.message.chat.id,
                                    message_id=query.message.message_id,
                                    text=value, reply_markup=mks.keyboard_new)
        old_value = value
        value = ""

    elif data == 'task 1':
        value = 'your task 1:'
        res = db.user_task(lgn)
        await bot.edit_message_text(chat_id=query.message.chat.id,
                                    message_id=query.message.message_id,
                                    text=res, reply_markup=None)
        old_value = value
        value = ""


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
