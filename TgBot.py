# -*- coding: utf-8 -*-
import logging
from datetime import datetime

import requests
import telebot
from pycbrf import ExchangeRates
from MapsAPI import MapAPI
import os
from flask import Flask, request

server = Flask(__name__)

PORT = int(os.environ.get('PORT', 5000))
TOKEN = "1719349692:AAHNGDF0WeCkGXy3Ef8uWuYXtWmzQF4VypE"
HEROKU_APP_NAME = "mapsapibot"
url = 'http://api.openweathermap.org/data/2.5/weather'
api_weather = 'e4a3da131fe7dd1aa4d06d1ded5c6963'
bot = telebot.TeleBot(TOKEN)
map_api = MapAPI()

main_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
btn1 = telebot.types.KeyboardButton("/weather⛅")
btn2 = telebot.types.KeyboardButton("/currency💸")
btn3 = telebot.types.KeyboardButton("/help❓")
main_markup.row(btn1, btn2, btn3)

weather_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
weather_back = telebot.types.KeyboardButton('Back⬅')
weather_markup.add(weather_back)

currency_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
item1 = telebot.types.KeyboardButton('GBP💷')
item2 = telebot.types.KeyboardButton('EUR💶')
item3 = telebot.types.KeyboardButton('CNY💴')
item4 = telebot.types.KeyboardButton('USD💵')
currency_back = telebot.types.KeyboardButton('Back⬅')
currency_markup.row(item1, item2, item3, item4)
currency_markup.add(currency_back)


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, 'Я бот, умеющий работать с картами и другими инструментами.'
                                      'Для получения полной информации, используй команду "help"',
                     reply_markup=main_markup)


@bot.message_handler(commands=["help", "help❓"])
def help(message):
    bot.send_message(message.chat.id, '''Этот бот в основном специализируется на работе с картами.
Для этого задайте параметры прямо в чате, используя "=" и перечисляя их с помощью ";".
Параметры:
geocode/геокод: координаты, адрес или название объекта
kind/toponym/топоним: тип топонима (дом, улица, метро, район, населенный пункт)
text/place/место: название организации
l/layer/слой: перечень слоев, (спутник, схема, гибрид, траффик)
z/zoom/масштаб: масштаб изображения (от 0 до 17)
scale/увеличение: коэффициент увеличения объектов на карте (от 1.0 до 4.0)
results/результаты: количество результатов, по умолчанию - 1
Другие команды:
/weather: вывод погоды по городу
/currency: курс валют (GBP, EUR, CNY, USD)
"back": вернуться назад.''')


@bot.message_handler(commands=["weather", "weather⛅"])
def weather(message):
    if message is None:
        return
    bot.send_message(message.chat.id, 'Чтобы узнать погоду, введите название города', reply_markup=weather_markup)
    bot.register_next_step_handler(message, get_weather)


def get_weather(message):
    city_name = message.text.strip().lower()
    if city_name.startswith('/'):
        bot.send_message(message.chat.id, "Невозможно вызвать команду в данный момент",
                         reply_markup=main_markup)
        return
    if city_name in ['stop', 'back', 'back⬅']:
        bot.send_message(message.chat.id, "Возвращаемся назад", reply_markup=main_markup)
        return
    try:
        params = {'APPID': api_weather, 'q': city_name, 'units': 'metric', 'lang': 'ru'}
        result = requests.get(url, params=params)
        weather = result.json()
        deg = weather['wind']['deg']
        wind_direction = [("С", abs(0 - deg)), ("В", abs(90 - deg)), ("Ю", abs(180 - deg)), ("З", abs(270 - deg))]
        wind_direction.sort(key=lambda s: s[1])
        bot.send_message(message.chat.id,
                         f"Погода в городе {str(weather['name'])}:\n"
                         f"температура: {str(int(weather['main']['temp']))}°\n"
                         f"Ощущается как: {str(int(weather['main']['feels_like']))}°\n"
                         f"Скорость ветра: {str(float(weather['wind']['speed']))} м/с, {wind_direction[0][0]}\n"
                         f"Давление: {str(float(weather['main']['pressure']))} мм рт. ст.\n"
                         f"Влажность: {str(int(weather['main']['humidity']))}%\n"
                         f"Видимость: {str(weather['visibility'])}\n"
                         f"Описание: {str(weather['weather'][0]['description'])}\n", reply_markup=main_markup)
    except Exception:
        bot.send_message(message.chat.id, "Город " + city_name + " не найден", reply_markup=main_markup)


@bot.message_handler(commands=["currency", "currency💸"])
def currency(message):
    bot.send_message(chat_id=message.chat.id, text="<b>Какой курс валюты вас интересует?</b>",
                     reply_markup=currency_markup, parse_mode="html")
    bot.register_next_step_handler(message, exchange_rate)


def exchange_rate(message):
    text = message.text.strip().lower()
    if text.startswith('/'):
        bot.send_message(message.chat.id, "Невозможно вызвать команду в данный момент",
                         reply_markup=main_markup)
        return
    if text in ['stop', 'back', 'back⬅']:
        bot.send_message(message.chat.id, "Возвращаемся назад", reply_markup=main_markup)
        return
    if text in ['usd💵', 'eur💶', 'cny💴', 'gbp💷']:
        text = text[:-1]
    if text in ['usd', 'eur', 'cny', 'gbp']:
        rates = ExchangeRates(datetime.now())
        bot.send_message(chat_id=message.chat.id,
                         text=f"<b>Сейчас курс: {text.upper()} = {float(rates[text.upper()].rate)}</b>",
                         parse_mode="html", reply_markup=main_markup)
    else:
        bot.send_message(message.chat.id, f'Не надйен курс валюты: {text.upper()}', reply_markup=main_markup)


@bot.message_handler(content_types=["text"])
def dialog(message):
    text = message.text.strip().lower()
    if text.startswith('/'):
        bot.send_message(message.chat.id, f'Бот не обладает командой "{text}"', reply_markup=main_markup)
        return
    if text in ['stop', 'back', 'back⬅']:
        bot.send_message(message.chat.id, "Нет запущенной комманды на данный момент", reply_markup=main_markup)
        return
    output = map_api.main(text)
    if isinstance(output, str):
        bot.send_message(message.chat.id, output)
    else:
        im = open("map.png", "rb")
        description = []
        for d in output:
            raw = []
            for key, value in d.items():
                if key != 'spn':
                    raw.append(f"{key}: {value}")
            description.append('\n'.join(raw))
        description.insert(0, f'По вашему запросу найдено результатов: {len(description)}:')
        description = '\n\n'.join(description)
        if len(description) > 963:
            description = description[:963] + "...\n...описание слишком длинное, что отобразить его полностью"
        bot.send_photo(message.chat.id, im, caption=description)


@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{HEROKU_APP_NAME}.herokuapp.com/{TOKEN}")
    return "?", 200


if __name__ == '__main__':
    server.run(host="0.0.0.0", port=PORT)
