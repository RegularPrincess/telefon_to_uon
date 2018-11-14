import datetime
import json
import time
import traceback

import requests
import config as cfg
from datetime import datetime as dt

call_ids = []


class Info:
    def __init__(self, number=None, duration=None, id=None, datetime=None):
        self.name = ''
        self.number = number
        self.answers = []
        self.duration = duration
        self.datetime = datetime
        self.id = id


def send_data_to_uon(data, line_name_telefon):
    today = datetime.datetime.today()
    t = today.time()
    date_str = '{} {}:{}:{}'.format(today.date(), t.hour + cfg.time_zone_from_msk, t.minute, t.second)
    note = 'Примечания: {}'.format("\n".join(data.answers))
    note += '\n' + line_name_telefon
    payload = {
        'r_dat': date_str,
        'r_u_id': cfg.default_uon_admin_id,
        'u_name': data.name,
        'source': '"Телефонистка"',
        'u_phone': data.number,
        'u_note': note
    }

    print(payload)
    url = 'https://api.u-on.ru/{}/lead/create.json'.format(cfg.uon_key)
    response = requests.post(url, data=payload)
    resp_json = json.loads(response.text)
    print(response)
    print(response.text)
    f = open('text.log', 'a')
    f.write(str(dt.today()) + '   ')
    f.write(data.number + '   ')
    f.write(response.text + '\n')
    f.close()
    return resp_json['id']


def get_record_link(call_id):
    link = "https://api.telefonistka.ru/v1/calls/{}/record.mp3?auth_api_key={}".format(call_id, cfg.telefonistka_key)
    return link


def send_call_info(data, internall_id):
    # payload = {
    #     'start': data.datetime,
    #     'manager_id': cfg.default_uon_admin_id,
    #     'phone': data.number,
    #     'duration': data.duration,
    #     'record_link': get_record_link(data.id),
    #     'direction': 2
    # }
    # url = 'https://api.u-on.ru/{}/call_history/create.json'.format(cfg.uon_key)
    # response = requests.post(url, data=payload)
    # print(response)
    # print(response.text)

    payload = {
        'datetime': data.datetime,
        'r_id': internall_id,
        'type_id': 1,
        'text': get_audio_btn(get_record_link(data.id)) +
                '\n Продолжительность: {} \n Номер: {}'.format(data.duration, data.number)
    }
    url = 'https://api.u-on.ru/{}/request-action/create.json'.format(cfg.uon_key)
    response = requests.post(url, data=payload)
    print(response)
    print(response.text)


def get_audio_btn(link):
    audio_btn = '<audio src="{}" ' \
                'controls="controls" ' \
                'preload="none"></audio>'.format(link)
    return audio_btn


def get_new_calls(from_time, api_key):
    # from_time = '2018-09-22T09:01:28.568068'
    url = 'https://api.telefonistka.ru/v1/calls/search?from_time={}&auth_api_key={}' \
        .format(from_time, api_key)
    response = requests.get(url, )
    print(response)
    print(response.text)
    calls = []
    if response.status_code == 200:
        resp_json = json.loads(response.text)
        resp_list = resp_json["list"]
        for r in resp_list:
            if r["id"] not in call_ids:
                call_ids.append(r["id"])
                calls.append(r["id"])
            else:
                f = open('text.txt', 'a')
                f.write("it's happen")
                f.close()
    return calls


def get_call_details(call_id):
    url = 'https://api.telefonistka.ru/v1/calls/{}/messages?auth_api_key={}'.format(call_id, cfg.telefonistka_key)
    response = requests.get(url, )
    print(call_id)
    print(response)
    print(response.text)
    info = Info()
    resp_json = json.loads(response.text)
    call = resp_json['list'][0]
    info.answers.append(call["caller_message"])
    i = call["datetime"].index('.') - len(call["datetime"])
    datetime_object = dt.strptime(call["datetime"][:i], "%Y-%m-%dT%H:%M:%S")
    datetime_object += datetime.timedelta(hours=3)
    info.datetime = datetime_object
    info.answers.append("Дата звонка: " + str(datetime_object))
    info.name = call["caller_name"]
    info.number = call["caller_phone"]
    info.id = call_id

    # get duration
    url = 'https://api.telefonistka.ru/v1/calls/{}?auth_api_key={}'.format(call_id, cfg.telefonistka_key)
    response = requests.get(url, )
    print(response)
    print(response.text)
    resp_json = json.loads(response.text)
    if resp_json["answer_datetime"] is None:
        info.duration = 0
        info.answers.append("Длительность звонка: 0")
    else:
        i = resp_json["answer_datetime"].index('.') - len(resp_json["answer_datetime"])
        answer_datetime = dt.strptime(resp_json["answer_datetime"][:i], "%Y-%m-%dT%H:%M:%S")
        i = resp_json["finish_datetime"].index('.') - len(resp_json["finish_datetime"])
        finish_datetime = dt.strptime(resp_json["finish_datetime"][:i], "%Y-%m-%dT%H:%M:%S")
        duration = finish_datetime - answer_datetime
        info.duration = duration.seconds
        info.answers.append("Длительность звонка: " + str(duration))
    # info.answers.append("Ссылка на запись звонка: " + get_record(call_id))
    return info


#
# call_desc = get_call_details('6453570962252796484')
# id = send_data_to_uon(call_desc)
# send_call_info(call_desc, id)

def start():
    while True:
        today = datetime.datetime.today()
        today -= datetime.timedelta(hours=4, minutes=20)
        today -= datetime.timedelta(hours=(3 - cfg.time_zone_from_msk))
        # print(today)
        time_str = str(today).replace(' ', 'T')
        time.sleep(3)
        new_calls = get_new_calls(time_str, cfg.telefonistka_key)
        print("Количество ")
        print(len(new_calls))
        for c in new_calls:
            try:
                call_desc = get_call_details(c)
                id = send_data_to_uon(call_desc, 'ТА Пегас Туристик на "Короленко"')
                send_call_info(call_desc, id)
            except BaseException as e:
                var = traceback.format_exc()
                print(var)
                f = open('text.log', 'a')
                f.write(str(dt.today()) + " id=" + c + '\n' )
                f.write(var + '\n')
                f.write(str(e) + '   \n')
                f.close()

        new_calls = get_new_calls(time_str, cfg.telefonistka_key2)
        print(len(new_calls))
        for c in new_calls:
            call_desc = get_call_details(c)
            id = send_data_to_uon(call_desc, 'Туристическая школа')
            send_call_info(call_desc, id)


# get_call_details('6465486176522840644')

if __name__ == '__main__':
    start()
    # 2018-09-22T09:01:28.568068
