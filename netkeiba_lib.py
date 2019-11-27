# -*- coding:utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import requests
import re
import sqlite3
import csv
from tqdm import tqdm
import pandas as pd

# driver = webdriver.Chrome()
'''
def netkeiba_login(driver):
    driver.get('http://regist.netkeiba.com/account?pid=login')
    login_id = driver.find_element_by_name('login_id')
    login_id.send_keys('nagasakihakyoumoamedatta@gmail.com')
    pswd = driver.find_element_by_name('pswd')
    pswd.send_keys('ここにパスワードを入力')
    loginbox = driver.find_element_by_class_name('loginbox')
    loginbox.find_element_by_xpath('//*[@type="image"]').click()
'''
# driver.quit()

# s = requests.session()

def login(s):
    payload = {
        'pid': 'login',
        'action': 'auth',
        'return_url2': None,
        'mem_tp': None,
        'login_id': 'nagasakihakyoumoamedatta@gmail.com',
        'pswd': 'mocha1225keiba'
    }
    s.post('https://regist.netkeiba.com/account/', data=payload)

# get BeautifulSoup object from race ID
def getsoup(s, race_id):
    r = s.get('http://db.netkeiba.com/race/' + race_id)
    r.encoding = r.apparent_encoding
    soup = BeautifulSoup(r.text, 'lxml')
    return soup

def getpayouts(soup):
    pay_tables = soup.find_all(summary='払い戻し')
    tan = pay_tables[0].select('.tan')[0].parent.find_all('td')
    try:
        fuku = pay_tables[0].select('.fuku')[0].parent.find_all('td')
    except:
        fuku = '複勝の発売はありません'
    try:
        waku = pay_tables[0].select('.waku')[0].parent.find_all('td')
    except:
        waku = '枠連の発売はありません'
    uren = pay_tables[0].select('.uren')[0].parent.find_all('td')
    wide = pay_tables[1].select('.wide')[0].parent.find_all('td')
    utan = pay_tables[1].select('.utan')[0].parent.find_all('td')
    sanfuku = pay_tables[1].select('.sanfuku')[0].parent.find_all('td')
    santan = pay_tables[1].select('.santan')[0].parent.find_all('td')
    payouts = {
        'tan': tan,
        'fuku': fuku,
        'waku': waku,
        'uren': uren,
        'wide': wide,
        'utan': utan,
        'sanfuku': sanfuku,
        'santan': santan
    }

    dbdata = []
    for i in payouts:
        try:
            row = []
            for j in range(2):
                text = re.search('<td( class="txt_r")?>(.+)</td>', str(payouts[i][j])).group(2)
                text2 = text.replace(' ', '').replace(',', '').replace('→', '-').split('<br/>')
                row.append(text2)
                if j == 1:
                    for k in range(len(text2)):
                        row2 = [i, row[0][k], row[1][k]]
                        dbdata.append(row2)
        except:
            pass
    return dbdata

def getpassage(soup):
    passages = soup.find(summary='コーナー通過順位').find_all('td')
    passages = list(map(lambda x: x.text, passages))
    return passeges

# 同着処理
# create table payout (id, race_id, win, place, bracket_quinella, quinella, quinella_place, exacta, trio, trifecta)
# create table kaisai (id, year, course, kaisuu, kaisainissuu)
# def updatekaisai():
# create table parent (id, horse_id, sire, blood_mare)

def shussou_race_id(horse_id):
    with sqlite3.connect('netkeiba.db') as con:
        cur = con.cursor()
        sql = 'select race_id from horse where horse_id=?'
        cur.execute(sql, [horse_id])
        races = cur.fetchall()
        races = list(map(lambda x: x[0], races))
    return races

def return_id(horse_name):
    with sqlite3.connect('netkeiba.db') as con:
        cur = con.cursor()
        sql = 'select horse_id from horse where horse_name=?'
        cur.execute(sql, [horse_name])
        return cur.fetchone()[0]

