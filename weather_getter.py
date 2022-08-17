# coding=utf-8
"""
天气爬虫，爬取某个城市的天气
该文件后续可能修改
"""
import asyncio
import random
import socket  # 用做异常处理
from urllib.parse import quote

import requests  # 导入requests包
from bs4 import BeautifulSoup

from global_config import logger
from model import Weather


def get_html(url, can_wait: bool = False, retries_times: int = 5):
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
    times: int = 0
    while times < retries_times:
        times += 1
        try:
            rep = requests.get(url, headers=header, timeout=timeout)
            rep.encoding = "utf-8"
            return rep.text
        except socket.timeout as e:
            print("3:", e)
            logger.error(str(e))
            if can_wait:
                asyncio.sleep(random.choice(range(8, 15)))
        except socket.error as e:
            print("4:", e)
            logger.error(str(e))
            if can_wait:
                asyncio.sleep(random.choice(range(20, 60)))
    return ''


def get_bing_weather(city_name: str, city_id: str, can_wait: bool = False) -> Weather or None:
    try:
        city = city_name + '天气'
        url = "https://cn.bing.com/search?q=" + quote(city) + '&PC=U316&FORM=CHROMN'

        response = get_html(url, can_wait)
        soup = BeautifulSoup(response, 'html.parser')
        max_temperature = soup.select(
            '#b_results > li.b_ans.b_top.b_topborder > div > div > div.wtr_hero > div > div.wtr_condition > div.wtr_condiPrimary > div.wtr_condiHighLow > div.wtr_high > span')
        min_temperature = soup.select(
            '#b_results > li.b_ans.b_top.b_topborder > div > div > div.wtr_hero > div > div.wtr_condition > div.wtr_condiPrimary > div.wtr_condiHighLow > div.wtr_low')
        humidity = soup.select(
            '#b_results > li.b_ans.b_top.b_topborder > div > div > div.wtr_hero > div > div.wtr_condition > div.wtr_condiPrimary > div.wtr_condiAttribs > div.wtr_currHumi')
        weather_type = soup.select(
            '#b_results > li.b_ans.b_top.b_topborder > div > div > div.wtr_hero > div > div.wtr_condition > div.wtr_condiSecondary.wtr_nowrap > div.wtr_caption')

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
    except IndexError as e:
        logger.error(e)
    return None


def get_baidu_row_weather(city_name: str, city_id: str, can_wait: bool = False) -> Weather or None:
    try:
        city = city_name + '天气'
        url = "https://weathernew.pae.baidu.com/weathernew/pc?query=" + quote(city) + "&srcid=4982"

        response = get_html(url, can_wait)
        soup = BeautifulSoup(response, 'html.parser')
        temperature = soup.select('#sfr-app > div > div.rt-body > div > div.weather-main > div > div.weather-banner > div.weather-banner-header > p.weather-banner-header-left > span:nth-child(2) > span:nth-child(1)')
        humidity = soup.select('#sfr-app > div > div.rt-body > div > div.weather-main > div > div.weather-banner > div.weather-banner-footer > span:nth-child(1)')
        weather_type = soup.select('#sfr-app > div > div.rt-body > div > div.weather-main > div > div.weather-banner > div.weather-banner-content > div.weather-banner-content-right > div.weather-banner-content-wind > span:nth-child(2)')

        weather: Weather = Weather()
        weather.city_id = city_id
        weather.city_name = city_name
        temperature_text = temperature[0].text.replace('°', '').replace('C', '')
        temperature_data = temperature_text.split('~')
        weather.min_temperature = int(temperature_data[0])
        weather.max_temperature = int(temperature_data[1])
        weather.humidity = int(humidity[0].text.replace('湿度', '').replace('%', '').replace(' ', ''))
        weather.weather_type = weather_type[0].text
        return weather
    except ValueError as e:
        logger.error(e)
    except IndexError as e:
        logger.error(e)
    return None


def get_baidu_weather(city_name: str, city_id: str, can_wait: bool = False) -> Weather or None:
    try:
        city = city_name + '天气'
        url = "https://www.baidu.com/s?wd=" + quote(city)

        response = get_html(url, can_wait)
        soup = BeautifulSoup(response, 'html.parser')
        temperature = soup.select('#\\31  > div.op_weather4_twoicon_container_div > div.op_weather4_twoicon > a.op_weather4_twoicon_today.OP_LOG_LINK > p.op_weather4_twoicon_temp')
        weather_type = soup.select('#\\31  > div.op_weather4_twoicon_container_div > div.op_weather4_twoicon > a.op_weather4_twoicon_today.OP_LOG_LINK > p.op_weather4_twoicon_weath')

        weather: Weather = Weather()
        weather.city_id = city_id
        weather.city_name = city_name
        temperature_text = temperature[0].text.replace('°', '').replace('C', '').replace('℃', '')
        temperature_data = temperature_text.split('~')
        weather.min_temperature = int(temperature_data[0])
        weather.max_temperature = int(temperature_data[1])
        weather.humidity = 50
        weather.weather_type = weather_type[0].text
        return weather
    except ValueError as e:
        logger.error(e)
    except IndexError as e:
        logger.error(e)
    return None


def get_city_weather(city_name: str, city_id: str, can_wait: bool = False) -> Weather:
    # 对于日照市需要特殊处理
    if city_name == '日照':
        city_name += '市'
    bing_weather = get_bing_weather(city_name, city_id, can_wait)
    if bing_weather is not None:
        return bing_weather
    baidu_weather = get_baidu_row_weather(city_name, city_id, can_wait)
    if baidu_weather is not None:
        return baidu_weather
    baidu_weather = get_baidu_weather(city_name, city_id, can_wait)
    if baidu_weather is not None:
        return baidu_weather
    return Weather()


if __name__ == '__main__':
    pass
