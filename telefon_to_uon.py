import datetime
import json
import time
import requests
import config as cfg


class Info:
    def __init__(self):
        self.name = ''
        self.number = ''
        self.answers = []


def send_data_to_uon(data):
    today = datetime.datetime.today()
    t = today.time()
    date_str = '{} {}:{}:{}'.format(today.date(), t.hour - (3 + cfg.time_zone_from_msk), t.minute, t.second)
    note = 'Примечания: {}'.format("\n".join(data.answers))
    payload = {
        'r_dat': date_str,
        'r_u_id': cfg.default_uon_admin_id,
        'u_name': data.name,
        'source': '"Телефонистка"',
        'u_phone': data.number,
        'u_note': note
    }#'2018-09-18T19:08:30.204146'

    print(payload)
    url = 'https://api.u-on.ru/{}/lead/create.json'.format(cfg.uon_key)
    response = requests.post(url, data=payload)
    print(response)
    print(response.text)


def get_new_calls(from_time):
    url = 'https://api.telefonistka.ru/v1/calls/search?from_time={}&auth_api_key={}'\
        .format(from_time, cfg.telefonistka_key)
    response = requests.get(url, )
    print(response)
    print(response.text)
    calls = []
    if response.status_code == 200:
        resp_json = json.loads(response.text)
        resp_list = resp_json["list"]
        for r in resp_list:
            calls.append(r["id"])
    return calls


def get_call_details(call_id):
    url = 'https://api.telefonistka.ru/v1/calls/{}/messages?auth_api_key={}'.format(call_id, cfg.telefonistka_key)
    response = requests.get(url,)
    print(response)
    print(response.text)
    info = Info()
    resp_json = json.loads(response.text)
    call = resp_json['list'][0]
    info.answers.append(call["caller_message"])
    info.answers.append("Дата звонка: " + call["datetime"])
    info.name = call["caller_name"]
    info.number = call["caller_phone"]
    return info


def start():
    while True:
        today = datetime.datetime.today()
        time_str = str(today).replace(' ', 'T')
        time.sleep(600)
        new_calls = get_new_calls(time_str)
        for c in new_calls:
            call_desc = get_call_details(c)
            send_data_to_uon(call_desc)


if __name__ == '__main__':
    start()
