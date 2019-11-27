import datetime as dt
import requests
from bs4 import BeautifulSoup
import re
from babaCode import n2c
import numpy as np
import time
from selenium import webdriver

url = 'https://race.netkeiba.com/?pid=race_list'
r = requests.get(url)
r.encoding = r.apparent_encoding
soup = BeautifulSoup(r.text, 'lxml')
places = soup.select('.race_top_hold_list')
race_list = []
for place in places:
    kaisaidata = place.find('p', class_='kaisaidata')
    re_obj = re.search('(\d)回([^\d]+)(\d+)日目', kaisaidata.text)
    place_str = re_obj.group(2)
    place_code = hex(n2c(place_str))[-1]
    kaisuu = re_obj.group(1)
    day = hex(int(re_obj.group(3)))[-1]

    races = place.select('.race_top_data_info')
    for race in races:
        race_num_str = int(race.img['alt'].replace('R', ''))
        race_num = hex(race_num_str)[-1]
        racedata = race.find('div', class_='racedata')
        hassou = re.search('\d{2}:\d{2}', racedata.text).group()
        race_list.append([place_code, kaisuu, day, race_num, hassou])
else:
    for i in range(len(race_list)-1):
        for j in range(len(race_list)-i-1):
            if race_list[j][4] > race_list[j+1][4]:
                race_list[j], race_list[j+1] = race_list[j+1], race_list[j]
    print(race_list)

browser = webdriver.Chrome()
browser.set_window_size(854+50, 480+5)
date = dt.datetime.today().strftime('%Y/%Y%m%d/%y')
for i, race in enumerate(race_list):
    if race[4] < dt.datetime.now().strftime('%H:%M'):
        continue
    place_code = race[0]
    kaisuu = race[1]
    day = race[2]
    race_num = race[3]
    target = 'race/' + date + place_code + kaisuu + day + race_num + '_p'
    url = 'https://regist.prc.jp/api/windowopen.aspx?target=' + target + '&quality=1'
    # TODO: ログインの自動化
    browser.get(url)

    twenty_minutes_later = (dt.datetime.now() + dt.timedelta(minutes=20)).strftime('%H:%M')
    next_race = race_list[i+1][4]
    while twenty_minutes_later < next_race:
        time.sleep(60)
        twenty_minutes_later = (dt.datetime.now() + dt.timedelta(minutes=20)).strftime('%H:%M')
