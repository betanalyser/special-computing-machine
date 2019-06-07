import re
import json
import time

from lxml import html
from requests import Request, Session
from requests import Timeout, TooManyRedirects, RequestException


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

NEED_SPORT_KINDS = ['Футбол', 'Хоккей', 'Баскетбол']


# service ####


def safe_request(prepare_request, session=session, attempts=5, sleep=2):
    for attemp in range(attempts):
        try:
            response = session.send(
                session.prepare_request(prepare_request)
            )
            if response.status_code == 200:
                return response
        except (Timeout, TooManyRedirects, RequestException):
            # time.sleep(sleep)
            pass
    else:
        raise RuntimeError(f'invalid status code')


###

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
        'lang': 'rus',
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


def get_actual_events(
        coeff_min=float('-inf'), coeff_max=float('inf'),
        sport_kinds=NEED_SPORT_KINDS):
    '''
    Получаем некоторые данные всех текущих ивентов с главной.
    sports_kinds - фильтр в виде списка названий видов спорта
        названия должны быть точными.
        Можно указать None если хотим все ивенты.
    '''

    def event_fits(event):
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

    response = safe_request(req_topEvents3)
    json_ = response.json()
    result = []
    for event in json_['events']:
        if event_fits(event):
            result.append(
                {
                    'event_id': event['id'],
                    'competition': event['competitionName'],
                    'sport': event['skName'],
                    'start': event['startTimeTimestamp']
                    # стороны, коэффы и места в таблице добавляются позже
                }
            )
    return result


def get_match(event_id, url_sportradar=URL_SPORTRADAR, lang='ru'):
    url_match = f'{url_sportradar}/{lang}/match/m{event_id}'
    request = Request(method='GET', url=url_match)
    response = safe_request(request)
    return get_json(response)


def get_teams_info(event_id):
    # возвращает None если данные о паре не найдены
    matchdict = get_match(event_id)
    if not matchdict['options']['h2hParamsInfo']:
        # если почему-то матч не найден
        return
    params = matchdict['routing']['params']
    season = params['season']
    match_id = params['matchId']
    hometeam_uid = int(params['homeTeamUid'])
    awayteam_uid = int(params['awayTeamUid'])

    target_field = f'stats_team_odds_client/{hometeam_uid}'
    data = matchdict['fetchedData'][target_field]['data']

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
            tmp_dict[datatype] = value
        target_odds_data[field] = tmp_dict
    target_odds_data['type'] = type_

    ###

    def team_data(team_uid):
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
        # поля страны отдельно
        country = {}
        country_data = teamdict.get('cc')
        if country_data:
            for field in ['name', 'a2', 'a3', 'ioc', 'continent']:
                country[field] = country_data[field]
            result['country'] = country
        return result

    hometeam_data = team_data(hometeam_uid)
    awayteam_data = team_data(awayteam_uid)

    target_field = f'stats_season_tables/{season}'
    target = matchdict['fetchedData'].get(target_field)
    if not target:
        return

    tables = target['data']['tables']
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
                break

    return {
        'home': hometeam_data,
        'away': awayteam_data,
        'odds': target_odds_data
    }


def get_actual_outcomes(
        coeff_min=float('-inf'), coeff_max=float('inf'),
        sport_kinds=NEED_SPORT_KINDS, count=float('inf')):

    events = get_actual_events(
        coeff_min=coeff_min,
        coeff_max=coeff_max,
        sport_kinds=sport_kinds
    )
    result = []
    n = 0
    for event in events:
        teams_info = get_teams_info(event['event_id'])
        if teams_info:
            teams_info.update(event)
            result.append(teams_info)
            n += 1
            if n >= count:
                break
    return result
