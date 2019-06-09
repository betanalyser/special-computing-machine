# -*- coding: utf-8 -*-
import config
import telebot
from telebot import apihelper, types
import data
from fonbet import actual_outcomes
from datetime import datetime
import pickle
from apscheduler.schedulers.background import BackgroundScheduler
from translate import Translator
import proxy

apihelper.proxy = proxy.PROXY


bot = telebot.TeleBot(config.token)
translator = Translator(from_lang='ru', to_lang='en', provider='mymemory')


def dump_users_data(users_data):
    with open('users.pickle', 'wb') as f:
        pickle.dump(users_data, f)


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
    events = actual_outcomes()
    for event in events:
        for user in data.users:
            messages_for_send = []
            if data.users[user]['State'] == 4 and any(data.users[user]['SelectedSports'].values()):
                if (data.users[user]['SelectedSports'][data.supported_sport_events_ru_en[event['sport']]] and
                        event['winner']['side'] is not None and
                        data.users[user]['EnteredCoefficients'][0]
                        < event['winner']['odds'] <
                        data.users[user]['EnteredCoefficients'][1]):
                    current_message = data.event_message_template.format(
                        sport_type=data.supported_sport_events_ru_en[event['sport']],
                        competition=translator.translate(event['competition']),
                        home_name=translator.translate(event['home']['name']),
                        home_abbr=translator.translate(event['home']['abbr']),
                        away_name=translator.translate(event['away']['name']),
                        away_abbr=translator.translate(event['away']['abbr']),
                        home_chance=event['odds']['home']['value'],
                        away_chance=event['odds']['away']['value'],
                        draw_chance=event['odds']['draw']['value'],
                        home_weight=event['home']['weight'],
                        away_weight=event['away']['weight'],
                        winner_name=translator.translate(event[event['winner']['side']]['name']),
                        winner_coefficient=event['winner']['odds'],
                        event_time=datetime.utcfromtimestamp(event['start']).strftime('%H:%M %d/%m/%Y'),
                        )
                    messages_for_send.append({'Message': current_message, 'EventLink': event['link']})
            send_events(user, messages_for_send)


def set_user(message):
    user = {'State': 1,
            'SelectedSports':
                {data.supported_sport_events[0]: False,
                 data.supported_sport_events[1]: False,
                 data.supported_sport_events[2]: False},
            'EnteredCoefficients': [0.0, 0.0]
            }
    data.users[message.chat.id] = user


def reset_user_data(message):
    data.users[message.chat.id]['SelectedSports'] = {data.supported_sport_events[0]: False,
                                                     data.supported_sport_events[1]: False,
                                                     data.supported_sport_events[2]: False}
    data.users[message.chat.id]['EnteredCoefficients'] = [0.0, 0.0]


def second_stage(message):
    data.users[message.chat.id]['State'] = 2
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
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


def third_stage(message):
    data.users[message.chat.id]['State'] = 3
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    cancel = types.KeyboardButton(text='Cancel')
    keyboard.add(cancel)
    try:
        bot.send_message(message.chat.id,
                         data.OK_TEXT_COEFFICIENTS_1,
                         reply_markup=keyboard)
    except ConnectionError as e:
        raise e


def fourth_stage(message):
    data.users[message.chat.id]['State'] = 4
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    reset = types.KeyboardButton(text='Reset parameters')
    keyboard.add(reset)
    try:
        bot.send_message(message.chat.id,
                         data.EXCELLENT_SEARCHING,
                         reply_markup=keyboard)
    except ConnectionError as e:
        raise e
    data.users[message.chat.id]['EnteredCoefficients'] = sorted(data.users[message.chat.id]['EnteredCoefficients'])
    parse_events()


def flip_sport_type(message, sport_name):
    if not data.users[message.chat.id]['SelectedSports'][sport_name]:
        return True
    else:
        return False


def check_coefficient(coefficient):
    try:
        float(coefficient)
        return True
    except ValueError:
        return False


def set_schedulers():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=parse_events(),
        trigger='interval',
        minutes=5
    )
    scheduler.add_job(
        func=dump_users_data(data.users),
        trigger='interval',
        minutes=5
    )


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
    except ConnectionError as e:
        raise e
    second_stage(message)


@bot.message_handler(content_types=['text'])
def users_distribution(message):
    if data.users[message.chat.id]['State'] == 2:
        choosing_sports(message)
    elif data.users[message.chat.id]['State'] == 3:
        parse_coefficients(message)
    elif data.users[message.chat.id]['State'] == 4:
        events_streaming(message)


def events_streaming(message):
    if message.text == 'Reset parameters':
        reset_user_data(message)
        second_stage(message)


def parse_coefficients(message):
    if message.text == 'Cancel':
        reset_user_data(message)
        second_stage(message)
    if check_coefficient(message.text):
        if not any(data.users[message.chat.id]['EnteredCoefficients']):
            data.users[message.chat.id]['EnteredCoefficients'][0] = float(message.text)
            keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            cancel = types.KeyboardButton(text='Cancel')
            keyboard.add(cancel)
            try:
                bot.send_message(message.chat.id,
                                 data.OK_TEXT_COEFFICIENTS_2,
                                 reply_markup=keyboard)
            except ConnectionError as e:
                raise e
        else:
            data.users[message.chat.id]['EnteredCoefficients'][1] = float(message.text)
            fourth_stage(message)


def choosing_sports(message):
    msg = message.text.replace('✅ ', '')
    if msg == data.DONE:
        third_stage(message)
    else:
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
        # TODO set_schedulers()
        try:
            bot.polling(none_stop=True)
        except ConnectionError:
            print('Connection error')
