# coding=utf-8
"""
天气爬虫，爬取某个城市的天气
该文件后续可能修改
"""

import requests  # 导入requests包
from bs4 import BeautifulSoup
import random
import time
import socket  # 用做异常处理
from urllib.parse import quote
from model import Weather
from global_config import logger


def get_html(url, data=None):
    """
    模拟浏览器来获取网页的html代码
    """
    header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    # 设定超时时间，取随机数是因为防止被网站认为是爬虫
    timeout = random.choice(range(80, 180))
    while True:
        try:
            rep = requests.get(url, headers=header, timeout=timeout)
            rep.encoding = "utf-8"
            break
        except socket.timeout as e:
            print("3:", e)
            time.sleep(random.choice(range(8, 15)))
        except socket.error as e:
            print("4:", e)
            time.sleep(random.choice(range(20, 60)))
    return rep.text


def get_city_weather(city_name: str, city_id: str) -> Weather:
    try:
        # 对于日照市需要特殊处理
        if city_name == '日照':
            city_name += '市'
        city = city_name + '天气'
        url = "https://cn.bing.com/search?q=" + quote(city) + '&PC=U316&FORM=CHROMN'
        
        response = get_html(url)
        soup = BeautifulSoup(response, 'html.parser')
        max_temperature = soup.select(
            '#b_results > li.b_ans.b_top.b_topborder > div > div > div.wtr_hero > div > div.wtr_condition > div.wtr_condiPrimary > div.wtr_condiHighLow > div.wtr_high > span')
        min_temperature = soup.select(
            '#b_results > li.b_ans.b_top.b_topborder > div > div > div.wtr_hero > div > div.wtr_condition > div.wtr_condiPrimary > div.wtr_condiHighLow > div.wtr_low')
        humidity = soup.select(
            '#b_results > li.b_ans.b_top.b_topborder > div > div > div.wtr_hero > div > div.wtr_condition > div.wtr_condiPrimary > div.wtr_condiAttribs > div.wtr_currHumi')
        weather_type = soup.select(
            '#b_results > li.b_ans.b_top.b_topborder > div > div > div.wtr_hero > div > div.wtr_condition > div.wtr_condiSecondary.wtr_nowrap > div.wtr_caption')
        
        # 方便后续调试，该文件后续要优化，暂且先这样放着
        # print(response)
        # print(max_temperature)
        # print(min_temperature)
        # print(humidity)
        # print(weather_type)
        weather: Weather = Weather()
        weather.city_id = city_id
        weather.city_name = city_name
        weather.min_temperature = int(min_temperature[0].text.replace('°', ''))
        weather.max_temperature = int(max_temperature[0].text.replace('°', ''))
        weather.humidity = int(humidity[0].text.replace('湿度: ', '').replace('%', ''))
        weather.weather_type = weather_type[0].text
        return weather
    except ValueError as e:
        logger.error(e)
        return Weather()
    except IndexError as e:
        logger.error(e)
        return Weather()
