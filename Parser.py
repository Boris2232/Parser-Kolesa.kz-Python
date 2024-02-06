import telebot
from bs4 import BeautifulSoup
from soup import requests
from telebot import types
from tqdm import tqdm
import csv

bot = telebot.TeleBot('')
HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}


def parse_car_names(link):
    html_code = requests.get(link, headers=HEADERS, params=None)
    if html_code.status_code == 200:
        soup = BeautifulSoup(html_code.text, 'html.parser')
        items = str(soup.find('div', class_="block-links-list row"))
        car_names = list(filter(lambda x: 'href=' in x, items.split('\n')))
        list_of_names = [i.split('href="')[-1].split('"')[0].split('/')[-2] for i in car_names]
        list_of_names = [i.replace('-', '_') for i in list_of_names]
        return list_of_names


class Parser:
    def __init__(self, link, car_name):
        self.link = link
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}
        self.html = None
        self.cars = []
        self.chosen__car = car_name

    def get_html(self, params=None):
        try:
            html_code = requests.get(self.link, headers=self.headers, params=params)
            self.html = html_code
            return html_code
        except all:
            pass

    def check(self):
        return self.html.status_code == 200

    def store_all_data(self):
        self.cars.extend(self.get_material(self.html.text))
        how_many = int(self.pages_count(self.html.text))
        for page_number in tqdm(range(1, how_many + 1), desc="Parsing pages"):
            url = str(f'https://kolesa.kz/cars/{self.chosen__car}/?page={page_number}')
            html1 = self.get_html(url)
            self.cars.extend(self.get_material(html1.text))
        print('Found', len(self.cars), 'cars')
        self.save_cars_to_csv()

    def save_cars_to_csv(self):
        file_name = f'Kolesa.kz-{self.chosen__car}.csv'
        csv_headers = ['Car_name', 'Price_tg', 'City', 'Description', 'Link']
        data = [{'Car_name': i['title'], 'Price_tg': i['price_tg'].replace('\xa0', '.'), 'City': i['city'],
                 'Description': i['description'],
                 'Link': i['link'], } for i in self.cars]
        with open(file_name, 'wt', encoding='utf-16') as file:
            writer = csv.DictWriter(file, fieldnames=csv_headers, delimiter='\t')
            writer.writeheader()
            writer.writerows(data)

    def get_material(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all('div', class_='a-card__info')
        cars = []
        for item in items:
            cars.append({
                'title': item.find('h5', class_='a-card__title').get_text(strip=True),
                'price_tg': item.find('span', class_='a-card__price').get_text(strip=True),
                'city': item.find('span', class_='a-card__param').get_text(strip=True),
                'description': item.find('p', class_='a-card__description').get_text(strip=True),
                'link': 'https://kolesa.kz/' + item.find('a', class_='a-card__link').get('href')
            })
        return cars

    def pages_count(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        pagination = str(soup.find_all('div', class_='pager'))
        max_page_number = 1
        pagination = list(filter(lambda x: '<li>' in x, pagination.split('\n')))
        for i in pagination:
            splitted_string = i.split('</a></span></li>')[0].split('>')[-1]
            if splitted_string.isdigit():
                max_page_number = max(int(splitted_string), max_page_number)
        return max_page_number


@bot.message_handler(commands=['start'])
def start(message):
    global chat_id_
    chat_id_ = message.chat.id
    name = f'Hello, {message.from_user.first_name} {message.from_user.last_name}'
    bot.send_message(message.chat.id, name, parse_mode='html')
    bot.send_message(message.chat.id, 'type {/parsing} to start', parse_mode='html')


@bot.message_handler(commands=['parsing'])
def parsing(message):
    link = 'https://kolesa.kz'
    s1 = '     '.join(['/' + i for i in parse_car_names(link)])
    bot.send_message(message.chat.id, 'Choose the car from list:')
    bot.send_message(message.chat.id, s1)


@bot.message_handler(content_types=['text'])
def save(message):
    bot.send_message(message.chat.id, f'OK, Now I will scrap data about {str(message.text[1::]).capitalize()}')
    car_name = message.text[1::].replace('_', '-')
    link = f'https://kolesa.kz/cars/{car_name}/'
    car_name = message.text[1::].lower()
    parser = Parser(link, car_name)
    parser.get_html()
    if parser.check():
        parser.store_all_data()
    with open(f'./Kolesa.kz-{car_name}.csv', 'rb') as csv_file:
        bot.send_document(message.chat.id, csv_file)
    bot.send_message(message.chat.id, f'Here is your csv file with all data')


bot.polling()
