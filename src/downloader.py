#! /usr/bin/env python3


import re
import time
import requests
import dryscrape
import configparser
import mysql.connector
from bs4 import BeautifulSoup as bs




class LBC_object(object):
	""""""

	def __init__(self):
		self.url = None
		self.price = None
		self.date = None
		self.name = None
		self.loc = None
		self.categ = None
		self.desc = None

	def insert(self, configuration):
		""""""

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
		connection = mysql.connector.connect(**config, buffered=True)

		# Category
		cursor = connection.cursor()
		command = 'SELECT idCategory FROM category WHERE name = %(name)s ;'
		data = {'name': self.categ}
		cursor.execute(command, data)
		idCategory = [x[0] for x in cursor]
		cursor.close()
		# Insert if not
		if len(idCategory) == 0:
			cursor = connection.cursor()
			command = 'INSERT INTO category (name) VALUES (%(name)s) ;'
			data = {'name': self.categ}
			cursor.execute(command, data)
			print('ENRICHMENT: {} inserted.'.format(self.categ))
			command = 'SELECT idCategory FROM category WHERE name = %(name)s ;'
			data = {'name': self.categ}
			cursor.execute(command, data)
			idCategory = [x[0] for x in cursor][0]
			cursor.close()
		else:
			idCategory = idCategory[0]

		# Localisation
		cursor = connection.cursor()
		command = 'SELECT idLoc FROM localisation WHERE codePostal = %(loc)s ;'
		data = {'loc': self.loc}
		cursor.execute(command, data)
		idLoc = [x[0] for x in cursor]
		cursor.close()
		# Insert if not
		if len(idLoc) == 0:
			cursor = connection.cursor()
			command = 'INSERT INTO localisation (departement, region, codePostal) VALUES (%(departement)s, %(region)s, %(codePostal)s) ;'
			data = {
				'departement': self.loc[:2],
				'region': None,
				'codePostal': self.loc
			}
			cursor.execute(command, data)
			print('ENRICHMENT: {} inserted.'.format(self.loc))
			command = 'SELECT idLoc FROM localisation WHERE codePostal = %(codePostal)s ;'
			data = {'codePostal': self.loc}
			cursor.execute(command, data)
			idLoc = [x[0] for x in cursor][0]
			cursor.close()
		else:
			idLoc = idLoc[0]

		# Object
		cursor = connection.cursor()
		command = 'INSERT INTO objects (date, name, idLoc, idCategory, url, price, description) VALUES (%(date)s, %(name)s, %(idLoc)s, %(idCategory)s, %(url)s, %(price)s, %(description)s) ;'
		data = {
			'date': self.date,
			'name': self.name,
			'idLoc': idLoc,
			'idCategory': idCategory,
			'url': self.url,
			'price': self.price,
			'description': self.desc
		}
		try:
			cursor.execute(command, data)
		except Exception as E:
			print(E)
		cursor.close()


class DailyParser(object):
	""""""

	def __init__(self, configuration):

		self.configuration = configuration

		self.lbc_url = 'https://www.leboncoin.fr'
		self.base_url = 'https://www.leboncoin.fr/recherche/?page='
		self.today = time.strftime('%Y-%m-%d')

	def get_daily_offers(self):
		"""Parse LBC to insert every item into an SQL DB"""

		page = 1
		session = dryscrape.Session()

		while page < 35:

			#~ raw_data = requests.get('{}{}'.format(self.base_url, page)).text
			#~ raw_data_indexed = bs(raw_data, 'lxml')
			#~ sold_objects = raw_data_indexed.find_all('li', attrs={'class': '_3DFQ-'})
			session.visit('{}{}'.format(self.base_url, page))
			response = session.body()
			soup = bs(response, 'lxml')
			sold_objects = soup.find_all('li', attrs={'class': '_3DFQ-'})
			print('PAGE: {}{}\t{} objects.'.format(self.base_url, page, len(sold_objects)))

			for sold_object in sold_objects:

				tst = time.time()
				desc_object = LBC_object()
				# URL
				desc_object.url = sold_object.find_all('a', attrs={'class': 'clearfix trackable'}, href=True)[0]['href']
				# Price, optional
				try:
					desc_object.price = int(re.sub(' ', '', sold_object.find_all('span', attrs={'itemprop': 'price'})[0].text))
				except IndexError:
					desc_object.price = None
				# Date
				if re.search('Aujourd\'hui', sold_object.find_all('div', attrs={'data-qa-id': 'listitem_date'})[0].text):
					desc_object.date = self.today
				elif re.search('Hier', sold_object.find_all('div', attrs={'data-qa-id': 'listitem_date'})[0].text):
						desc_object.date = self.today-timedelta(1)
				# Name
				desc_object.name = sold_object.find_all('span', attrs={'data-qa-id': 'aditem_title'})[0].text
				# Localisation
				desc_object.loc = re.findall('[0-9]{5}', sold_object.find_all('p', attrs={'itemprop': 'availableAtOrFrom'})[0].text)[0]
				# Category
				desc_object.categ = sold_object.find_all('p', attrs={'data-qa-id': 'aditem_category'})[0].text
				# Description
				session.visit('{}{}'.format(self.lbc_url, desc_object.url))
				response = session.body()
				object_data = bs(response, 'lxml')
				try:
					desc_object.desc = re.findall('"category_name":"{}","subject":"{}","body":"(.*?)"'.format(desc_object.categ, desc_object.name), str(object_data))[0]
				except:
					continue
				# Insertion
				desc_object.insert(configuration=self.configuration)
				# Stdout
				tsp = time.time()
				print('OBJECT: {} inserted ({} sec).'.format(desc_object.name, round(tsp-tst, 2)))

			page += 1



if __name__ == '__main__':


	configuration = configparser.ConfigParser()
	configuration.read('../configuration.cfg')

	parser = DailyParser(configuration=configuration)

	# Have to be parallelized
	parser.get_daily_offers()
