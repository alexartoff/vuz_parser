import requests
import json
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import csv
import re
from dataclasses import dataclass, asdict, field
from time import sleep
from datetime import datetime
import os


URFU_USER_ID = '12345678900' ## СНИЛС поступающего в УрФУ
SPBGU_USER_ID = '123-456-789 00' ## СНИЛС поступающего в СПбГУ
URFU_SPEC_ID = '06.03.01' ## Номер (код) специальности
URFU_INNER_VUZ = {
        "1": "942", ## Институт естественных наук и математики в составе УрФУ
        "2": "945", ## Уральский гуманитарный институт в составе УрФУ
        "3": "946", ## Физико-технологический институт в составе УрФУ
        "4": "943", ## Химико-технологический институт в составе УрФУ
        "5": "938", ## Институт новых материалов и технологий в составе УрФУ
        # "6": "952", ## Уральский энергетический институт в составе УрФУ
        # "7": "951", ## Уральская передовая инженерная школа в составе УрФУ
        # "8": "950", ## Институт экономики и управления в составе УрФУ
        # "9": "947", ## Институт фундаментального образования в составе УрФУ
    }
SPBGU_SPEC_ID = {
        "095": ("biologiya", 100), ## код специальности, название, кол-во бюджетных мест
        "467": ("himiya", 80),
        "139": ("psihologiya", 40),
        "440": ("psihologiya slujebnoi deyatelnosti", 10),
        "445": ("klinicheskaya psihologiya", 40),
        "090": ("ekologiya", 20),
        "070": ("himiya materialov", 25),
        "102": ("pochvovedenie", 10),
        "144": ("konfliktologiya", 10),
        "435": ("farmaciya", 5),
        "462": ("geologiya", 45),
    }
RESULT_CSV_KEYS = ['nomer', 'prioritet', 'pravo', 'original', 'snils', 'reg_nom', 'summa', 'comment', 'mesto']
SLEEP_TIMER = 15 ## задержка после загрузки данных с сервера


@dataclass
class URFU9:
    nomer: int
    snils: str
    reg_nomer: int
    prioritet: int
    original: str
    exam01: str
    dostigeniya: str
    summa: int
    pravo: str
    comment: str = field(default='')

@dataclass
class URFU12:
    nomer: int
    snils: str
    reg_nomer: int
    prioritet: int
    original: str
    exam01: str
    exam02: str
    exam03: str
    exam04: str
    dostigeniya: str
    summa: int
    pravo: str
    comment: str = field(default='')

@dataclass
class URFU14:
    nomer: int
    snils: str
    reg_nomer: int
    prioritet: int
    original: str
    exam01: str
    exam02: str
    exam03: str
    exam04: str
    exam05: str
    exam06: str
    dostigeniya: str
    summa: int
    pravo: str
    comment: str = field(default='')

@dataclass
class URFU15:
    nomer: int
    snils: str
    reg_nomer: int
    prioritet: int
    original: str
    exam01: str
    exam02: str
    exam03: str
    exam04: str
    exam05: str
    exam06: str
    exam07: str
    dostigeniya: str
    summa: int
    pravo: str
    comment: str = field(default='')

@dataclass
class URFU16:
    nomer: int
    snils: str
    reg_nomer: int
    prioritet: int
    original: str
    exam01: str
    exam02: str
    exam03: str
    exam04: str
    exam05: str
    exam06: str
    exam07: str
    exam08: str
    dostigeniya: str
    summa: int
    pravo: str
    comment: str = field(default='')

@dataclass
class URFU17:
    nomer: int
    snils: str
    reg_nomer: int
    prioritet: int
    original: str
    exam01: str
    exam02: str
    exam03: str
    exam04: str
    exam05: str
    exam06: str
    exam07: str
    exam08: str
    exam09: str
    dostigeniya: str
    summa: int
    pravo: str
    comment: str = field(default='')

@dataclass
class InfoResult:
    nomer: int
    prioritet: int
    pravo: str
    original: str
    snils: str
    reg_nom: int
    summa: int
    comment: str
    mesto: int

@dataclass
class SPBGUInfo:
    user_id: int
    spec_id: int
    nomer: int
    snils: str
    summ: int
    pravo: bool
    original: bool
    prioritet: int
    dostijeniya: int


