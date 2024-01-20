from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def create_keyboard(data):
    """Контекстные кнопки: логин - выход, меню - выход"""
    s_btns = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m_btns = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    btn_lgn = KeyboardButton('/login')
    btn_out = KeyboardButton('/quit')
    btn_men = KeyboardButton('/menu')

    if data == "login":
        return s_btns.add(btn_lgn, btn_out)
    else:
        return m_btns.add(btn_men, btn_out)

sing_buttons = create_keyboard("login")
menu_buttons = create_keyboard("menu")


async def create_keyboard_inline():
    """Инлайн-кнопки: все задачи, мои задачи"""
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton('all tasks', callback_data='all tasks'),
                InlineKeyboardButton('my tasks', callback_data='my tasks'))
    return keyboard


async def create_keyboard_tasks(tasks_short):
    """Инлайн-кнопки: список задач из мои задачи"""
    keyboard_tasks = InlineKeyboardMarkup(row_width=1)
    keys_list = tasks_short.keys()
    for i in keys_list:
        keyboard_tasks.add(InlineKeyboardButton(f'{i}', callback_data=f'{i}'))
    return keyboard_tasks


async def create_keyboard_my_tasks():
    """Инлайн-кнопки: сменить статус - мои задачи"""
    keyboard_my_tasks = InlineKeyboardMarkup()
    keyboard_my_tasks.row(InlineKeyboardButton('change status', callback_data='change status'),
                        InlineKeyboardButton('my tasks', callback_data='my tasks'))
    return keyboard_my_tasks


async def create_keyboard_edit_task(statuses):
    """Инлайн-кнопки: список статусов для задачи"""
    keyboard_task_edit = InlineKeyboardMarkup(row_width=1)
    for i in statuses:
        keyboard_task_edit.add(InlineKeyboardButton(f'{i}', callback_data=f'{i}'))
    return keyboard_task_edit


async def create_keyboard_to_status():
    """Инлайн-кнопки: подтвердить - отменить"""
    keyboard_to_status = InlineKeyboardMarkup()
    keyboard_to_status.row(InlineKeyboardButton('confirm', callback_data='confirm'),
                        InlineKeyboardButton('cancel', callback_data='cancel'))
    return keyboard_to_status
