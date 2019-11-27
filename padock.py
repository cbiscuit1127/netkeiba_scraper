import requests
from selenium import webdriver
from babaCode import c2n
import sqlite3
import datetime as dt

race_id = 201910010101

race_num = race_id % 100
race_kaisuu = race_id // 100 % 100
race_kaisai = race_id // 100 ** 2 % 100
race_course = race_id // 100 ** 3 % 100
race_Year = race_id // 100 ** 4
race_year = race_id // 100 ** 4 % 100

with sqlite3.connect('netkeiba.db') as con:
    cur = con.cursor()
    cur.execute('select hiduke from race where race_id=?', (race_id, ))
    hiduke = dt.datetime.strptime(cur.fetchone()[0], '%Y-%m-%d %H:%M:%S')
    prc_hiduke = hiduke.strftime('%Y%m%d')
    prc_id = '{:0=2}{:x}{:x}{:x}{:x}'.format(race_year, race_course, race_kaisai, race_kaisuu, race_num)
    url = 'https://regist.prc.jp/api/windowopen.aspx?target=race/' + str(race_Year) + '/' + prc_hiduke + '/'+ prc_id + '_p&quality=1'

    browser = webdriver.Chrome()
    browser.get(url)

    try:
        browser.find_element_by_id('btnJravan').click()
        browser.find_element_by_id('jvuserid').send_keys("nagasakihakyoumoamedatta@gmail.com")
        pswd = input('パスワードを入力：')
        browser.find_element_by_id('jvpass').send_keys(pswd)
        browser.find_element_by_id('tnRogin').click()
    except:
        pass

    sql = 'select umaban, horse_name, weight from horse_x_race where race_id=? order by umaban asc'
    cur.execute(sql, [race_id])
    horse_list = cur.fetchall()
    for horse in horse_list:
        print(horse[0], horse[1], horse[2])
    while True:
        str = input('「馬番または馬名 評価（5点満点）またはコメント」の形式で入力：')
        search_text = str.split(' ')[0]
        ev_or_comment = str.split(' ')[1]
        if ev_or_comment in range(1, 6):
            evaluation = ev_or_comment
            comment = ''
        else:
            evaluation = 0
            comment = ev_or_comment
        sql = 'select horse_id from horse_x_race where umaban=? or horse_name like ?'
        cur.execute(sql, [search_text, '%' + search_text + '%'])
        horse_id = cur.fetchone()[0]
        sql = 'select evaluation, comment from padock where horse_id=? and race_id=?'
        cur.execute(sql, [horse_id, race_id])
        try:
            sql = 'update padock set evaluation=? and comment=? where horse_id=? and race_id=?'
            padock_record = cur.fetchone()
            con.execute(sql, [max(padock_record[0], evaluation), padock_record[1] + comment, horse_id, race_id])
        except:
            sql = 'insert into padock values(?, ?, ?, ?, ?)'
            con.execute(sql, [0, horse_id, race_id, evaluation, comment])
        con.commit()
