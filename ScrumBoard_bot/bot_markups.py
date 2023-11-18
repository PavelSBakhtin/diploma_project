from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot_main import dict_tasks

btn = ReplyKeyboardMarkup(row_width=2)
btn_lgn = KeyboardButton('/login')
btn_out = KeyboardButton('/quit')
button = btn.add(btn_lgn, btn_out)

btns = ReplyKeyboardMarkup(row_width=2)
btn_opt = KeyboardButton('/menu')
btn_out = KeyboardButton('/quit')
buttons = btns.add(btn_opt, btn_out)

keyboard = InlineKeyboardMarkup()
keyboard.row(InlineKeyboardButton('my tasks', callback_data='my tasks'),
             InlineKeyboardButton('all tasks', callback_data='all tasks'))

async def create_keyboard_tasks(upline_shot):
    keys_list = list(dict_tasks(upline_shot).keys())
    keyboard_tasks = InlineKeyboardMarkup(row_width=1)
    for i in keys_list:
        keyboard_tasks.add(InlineKeyboardButton(f'{i}', callback_data=f'{i}'))
    return keyboard_tasks

keyboard_my_tasks = InlineKeyboardMarkup().add(InlineKeyboardButton('my tasks', callback_data='my tasks'))

# keyboard_new = InlineKeyboardMarkup()
# keyboard_new.row(InlineKeyboardButton('add task', callback_data='add task'),
#                  InlineKeyboardButton('cancel', callback_data='cancel'))
