import csv
f = open('babaCode.csv', 'r', encoding='utf-8')
reader = csv.reader(f)
rows = []
for row in reader:
    rows.append(row)
f.close()

#mode: 0 keiba.go.jp/kichiuma-chiho.net ; 1 netkeiba.com;

def n2c(name, mode=0):#name to code
    for row in rows:
        if name == row[3]:
            result = int(row[mode+1])
            return result
    else:
        return ''

def c2n(code, mode=0):#code to name
    for row in rows:
        if code == int(row[mode+1]):
            result = row[3]
            return result
    else:
        return ''

def ichiran(cat = 0, mode=0):
    for row in rows:
        if cat == 0 or (cat == 1 and row[0] == 'j') or (cat == 2 and row[0] == 'n'):
            print(row[1+mode] + ' ' + row[3], end=' ')
    print('')

def kaisai(mode=0):
    import urllib.request
    from bs4 import BeautifulSoup

    url = 'http://www2.keiba.go.jp/KeibaWeb/TodayRaceInfo/TodayRaceInfoTop'
    res = urllib.request.urlopen(url)
    soup = BeautifulSoup(res, 'html.parser')
    baba = soup.select('.dbdata3')[1].find_all('a')
    result = []
    for i in baba:
        if i.span.text == '帯広ば':
            continue
        result.append([n2c(i.span.text, mode), i.span.text])
    for i in result:
        print(i[0], i[1], end=' ')
    print()
    return result
