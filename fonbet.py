import re
import json
import time

from lxml import html
from requests import Request, Session
from requests import Timeout, TooManyRedirects, RequestException
from apscheduler.schedulers.background import BackgroundScheduler

# constants ####


headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36'
}

session = Session()
session.headers.update(headers)


XPATH_JSON = 'string(//body/script[@type="text/javascript"][1]/text())'
REGEX_JSON = re.compile(
    r'(?<=window\.__INITIAL_STATE__=).+}',
    re.DOTALL | re.IGNORECASE
)

NEED_SPORT_KINDS = ['Football', 'Hockey', 'Basketball']
SPORT_TO_NAME = {
    'Football': 'football',
    'Hockey': 'hockey',
    'Basketball': 'basketball'
}

BIG_COEFF = 2.0

# service ####


def safe_request(prepare_request, session=session, attempts=5, sleep=5):
    for attemp in range(attempts):
        try:
            response = session.send(
                session.prepare_request(prepare_request)
            )
            if response.status_code == 200:
                return response
        except (Timeout, TooManyRedirects, RequestException):
            time.sleep(sleep)
    else:
        raise RuntimeError('invalid status code')


URL_FONBET = 'https://www.fonbet.ru'
URL_SPORTRADAR = 'https://s5.sir.sportradar.com/fonbet'

req_urls_json = Request(
    method='GET',
    url=f'{URL_FONBET}/urls.json',
    # params={0.9435932890190599}
)

URLS_JSON = safe_request(req_urls_json).json()
URL_COMMON = f'https:{URLS_JSON["common"][0]}'
URL_LINE = f'https:{URLS_JSON["line"][0]}'

req_topEvents3 = Request(
    method='GET',
    url=f'{URL_LINE}/line/topEvents3',
    params={
        'place': 'line',
        'lang': 'eng',
        'sysId': 1,
        # 'salt': '1mnb3r7hefmjwf3r9he',
        # 'smartFilterId': 11  # id из smartFilters (подборки)
    }
)


###


def get_json(response, xpath_json=XPATH_JSON, regex=REGEX_JSON):
    text = html.fromstring(response.text)
    tag_content = text.xpath(xpath_json)
    json_str = regex.search(tag_content)
    if json_str is not None:
        return json.loads(json_str.group())


def event_fits(event, sport_kinds, coeff_min, coeff_max):
    if sport_kinds and event['skName'] not in sport_kinds:
        return False
    for market in event['markets']:
        if market['ident'] == 'Results':  # Исходы
            break
    for row in market['rows']:
        if 'isTitle' not in row:
            for cell in row['cells']:
                if 'isTitle' not in cell:
                    value = cell.get('value')
                    if value:
                        if coeff_min <= value <= coeff_max:
                            return True
    return False


def actual_events(
        coeff_min=float('-inf'), coeff_max=float('inf'),
        sport_kinds=NEED_SPORT_KINDS):
    '''
    Получаем первичные данные всех текущих ивентов с главной.
    sports_kinds - фильтр в виде списка названий видов спорта на русском
        названия должны быть точными. Можно указать None если хотим все ивенты.
    '''
    response = safe_request(req_topEvents3)
    json_ = response.json()
    result = []
    for event in json_['events']:
        if event_fits(event, sport_kinds,
                      coeff_min=coeff_min, coeff_max=coeff_max):
            sk_name = event['skName']
            event_id = event['id']
            comp_id = event["competitionId"]
            sport = SPORT_TO_NAME[sk_name]
            link = f'{URL_FONBET}/#!/bets/{sport}/{comp_id}/{event_id}'

            result.append(
                {
                    'event_id': event_id,
                    'link': link,
                    'competition': event['competitionName'],
                    'sport': sk_name,
                    'start': event['startTimeTimestamp']
                    # стороны, коэффы и места в таблице добавляются позже
                }
            )
    return result


def get_match(event_id, url_sportradar=URL_SPORTRADAR, lang='en'):
    url_match = f'{url_sportradar}/{lang}/match/m{event_id}'
    response = safe_request(Request(method='GET', url=url_match))
    return get_json(response)


def team_data(team_uid, matchdict):
    target_field = f'stats_team_odds_client/{team_uid}'
    teamdict = matchdict['fetchedData'][target_field]['data']['team']
    need_fields_team = [
        'name',
        'mediumname',
        'nickname',
        'abbr',
        'suffix',
        'sex'
    ]
    result = {}
    for field in need_fields_team:
        result[field] = teamdict[field]
    country_data = teamdict.get('cc')  # поля страны отдельно
    if country_data:
        country = {}
        for field in ['name', 'a2', 'a3', 'ioc', 'continent']:
            country[field] = country_data[field]
    else:
        country = None
    result['country'] = country
    return result


