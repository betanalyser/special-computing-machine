# -*- coding: utf-8 -*-
import config
import telebot
from telebot import apihelper, types
import proxy
from data import WELCOME_MESSAGE, WHAT_SPORTS_INTEREST_YOU, DONE, supported_sport_events
apihelper.proxy = proxy.PROXY

bot = telebot.TeleBot(config.token)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id,
                     WELCOME_MESSAGE.format(bot.get_chat(message.chat.id).first_name))
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    for sport_name in supported_sport_events:
        sport = types.InlineKeyboardButton(text=sport_name)
        keyboard.add(sport)
    button = types.InlineKeyboardButton(text=DONE)
    keyboard.add(button)
    bot.send_message(message.chat.id,
                     WHAT_SPORTS_INTEREST_YOU,
                     reply_markup=keyboard)


@bot.message_handler(content_types=['text'])
def choosing_sports(message):
    if message.text == supported_sport_events[0]:
        print('test')
    elif message.text == supported_sport_events[1]:
        pass
    elif message.text == supported_sport_events[2]:
        pass


if __name__ == '__main__':
     bot.polling(none_stop=True)