def race_detail(race_id, cur=None):
    if cur == None:
        with sqlite3.connect('netkeiba.db') as con:
            cur = con.cursor()
            sql = 'select * from race where race_id=?'
            cur.execute(sql, [race_id])
            race_detail = cur.fetchone()
            sql = 'select * from horse where race_id=?'
            cur.execute(sql, [race_id])
            horse_detail = cur.fetchall()
        return [race_detail, horse_detail]
    else:
        sql = 'select * from race where race_id=?'
        cur.execute(sql, [race_id])
        race_detail = cur.fetchone()
        sql = 'select * from horse where race_id=?'
        cur.execute(sql, [race_id])
        horse_detail = cur.fetchall()
        return [race_detail, horse_detail]

def horse_detail(race_id, horse_id, cur=None):
    if cur == None:
        with sqlite3.connect('netkeiba.db') as con:
            cur = con.cursor()
            sql = 'select * from horse where horse_id=? and race_id=?'
            cur.execute(sql, [horse_id, race_id])
            result = cur.fetchone()
        return result
    else:
        sql = 'select * from horse where horse_id=? and race_id=?'
        cur.execute(sql, [horse_id, race_id])
        result = cur.fetchone()
        return result

def update_kyuusha_comment():
    with sqlite3.connect('netkeiba.db') as con:
        cur = con.cursor()
        sql = 'select kyuusha_comment as kc from horse_x_race where kc like "/%"'
        cur.execute(sql)
        result = list(map(lambda x: x[0], cur.fetchall()))
        s = requests.session()
        login(s)
        pbar = tqdm(total=int(len(result)/100))
        for num, i in enumerate(result):
            url = 'http://db.netkeiba.com' + i
            r = s.get(url)
            r.encoding = r.apparent_encoding
            kcsoup = BeautifulSoup(r.text, 'lxml')
            # import pdb; pdb.set_trace()
            kc = kcsoup.select('.db_main_deta')[0].table.table.find_all('td')[1].text
            sql = 'update horse_x_race set kyuusha_comment=? where kyuusha_comment=?'
            print(kc)
            con.execute(sql, [kc, i])
            if (num + 1) % 100 == 0:
                con.commit()
                pbar.update(1)
        con.commit()
        pbar.close

def update_choukyou():
    with sqlite3.connect('netkeiba.db') as con:
        cur = con.cursor()
        cur.execute('select race_id, horse_id from horse')
        s = requests.session()
        login(s)

def getallraceid():
    with sqlite3.connect('netkeiba.db') as con:
        cur = con.cursor()
        sql = 'select race_id from race'
        cur.execute(sql)
        result = list(map(lambda x: x[0], cur.fetchall()))
    return result

def race_lap_str_to_list(str):
    result = str.split('-')
    result = list(map(lambda x: float(x), result))
    return result

def race_lap_list_to_str(list_):
    result = '-'.join(list_)
    return result

def course_data_initialize():
    '''コース形態のメンテナンス'''
    with open('course.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        with sqlite3.connect('netkeiba.db') as con:
            sql = 'drop table if exists course'
            con.execute(sql)
            sql = 'create table course (id integer, place text, track text, distance integer, start real, chokusen real, corner integer, bikou text, size text, saka text, houkou text)'
            con.execute(sql)
            sql = 'insert into course values(?,?,?,?,?,?,?,?,?,?,?)'
            for i, j in enumerate(reader):
                list_ = [i] + j
                con.execute(sql, list_)
            con.commit()

def first_lap_speed_per_two_furlong(distance, time_):
    first_lap_length = distance % 200
    result = time_ * 200 / first_lap_length
    return result

def time_list(course='東京', track='芝', distance=1600):
    with sqlite3.connect('netkeiba.db') as con:
        cur = con.cursor()
        sql = 'select horse_x_race.race_id, chakujun, time, agari from horse_x_race inner join race on horse_x_race.race_id=race.race_id \
        where course=? and track=? and distance=?'
        cur.execute(sql, [course, track, distance])
        result = cur.fetchall()
        pattern = '\d+$'
        match = lambda row: re.search(pattern, str(row[1]))
        result = list(filter(match, result))
        header = list(map(lambda x: x[0], cur.description))
    result = pd.DataFrame(result, columns=header)
    return result
