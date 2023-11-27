import logging
import bot_markups as mks
from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, Message, CallbackQuery
from bot_mfuncs import sing_in, tasks_load, descr_load, task_change


logging.basicConfig(level=logging.INFO, filename='bot_logging.txt', filemode='a',  #'utf-8',
                    format='%(asctime)s: %(levelname)s %(funcName)s-%(lineno)d %(message)s')

with open('key.txt', 'r') as f:
    text = f.readline()
TOKEN = str(text)
MSG = '{}, choose an action'

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot, storage=MemoryStorage())

bot_users_online = {}
bot_users_tasks = {}
bot_users_change = {}


class Form(StatesGroup):
    first_msg = State()
    second_msg = State()
    third_msg = State()
    fourth_msg = State()
    login_user = State()
    password_user = State()
    tasks_id_user = State()
    tasks_all_user = State()


@dp.message_handler(commands=['start'])
async def start_handler(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    user_full_name = message.from_user.full_name
    user_bot = message.from_user.is_bot
    user_msg = message.text
    logging.info(f'{user_id=}, {user_bot=}, {user_msg=}')
    bot_users_online[user_id] = None
    await message.reply(f'Hi, {user_full_name}!')
    await message.answer(MSG.format(user_name), reply_markup=mks.sing_buttons)
    print(bot_users_online) # удалить (!)
    print(bot_users_tasks) # удалить (!)


@dp.message_handler(commands=['quit'])
async def quit_handler(message: Message):
    user_id = message.from_user.id
    if user_id in bot_users_online:
        msg_id = message.message_id
        user_msg = message.text
        logging.info(f'{user_id=}, {msg_id=}, {user_msg=}')
        bot_users_online.pop(user_id)
        bot_users_tasks.pop(user_id)
        bot_users_change.pop(user_id)
        await message.answer('Goodbye! See you...', reply_markup=ReplyKeyboardRemove())
        print(bot_users_online) # удалить (!)
        print(bot_users_tasks) # удалить (!)
        print(bot_users_change) # удалить (!)


@dp.message_handler(commands=['login'])
async def login_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in bot_users_online:
        msg_id = message.message_id
        user_msg = message.text
        logging.info(f'{user_id=}, {msg_id=}, {user_msg=}')
        await Form.first_msg.set()
        bot_sent = await message.answer('enter login:')
        async with state.proxy() as data:
            data['first_msg'] = bot_sent.message_id
        await Form.login_user.set()


@dp.message_handler(state=Form.login_user)
async def login_text(message: Message, state: FSMContext):
    user_id = message.from_user.id
    msg_id = message.message_id
    lgn = message.text
    logging.info(f'{user_id=}, {msg_id=}, {lgn=}')
    async with state.proxy() as data:
        data['second_msg'] = msg_id
        data['login_user'] = lgn
    await Form.third_msg.set()
    bot_sent = await message.answer('enter password:')
    async with state.proxy() as data:
            data['third_msg'] = bot_sent.message_id
    await Form.password_user.set()


@dp.message_handler(state=Form.password_user)
async def password_text(message: Message, state: FSMContext):
    user_name = message.from_user.first_name
    user_id = message.from_user.id
    msg_id = message.message_id
    pswd = message.text
    logging.info(f'{user_id=}, {msg_id=}, {pswd=}')
    async with state.proxy() as data:
        data['fourth_msg'] = msg_id
        data['password_user'] = pswd
    new_text = len(pswd) * '*'
    lgn = data['login_user']
    await bot.delete_message(user_id, data['fourth_msg'])
    await bot.delete_message(user_id, data['third_msg'])
    await bot.delete_message(user_id, data['second_msg'])
    await bot.delete_message(user_id, data['first_msg'])
    await message.answer(f'Data accepted:\n{lgn}, {new_text}')
    await Form.tasks_id_user.set()

    response_sing = sing_in(data['login_user'], data['password_user'])
    if response_sing.status_code == 200:
        # Аутентификация прошла успешно:
        logging.info(f'{user_id=}, Successful authorization')
        response_data = response_sing.json()
        access_token = response_data['access']
        refresh_token = response_data['refresh']
        user_tasks_id = response_data['id']
        logging.info(f'{user_id=}, Loaded info: {response_data}')
        await message.answer('Successful authorization')
        bot_users_online[user_id] = dict(login=data['login_user'],
                                         password=data['password_user'],
                                         login_status=True,
                                         access_token=response_data['access'])
        async with state.proxy() as data:
            data['tasks_id_user'] = user_tasks_id
        await Form.tasks_all_user.set()
    
    else:
        # Аутентификация не удалась:
        logging.info(f'{user_id=}, Error: {response_sing.status_code}')
        bot_users_online[user_id] = dict(login=data['login_user'],
                                         password=data['password_user'],
                                         login_status=False)
        await state.finish()
        await message.answer('The login or password is entered incorrectly,\nor such user does not exist')
        await message.answer(f'{MSG.format(user_name)}, use the buttons')
    
    if bot_users_online[user_id]['login_status'] == True:
        logging.info(f'{user_id=}, Data is loading...')
        response_tasks = tasks_load(access_token)
        if response_tasks.status_code == 200:
            # Авторизация прошла успешно:
            logging.info(f'{user_id=}, Data loaded successfully')
            response_list = response_tasks.json()
            download = descr_load(response_list, user_tasks_id)
            async with state.proxy() as data:
                data['tasks_all_user'] = download
            logging.info(f'{user_id=}, Loaded info: {response_list}')
            logging.info(f'{user_id=}, Descriptions loaded successfully')
            bot_users_tasks[user_id] = dict({user_tasks_id: data['tasks_all_user']})
            await state.finish()
            await message.answer(MSG.format(user_name), reply_markup=mks.menu_buttons)

        else:
            # Авторизация не удалась:
            logging.info(f'{user_id=}, Error: {response_tasks.status_code}')
            await state.finish()
            await message.answer('Data not loaded')
            await message.answer(f'{MSG.format(user_name)}, use the buttons')
    
    else:
        bot_users_online[user_id] = None
        await state.finish()
        await message.answer('Something went wrong, try again')

    print(bot_users_online) # удалить (!)
    print(bot_users_tasks) # удалить (!)


@dp.message_handler(commands=['menu'])
async def options_handler(message: Message):
    user_id = message.from_user.id
    if user_id in bot_users_online:
        if bot_users_online[user_id]['login_status'] == True:
            msg_id = message.message_id
            user_msg = message.text
            logging.info(f'{user_id=}, {msg_id=}, {user_msg=}')
            await message.answer('Select from the menu:', reply_markup=mks.keyboard)
        else:
            await message.answer('You are not authenticated', reply_markup=mks.sing_buttons)
    else:
        await message.answer('Something went wrong, use the buttons',
                             reply_markup=mks.sing_buttons)


# @dp.message_handler()
# async def data_handler(message: Message, data):
#     await message.answer(data)


@dp.callback_query_handler(lambda call: True)
async def callback_options(query: CallbackQuery):

    data = query.data
    user_id = query.from_user.id
    msg_id=query.message.message_id
    user_name = query.from_user.first_name
    user_id_for_tasks = list(bot_users_tasks[user_id])[0]
    tasks_short = bot_users_tasks[user_id][user_id_for_tasks]['my']
    STATUSES = ['to-work', 'in-work', 'agreement', 'completed']

    if data == 'all tasks':
        if bot_users_tasks[user_id][user_id_for_tasks]['all'] == None:
            await bot.edit_message_text(chat_id=user_id, message_id=msg_id,
                                        text='There are no current tasks',
                                        reply_markup=None)
            logging.info(f'{user_id=}, message: There are no current tasks')
        else:
            await bot.edit_message_text(chat_id=user_id, message_id=msg_id,
                                        text='all tasks now:', reply_markup=None)
            for i in bot_users_tasks[user_id][user_id_for_tasks]['all']:
                await bot.send_message(chat_id=query.message.chat.id, text=f'{i}')
            logging.info(f'{user_id=}, All tasks have been sent')

    elif data == 'my tasks':
        if bot_users_tasks[user_id][user_id_for_tasks]['my'] == None:
            await bot.edit_message_text(chat_id=user_id, message_id=msg_id,
                                        text='You have no current tasks',
                                        reply_markup=None)
            logging.info(f'{user_id=}, message: You have no current tasks')
        else:
            await bot.edit_message_text(chat_id=user_id, message_id=msg_id, text='your tasks now:',
                                        reply_markup=await mks.create_keyboard_tasks(tasks_short))
            logging.info(f'{user_id=}, All user tasks have been sent')

    elif data in tasks_short.keys():
        task_using = data
        if bot_users_tasks[user_id][user_id_for_tasks]['my'] == None:
            await bot.edit_message_text(chat_id=user_id, message_id=msg_id,
                                        text='You have no current tasks',
                                        reply_markup=None)
            logging.info(f'{user_id=}, message: You have no current tasks')
        else:
            result = tasks_short.get(data)
            await bot.edit_message_text(chat_id=user_id, message_id=msg_id,
                                        text=f'your {data}:', reply_markup=None)
            await bot.send_message(chat_id=query.message.chat.id, text=result)
            logging.info(f'{user_id=}, {data} have been sent')
            await bot.send_message(chat_id=query.message.chat.id, text=f'{MSG.format(user_name)}:',
                                   reply_markup=mks.keyboard_my_tasks)
            bot_users_change[user_id] = dict({'task_id': task_using[5:]})

    elif data == 'change status':
        if bot_users_tasks[user_id][user_id_for_tasks]['my'] == None:
            await bot.edit_message_text(chat_id=user_id, message_id=msg_id,
                                        text='You have no current tasks',
                                        reply_markup=None)
            logging.info(f'{user_id=}, message: You have no current tasks')
        else:
            await bot.edit_message_text(chat_id=user_id, message_id=msg_id, text='select a task status:',
                                        reply_markup=await mks.create_keyboard_my_task(STATUSES))
            logging.info(f'{user_id=}, message: Start changing task status')

    elif data in STATUSES:
        status = data
        if bot_users_tasks[user_id][user_id_for_tasks]['my'] == None:
            await bot.edit_message_text(chat_id=user_id, message_id=msg_id,
                                        text='You have no current tasks',
                                        reply_markup=None)
            logging.info(f'{user_id=}, message: You have no current tasks')
        else:
            await bot.edit_message_text(chat_id=user_id, message_id=msg_id,
                                        text=f'confirm changes: status -> {data}',
                                        reply_markup=mks.keyboard_to_status)
            logging.info(f'{user_id=}, message: Selected status to change')
            bot_users_change[user_id].update({'status': status})
            print(bot_users_change) # удалить (!)

    elif data == 'confirm':
        if bot_users_tasks[user_id][user_id_for_tasks]['my'] == None:
            await bot.edit_message_text(chat_id=user_id, message_id=msg_id,
                                        text='You have no current tasks',
                                        reply_markup=None)
            logging.info(f'{user_id=}, message: You have no current tasks')
        else:
            task_id_to_change = bot_users_change[user_id]['task_id']
            status_to_change = bot_users_change[user_id]['status']
            access_token = bot_users_online[user_id]['access_token']
            user_tasks_id = int(*(list(bot_users_tasks[user_id].keys())))
            response_change = task_change(task_id_to_change, status_to_change, access_token)
            logging.info(f'{user_id=}, message: Request to change task status')
            if response_change.status_code == 200:
                response_tasks = tasks_load(access_token)
                if response_tasks.status_code == 200:
                    logging.info(f'{user_id=}, Data updated successfully')
                    response_list = response_tasks.json()
                    download = descr_load(response_list, user_tasks_id)
                    logging.info(f'{user_id=}, Loaded info: {response_list}')
                    logging.info(f'{user_id=}, Descriptions loaded successfully')
                    bot_users_tasks[user_id][user_tasks_id].update(download)
                    print(bot_users_tasks) # удалить (!)
                    await bot.edit_message_text(chat_id=user_id, message_id=msg_id,
                                                text='Data updated successfully',
                                                reply_markup=None)
                else:
                    logging.info(f'{user_id=}, Error: {response_tasks.status_code}')
                    await bot.edit_message_text(chat_id=user_id, message_id=msg_id,
                                                text='Updated task data was not loaded',
                                                reply_markup=None)
                bot_users_change[user_id] = None
                await bot.edit_message_text(chat_id=user_id, message_id=msg_id,
                                            text='Task status changed successfully',
                                            reply_markup=mks.keyboard)
                logging.info(f'{user_id=}, message: Task status changed successfully')
            else:
                value = 'Something went wrong, try again'
                await bot.send_message(chat_id=query.message.chat.id, text=value)

    elif data == 'cancel':
        if bot_users_tasks[user_id][user_id_for_tasks]['my'] == None:
            await bot.edit_message_text(chat_id=user_id, message_id=msg_id,
                                        text='You have no current tasks',
                                        reply_markup=None)
            logging.info(f'{user_id=}, message: You have no current tasks')
        else:
            bot_users_change[user_id] = None
            await bot.edit_message_text(chat_id=user_id, message_id=msg_id,
                                        text='Select from the menu:',
                                        reply_markup=mks.keyboard)
            logging.info(f'{user_id=}, message: Action canceled')

    else:
        bot_users_online[user_id] = None
        bot_users_tasks[user_id] = None
        bot_users_change[user_id] = None
        value = 'Something went wrong, use the menu button'
        await bot.edit_message_text(chat_id=user_id, message_id=msg_id,
                                    text=value, reply_markup=mks.sing_buttons)
        logging.info(f'{user_id=}, message: Unknown request')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
