#「Yahoo競馬」から開催一覧を取得して「kaisai.csv」に出力するプログラム
import urllib.request
from bs4 import BeautifulSoup
import csv

f = open('kaisai.csv', 'wt', newline='', encoding='utf-8')
writer = csv.writer(f)

START = 2019
for i in range(2020-START):
    print(i+START)
    for j in range(10):
        try:
            url = 'https://keiba.yahoo.co.jp/schedule/list/'+str(i+START)+'/?place='+str(j+1).zfill(2)
            res = urllib.request.urlopen(url)
            soup = BeautifulSoup(res, 'html.parser')
            rows = soup.select('.mgnBS')[1].find_all('tr')
            for k in rows:
                try:
                    text = k.td.a.text
                    lists = text.split('回')
                    kai = int(lists[0].strip())
                    nichi = int(lists[1][2:-1])
                    row = [i+START, j+1, kai, nichi]
                    writer.writerow(row)
                except:
                    pass
        except:
            pass

f.close()