def urfu_load_pages():
    user_agent = UserAgent().chrome
    for v in URFU_INNER_VUZ.keys():
        link = f"https://urfu.ru/api/ratings/info/68/{URFU_INNER_VUZ.get(v)}/"
        print('loading from', link)

        resp = requests.get(url=link, headers={'User-Agent': user_agent})
        actual_url_dict = json.loads(resp.text)
        actual_file_name = str(actual_url_dict.get("url")).split("/")[-1]

        actual_full_link = f"https://urfu.ru{actual_url_dict.get("url")}"
        resp = requests.get(actual_full_link, headers={'User-Agent': user_agent})
        page = resp.content.decode('utf-8')

        if not os.path.exists('saved_data/urfu'):
            os.makedirs('saved_data/urfu')
        with open(f"saved_data/urfu/{actual_file_name}", "w") as wf:
            wf.write(page)
        sleep(SLEEP_TIMER)


def get_latest_urfu_files() -> list[str]:
    files_list = os.listdir('saved_data/urfu')
    output = []
    for v_id in URFU_INNER_VUZ.values():
        latest = sorted(list(filter(lambda item: f'00{v_id}' in item, files_list)))[-1]
        output.append(latest)
    return sorted(output)


def get_urfu_spec_users(files_list, vuz_number) -> dict[int, list[URFU9 | URFU12| URFU14 | URFU15 | URFU16 | URFU17]]:
    file_spec = list(filter(lambda item: f'00{URFU_INNER_VUZ.get(vuz_number)}' in item, files_list))[0]

    with open(f"saved_data/urfu/{file_spec}") as rf:
        saved_raw_page = rf.read()

    soup = BeautifulSoup(saved_raw_page, 'lxml')
    tables = soup.find_all('table', {'class': 'table-header'})
    count = 0
    spec_users_dict: dict[int, list[URFU9 | URFU12| URFU14 | URFU15 | URFU16 | URFU17]] = {
        1: [],
        2: [],
        3: [],
        4: []
    }
    for table in tables:
        if URFU_SPEC_ID in table.text:
            count += 1
            tables_data = table.find_next('div').find_next('table')
            accept_plan = table.find_next('div').text
            accept_plan_number = re.search(r'\d+', accept_plan)[0]
            all_tr = tables_data.find_all('tr', {'class': re.compile(r'tr-')})
            for tr in all_tr:
                all_td = tr.find_all('td')
                td_list = [td.text for td in all_td]
                if len(td_list) == 9:
                    user_info = URFU9(*td_list)
                elif len(td_list) == 12:
                    user_info = URFU12(*td_list)
                elif len(td_list) == 14:
                    user_info = URFU14(*td_list)
                elif len(td_list) == 15:
                    user_info = URFU15(*td_list)
                elif len(td_list) == 16:
                    user_info = URFU16(*td_list)
                elif len(td_list) == 17:
                    user_info = URFU17(*td_list)
                if user_info.snils == URFU_USER_ID:
                    user_info.comment = f'план приема {accept_plan_number}   -= !!! =-'
                else:
                    user_info.comment = f'план приема {accept_plan_number}'
                spec_users_dict.get(count).append(user_info)
    return spec_users_dict


def get_urfu_other_users(files_list) -> list[URFU9 | URFU12| URFU14 | URFU15 | URFU16 | URFU17]:
    all_other_users: list[URFU9 | URFU12| URFU14 | URFU15 | URFU16 | URFU17] = []
    for file in files_list:
        with open(f"saved_data/urfu/{file}") as rf:
            saved_raw_page = rf.read()
        soup = BeautifulSoup(saved_raw_page, 'lxml')
        tables = soup.find_all('table', {'class': 'supp table-header', 'id': re.compile(r'\d+')})
        for table in tables:
            if "Форма освоения" not in table.text:
                special_code = re.search(r'\w+.\s\d\d.\d\d.\d\d\s\w+[\w\s-]\w+[\w\s]\w+', table.text)[0]
                # print(special_code)
            tables_data = table.find_next('div').find_next('table', {'class': 'supp'})
            accept_plan = table.find_next('div').text
            accept_plan_number = re.search(r'\d+', accept_plan)[0]
            # print(accept_plan_number)
            all_tr = tables_data.find_all('tr', {'class': re.compile(r'tr-')})
            for tr in all_tr:
                all_td = tr.find_all('td')
                td_list = [td.text for td in all_td]
                if len(td_list) == 9:
                    user_info = URFU9(*td_list)
                elif len(td_list) == 12:
                    user_info = URFU12(*td_list)
                elif len(td_list) == 14:
                    user_info = URFU14(*td_list)
                elif len(td_list) == 15:
                    user_info = URFU15(*td_list)
                elif len(td_list) == 16:
                    user_info = URFU16(*td_list)
                elif len(td_list) == 17:
                    user_info = URFU17(*td_list)
                user_info.comment = f'план приема - {accept_plan_number} чел; {special_code}'
                all_other_users.append(user_info)
    return all_other_users


