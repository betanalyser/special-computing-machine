# -*- coding: utf-8 -*-
WELCOME_MESSAGE = """Hello, {}!
In this bot you will be able to receive events suitable for your coefficients in sports!"""
WHAT_SPORTS_INTEREST_YOU = 'What sports interest you?'
DONE = 'Done'
ON_CHOOSING_SPORT = 'Ok. Something else?'
GO_TO_THE_EVENT_PAGE = 'Go to the event page'
supported_sport_events = ['Football ⚽️', 'Basketball 🏀', 'Hockey 🏒']
MINUTE = 1000 * 60
five_min_delay = MINUTE * 5
"""
Format
{
	'ChatId': {
		'State': None,
		'SelectedSports': 
			{
			'SportName: None
			},
		'EnteredCoefficients': [None, None]
	}
}
"""
users = {}
supported_sport_events_ru_en = {
	'Футбол': supported_sport_events[0],
	'Баскетбол': supported_sport_events[1],
	'Хоккей': supported_sport_events[2]
}
event_message_template = """*{sport_type}*
{competition}
{home_name} — {away_name}

Скорее всего победит: {winner_name}
Коэффициент: {winner_coefficient}

Дата начала события: {event_time}
"""
