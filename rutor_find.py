import asyncio
import aiohttp
import csv
from bs4 import BeautifulSoup
import time

rutor_url = 'http://mega-bit.ga'
all_words_prefix = '/search/0/0/100/0/'
any_words_prefix = '/search/0/0/200/0/'
logic_prefix = '/search/0/0/300/0/'

search = 'assassins creed'

SAVE_RESULT = True
file_save = 'find_rutor.csv'



class Client():

	def __init__(self, headers='', session=None):
		self.headers = headers
		if session is None:
			self.session = aiohttp.ClientSession(headers=self.headers)
		else:
			self.session = session


	async def send(self, url):
		data = await self._fetch(url)
		return data, url

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
			print('-----', response)
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

	async def get_total_pages(self, html, send):
		# print(html)
		url_pages = []
		soup = BeautifulSoup(html, 'lxml')
		pages = soup.find('div', id='index').find('b').find_all('a')
		if len(pages) == 0:
			return [send,]

		for page in pages:
			url = str(page).split('"')[1]
			url_pages.append(rutor_url+url)
		url_pages.insert(0,send)
		return url_pages

	async def get_content(self, html):
		soup = BeautifulSoup(html, 'lxml')
		urls = soup.find('div', id='index').find('table').find_all('tr')
		del urls[0]
		if len(urls) == 0:
			print('не найдено')
			return []
		result=[]
		for a in urls:
			soup = BeautifulSoup(str(a), 'lxml')
			b = soup.find_all('a' )
			self_url = str(b[0]).split('"')[3]
			magnet = str(b[1]).split('"')[1]
			url_resurs = str(b[2]).split('"')[1]
			name = str(b[2]).split('"')[2][1:-5]
			res = (name, self_url, magnet, url_resurs )
			result.append(res)
		return result

	async def get_urls_content(self, html_list):
		t1 = time.clock()
		tasks = []
		for html in html_list:
			task = loop.create_task(self.get_content(html))
			tasks.append(task)
		data = await asyncio.gather(*tasks)
		t2 = time.clock() - t1
		print('a',t2)
		return data


class Save:

	@classmethod
	async def save_csv(cls, data_ar):
		with open(file_save, 'a') as f:
			for data_list in data_ar:
				for data in data_list:
					writer = csv.writer(f)
					writer.writerow( ( data[0],
			                        data[1],
			                        data[2],
			                        data[3]) )



async def main():
	send = rutor_url+all_words_prefix+search
	async with Client() as cl:

		html, send = await cl.send(send)
		bs = Bs()
		total_pages = await bs.get_total_pages(html, send)
		data = await cl.get_all(total_pages)
		urls_pages = await bs.get_urls_content(data)
		print(urls_pages)
		if SAVE_RESULT:
			await Save.save_csv(urls_pages)




if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	task = [
		loop.create_task(main())
		]
	wait_tasks = asyncio.wait(task)
	loop.run_until_complete(wait_tasks)

