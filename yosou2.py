import sqlite3
import requests
from bs4 import BeautifulSoup
import re
import numpy as np
import pandas as pd

def nk_denma():
    URL = 'http://race.netkeiba.com'
    payload = {'pid': 'race_list'}
    r = requests.get(URL, params=payload)
    r.encoding = r.apparent_encoding
    soup = BeautifulSoup(r.text, 'lxml')

    race_info = soup.select('.race_top_hold_list')
    result = []
    for i in race_info:
        race_top_hold_data = i.select('.race_top_hold_data')[0]
        kaisai_data = race_top_hold_data.select('.kaisaidata')[0].text
        jyo_data = race_top_hold_data.select('.jyodata')[0].text
        racenames = i.select('.racename')
        race_names = list(map(lambda x: x.a.text, racenames))
        race_links = list(map(lambda x: URL + x.a['href'], racenames))
        race_numbers = list(map(img_alt, i.select('img')))
        race_numbers = list(filter(lambda x: x != None, race_numbers))
        race_numbers = list(filter(lambda x: re.match('\d+R', x), race_numbers))
        race_data = list(map(lambda x: x.text.strip(), i.select('.racedata')))
        place = [kaisai_data, jyo_data]
        for i in range(len(race_numbers)):
            place.append([race_numbers[i], race_names[i], race_data[i], race_links[i]])
        result.append(place)

    return result

def img_alt(obj):
    try:
        return obj['alt']
    except:
        return None

def horse_id_list(race_link):
    r = requests.get(race_link)
    r.encoding = r.apparent_encoding
    soup = BeautifulSoup(r.text, 'lxml')
    result = list(map(lambda x: x['href'], soup.find_all('a', href=re.compile('http://db\.netkeiba\.com/horse/\d+/'))))
    result = list(map(lambda x: int(re.search('\d+', x).group()), result))
    return result

def horse_info(race_link):
    r = requests.get(race_link)
    r.encoding = r.apparent_encoding
    soup = BeautifulSoup(r.text, 'lxml')
    result = list(map(lambda x: x.find_all('td'), soup.select('.bml1')))
    detail = lambda x: [x[0].text, x[1].text, x[3].text.replace('\n', ''), \
    x[4].text, x[5].text, x[6].text, x[7].text, x[8].text, x[9].text, re.search('/horse/(\d+)/', x[3].a['href']).group(1)]
    result = list(map(detail, result))
    return result

def race_ichiran():
    for i in nk_denma():
        for j in i:
            print(j)

def horse_csv(race_link):
    import zensou
    work = horse_id_list(race_link)
    for i in work:
        data = zensou.df(i)
        data.to_csv(str(i) + '.csv')

def data_frame(horse_id):
    con = sqlite3.connect('netkeiba.db')
    cur = con.cursor()
    cur.execute('select * from horse_x_race inner join race on horse_x_race.race_id=race.race_id where horse_id=? order by hiduke desc', [horse_id])
    history = cur.fetchall()
    df = pd.DataFrame(history, columns=list(map(lambda x: x[0], cur.description)))
    return df

if __name__ == '__main__':
    con = sqlite3.connect('netkeiba.db')
    cur = con.cursor()
    denma = nk_denma()
    for basho in denma:
        kaisai = basho[0]
        weather_baba = basho[1]
        races = basho[2:]
        for race in races:
            rlink = race[-1]
            horses = horse_info(rlink)
            for horse in horses:
                hid = horse[-1]
                cur.execute('select * from horse_x_race inner join race on horse_x_race.race_id=race.race_id where horse_id=? order by hiduke desc', [hid])
                history = cur.fetchall()
                print(len(history))
            else:
                import pdb; pdb.set_trace()
    con.close()