def urfu():
    print('=== УрФУ ===')
    urfu_load_pages()
    latest_files = get_latest_urfu_files()

    spec_users_dict = get_urfu_spec_users(latest_files, '1') ## see line #16 - VUZ number
    all_other_users = get_urfu_other_users(latest_files)

    count = 0
    kvota = {
        0: 'Отдельная квота',
        1: 'Особая квота',
        2: 'Целевая квота',
        3: 'Основные места'
    }
    now = datetime.now()
    
    for users in spec_users_dict.values():
        # users_with_pravo = list(filter(lambda user: user.pravo == 'Да', users))
        print('\n', kvota.get(count))
        with open(f"Д{now.day}-{now.hour}Ч{now.minute}М-N{count}-{kvota.get(count)}.csv", "w") as wf:
            writer = csv.DictWriter(wf, RESULT_CSV_KEYS)
            writer.writeheader()
            total_count = 1
            for user in users: # [:50]
                # print(f'#{user.nomer} ПРИОРИТЕТ[{user.prioritet}] ПРЕИМ.ПРАВО[{user.pravo if user.pravo else "Не"}] ОРИГ.ДОК[{user.original if user.original else "Не"}] СНИЛС[{user.snils}] РЕГ.№{user.reg_nomer} СУММА={user.summa}   {user.comment}')
                find_list = list(filter(lambda other_user: user.reg_nomer == other_user.reg_nomer, all_other_users))
                if find_list:
                    find_list_sorted = sorted(find_list, key=lambda user: user.prioritet)
                    for find_user in find_list_sorted:
                        if user.prioritet == find_user.prioritet:
                            # print ('\tРАСЧЕТНОЕ МЕСТО =', total_count, '\n')
                            res_user = InfoResult(
                                user.nomer,
                                user.prioritet,
                                user.pravo,
                                user.original,
                                user.snils,
                                user.reg_nomer,
                                user.summa,
                                user.comment,
                                total_count
                            )
                            writer.writerows([asdict(res_user)])
                            total_count += 1
                            break
                        elif (user.prioritet > find_user.prioritet) and (int(find_user.nomer) <= int(re.search(r'\d+', find_user.comment)[0])):
                            print (f'\t#{user.nomer} РЕГ.№{user.reg_nomer} ПРИОР.ПРАВО[{user.pravo if user.pravo else "Не"}] ПРИОРИТЕТ[{user.prioritet}] УХОДИТ на {find_user.comment.split(";")[-1].strip()} #{find_user.nomer} с ПРИОРИТЕТом[{find_user.prioritet}] СНИЛС[{user.snils if user.snils else "---"}]')
                            total_count += 0
                            break
                        else:
                            # print(f'\tПРИОРИТЕТ[{find_user.prioritet}] ПРЕИМ.ПРАВО[{find_user.pravo if find_user.pravo else "Не"}] ОРИГ.ДОК[{find_user.original if find_user.original else "Не"}] #{find_user.nomer} СНИЛС[{find_user.snils}]   {find_user.comment}')
                            res_user = InfoResult(
                                user.nomer,
                                find_user.prioritet,
                                find_user.pravo,
                                find_user.original,
                                find_user.snils,
                                find_user.reg_nomer,
                                find_user.summa,
                                f'#{find_user.nomer} - {find_user.comment}',
                                total_count
                            )
                            writer.writerows([asdict(res_user)])
                if user.snils == URFU_USER_ID:
                    print(f'!!#{user.nomer} РЕГ.№{user.reg_nomer} ПРИОР.ПРАВО[{user.pravo if user.pravo else "Не"}] ПРИОРИТЕТ[{user.prioritet}] --- MECTO: {total_count - 1}/45 СНИЛС[{user.snils}]')
            count += 1


def get_urfu_by_regnom(regnom, count=0):
    print(f'\n{count if count > 0 else ''} === search by REG.№{regnom} ===')
    latest_files = get_latest_urfu_files()
    all_other_users: list[URFU9 | URFU12| URFU14 | URFU15 | URFU16 | URFU17] = get_urfu_other_users(latest_files)
    users_with_regnom: list[URFU9 | URFU12| URFU14 | URFU15 | URFU16 | URFU17] = list(filter(lambda user: user.reg_nomer == regnom, all_other_users))
    users_with_regnom_sorted = sorted(users_with_regnom, key=lambda user: user.prioritet)
    # for user in users_with_regnom_sorted:
    #     plan_priema = re.search(r'\d+', user.comment.split(';')[0])[0]
    #     print(f"[#{user.nomer} из {plan_priema}] ПРИОРИТЕТ[{user.prioritet}] {user.comment.split(';')[-1].strip()};\tСНИЛС[{user.snils if user.snils else '---'}] РЕГ.№{user.reg_nomer} ОРИГ.ДОК[{user.original if user.original else 'Не'}]")
    return users_with_regnom_sorted


