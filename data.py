# -*- coding: utf-8 -*-
WELCOME_MESSAGE = """Hello, {}!
In this bot you will be able to receive events suitable for your coefficients in sports!"""
WHAT_SPORTS_INTEREST_YOU = 'What sports interest you?'
DONE = 'Done'
ON_CHOOSING_SPORT = 'Ok. Something else?'
supported_sport_events = ['Football', 'Basketball', 'Hockey']
"""
Format
{
	'Chat id': {
		'State': None,
		'Selected sports': 
			{
			'Sport name: None
			},
		'Entered coefficients': [None, None]
	}
}
"""
users = {}
