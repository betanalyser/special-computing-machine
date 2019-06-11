# -*- coding: utf-8 -*-
import config
import telebot
from telebot import apihelper, types
import data
from datetime import datetime
import pickle
from apscheduler.schedulers.background import BackgroundScheduler
import os.path
import proxy
from fonbet import get_suitable_events

apihelper.proxy = proxy.PROXY


bot = telebot.TeleBot(config.token)


def dump_users_data(users_data):
    with open('users.pickle', 'wb') as f:
        pickle.dump(users_data, f)


def is_users_data_file_exists(path):
    return os.path.exists(path=path)


def load_users_data():
    path = 'users.pickle'
    if not is_users_data_file_exists(path):
        with open(path, 'wb') as f:
            pickle.dump(data.users, f)
    with open(path, 'rb') as f:
        return pickle.load(f)


def send_events(chat_id, events):
    for event in events:
        try:
            keyboard = types.InlineKeyboardMarkup()
            url_button = types.InlineKeyboardButton(
                text=data.GO_TO_THE_EVENT_PAGE,
                url=event['EventLink'])
            keyboard.add(url_button)
            bot.send_message(chat_id, event['Message'],
                             reply_markup=keyboard,
                             parse_mode='Markdown')
        except ConnectionError as exception:
            raise exception


def parse_events(for_all=True, message=''):
    if for_all:
        dbase = data.users
    else:
        dbase = {message.chat.id: data.users[message.chat.id]}
    for user in dbase:
        messages_for_send = []
        if data.users[user]['State'] == 4:
            for event in get_suitable_events(
                    coeff_min=data.users[user]['EnteredCoefficients'][0],
                    coeff_max=data.users[user]['EnteredCoefficients'][1],
                    sport_kinds=[sport[0].split(' ')[0]
                                 for sport in data
                                         .users[user]['SelectedSports']
                                         .items()
                                 if sport[1]]):
                if not event['winner']['side'] is None:
                    winner_name = event[event['winner']['side']]['name']
                else:
                    winner_name = 'Draw'
                winner_coefficient = event['winner']['odds']
                if event['odds']['type'] == '3way':
                    current_message = data.event_msg_template_3_way.format(
                        sport_type=data.supported_sport_events_emoji[
                            event['sport']
                        ],
                        competition=event['competition'],
                        home_name=event['home']['name'],
                        home_abbr=event['home']['abbr'],
                        away_name=event['away']['name'],
                        away_abbr=event['away']['abbr'],
                        home_chance=event['odds']['home']['value'],
                        away_chance=event['odds']['away']['value'],
                        draw_chance=event['odds']['draw']['value'],
                        home_weight=event['home']['weight'],
                        away_weight=event['away']['weight'],
                        winner_name=winner_name,
                        winner_coefficient=winner_coefficient,
                        event_time=datetime.utcfromtimestamp(
                            event['start']
                        ).strftime('%H:%M %d/%m/%Y'),
                    )
                else:
                    current_message = data.event_msg_template_2_way.format(
                        sport_type=data.supported_sport_events_emoji[
                            event['sport']
                        ],
                        competition=event['competition'],
                        home_name=event['home']['name'],
                        home_abbr=event['home']['abbr'],
                        away_name=event['away']['name'],
                        away_abbr=event['away']['abbr'],
                        home_chance=event['odds']['home']['value'],
                        away_chance=event['odds']['away']['value'],
                        home_weight=event['home']['weight'],
                        away_weight=event['away']['weight'],
                        winner_name=winner_name,
                        winner_coefficient=winner_coefficient,
                        event_time=datetime.utcfromtimestamp(
                            event['start']
                        ).strftime('%H:%M %d/%m/%Y'),
                    )
                messages_for_send.append(
                    {
                        'Message': current_message,
                        'EventLink': event['link']
                    })
            if not for_all and len(messages_for_send) == 0:
                bot.send_message(message.chat.id, data.DO_NOT_WORRY)
            else:
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
    data.users[message.chat.id]['SelectedSports'] = {
        data.supported_sport_events[0]: False,
        data.supported_sport_events[1]: False,
        data.supported_sport_events[2]: False
    }
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
    except ConnectionError as exception:
        raise exception


def third_stage(message):
    data.users[message.chat.id]['State'] = 3
    try:
        bot.send_message(message.chat.id,
                         data.OK_TEXT_COEFFICIENTS_1,
                         reply_markup=coefficient_keyboard(),
                         parse_mode='Markdown')
    except ConnectionError as exception:
        raise exception


def fourth_stage(message):
    data.users[message.chat.id]['State'] = 4
    data.users[message.chat.id]['EnteredCoefficients'] = sorted(
        data.users[message.chat.id]['EnteredCoefficients']
    )
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    reset = types.KeyboardButton(text=data.RESET_PARAMETERS)
    keyboard.add(reset)
    try:
        bot.send_message(message.chat.id,
                         data.EXCELLENT_SEARCHING
                         .format(
                             sport_types='\n - ' + '\n - '
                                .join([sport[0] for sport in data.
                                      users[message.chat.id]
                                      ['SelectedSports']
                                       .items() if sport[1]]),
                             min_coeff=str(data
                                           .users[message.chat.id]
                                           ['EnteredCoefficients'][0]).replace(
                                 'inf', '∞'
                                ),
                             max_coeff=str(data
                                           .users[message.chat.id]
                                           ['EnteredCoefficients'][1]).replace(
                                 'inf', '∞'
                                )
                         ),
                         reply_markup=keyboard,
                         parse_mode='Markdown')
    except ConnectionError as exception:
        raise exception
    parse_events(for_all=False, message=message)