def get_urfu_spec_all_info_by_regnom():
    latest_files = get_latest_urfu_files()
    spec_users_dict: dict[int, list[URFU9 | URFU12| URFU14 | URFU15 | URFU16 | URFU17]] = get_urfu_spec_users(latest_files, '1') ## see line #16 - VUZ number
    count = 1
    offset = 65
    now = datetime.now()
    with open(f"Д{now.day}-{now.hour}Ч{now.minute}М-ALL_INFO_0_{offset}.csv", "w") as wf:
        writer = csv.DictWriter(wf, ['number', 'regnom', 'data'])
        writer.writeheader()
        for spec_user in spec_users_dict.get(4)[:offset]:
            data_list = get_urfu_by_regnom(spec_user.reg_nomer, count)
            for data in data_list:
                plan_priema = re.search(r'\d+', data.comment.split(';')[0])[0]
                writer.writerow({
                    "number": count,
                    "regnom": spec_user.reg_nomer,
                    "data": f"[#{data.nomer} из {plan_priema}] ПРИОРИТЕТ[{data.prioritet}] {data.comment.split(';')[-1].strip()};\tСНИЛС[{data.snils if data.snils else '---'}] РЕГ.№{data.reg_nomer} ОРИГ.ДОК[{data.original if data.original else 'Не'}]"
                })
            count += 1


def spbgu_load_pages():
    # spbgu_data_url_old = 'https://application.spbu.ru/enrollee_lists/lists?id='
    spbgu_data_url = 'https://application.spbu.ru/enrollee_lists/list-view-lists?id='

    user_agent = UserAgent().chrome
    for spec_id in SPBGU_SPEC_ID.keys():
        link = f"{spbgu_data_url}{spec_id}"
        print('loading from', link, SPBGU_SPEC_ID.get(spec_id)[0])

        resp = requests.get(url=link, headers={'User-Agent': user_agent})
        json_data = json.loads(resp.text)

        with open(f"saved_data/spbgu/spbgu_{spec_id}_{int(datetime.timestamp(datetime.now()))}.json", "w") as wf:
            json.dump(json_data, wf, ensure_ascii=False, indent=4)
        sleep(SLEEP_TIMER)


def get_latest_spbgu_files() -> list[str]:
    files_list = os.listdir('saved_data/spbgu')
    output = []
    for spec_id in SPBGU_SPEC_ID.keys():
        latest = sorted(list(filter(lambda item: f'spbgu_{spec_id}' in item, files_list)))[-1]
        output.append(latest)
    return sorted(output)


def get_spbgu_spec_users(fileslist, spec_id) -> list[SPBGUInfo]:
    file = list(filter(lambda fn: f'spbgu_{spec_id}' in fn, fileslist))[0]
    spec_users_list: list[SPBGUInfo] = []
    with open(f"saved_data/spbgu/{file}") as rf:
        json_data = json.load(rf)
        # print(json_data, len(json_data))
        for data in json_data.get('list'):
            spec_user = SPBGUInfo(
                data.get('id'),
                data.get('competitive_group_id'),
                data.get('order_number'),
                data.get('user_code'),
                data.get('score_overall'),
                data.get('preemptive_right'),
                data.get('original_document'),
                data.get('priority_number'),
                data.get('score_achievements')
            )
            spec_users_list.append(spec_user)
    return spec_users_list


def get_spbgu_other_users(fileslist, spec_id) -> list[SPBGUInfo]:
    other_files = list(filter(lambda fn: f'spbgu_{spec_id}' not in fn, fileslist))
    other_users_list: list[SPBGUInfo] = []
    for file in other_files:
        with open(f"saved_data/spbgu/{file}") as rf:
            json_data = json.load(rf)
            # print(json_data, len(json_data))
            for data in json_data.get('list'):
                spec_user = SPBGUInfo(
                    data.get('id'),
                    data.get('competitive_group_id'),
                    data.get('order_number'),
                    data.get('user_code'),
                    data.get('score_overall'),
                    data.get('preemptive_right'),
                    data.get('original_document'),
                    data.get('priority_number'),
                    data.get('score_achievements')
                )
                other_users_list.append(spec_user)
    return other_users_list


