import logging
import bot_markups as mks
from aiogram import Bot, Dispatcher, executor
from aiogram.types import ReplyKeyboardRemove, Message, CallbackQuery
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
import requests


logging.basicConfig(level=logging.INFO, filename='bot_log.txt', filemode='a',  # 'utf-8',
                    format='%(asctime)s: %(levelname)s %(funcName)s-%(lineno)d %(message)s')

with open('key.txt', 'r') as f:
    text = f.readline()
TOKEN = str(text)
MSG = '{}, choose an action'

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot, storage=MemoryStorage())

# вставить ассинк далее
login_status = False
start_status = False
lgn = ''
upline_all = []
upline_shot = []


@dp.message_handler(commands=['start'])
async def start_handler(message: Message):
    global start_status
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    user_full_name = message.from_user.full_name
    user_bot = message.from_user.is_bot
    user_message = message.text
    logging.info(f'{user_id=}, {user_bot=}, {user_message=}')
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
    user_message = message.text
    msg_id = message.message_id
    logging.info(f'{user_id=}, {msg_id=}, {user_message=}')
    async with state.proxy() as data:
        data['login_user'] = message.text
    await Form.next()
    await bot.send_message(user_id, 'enter password:')


@dp.message_handler(state=Form.password_user)
async def password_text(message: Message, state: FSMContext):
    global lgn
    global login_status
    global upline_all
    global upline_shot
    user_name = message.from_user.first_name
    user_id = message.from_user.id
    user_message = message.text
    msg_id = message.message_id
    logging.info(f'{user_id=}, {msg_id=}, {user_message=}')
    async with state.proxy() as data:
        data['password_user'] = message.text
    lgn = data['login_user']
    pswd = data['password_user']
    await state.finish()
    new_text = len(user_message) * '*'
    for i in range(4):
        await bot.delete_message(user_id, msg_id-i)
    await bot.send_message(user_id, f'Data accepted:\n{lgn}, {new_text}')

    # Запрос к Django api/token для получения ответа:
    url = "http://localhost:8000/api/token/bot/"
    data_sing = {"email": lgn, "password": pswd}
    response_sing = requests.post(url, data_sing)

    # Обработка ответа от Django:
    if response_sing.status_code == 200:
        # Аутентификация прошла успешно:
        logging.info(f'{user_id=}, Successful authorization')
        response_data = response_sing.json()
        access_token = response_data['access']
        refresh_token = response_data['refresh']
        user_login_id = response_data['id']
        login_status = True
        logging.info(f'{user_id=}, Loaded info: {response_data}')
        await bot.send_message(user_id, 'Successful authorization')
        await bot.send_message(user_id, MSG.format(user_name), reply_markup=mks.buttons)

        # Запрос к Django api/v1/task для получения списка заданий:
        url = "http://127.0.0.1:8000/api/v1/task/"
        response_tasks = requests.get(url, access_token)

        if response_tasks.status_code == 200:
            # Аутентификация прошла успешно:
            logging.info(f'{user_id=}, Data loaded')
            response_list = response_tasks.json()

            for i in response_list:
                upline_all.append(f"task id :{ i['id']}\nName : {i['user_first_name']}\nLast Name : {i['user_last_name']}\nUser id : {i['user']}\nDescription : {i['description']}\nStatus : {i['status']}")
                logging.info(f'{user_id=}, Description loaded successfully: {i}')

            for j in response_list:
                if user_login_id == j['user'] and j['id'] not in upline_shot:
                    upline_shot.append(f"task id :{ j['id']}\nName : {j['user_first_name']}\nLast Name : {j['user_last_name']}\nUser id : {j['user']}\nDescription : {j['description']}\nStatus : {j['status']}")
                    logging.info(f'{user_id=}, Description loaded successfully: {j}')

        else:
            # Аутентификация не удалась:
            logging.info(f'{user_id=}, Error: {response_tasks.status_code}')
            await bot.send_message(user_id, 'Data not loaded')

    else:
        # Аутентификация не удалась:
        logging.info(f'{user_id=}, Error: {response_sing.status_code}')
        await bot.send_message(
            user_id, 'The login or password is entered incorrectly,\nor such user does not exist')


@dp.message_handler(commands=['menu'])
async def options_handler(message: Message):
    global login_status
    if login_status == True:
        await bot.send_message(message.from_user.id, 'select from the menu:', reply_markup=mks.keyboard)


@dp.message_handler(commands=['quit'])
async def quit_handler(message: Message):
    global login_status
    global start_status
    global lgn
    global upline_all
    global upline_shot
    await bot.send_message(message.from_user.id, 'Goodbye! See you...',
                           reply_markup=ReplyKeyboardRemove())
    login_status = False
    start_status = False
    lgn = ''
    upline_all = []
    upline_shot = []
    await bot.delete_webhook(drop_pending_updates=True)


def dict_tasks(upline_shot):
    tasks_dict = {}
    count = 1
    for i in upline_shot:
        tasks_dict[f'task {count}'] = i
        count += 1
    return tasks_dict


@dp.message_handler()
async def data_handler(message: Message, data):
    await bot.send_message(message.from_user.id, data)


value = ""
old_value = ""


@dp.callback_query_handler(lambda call: True)
async def callback_options(query: CallbackQuery):

    global value, old_value
    data = query.data
    global lgn
    global upline_all
    global upline_shot

    if data == 'my tasks':
        if len(upline_shot) == 0:
            await bot.send_message(chat_id=query.message.chat.id,
                                   text='You have no current tasks')
        else:
            value = 'your tasks now:'
            await bot.edit_message_text(chat_id=query.message.chat.id,
                                        message_id=query.message.message_id, text=value,
                                        reply_markup=await mks.create_keyboard_tasks(upline_shot))
            old_value = value
            value = ""

    elif data == 'all tasks':
        if len(upline_all) == 0:
            await bot.send_message(chat_id=query.message.chat.id,
                                   text='You have no current tasks')
        else:
            value = 'all tasks now:'
            await bot.edit_message_text(chat_id=query.message.chat.id,
                                        message_id=query.message.message_id,
                                        text=value, reply_markup=None)
            for i in upline_all:
                await bot.send_message(chat_id=query.message.chat.id, text=f'{i}')
            old_value = value
            value = ""

    elif data in list(dict_tasks(upline_shot).keys()):
        value = f'your {data}:'
        result = dict_tasks(upline_shot).get(data)
        await bot.edit_message_text(chat_id=query.message.chat.id,
                                    message_id=query.message.message_id,
                                    text=value, reply_markup=None)
        await bot.send_message(chat_id=query.message.chat.id, text=result)
        old_value = value
        value = ""
        await bot.send_message(chat_id=query.message.chat.id, text='Return to task list:',
                               reply_markup=mks.keyboard_my_tasks)

    else:
        value = 'Something went wrong, use the "menu" button'
        await bot.edit_message_text(chat_id=query.message.chat.id,
                                    message_id=query.message.message_id,
                                    text=value, reply_markup=None)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
