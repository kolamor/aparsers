import asyncio
import aiohttp
import csv
from bs4 import BeautifulSoup
import re


SAVE_RESULT = True
SAVE_HEADERS_SVG = True
FILE_SAVE = 'gamma-shin.csv'

BASE_URL = 'http://www.gamma-shin.ru'
POSFIX_SEARCH = '/tyres-search/'

HEADERS_SVG = ('name',
			'country',
			'photos',
			'productManufacturer',
			'price',
			'priceFormula',
			'minimalAmount',
			'paymentOption',
			'net',
			'gross',
			'volume',
			'diameter*',
			'load index*',
			'maximum load per tire',
			'maximum speed index*',
			'ply rating',
			'profile height*',
			'profile width',
			'seasonality*',
			'spikes',
			'the size*',
			'tread depth',
			'type of car',
)

class Client():

	def __init__(self, headers='', session=None):
		self.headers = headers
		if session is None:
			self.session = aiohttp.ClientSession(headers=self.headers)
		else:
			self.session = session

	async def send(self, url):
		data = await self._fetch(url)
		return data

	async def get_all(self, urls):
		tasks = []
		for url in urls:
			task = loop.create_task(self._fetch(url))
			tasks.append(task)
			all_data = await asyncio.gather(*tasks)
		return all_data

	async def _fetch(self,send):

		print(send)
		async with self.session.get(send) as response:
			# print('-----', response)
			if response.content_type == 'text/html':
				data = await response.text()
			if response.content_type == 'application/json':
				data =  await response.json()
			if response.content_type == 'text/xml':
				data = await response.text()
			if response.content_type == 'image/jpeg':
				data = await response.read()
			if response.content_type == 'image/png':
				data = await response.read()
		return data

	async def close(self):
		await self.session.close()

	async def __aenter__(self):
		return self

	async def __aexit__(self, exception_type, exception_value, traceback):
		await self.close()


class Bs:

	async def get_total_page(self, html):
		url_pages =[]
		soup = BeautifulSoup(html, 'lxml')
		pages = soup.find('body').find('div', id='page-wrapper').find('div', id='page-body')
		pages = pages.find('table').find_all('tr')[1].find('td', class_='page-left')
		pages = pages.find('div', class_='catalog-section').find_all('font', class_='text')[1]
		pages = pages.find_all('a')[0:-2]
		for page in pages:
			url = (str(page)).split('"')[1]
			url_pages.append(BASE_URL + url)
		url_pages.append(BASE_URL + POSFIX_SEARCH)
		return url_pages

	async def get_items(self, html):
		soup = BeautifulSoup(html, 'lxml')
		items = soup.find('body').find('div', id='page-wrapper').find('div', id='page-body')
		items = items.find('table').find_all('tr')[1].find('td', class_='page-left')
		items = items.find('div', class_='catalog-section').find('table', class_='stock')
		items = items.find_all('td')

		data =[]
		for item in items:
			inf = await self._item_pars(item)
			data.append(inf)
		return data


	async def _item_pars(self, items):
		name = items.find_all('img')[0].get('title').replace('_',' ')
		image = BASE_URL + items.find_all('img')[0].get('src')
		season = items.find_all('img')[1].get('title')
		if season == None:
			season = 'Всесезонные'
		if name == '':
			season = ''
		brand = items.find('div', class_='name').find('a').get('href').split('/')[2].replace('_',' ')
		name = brand +" " + name
		_size = str(items.find('div', class_='name').find('a').string).split()
		size = _size[0]
		_index = _size[1]
		load_index = _index[0:-1]
		speed_index = _index[-1]
		profile_height = size.split('/')[0]
		try:
			profile_width, diameter = size.split('/')[1].split('R')
		except Exception:
			profile_height, diameter = size.split('R')
			profile_width = ''
		price = items.find('div', class_='price').find('span', class_='num-price').string
		price =  re.findall(r'\d+', str(price))
		price = ''.join(price)
		in_stock = items.find('div', class_='inlinecart').find('input', type='text').get('value')
		country = ''
		priceFormula = ''
		minimalAmount = ''
		paymentOption = ''
		net = ''
		gross = ''
		volume = in_stock
		maximum_load_per_tire = ''
		index = ''
		spikes = ''
		tread_depth = ''
		type_of_car = ''

		data = (
				name,
				country,
				image,
				brand,
				price,
				priceFormula,
				minimalAmount,
				paymentOption,
				net,
				gross,
				volume,
				diameter,
				load_index,
				maximum_load_per_tire,
				speed_index,
				index,
				profile_height,
				profile_width,
				season,
				spikes,
				size,
				tread_depth,
				type_of_car,
			)
		return data


class Save:

	@classmethod
	async def save_csv(cls, data_ar):
		with open(FILE_SAVE, 'a') as f:
			writer = csv.writer(f)
			for data in data_ar:
				writer.writerow( [d for d in data] )

	@classmethod
	async def save_svg_headers(cls, headers):
		with open(FILE_SAVE, 'a') as f:
			writer = csv.writer(f)
			writer.writerow([head for head in headers])


async def main():
	psend = BASE_URL + POSFIX_SEARCH
	async with Client() as cl:
		html = await cl.send(psend)
		bs = Bs()
		url_pages = await bs.get_total_page(html)
		tasks = []
		for page in url_pages:
			task = loop.create_task(cl.send(page))
			tasks.append(task)
		data = await asyncio.gather(*tasks)
	if SAVE_HEADERS_SVG:
		await Save.save_svg_headers(HEADERS_SVG)
	for html in data:
		items = await bs.get_items(html)
		if SAVE_RESULT:
			await Save.save_csv(items)


if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	task = [
		loop.create_task(main())
		]
	wait_tasks = asyncio.wait(task)
	loop.run_until_complete(wait_tasks)