def f_sport_kind(message, sport_name):
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
        func=dump_users_data,
        args=[data.users],
        trigger='interval',
        minutes=5
    )
    scheduler.add_job(
        func=parse_events,
        trigger='interval',
        minutes=5
    )
    scheduler.start()


def configurating_keyboard(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    for sport_name in data.supported_sport_events:
        if data.users[message.chat.id]['SelectedSports'][sport_name]:
            sport = types.KeyboardButton(text='{}{}'.format(
                data.CHECKED_EMOJI,
                sport_name))
            keyboard.add(sport)
        else:
            sport = types.KeyboardButton(text=sport_name)
            keyboard.add(sport)
    button = types.KeyboardButton(text=data.DONE)
    keyboard.add(button)
    return keyboard


def coefficient_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=5)
    n = 0
    keyboard_row = []
    for coefficient in range(10, 30, 2):
        keyboard_row.append(types.KeyboardButton(text=str(coefficient / 10)))
        n += 1
        if n % 5 == 0:
            keyboard.row(
                keyboard_row[0],
                keyboard_row[1],
                keyboard_row[2],
                keyboard_row[3],
                keyboard_row[4]
            )
            keyboard_row = []
            n = 0
    keyboard.row(types.KeyboardButton(text=data.DOES_NOT_MATTER))
    cancel = types.KeyboardButton(text=data.CANCEL)
    keyboard.add(cancel)
    return keyboard


@bot.message_handler(commands=['start'])
def send_welcome(message):
    set_user(message)
    try:
        bot.send_message(message.chat.id,
                         data.WELCOME_MESSAGE.format(
                             bot.get_chat(message.chat.id).first_name)
                         )
    except ConnectionError as exception:
        print(exception)
    second_stage(message)


@bot.message_handler(content_types=['text'])
def users_distribution(message):
    if message.chat.id in data.users:
        if data.users[message.chat.id]['State'] == 2:
            choosing_sports(message)
        elif data.users[message.chat.id]['State'] == 3:
            parse_coefficients(message)
        elif data.users[message.chat.id]['State'] == 4:
            events_streaming(message)
    else:
        set_user(message)
        second_stage(message)


def events_streaming(message):
    if message.text == data.RESET_PARAMETERS:
        reset_user_data(message)
        second_stage(message)


def parse_coefficients(message):
    if message.text == data.CANCEL:
        reset_user_data(message)
        second_stage(message)
    else:
        if (check_coefficient(message.text) or
                message.text == data.DOES_NOT_MATTER):
            msg = message.text
            if not any(data.users[message.chat.id]['EnteredCoefficients']):
                if msg == data.DOES_NOT_MATTER:
                    msg = data.NEGATIVE_INFINITY
                data.users[message.chat.id]['EnteredCoefficients'][0] = float(
                    msg
                )
                keyboard = types.ReplyKeyboardMarkup(
                    row_width=1,
                    resize_keyboard=True
                )
                cancel = types.KeyboardButton(text=data.CANCEL)
                keyboard.add(cancel)
                try:
                    bot.send_message(message.chat.id,
                                     data.OK_TEXT_COEFFICIENTS_2,
                                     reply_markup=coefficient_keyboard())
                except ConnectionError as exception:
                    raise exception
            else:
                if msg == data.DOES_NOT_MATTER:
                    msg = data.POSITIVE_INFINITY
                data.users[message.chat.id]['EnteredCoefficients'][1] = float(
                    msg
                )
                fourth_stage(message)
        else:
            try:
                bot.send_message(message.chat.id,
                                 data.INVALID_COEFFICIENTS,
                                 reply_markup=coefficient_keyboard())
            except ConnectionError as exception:
                raise exception


def choosing_sports(message):
    msg = message.text.replace(data.CHECKED_EMOJI, '')
    if msg == data.DONE:
        if any(data.users[message.chat.id]['SelectedSports'].values()):
            third_stage(message)
        else:
            bot.send_message(message.chat.id,
                             data.INVALID_SPORT_CHOOSING,
                             reply_markup=configurating_keyboard(message))
    else:
        if msg in data.supported_sport_events:
            data.users[message.chat.id]['SelectedSports'][msg] = f_sport_kind(
                message, msg
            )
            try:
                bot.send_message(message.chat.id,
                                 data.ON_CHOOSING_SPORT,
                                 reply_markup=configurating_keyboard(message))
            except ConnectionError as exception:
                raise exception


if __name__ == '__main__':
    data.users = load_users_data()
    set_schedulers()
    while True:
        try:
            bot.polling(none_stop=True)
        except ConnectionError:
            pass
