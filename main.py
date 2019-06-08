# -*- coding: utf-8 -*-
import config
import telebot
from telebot import apihelper, types
import proxy
from data import WELCOME_MESSAGE, WHAT_SPORTS_INTEREST_YOU, DONE, ON_CHOOSING_SPORT
from data import users, supported_sport_events
apihelper.proxy = proxy.PROXY

bot = telebot.TeleBot(config.token)


def set_user(message):
    user = {'State': 1,
            'Selected sports':
                {supported_sport_events[0]: False,
                 supported_sport_events[1]: False,
                 supported_sport_events[2]: False},
            'Entered coefficients': [0.0, 0.0]
            }
    users[message.chat.id] = user


def third_stage(message):
    users[message.chat.id]['State'] = 3
    pass


def configurating_keyboard(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    for sport_name in supported_sport_events:
        if users[message.chat.id]['Selected sports'][sport_name]:
            sport = types.KeyboardButton(text='✅ {}'.format(sport_name))
            keyboard.add(sport)
        else:
            sport = types.KeyboardButton(text=sport_name)
            keyboard.add(sport)
    button = types.KeyboardButton(text=DONE)
    keyboard.add(button)
    return keyboard


@bot.message_handler(commands=['start'])
def send_welcome(message):
    set_user(message)
    bot.send_message(message.chat.id,
                     WELCOME_MESSAGE.format(bot.get_chat(message.chat.id).first_name))
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    for sport_name in supported_sport_events:
        sport = types.KeyboardButton(text=sport_name)
        keyboard.add(sport)
    button = types.KeyboardButton(text=DONE)
    keyboard.add(button)
    bot.send_message(message.chat.id,
                     WHAT_SPORTS_INTEREST_YOU,
                     reply_markup=keyboard)
    users[message.chat.id]['State'] = 2


@bot.message_handler(content_types=['text'])
def choosing_sports(message):
    msg = message.text.replace('✅ ', '')
    if msg == supported_sport_events[0]:
        if not users[message.chat.id]['Selected sports'][supported_sport_events[0]]:
            users[message.chat.id]['Selected sports'][supported_sport_events[0]] = True
        else:
            users[message.chat.id]['Selected sports'][supported_sport_events[0]] = False
    elif msg == supported_sport_events[1]:
        if not users[message.chat.id]['Selected sports'][supported_sport_events[1]]:
            users[message.chat.id]['Selected sports'][supported_sport_events[1]] = True
        else:
            users[message.chat.id]['Selected sports'][supported_sport_events[1]] = False
    elif msg == supported_sport_events[2]:
        if not users[message.chat.id]['Selected sports'][supported_sport_events[2]]:
            users[message.chat.id]['Selected sports'][supported_sport_events[2]] = True
        else:
            users[message.chat.id]['Selected sports'][supported_sport_events[2]] = False
    if msg in supported_sport_events:
        bot.send_message(message.chat.id,
                         ON_CHOOSING_SPORT,
                         reply_markup=configurating_keyboard(message))
    if msg == DONE:
        third_stage(message)


if __name__ == '__main__':
     bot.polling(none_stop=True)