def spbgu():
    print('\n\n=== СПбГУ ===')
    spbgu_load_pages()
    latest_files = get_latest_spbgu_files()
    spec_users_list = get_spbgu_spec_users(latest_files, '095')
    other_users_list = get_spbgu_other_users(latest_files, '095')
    total_count = 1
    now = datetime.now()

    with open(f"Д{now.day}-{now.hour}Ч{now.minute}М-СПбГУ-Биология.csv", "w") as wf:
        writer = csv.DictWriter(wf, RESULT_CSV_KEYS)
        writer.writeheader()
        for spec_user in spec_users_list:
            spec_id = str(spec_user.spec_id) if len(str(spec_user.spec_id)) == 3 else f'0{spec_user.spec_id}'
            # print('\n', spec_user)
            find_result = list(filter(lambda user: user.snils == spec_user.snils, other_users_list))
            find_result_sorted = sorted(find_result, key=lambda user: user.prioritet)
            if find_result_sorted:
                for u in find_result_sorted:
                    other_id = str(u.spec_id) if len(str(u.spec_id)) == 3 else f'0{u.spec_id}'
                    # print('\t', u, SPBGU_SPEC_ID.get(other_id)[0])
                    if spec_user.prioritet < u.prioritet:
                        # print(f"\tMECTO: {total_count}/{SPBGU_SPEC_ID.get(spec_id)[1]}")
                        _ = InfoResult(
                            spec_user.nomer,
                            spec_user.prioritet,
                            "Да" if spec_user.pravo else '',
                            "Да" if spec_user.original else '',
                            spec_user.snils,
                            spec_user.spec_id,
                            spec_user.summ,
                            "-= !!! =-" if spec_user.snils == SPBGU_USER_ID else '',
                            total_count
                        )
                        writer.writerows([asdict(_)])
                        total_count += 1
                        break
                    elif (spec_user.prioritet > u.prioritet) and (u.nomer <= SPBGU_SPEC_ID.get(other_id)[1]):
                        print(f"\t#{spec_user.nomer} ПРИОРИТЕТ[{spec_user.prioritet}] УХОДИТ на {SPBGU_SPEC_ID.get(other_id)[0]} (ID={other_id}) с ПРИОРИТЕТом[{u.prioritet}] на место {u.nomer}/{SPBGU_SPEC_ID.get(other_id)[1]}")
                        break
                    else:
                        # print(f"\tMECTO: {total_count}/{SPBGU_SPEC_ID.get(spec_id)[1]}")
                        _ = InfoResult(
                            spec_user.nomer,
                            spec_user.prioritet,
                            "Да" if spec_user.pravo else '',
                            "Да" if spec_user.original else '',
                            spec_user.snils,
                            spec_user.spec_id,
                            spec_user.summ,
                            "-= !!! =-" if spec_user.snils == SPBGU_USER_ID else '',
                            total_count
                        )
                        writer.writerows([asdict(_)])
                        total_count += 1
                        break
            else:
                # print(f"\tMECTO: {total_count}/{SPBGU_SPEC_ID.get(spec_id)[1]}")
                _ = InfoResult(
                    spec_user.nomer,
                    spec_user.prioritet,
                    "Да" if spec_user.pravo else '',
                    "Да" if spec_user.original else '',
                    spec_user.snils,
                    spec_user.spec_id,
                    spec_user.summ,
                    "-= !!! =-" if spec_user.snils == SPBGU_USER_ID else '',
                    total_count
                )
                writer.writerows([asdict(_)])
                total_count += 1
            if spec_user.snils == SPBGU_USER_ID:
                print(f'!!#{spec_user.nomer} СНИЛС[{spec_user.snils}] ПРИОРИТЕТ[{spec_user.prioritet}] --- MECTO: {total_count - 1}/{SPBGU_SPEC_ID.get(spec_id)[1]}')


def main():
    urfu()
    spbgu()
    get_urfu_spec_all_info_by_regnom()

    # data_list = get_urfu_by_regnom('331062')
    # for data in data_list:
    #     plan_priema = re.search(r'\d+', data.comment.split(';')[0])[0]
    #     print(f"[#{data.nomer} из {plan_priema}] ПРИОРИТЕТ[{data.prioritet}] {data.comment.split(';')[-1].strip()};\tСНИЛС[{data.snils if data.snils else '---'}] РЕГ.№{data.reg_nomer} ОРИГ.ДОК[{data.original if data.original else 'Не'}]")


if __name__ == '__main__':
    main()