def teams_info(event_id, coeff_min=float('-inf'), coeff_max=float('inf')):
    # возвращает None если данные о паре не найдены
    matchdict = get_match(event_id)
    if not matchdict['options']['h2hParamsInfo']:
        return  # почему-то матч не найден
    params = matchdict['routing']['params']
    season = params['season']
    match_id = params['matchId']
    hometeam_uid = int(params['homeTeamUid'])
    awayteam_uid = int(params['awayTeamUid'])

    target_field = f'stats_team_odds_client/{hometeam_uid}'
    fetched_data = matchdict['fetchedData']
    if target_field not in fetched_data:
        return
    data = data[target_field]['data']

    odds_list = data['odds'][match_id]
    for odds in odds_list:  # находим нужный словарь исходов
        if odds['type'] in ['2way', '3way']:
            break

    target_odds_data = {}
    type_ = odds['type']
    need_fields_odds = ['home', 'away']
    if type_ == '3way':
        need_fields_odds.append('draw')
    for field in need_fields_odds:
        tmp_dict = {}
        for datatype in ['odds', 'change']:
            value = odds[field].get(datatype)
            if value is not None:
                value = float(value)
            if datatype == 'odds':
                datatype = 'value'
            tmp_dict[datatype] = value
        target_odds_data[field] = tmp_dict
    target_odds_data['type'] = type_

    ###

    hometeam_data = {}
    awayteam_data = {}

    target_field = f'stats_season_tables/{season}'
    target = matchdict['fetchedData'].get(target_field)
    if not target:
        return  # у матча нет таблицы

    tables = target['data']['tables']
    status = False
    for table in tables:
        for row in table['tablerows']:
            team_uid = row['team']['uid']
            weight = row.get('pointsTotal')
            if not weight:
                weight = row['winTotal']

            if team_uid == hometeam_uid:
                hometeam_data['weight'] = weight
            elif team_uid == awayteam_uid:
                awayteam_data['weight'] = weight
            elif 'weight' in hometeam_data and 'weight' in awayteam_data:
                status = True
                break
    if not status:  # данных о команде почему-то нет в таблице
        return

    home_weight = hometeam_data['weight']
    away_weight = awayteam_data['weight']

    if coeff_max >= BIG_COEFF and home_weight == away_weight:
        home_odds = target_odds_data['home']['value']
        away_odds = target_odds_data['away']['value']
        if home_odds > away_odds:
            need_odds = home_odds
        else:
            need_odds = away_odds
        # просто ставим наибольший коэфф
        winner = {'side': None, 'odds': need_odds}

    else:
        if home_weight > away_weight:
            side = 'home'
        elif home_weight < away_weight:
            side = 'away'
        odds = target_odds_data[side]['value']
        if coeff_min <= odds <= coeff_max:
            winner = {'side': side, 'odds': odds}
        else:
            return

    hometeam_data.update(team_data(hometeam_uid, matchdict))
    awayteam_data.update(team_data(awayteam_uid, matchdict))

    return {
        'home': hometeam_data,
        'away': awayteam_data,
        'odds': target_odds_data,
        'winner': winner
    }


def actual_outcomes(
        coeff_min=float('-inf'), coeff_max=float('inf'),
        count=float('inf'), sport_kinds=NEED_SPORT_KINDS):

    events = actual_events(
        coeff_min=coeff_min,
        coeff_max=coeff_max,
        sport_kinds=sport_kinds
    )
    result = []
    n = 0
    for event in events:
        info = teams_info(event['event_id'])
        if info:
            info.update(event)
            result.append(info)
            n += 1
            if n >= count:
                break

    result.sort(key=lambda event: event['winner']['odds'], reverse=True)
    return result


###


EVENTS = None


def update_events():
    global EVENTS
    if not EVENTS:
        print('[UPDATE EVENTS] begin of receive events')
        EVENTS = actual_outcomes()
        print('[UPDATE EVENTS] events received')
    else:
        EVENTS = actual_outcomes()


scheduler = BackgroundScheduler()
scheduler.add_job(
    func=update_events,
    trigger='interval',
    minutes=1,
    id='update_events'
)
update_events()
scheduler.start()


def get_suitable_events(
    coeff_min=float('-inf'), coeff_max=float('inf'),
        count=float('inf'), sport_kinds=NEED_SPORT_KINDS):
    result = []
    n = 0
    for event in EVENTS:
        status = False
        winner = event['winner']
        if event['sport'] in sport_kinds:
            if not winner['side'] and coeff_max >= BIG_COEFF:
                status = True
            elif winner['side'] and coeff_min <= winner['odds'] <= coeff_max:
                status = True

        if status:
            result.append(event)
            n += 1
            if n >= count:
                break
    return result
