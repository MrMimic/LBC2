#!/usr/bin/python3

import re
import gmplot
import numpy as np
import configparser
import mysql.connector


class Drawer(object):

	def __init__(self, configuration):

		# Get data about coords
		with open('./eucircos_regions_departements_circonscriptions_communes_gps.csv', 'r') as mf:
			self.coord_map = [line.strip('\n').split(';') for line in mf.readlines()]
			self.coord_map = {x[9]: {'nom': x[8], 'lat': x[12], 'lon': x[11]} for x in self.coord_map if x[11] not in ['', '-'] and x[12] not in ['', '-']}

		# Get connection
		config = {
			'host': configuration.get('DATABASE', 'host'),
			'user': configuration.get('DATABASE', 'user'),
			'password': configuration.get('DATABASE', 'password'),
			'database': configuration.get('DATABASE', 'database'),
			'port': configuration.getint('DATABASE', 'port'),
			'use_pure': True,
			'raise_on_warnings': True,
			'get_warnings': True,
			'autocommit': True
			}
		self.connection = mysql.connector.connect(**config, buffered=True)

		with open('sql_requests/localisation_price.sql', 'r') as mf:
			command = mf.read()
		cursor = self.connection.cursor()
		cursor.execute(command)
		self.data = [x for x in cursor]
		cursor.close()

	def draw(self):

		category = 'Voitures'
		data = [x for x in self.data if x[1] == category]
		average_price = np.mean([x[2] for x in data])
		cp_to_draw = [str(x[0]) for x in data if x[2] < average_price]
		LAT = []; LONG = []
		for key, value in self.coord_map.items():
			if key in cp_to_draw:
				print(value)
				LAT.append(float(value['lat']))
				LONG.append(float(value['lon']))
		# Draw map
		gmap = gmplot.GoogleMapPlotter(47, 2.4, 6)
		gmap.scatter(LONG, LAT, '#d041e0', size=5000, marker=False)
		gmap.heatmap(LONG, LAT)
		gmap.draw("mymap.html")


if __name__ == '__main__':


	configuration = configparser.ConfigParser()
	configuration.read('../configuration.cfg')

	drawer = Drawer(configuration=configuration)
	drawer.draw()
