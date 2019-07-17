import os
import requests
import json
import time
import xlsxwriter
import sys
from flask import Flask

my_app = Flask(__name__)

@my_app.route("/")
def hello():
    return "Hello Flask, on Azure App Service for Linux"

def get_shortest_duration(origin, destination, avoid_tolls):

	request_string = 'https://maps.googleapis.com/maps/api/directions/json?origin=' + origin \
					 + '&destination=' + destination \
					 + '&sensor=false&mode=driving&alternatives=true' + \
					 '&key=AIzaSyAWIzWB1NsK6TKNCMlqLdbmhiq4hKm-Szk&departure_time=now'

	if avoid_tolls:
		request_string += "&avoid=tolls"

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

	print("miles: " + str(shortest_dist))
	print("mins: " + str(shortest_dur))
	return shortest_dur, shortest_dist


def run_all_combinations():
	cur_time = time.strftime("%Y%m%d-%H%M")
	print (cur_time)

	workbook = xlsxwriter.Workbook(cur_time + '.xlsx')
	worksheet = workbook.add_worksheet()
	row = 0
	worksheet.write(row, 0, 'Origin')
	worksheet.write(row, 1, 'Destination')
	worksheet.write(row, 2, 'without Tolls (Mins)')
	worksheet.write(row, 3, 'WITH Tolls (Mins)')
	worksheet.write(row, 4, 'without Tolls (Miles)')
	worksheet.write(row, 5, 'WITH Tolls (Miles)')
	row += 1

	origins = {"1117 NW 56th St, Seattle, WA 98107", "806-NW-63rd-St-98107"}
	destination = "3009 157th Pl NE, Redmond, WA 98052"

	for origin in origins:
		map_url = generate_map_url(origin, destination)

		avoid_tolls = get_shortest_duration(origin, destination, True)
		with_tolls = get_shortest_duration(origin, destination, False)
		worksheet.write(row, 0, origin)
		worksheet.write(row, 1, destination)
		worksheet.write(row, 2, avoid_tolls[0])
		worksheet.write(row, 3, with_tolls[0])
		worksheet.write(row, 4, avoid_tolls[1])
		worksheet.write(row, 5, with_tolls[1])
		worksheet.write(row, 6, map_url)

		row += 1

	workbook.close()

def generate_map_url(origin, destination):
	return "https://www.google.com/maps/dir/" + origin + "/" + destination

run_all_combinations()