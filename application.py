import time
import pyodbc
import requests
import json
import sys
import logging
from datetime import datetime
from pytz import timezone
from flask import Flask

app = Flask(__name__)

server = 'commuteanalyzer.database.windows.net'
database = 'commuteanalyzer'
username = 'sagar.kangutkar'
password = 'BuffaloFlames14'
driver = '{ODBC Driver 17 for SQL Server}'
cnxn = pyodbc.connect(
    'DRIVER=' + driver + ';SERVER=' + server + ';PORT=1433;DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
cursor = cnxn.cursor()

homes = {"1117 NW 56th St, Seattle, WA 98107", "806-NW-63rd-St-98107"}
offices = {"3009 157th Pl NE, Redmond, WA 98052"}

fmt = "%Y-%m-%d %H:%M:%S"
now_pacific = datetime.now(timezone('US/Pacific'))
cur_time = now_pacific.strftime(fmt)
is_weekday = True if now_pacific.weekday() < 5 else False


def init():
    cursor.execute("SELECT count(*) FROM CommuteAnalyzer")
    all_data = 'number of rows -->'
    all_data += str(cursor.fetchone()[0])
    return all_data


@app.route("/")
def run():
    logging.basicConfig(level=logging.DEBUG)
    all_data = init()

    # only concerned window. Else break
    cur_hour = now_pacific.hour
    if is_weekday and ((cur_hour >= 7 and cur_hour < 11) or (cur_hour >= 15 and cur_hour < 19)):
        run_all_combinations()

        cursor.execute("SELECT * FROM CommuteAnalyzer")
        logging.debug("Inside Commute Window --> " + str(cursor.fetchone()[0]))

        for row in cursor.fetchall():
            all_data += str(row)
            all_data += '\n'

    else:
        all_data = "outside the daily commute window " + all_data
        logging.debug(all_data)
    return all_data


@app.route("/force")
def force_run():
    all_data = init()

    # run always on force
    run_all_combinations()

    cursor.execute("SELECT * FROM CommuteAnalyzer")
    for row in cursor.fetchall():
        all_data += str(row)
        all_data += '\n\n'

    return all_data


def temp():
    print(now_pacific.hour)


# saa = "->"
# cursor.execute("insert into CommuteAnalyzer values('" + saa + "', 'desti', 1, 2, 3, 4, 'maps link', " + time.strftime("%Y%m%d-%H%M") +")")
# cnxn.commit()

# cursor.execute("SELECT count(*) FROM CommuteAnalyzer")
# print ("-->" + str(cursor.fetchone()[0]))
# cursor.execute("SELECT * FROM CommuteAnalyzer")

# #print ("cur time ===> " + cur_time)

# for row in cursor.fetchall():
#     print (row)

# return "Hello World!"

def get_shortest_duration(origin, destination, avoid_tolls):
    request_string = 'https://maps.googleapis.com/maps/api/directions/json?origin=' + origin \
                     + '&destination=' + destination \
                     + '&sensor=false&mode=driving&alternatives=true' + \
                     '&key=AIzaSyAWIzWB1NsK6TKNCMlqLdbmhiq4hKm-Szk&departure_time=now'

    if avoid_tolls:
        request_string += "&avoid=tolls"

    # print (request_string)

    r = requests.get(request_string)

    resp = json.loads(r.text)
    # print(resp['routes'])
    routes = resp['routes']
    shortest_dur = sys.maxsize
    shortest_dist = sys.float_info.max

    for key in range(0, len(routes)):
        value = routes[key]
        legs = value['legs']
        duration = 0
        distance = 0

        for l in range(0, len(legs)):
            leg = legs[l]
            duration += int(leg['duration_in_traffic']['text'].split(" ", 1)[0])
            distance += float(leg['distance']['text'].split(" ", 1)[0])

        # print duration
        # print distance

        shortest_dur = min(shortest_dur, duration)
        shortest_dist = min(shortest_dist, distance)

    # print("miles: " + str(shortest_dist))
    # print("mins: " + str(shortest_dur))
    return shortest_dur, shortest_dist


def run_all_combinations():
    # afternoon
    if now_pacific.hour > 12:
        origins = offices
        destinations = homes
    else:
        # mornings
        origins = homes
        destinations = offices

    for origin in origins:
        for destination in destinations:
            map_url = generate_map_url(origin, destination)
            # print (origin + " ----> " + destination)
            avoid_tolls = get_shortest_duration(origin, destination, True)
            with_tolls = get_shortest_duration(origin, destination, False)
            query = "insert into CommuteAnalyzer values('" + origin + "','" + destination + "', " + str(
                avoid_tolls[0]) + ", " + str(with_tolls[0]) + ", " + str(avoid_tolls[1]) + ", " + str(
                with_tolls[1]) + ", '" + map_url + "'," + "'" + cur_time + "')"
            cursor.execute(query)
            cnxn.commit()


# print ("................................................")
# cursor.execute("SELECT * FROM CommuteAnalyzer")
# for row in cursor.fetchall():
#    print (row)

def generate_map_url(origin, destination):
    return "https://www.google.com/maps/dir/" + origin + "/" + destination

# print(force_run())
# temp()