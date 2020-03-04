# coding: utf-8
import requests
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
from cachetools import cached, TTLCache

zsecache = TTLCache(maxsize=5, ttl=900)

@cached(zsecache)
def fetch_zse_stocks():
	""" get the ZSE stocks for a particular day with their currency code and data """
	get_stock_page = requests.get("https://africanfinancials.com/zimbabwe-stock-exchange-share-prices/")
	get_stock_page.text
	get_stock_data = BeautifulSoup(get_stock_page.text, 'lxml')
	stock_table_html = get_stock_data.find(id="af_industrials")
	stock_table_rows = stock_table_html.tbody.findAll('tr')

	stocks_list = []
	# iterate and save the stocks
	for row in stock_table_rows:
		stock_info = {
			"symbol": row.a['href'].replace('https://africanfinancials.com/company/zw-', '')+".zw",
			"name": row.a.text,
			"price": row.find(attrs={"class": "numeric"}).text.replace(",", ""),
		}
		stocks_list.append(stock_info)
	return stocks_list


def create_stocks_json():
	stocks_datalist = fetch_zse_stocks()
	stocks_filename = datetime.now().strftime("%d_%m_%Y") + ".json"
	with open(stocks_filename, 'w') as file:
		stocks_as_json = json.dumps(stocks_datalist, indent=4)
		file.write(stocks_as_json)


@cached(zsecache)
def get_current_stock_data():
	# today_stocks_filename = datetime.now().strftime("%d_%m_%Y") + ".json"
	# first we check if the file exists, if it doesn't we create it
	# if not os.path.isfile("./{}".format(today_stocks_filename)):
	#	create_stocks_json()
	#
	# then we open the file and create stuff
	#with open(today_stocks_filename, 'r') as file:
	#	stocks_data = json.loads(file.read())
	stocks_data = fetch_zse_stocks()
	return stocks_data


def get_stock_price(symbol):
	stocks_data = get_current_stock_data()

	# get the data from the dictionary
	for stock in stocks_data:
		if stock['symbol'].lower() == symbol.lower():
			stock_price = stock['price']
			return stock_price


def get_stock_symbols():
	stocks_data	= get_current_stock_data()
	# iterate and get stocks symbol from the stocks database
	return [stock['symbol'] for stock in stocks_data]