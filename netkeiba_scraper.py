import requests
from bs4 import BeautifulSoup
import csv
import sqlite3
from netkeiba_lib import *
import datetime as dt
import re
from babaCode import c2n
from babaCode import n2c
from selenium import webdriver
from tqdm import tqdm
import time as tm
import configparser

def netkeiba_scraper():
    # open kaisai file
    f = open('kaisai.csv', 'r')
    reader = csv.reader(f)
    kaisai = []
    for row in reader:
        kaisai.append(row)
    f.close()

    pbar = tqdm(total = len(kaisai))
    print()

    # open database
    con = sqlite3.connect('netkeiba.db')
    cur = con.cursor()

    # initialize database
    def db_initialize():
        sql = 'drop table if exists race'
        con.execute(sql)
        sql = 'drop table if exists horse'
        con.execute(sql)
        sql = 'drop table if exists training'
        con.execute(sql)
        sql = 'drop table if exists padock'
        con.execute(sql)
        sql = 'drop table if exists error'
        con.execute(sql)
        sql = 'create table race (id integer, race_id integer, race_name text, track text, distance integer, weather text, condition text, hiduke text, kaisai_kaisuu integer, course text, kaisai_date integer, class text, race_lap text, baba_ind integer, baba_comment text, corner_pass_order, race_comment text)'
        con.execute(sql)
        sql = 'create table horse_x_race (id integer, horse_id integer, horse_name text, race_id integer, chakujun integer, wakuban integer, umaban integer, gender text, age text, handicap integer, jockey text, time real, chakusa text, time_ind integer, tsuuka text, agari real, win real, ninki integer, weight integer, kyuusha_comment text, bikou text, trainer text, trainer_place text, owner text, race_tanpyo text)'
        con.execute(sql)
        sql = 'create table training (id integer, horse_id integer, race_id integer, hiduke text, course text, condition text, noriyaku text, time text, comment text, position integer, ashiiro text, evaluation_comment text, evaluation text)'
        con.execute(sql)
        sql = 'create table padock (id integer, horse_id integer, race_id integer, evaluation integer, comment text)'
        con.execute(sql)
        sql = 'create table error_race(id integer, race_id integer, comment text)'
        con.execute(sql)

    # comment out if & only if you do not want to initialize DB.
    #db_initialize()

    # count race record length
    cur.execute('select count(*) from race')
    race_count = cur.fetchone()[0]

    # count horse_x_race record length
    cur.execute('select count(*) from horse_x_race')
    horse_x_race_count = cur.fetchone()[0]

    # netkeiba.comにログイン
    s = requests.session()
    login(s)

    browser = webdriver.Chrome()

    last_update_list = last_update()
    print(last_update_list)

    for i in kaisai:
        pbar.update(1)
        for j in range(1, 13): # TODO: 1-12Rを並列化
            race_number = str(j).zfill(2)
            race_id = i[0] + i[1].zfill(2) + i[2].zfill(2) + i[3].zfill(2) + race_number

            # 最新のレースよりあとのレースだけ取得
            place_last_race_id = last_update_list[int(i[1])-1]
            if place_last_race_id >= int(race_id):
                continue
            cur.execute('select * from race where race_id = ?', [race_id])
            exist = len(cur.fetchall())

            try:
                if exist == 0:
                    # ソースを取得
                    course = c2n(int(i[1]), 1)
                    kaisai_kaisuu = i[2]
                    kaisai_date = i[3]

                    t1 = tm.time()

                    soup = getsoup(s, race_id)

                    t2 = tm.time()
                    '''
                    # デバッグ用
                    with open(race_id + '.txt', 'wt', encoding='utf-8') as f:
                        f.write(soup.text)
                    '''
                    race_data = soup.select('.data_intro')[0]
                    race_table = soup.select('.race_table_01')[0].find_all('tr')
                    try:
                        race_lap = soup.select('.race_lap_cell')[0].text.replace(' ', '')
                    except:
                        # 障害競走用
                        race_lap = ''

                    race_name = race_data.h1.text.strip()
                    search_text = race_data.select('.smalltxt')[0].text
                    race_age = re.search('サラ.+歳上?', search_text).group()
                    race_class = re.search('(新馬|未勝利|\d+万下|オープン)', search_text).group()
                    race_jouken = race_data.span.text.split('\xa0/\xa0')
                    track_and_distance = race_jouken[0]
                    track = track_and_distance[0]
                    distance = re.search('(\d+)m', track_and_distance).group(1)
                    weather = race_jouken[1].replace('天候 : ', '')
                    condition = race_jouken[2].lstrip('芝ダート : ')
                    hiduke = dt.datetime.strptime(race_data.select('.smalltxt')[0].text.split(' ')[0], '%Y年%m月%d日')
                    print(hiduke, course, race_id, race_name, race_age, race_class, race_lap)
                    try:
                        baba_ind = re.search('-?\d+', soup.find(summary='馬場情報').find_all('tr')[0].td.text).group()
                    except:
                        # 障害競走用
                        baba_ind = ''

                    try:
                        baba_comment = soup.find(summary='馬場情報').find_all('tr')[1].td.text
                    except:
                        baba_comment = ''

                    try:
                        corner_pass_order = soup.find(summary='コーナー通過順位')
                        rows = corner_pass_order.find_all('tr')
                        corner_pass_order_str = ''
                        for row in rows:
                            corner_pass_order_str += row.th.text + ':' + row.td.text + ','
                    except:
                        corner_pass_order_str = ''

                    try:
                        race_comment = soup.find(summary='レース分析').td.text
                    except:
                        race_comment = ''

                    try:
                        race_tanpyo_list = soup.find(summary='注目馬 レース後の短評').find_all('tr')
                    except:
                        race_tanpyo_list = []

                    sql = 'insert into race values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
                    race_count += 1
                    con.execute(sql, [race_count, race_id, race_name, track, distance, weather, condition, hiduke, kaisai_kaisuu, course, kaisai_date, race_class, race_lap, baba_ind, baba_comment, corner_pass_order_str, race_comment])

                    for row in race_table:
                        cols = row.find_all('td')
                        if len(cols):
                            chakujun = cols[0].text
                            wakuban = cols[1].text
                            umaban = cols[2].text
                            horse_name = cols[3].text.strip()
                            race_tanpyo = ''
                            for num in range(int(len(race_tanpyo_list)/2)):
                                tanpyo_title = race_tanpyo_list[2*num].th.text
                                init_pos = tanpyo_title.find(horse_name)
                                if init_pos != -1:
                                    race_tanpyo += race_tanpyo_list[2*num+1].td.text
                            horse_id = re.search('[0-9]+', cols[3].a['href']).group()
                            gender = cols[4].text[0]
                            age = cols[4].text[1:]
                            handicap = cols[5].text
                            jockey = cols[6].text.strip()
                            time_str = cols[7].text.split(':')
                            try:
                                time = int(time_str[0]) * 60 + float(time_str[1])
                            except:
                                time = 0
                            chakusa = cols[8].text
                            time_ind = cols[9].text
                            tsuuka = cols[10].text
                            agari = cols[11].text
                            win = cols[12].text
                            ninki = cols[13].text
                            weight = cols[14].text
                            try:
                                choukyou_url = cols[15].a['href']
                            except:
                                choukyou_url = ''
                            try:
                                kyuusha_comment = cols[16].a['href']
                            except:
                                kyuusha_comment = ''
                            bikou = cols[17].text.strip()
                            trainer = cols[18].text.strip().replace('\n', '')
                            trainer_place = trainer[1:2]
                            trainer = trainer[3:]
                            owner = cols[19].text.strip()

                            if True:
                                sql = 'insert into horse_x_race values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
                                horse_x_race_count += 1
                                con.execute(sql, [horse_x_race_count, horse_id, horse_name, race_id, chakujun, wakuban, umaban, gender, age, handicap, jockey, time, chakusa, time_ind, tsuuka, agari, win, ninki, weight, kyuusha_comment, bikou, trainer, trainer_place, owner, race_tanpyo])

                            # get training data
                            # 現状の問題点：時間がかかる。
                            '''
                            if choukyou_url:
                                choukyou_url = '/?pid=horse_comment&id=' + horse_id + '&rid=' + race_id
                                r = s.get('http://db.netkeiba.com' + choukyou_url)
                                r.encoding = r.apparent_encoding
                                choukyou_soup = BeautifulSoup(r.text, 'lxml')
                                choukyou_table = choukyou_soup.find(summary='調教タイム').find_all('tr')
                                for tr in choukyou_table:
                                    choukyou_cols = tr.find_all('td')
                                    if len(choukyou_cols):
                                        choukyou_hiduke = choukyou_cols[0].text[:-3]
                                        choukyou_course = choukyou_cols[1].text
                                        choukyou_condition = choukyou_cols[2].text
                                        choukyou_noriyaku = choukyou_cols[3].text
                                        try:
                                            training_time_data_list = choukyou_cols[4].select('.TrainingTimeDataList')[0].find_all('li')
                                            training_time_data_list = list(filter(lambda x: x.text!='-', training_time_data_list))
                                            training_time_data_list = list(map(lambda x: x.text, training_time_data_list))
                                            training_time_data_str = '-'.join(training_time_data_list)
                                            choukyou_time = training_time_data_str

                                            training_heisou = choukyou_cols[4].select('.TrainingHeisou')
                                            training_heisou = list(map(lambda x: x.text, training_heisou))
                                            training_heisou_str = ','.join(training_heisou)
                                            choukyou_comment = training_heisou_str
                                        except:
                                            choukyou_time = ''
                                            choukyou_comment = choukyou_cols[4].text
                                        choukyou_position = choukyou_cols[5].text
                                        choukyou_ashiiro = choukyou_cols[6].text
                                        choukyou_evaluation_comment = choukyou_cols[7].text
                                        choukyou_evaluation = choukyou_cols[8].text
                                        sql = 'insert into training values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
                                        con.execute(sql, [1, horse_id, race_id, choukyou_hiduke, choukyou_course, choukyou_condition, choukyou_noriyaku, choukyou_time, choukyou_comment, choukyou_position, choukyou_ashiiro, choukyou_evaluation_comment, choukyou_evaluation])
                            '''
                    con.commit()

                    t3 = tm.time()
                    print(t2-t1, t3-t2)
            except (AttributeError, IndexError) as err:
                print('Error: {}'.format(err))
            except:
                cur.execute('select * from error_race where race_id=?', [race_id])
                error_cleared = cur.fetchall()
                if len(error_cleared) == 0:
                    error_url = 'http://db.netkeiba.com/race/' + race_id
                    browser.get(error_url)
                    '''
                    error_comment = input('>> ')
                    command = ''
                    while command not in ['quit', 'exit', 'continue', 'break']:
                        command = input('>> ')
                    '''
                    error_comment = 'Error'
                    cur.execute('select * from error_race')
                    errors = cur.fetchall()
                    sql = 'insert into error_race values(?, ?, ?)'
                    con.execute(sql, [len(errors)+1, race_id, error_comment])
                    con.commit()

    pbar.close()

    # close database
    con.commit()
    con.close()
    browser.quit()

def last_update():
    result = []
    config = configparser.ConfigParser()
    config.read('settings.ini')
    try:
        config.add_section('last_update')
    except:
        pass
    with sqlite3.connect('netkeiba.db') as con:
        f = open('settings.ini', 'w')
        cur = con.cursor()
        for i in range(1, 11):
            place = c2n(i)
            cur.execute('select * from (select race_id from race where course=?) order by race_id desc', [place])
            last_update = cur.fetchone()[0]
            result.append(last_update)
            config.set('last_update', str(i), str(last_update))
        config.write(f)
        f.close()
    return result

if __name__ == '__main__':
    netkeiba_scraper()
