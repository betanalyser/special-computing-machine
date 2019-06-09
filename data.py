# -*- coding: utf-8 -*-
WELCOME_MESSAGE = """Hello, {}!
In this bot you will be able to receive events suitable for your coefficients in sports!"""
WHAT_SPORTS_INTEREST_YOU = 'What sports interest you?'
DONE = 'Done'
ON_CHOOSING_SPORT = 'Ok. Something else?'
GO_TO_THE_EVENT_PAGE = 'Go to the event page'
OK_TEXT_COEFFICIENTS_1 = """OK. Let us know with which coefficients events you are looking for.
Text them one by one in the 1.01 format."""
OK_TEXT_COEFFICIENTS_2 = 'Done. Text second coefficient.'
EXCELLENT_SEARCHING = 'Excellent! Now we are going to look for suitable events and then we will send them you.'
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
{home_name} ({home_abbr}) — {away_name} ({away_abbr})

*Coefficients*
Chance of winning {home_name}: {home_chance}
Chance of winning {away_name}: {away_chance}
Chance of draw {away_name}: {draw_chance}

*Weights*
Weight of the {home_name} in the tournament table: {home_weight}
Weight of the {away_name} in the tournament table: {away_weight}

*Suggestion*
Most likely to win: {winner_name}
Coefficient: {winner_coefficient}

Event start date: {event_time}
"""
