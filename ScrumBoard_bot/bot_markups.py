from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

btn = ReplyKeyboardMarkup(row_width=2)
btn_lgn = KeyboardButton('/login')
btn_out = KeyboardButton('/quit')
button = btn.add(btn_lgn, btn_out)

btns = ReplyKeyboardMarkup(row_width=2)
btn_opt = KeyboardButton('/options')
btn_out = KeyboardButton('/quit')
buttons = btns.add(btn_opt, btn_out)

keyboard = InlineKeyboardMarkup()
keyboard.row(InlineKeyboardButton('tasks', callback_data='tasks'),
             InlineKeyboardButton('new task', callback_data='new task'))

keyboard_next = InlineKeyboardMarkup()
keyboard_next.row(InlineKeyboardButton('task 1', callback_data='task 1'),
                  InlineKeyboardButton('task 2', callback_data='task 2'))

keyboard_new = InlineKeyboardMarkup()
keyboard_new.row(InlineKeyboardButton('add task', callback_data='add task'),
                 InlineKeyboardButton('cancel', callback_data='cancel'))
