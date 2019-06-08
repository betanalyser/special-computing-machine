# -*- coding: utf-8 -*-
import config
import telebot
from telebot import apihelper, types
import data
from fonbet import actual_outcomes
import time
from datetime import datetime
import pickle
from apscheduler.schedulers.background import BackgroundScheduler
import proxy

apihelper.proxy = proxy.PROXY


bot = telebot.TeleBot(config.token)


def dump_users_data(data):
    with open('users.pickle', 'wb') as f:
        pickle.dump(data, f)


def load_users_data():
    with open('users.pickle', 'rb') as f:
        return pickle.load(f)


def send_events(chat_id, events):
    for event in events:
        try:
            keyboard = types.InlineKeyboardMarkup()
            url_button = types.InlineKeyboardButton(text=data.GO_TO_THE_EVENT_PAGE, url=event['EventLink'])
            keyboard.add(url_button)
            bot.send_message(chat_id, event['Message'], reply_markup=keyboard, parse_mode='Markdown')
        except ConnectionError as e:
            raise e


def parse_events():
    while True:
        events = actual_outcomes()
        for event in events:
            for user in data.users:
                messages_for_send = []
                if data.users[user]['State'] == 3 and any(data.users[user]['SelectedSports'].values()):
                    if (data.users[user]['SelectedSports'][data.supported_sport_events_ru_en[event['sport']]] and
                            event['winner']['side'] is not None):
                        current_message = data.event_message_template.format(
                            sport_type=event['sport'],
                            competition=event['competition'],
                            home_name=event['home']['name'],
                            away_name=event['away']['name'],
                            winner_name=event[event['winner']['side']]['name'],
                            winner_coefficient=event['winner']['odds'],
                            event_time=datetime.utcfromtimestamp(event['start']).strftime('%H:%M %d/%m/%Y'),
                            )
                        messages_for_send.append({'Message': current_message, 'EventLink': event['link']})
                send_events(user, messages_for_send)
        time.sleep(data.five_min_delay)


def set_user(message):
    user = {'State': 1,
            'SelectedSports':
                {data.supported_sport_events[0]: False,
                 data.supported_sport_events[1]: False,
                 data.supported_sport_events[2]: False},
            'EnteredCoefficients': [0.0, 0.0]
            }
    data.users[message.chat.id] = user


def third_stage(message):
    data.users[message.chat.id]['State'] = 3
    # TODO Add messages
    parse_events()


def flip_sport_type(message, sport_name):
    if not data.users[message.chat.id]['SelectedSports'][sport_name]:
        return True
    else:
        return False


def configurating_keyboard(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    for sport_name in data.supported_sport_events:
        if data.users[message.chat.id]['SelectedSports'][sport_name]:
            sport = types.KeyboardButton(text='✅ {}'.format(sport_name))
            keyboard.add(sport)
        else:
            sport = types.KeyboardButton(text=sport_name)
            keyboard.add(sport)
    button = types.KeyboardButton(text=data.DONE)
    keyboard.add(button)
    return keyboard


@bot.message_handler(commands=['start'])
def send_welcome(message):
    set_user(message)
    try:
        bot.send_message(message.chat.id,
                         data.WELCOME_MESSAGE.format(bot.get_chat(message.chat.id).first_name))
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    except ConnectionError as e:
        raise e
    for sport_name in data.supported_sport_events:
        sport = types.KeyboardButton(text=sport_name)
        keyboard.add(sport)
    button = types.KeyboardButton(text=data.DONE)
    keyboard.add(button)
    try:
        bot.send_message(message.chat.id,
                         data.WHAT_SPORTS_INTEREST_YOU,
                         reply_markup=keyboard)
    except ConnectionError as e:
        raise e
    data.users[message.chat.id]['State'] = 2


@bot.message_handler(content_types=['text'])
def choosing_sports(message):
    msg = message.text.replace('✅ ', '')
    if msg == data.DONE:
        third_stage(message)
    data.users[message.chat.id]['SelectedSports'][msg] = flip_sport_type(message, msg)
    if msg in data.supported_sport_events:
        try:
            bot.send_message(message.chat.id,
                             data.ON_CHOOSING_SPORT,
                             reply_markup=configurating_keyboard(message))
        except ConnectionError as e:
            raise e


if __name__ == '__main__':
    while True:
        data.users = load_users_data()
        scheduler = BackgroundScheduler()
        try:
            bot.polling(none_stop=True)
        except ConnectionError:
            print('Connection error')
