import logging
import bot_markups as mks
from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, Message, CallbackQuery
from bot_mfuncs import sing_in, tasks_load, descr_load, task_change

"""
Запись логов в файл с уровнем инфо:
"""
logging.basicConfig(level=logging.INFO, filename='bot_logging.txt', filemode='a',  #'utf-8',
                    format='%(asctime)s: %(levelname)s %(funcName)s-%(lineno)d %(message)s')

"""
Присвоение значения токена константе:
"""
with open('key.txt', 'r') as f:
    text = f.readline()
TOKEN = str(text)
"""
Регуляно используемое сообщение присвоено константе:
"""
MSG = '{}, choose an action'

"""
Создание бота и диспетчера для него:
"""
bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot, storage=MemoryStorage())

"""
Словари для временного хранения информации о пользователях онлайн:
"""
bot_users_online = {} # ключи: id пользователя бота; значения: логин, пароль, статус, акцесс-токен.
bot_users_tasks = {}  # ключи: all, my; значения: все задачи, задачи пользователя.
bot_users_change = {} # ключ: id задачи; значение: новый статус задачи.


"""
Класс онлайн пользователя для машины состояний:
"""
class Form(StatesGroup):
    first_msg = State()      # запрос логина пользователя (для удаления его из чата)
    second_msg = State()     # логин, ответ пользователя (для удаления его из чата)
    third_msg = State()      # запрос пароля пользлвателя (для удаления его из чата)
    fourth_msg = State()     # пароль, ответ пользователя (для удаления его из чата)
    login_user = State()     # логин, для записи в словарь bot_users_online
    password_user = State()  # пароль, для записи в словарь bot_users_online
    tasks_id_user = State()  # id из базы данных, для записи в словарь bot_users_tasks
    tasks_all_user = State() # задачи из базы данных, для записи в словарь bot_users_tasks


"""
Хендлер команды старт:
запись в логи о том, кто вызвал команду;
запись пользователя в словарь bot_users_online;
приветственное сообщение бота пользователю с обращением по имени;
отправка регуляно используемого сообщения ботом с кнопками авторизации и выхода.
"""
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


"""
Хендлер команды выход:
команда сработает только если пользователь задавал команду старт;
запись в логи о вызове команды;
удаление всей информации о пользователе в словарях временного хранения данных о пользователях онлайн;
бота прощается с пользователем и удаляет кнопки меню.
"""
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


"""
Хендлер команды логин:
запись в логи о вызове команды;
если пользователь онлайн - открывается машина состояний;
бот запрашивает логин, запоминает первое сообщение для дальнейшего удаления;
передача состояния к экземпляру класса Form - логин.
"""
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


"""
Хендлер ответа на запрос логина:
запись в логи о вызове команды;
фиксация ответного сообщения с логином пользователя, плюс - для дальнейшего удаления;
бот запрашивает пароль, запоминает и это сообщение для дальнейшего удаления;
передача состояния к экземпляру класса Form - пароль.
"""
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


"""
Хендлер ответа на запрос пароля:
запись в логи о вызове команды;
фиксация ответного сообщения с паролем пользователя;
бот удаляет четыре сообщения из чата в целях информационной безопасности
(удаляются запросы логина и пароля, а также сами сообщения с логином и паролем пользователя);
бот сообщает, что принял от пользователя логин и длину паролья;
передача состояния к экземпляру класса Form - id пользователя в базе данных.
"""
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

    """
    1. Запрос к базе данных с логином и паролем для аутентификации пользователя:
    - если аутентификация положительная:
    в логи записываются полученные данные из базы данных, бот сообщает об успешной аутентификации,
    в словарь bot_users_online записываются логин, пароль, статус True, акцесс-токен,
    передача состояния к экземпляру класса Form - все задачи из базы данных;
    - если аутентификация отрицательная:
    бот информирует об этом пользователя, в логи записывается статус ошибки аутентификации,
    логин-статус пользователя присваевается False, машина состояний закрывается.
    2. После аутентификации отправляется запрос на авторизацию пользователя к базе данных:
    - если авторизация положительная:
    в логи записываются задачи из базы данных, бот сообщает об успешной авторизации,
    в словарь bot_users_tasks записываются два словаря - все задачи, мои задачи,
    машина состояний закрывается, бот отправляет регулярное сообшение и меняет кнопку логин на меню;
    - если авторизация отрицательная:
    бот информирует об этом пользователя, в логи записывается статус ошибки авторизации,
    просит пользователя воспользоваться кнопками меню, машина состояний закрывается.
    """
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
        logging.info(f'{user_id=}, message: user is not authorized')


"""
Хендлер команды меню:
проверка - пользователь онлайн, логин-статус True,
если - да, то запись в логи о вызове команды, появляется меню с инлайн-кнопками;
если - нет, или что-то пошло не по логике, то бот сообщает об этом пользователю
и меняет кнопки на изначальные - догин и выход.

"""
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


"""
Хендлер на любое сообщение от пользователя:
бот отвечает, что - не понимает команду и, что - у него есть конкретный алгоритм.
"""
@dp.message_handler()
async def data_handler(message: Message):
    await message.answer("I don't understand you,\nthis is not included in my algorithm")


"""
Хендлер работы с инлайн-кнопками:
1) две кнопки - все задачи, мои задачи,
при нажатии на все задачи - выводится соответствеющий список,
при нажатии на мои задачи - выводится список кнопок по количеству задач;
2) после выбора задачи из списка - поялвяется описание самой задачи,
а под ней две кнопки - изменить статус и мои задачи;
3) при нажатии на изменить статус - выводится список фиксированных статусов из STATUSES,
после выбора статуса в словарь bot_users_change записывается id задачи и новый её статус,
далее появляются две кнопки - подтвердить и отменить;
4) при нажатии кнопки подтвердить - отправляется запрос к базе данных на изменение статуса задачи,
при нажатии кнопки отменить - информация в словаре bot_users_change стерается;
5) если в базе данных изменения произошли успешно, из неё выгружаются обновленные данные и
перезаписываются в словаре bot_users_tasks, о чём бот сообщает пользователю,
если в базе данных изменения не произошли - информация в словаре bot_users_change стерается,
бот предлагает пользователю начать процедуру заново;
6) каждый этап кол-бэка логируется, при возникновении поломки алгоритма меню инлайн-кнопок
стерается информация о пользователе во всех словарях временного хранения информации и
бот предлагает начать всё заново, появляются кнопки логин и выход.
"""
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


"""
Запиуск телеграм-бота
"""
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
