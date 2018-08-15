#! /usr/bin/env python3


import re
import datetime
import requests
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

	def insert(self):
		print('INSERT MYSQL')


class DailyParser(object):
	""""""

	def __init__(self):
		self.base_url = 'https://www.leboncoin.fr/recherche/?regions=11&cities=Rouen_76000'
		self.today = datetime.datetime.now()

	def get_daily_offers(self):
		
		raw_data = requests.get(self.base_url).text
		raw_data_indexed = bs(raw_data, 'lxml')
		sold_objects = raw_data_indexed.find_all('li', attrs={'class': '_3DFQ-'})

		for sold_object in sold_objects:


			desc_object = LBC_object()
			# URL
			desc_object.url = sold_object.find_all('a', attrs={'class': 'clearfix trackable'}, href=True)[0]['href']
			# Price, optional
			try:
				desc_object.price = int(re.sub(' ', '', sold_object.find_all('span', attrs={'itemprop': 'price'})[0].text))
			except IndexError:
				desc_object.price = None
			# Date /!\ CONVERSION HAVE TO BE BETTER EXECUTED
			if re.search('Aujourd\'hui', sold_object.find_all('div', attrs={'data-qa-id': 'listitem_date'})[0].text):
				desc_object.date = '{}/{}/{}'.format(self.today.day, self.today.month, self.today.year)
			elif re.search('Hier', sold_object.find_all('div', attrs={'data-qa-id': 'listitem_date'})[0].text):
					desc_object.date = '{}/{}/{}'.format((self.today-timedelta(1)).day, (self.today-timedelta(1)).month, (self.today-timedelta(1)).year)
			# Name
			desc_object.name = sold_object.find_all('span', attrs={'data-qa-id': 'aditem_title'})[0].text
			# Localisation
			desc_object.loc = re.findall('[0-9]{5}', sold_object.find_all('p', attrs={'itemprop': 'availableAtOrFrom'})[0].text)[0]
			# Category
			desc_object.categ = sold_object.find_all('p', attrs={'data-qa-id': 'aditem_category'})[0].text
			# Description

			print('-'*50)
			print('name: {}\nprice: {}\ndate: {}\nloc: {}\ncateg: {}\nurl: {}'.format(desc_object.name, desc_object.price, desc_object.date, desc_object.loc, desc_object.categ, desc_object.url))
			desc_object.insert()





if __name__ == '__main__':

	parser = DailyParser()
	parser.get_daily_offers()
