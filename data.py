# -*- coding: utf-8 -*-
WELCOME_MESSAGE = """Hello, {} 👋!
In this bot you will be able to receive suitable sport events according to
coefficients that you are interested in! 🎲"""
WHAT_SPORTS_INTEREST_YOU = 'What sports interest you? 🎯'
DONE = 'Done'
CANCEL = 'Cancel'
RESET_PARAMETERS = 'Reset parameters'
CHECKED_EMOJI = '✅ '
DOES_NOT_MATTER = 'Does not matter'
POSITIVE_INFINITY = 'inf'
NEGATIVE_INFINITY = '-inf'
ON_CHOOSING_SPORT = 'Ok. Something else? 😼'
INVALID_SPORT_CHOOSING = 'You need to choose at least one kind of sport.'
GO_TO_THE_EVENT_PAGE = 'Go to the event page 🔗'
OK_TEXT_COEFFICIENTS_1 = """OK.
Let us know with which coefficients events you are looking for. 👀
Text them one by one in the __1.23__ format."""
OK_TEXT_COEFFICIENTS_2 = 'Done. Text the second coefficient.'
INVALID_COEFFICIENTS = 'Invalid coefficient. Try again.'
DO_NOT_WORRY = """No matching events found.
Do not worry, the database is updated every 5 minutes. ⏰"""
EXCELLENT_SEARCHING = """Excellent! 👌
Now we are going to look for suitable events and then we will send them you.
Note that the database is updated every 5 minutes. ⏰

*Your searching parameters 🧮*
Kinds of sport: {sport_types}
Min coefficient: {min_coeff}
Max coefficient: {max_coeff}"""
supported_sport_events_emoji = {'Football': '⚽',
                                'Basketball': '🏀',
                                'Hockey': '🏒'}
supported_sport_events = [
    'Football {}'.format(supported_sport_events_emoji['Football']),
    'Basketball {}'.format(supported_sport_events_emoji['Basketball']),
    'Hockey {}'.format(supported_sport_events_emoji['Hockey']
                       )]
MINUTE = 1000 * 60
five_min_delay = MINUTE * 5
users = {}
supported_sport_events_ru_en = {'Футбол': supported_sport_events[0],
                                'Баскетбол': supported_sport_events[1],
                                'Хоккей': supported_sport_events[2]}
event_msg_template_3_way = """{sport_type} *{competition}*
{home_name} ({home_abbr}) — {away_name} ({away_abbr})

*Coefficients* 🧮
Win {home_name}: {home_chance}
Win {away_name}: {away_chance}
Draw: {draw_chance}

*Weights on the tournament table* 🎚
{home_name}: {home_weight}
{away_name}: {away_weight}

*Suggestion* 💰
Most likely to win: {winner_name}
Coefficient: {winner_coefficient}

📅 Event start date: {event_time} UTC
"""
event_msg_template_2_way = """{sport_type} *{competition}*
{home_name} ({home_abbr}) — {away_name} ({away_abbr})

*Coefficients* 🧮
Chance of winning {home_name}: {home_chance}
Chance of winning {away_name}: {away_chance}

*Weights on the tournament table* 🎚
{home_name}: {home_weight}
{away_name}: {away_weight}

*Suggestion* 💰
Most likely to win: {winner_name}
Coefficient: {winner_coefficient}

📅 Event start date: {event_time} UTC
"""
