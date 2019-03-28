import asyncio
import aiohttp
import csv
from bs4 import BeautifulSoup

primary_url = 'https://marketplace.xbox.com'
prefix = '/ru-RU/Games/Xbox360Games'
headers = {
	'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0'
	}



class Clien():

	def __init__(self, headers, session=None):
		self.headers = headers
		if session is None:
			self.session = aiohttp.ClientSession(headers=self.headers)
		else:
			self.session = session


	async def parse(self, url):
		data = await self._fetch(url)
		return data


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

class SaveSvg():

	@classmethod
	async def unzip_multi(cls, data):
		with open('xbox360market.csv', 'a') as f:
			for tup in data:
				await cls.save_svg(f,tup)

	@classmethod
	async def save_svg(cls,f, data):
		# print(data)
		# with open('rutor_xbox360.csv', 'a') as f:
		writer = csv.writer(f)
		writer.writerow( ( data[0],
                        data[1],
                        data[2],
                        ))

class SaveImg():

	def __init__(self, client):
		self.client = client
		self.count = 0
		self.qwe = []


	async def get(self, data):
		try:
			binarf = await self.client.parse(data[2])
			self.count +=1
		except Exception:
			print('img!!')
			binarf = b''
		self.qwe.append((data[0], binarf))


	async def sv(self):
		for data in self.qwe:
			f = open('img/'+ data[0]+'.jpg', "wb")
			f.write(data[1])
			f.close()


	async def save(self, data):
		print(data[2])

		try:
			binarf = await self.client.parse(data[2])
			self.timer +=1
		except Exception:
			print('img!!')
			binarf = b''
		f = open('img/'+ data[0]+'.jpg', "wb")
		f.write(binarf)
		f.close()

class Bs:

	def __init__(self, *args, **kwargs):
	    self.list_next_page = [primary_url+prefix]
	    self.body_titles = []

	async def get_next_pages(self, html):
		url_pages = []
		soup = BeautifulSoup(html, 'lxml')
		pages = soup.find('div', id='bodycolumn').find('div', id='BodyContent')
		pages = pages.find('div', class_='Paging').find('a', class_='Next')
		next_page = str(pages).split('"')[3]
		self.list_next_page.append(primary_url+next_page)
		return primary_url+next_page

	async def get_content(self, html):
		soup = BeautifulSoup(html, 'lxml')
		product = soup.find('div', id='bodycolumn').find('div', id='BodyContent')
		product = product.find('ol', class_='ProductResults GameTiles').find_all('li')
		for pr in product:
			body = str(pr.find('a')).split('"')
			title = body[13]
			url = body[1]
			image = body[9]
			self.body_titles.append((title, url, image))
		print(title, url, image)
		return self.body_titles




async def main():
	url = primary_url+prefix
	bs = Bs()
	async with Clien(headers=headers) as cl:
		while True:
			try:
				data = await cl.parse(url)
				url = await bs.get_next_pages(data)
				asyncio.sleep(1)
				print(url)
			except Exception:
				print('dadam')
				break

		for page in bs.list_next_page:
			data = await cl.parse(page)
			await bs.get_content(data)

		# await SaveSvg.unzip_multi(bs.body_titles)
		save_pic = SaveImg(cl)
		tasks = []
		print(len(bs.body_titles))
		for tit in bs.body_titles:
			task = loop.create_task(save_pic.get(tit))
			# task = loop.create_task(save_pic.save(tit))
			tasks.append(task)
		await asyncio.gather(*tasks)
		await save_pic.sv()
	print(save_pic.count)







if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	task = [
            # loop.create_task(main3()),
            loop.create_task(main())
		]
	wait_tasks = asyncio.wait(task)
	loop.run_until_complete(wait_tasks)