import sqlite3
import numpy as np
from netkeiba_lib import race_lap_str_to_list
from netkeiba_lib import race_lap_list_to_str
import csv

def kijun_time():
    f = open('kijun_time.csv', 'wt', newline='', encoding='utf-8')

    kt_con = sqlite3.connect('kijun_time.db')
    kt_con.execute('drop table if exists race_lap')
    kt_con.execute('create table race_lap(place, track, distance, race_lap_avg, race_lap_std)')
    kt_con.execute('drop table if exists fnl')
    kt_con.execute('create table fnl(place, track, distance, former_avg, latter_avg, former_std, latter_std)')
    kt_con.commit()

    with sqlite3.connect('netkeiba.db') as con:
        cur = con.cursor()

        # calculate avg & std of each course
        sql = "select course, track, distance from race where track<>'障' group by course, track, distance"
        cur.execute(sql)
        courses = cur.fetchall()
        for course in courses:
            sql = 'select race_lap from race where course=? and track=? and distance=?'
            cur.execute(sql, course)
            race_laps = cur.fetchall()
            race_laps = list(map(lambda x: race_lap_str_to_list(x[0]), race_laps))
            race_laps = np.asarray(race_laps)
            race_lap_avg = np.mean(race_laps, axis=0)
            # TODO:
            race_lap_avg_str = race_lap_list_to_str(list(map(lambda x: x.astype('unicode'), race_lap_avg)))
            race_lap_std = np.std(race_laps, axis=0)
            # TODO:
            race_lap_std_str = race_lap_list_to_str(list(map(lambda x: x.astype('unicode'), race_lap_std)))
            payload = list(course) + [race_lap_avg_str, race_lap_std_str]
            kt_con.execute('insert into race_lap values(?, ?, ?, ?, ?)', payload)
            kt_con.commit()

        # calculate former & latter time of each horse
        for course in courses:
            sql = "select time, agari from horse_x_race inner join race on horse_x_race.race_id=race.race_id where course=? and track=? and distance=? and time<>0 and agari<>''"
            cur.execute(sql, course)
            horse_time_list = cur.fetchall()
            for i in horse_time_list:
                if not type(i[0]) == type(i[1]):
                    print(i)
            horse_time_array = np.asarray(list(map(lambda x: [float(x[0]), float(x[1])], horse_time_list)))
            avg__ = np.mean(horse_time_array, axis=0)
            std__ = np.std(horse_time_array, axis=0)
            payload = list(course) + list(avg__) + list(std__)
            kt_con.execute('insert into fnl values(?, ?, ?, ?, ?, ?, ?)', payload)
            kt_con.commit()
