# coding=utf-8
"""
天气爬虫，爬取某个城市的天气
该文件后续可能修改
"""
import asyncio
import json
import random
import socket  # 用做异常处理
from datetime import datetime, timedelta
from urllib.parse import quote

import requests  # 导入requests包
from bs4 import BeautifulSoup

import global_config
from global_config import logger
from model import Weather


def get_html(url, can_wait: bool = False, retries_times: int = 5, cookie: str = ''):
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
    if cookie != '':
        header['Cookie'] = cookie
    # 设定超时时间，取随机数是因为防止被网站认为是爬虫
    timeout = random.choice(range(120, 240))
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
        # 对于日照市需要特殊处理
        if city_name == '日照':
            city_name += '市'
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
        weather.min_temperature = int(min_temperature[0].text.replace('°', '').strip())
        weather.max_temperature = int(max_temperature[0].text.replace('°', '').strip())
        weather.humidity = int(humidity[0].text.replace('湿度: ', '').replace('%', '').strip())
        weather.weather_type = weather_type[0].text.strip()
        weather.source = '微软'
        return weather
    except ValueError as e:
        logger.error(e)
    except IndexError as e:
        logger.error(e)
    return None


def get_msn_weather(city_name: str, city_id: str, can_wait: bool = False) -> Weather or None:
    url = "https://www.msn.cn/zh-cn/weather/forecast/in-" + quote(
        city_name) + "?ocid=ansmsnweather&loc=eyJsIjoi5YyX5Lqs5biCIiwiYyI6IuS4reWNjuS6uuawkeWFseWSjOWbvSIsImkiOiJjbiIsInQiOjEwMiwiZyI6InpoLWNuIiwieCI6IjExNi40MDc0MTciLCJ5IjoiMzkuOTA0MTcyIn0%3D&weadegreetype=C"
    return None


def get_baidu_weather(city_name: str, city_id: str, can_wait: bool = False) -> Weather or None:
    try:
        city = city_name + '天气'
        url = "https://www.baidu.com/s?wd=" + quote(
            city) + '&rsv_spt=1&rsv_iqid=0xd192674d0009f891&issp=1&f=8&rsv_bp=1&rsv_idx=2&ie=utf-8&tn=baiduhome_pg&rsv_enter=1&rsv_dl=ib&rsv_sug3=20&rsv_sug1=7&rsv_sug7=101&rsv_sug2=0&rsv_btype=i&inputT=3571&rsv_sug4=4865'
        
        response = get_html(url, can_wait, cookie=global_config.baidu_login_cookie)
        soup = BeautifulSoup(response, 'html.parser')
        
        temperature = soup.select(
            '#content_left > div:nth-child(1) > div.op_weather4_twoicon_container_div > div.op_weather4_twoicon > a.op_weather4_twoicon_today.OP_LOG_LINK > p.op_weather4_twoicon_temp')
        weather_type = soup.select(
            '#content_left > div:first-child >  div.op_weather4_twoicon_container_div > div.op_weather4_twoicon > a.op_weather4_twoicon_today.OP_LOG_LINK > p.op_weather4_twoicon_weath')
        air_condition_number = soup.select(
            '#content_left > div:first-child > div.op_weather4_twoicon_container_div > div.op_weather4_twoicon > a.op_weather4_twoicon_today.OP_LOG_LINK > div.op_weather4_twoicon_realtime_quality_wrap > span > span:nth-child(1)')
        air_condition = soup.select(
            '#content_left > div:first-child > div.op_weather4_twoicon_container_div > div.op_weather4_twoicon > a.op_weather4_twoicon_today.OP_LOG_LINK > div.op_weather4_twoicon_realtime_quality_wrap > span > span:nth-child(2)')
        
        weather: Weather = Weather()
        weather.city_id = city_id
        weather.city_name = city_name
        temperature_text = temperature[0].text.replace('°', '').replace('C', '').replace('℃', '').strip()
        temperature_data = temperature_text.split('~')
        weather.min_temperature = int(temperature_data[0])
        weather.max_temperature = int(temperature_data[1])
        weather.humidity = 50
        weather.weather_type = weather_type[0].text.strip()
        # 对于空气质量没有爬到也无所谓
        try:
            weather.air_quality_number = int(air_condition_number[0].text.strip())
        except ValueError:
            pass
        weather.air_quality = air_condition[0].text.strip()
        weather.source = '百度'
        return weather
    except ValueError as e:
        logger.error(e)
    except IndexError as e:
        logger.error(e)
    return None


def get_weather_sojson(city_name: str, city_id: str, can_wait: bool = False) -> Weather or None:
    try:
        header = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        }
        url = "http://toy1.weather.com.cn/search?cityname=" + quote(
            city_name) + "&callback=success_jsonpCallback&_=1660895421896"
        timeout = random.choice(range(120, 240))
        query_city_index = requests.get(url, headers=header, timeout=timeout)
        query_city_index_text = query_city_index.text.strip().replace('success_jsonpCallback(', '').replace(')', '')
        city_list = json.loads(query_city_index_text)
        if len(city_list) == 0:
            return None
        city_index_data = city_list[0]['ref'].split('~')
        if len(city_index_data) == 0:
            return None
        city_index: str = city_index_data[0]
        
        url = "http://t.weather.sojson.com/api/weather/city/" + city_index
        response = get_html(url, can_wait)
        ans = json.loads(response)
        if ans['code'] == '40310003':
            return None
        if ans['status'] != 200:
            logger.info('未能获取城市<%s>的天气' % city_name)
            return None
        
        weather: Weather = Weather()
        weather.city_id = city_id
        weather.city_name = city_name
        weather.humidity = int(ans['data']['shidu'][:-1])
        weather.min_temperature = int(ans['data']['forecast'][0]['low'].replace('低温 ', '').replace('℃', ''))
        weather.max_temperature = int(ans['data']['forecast'][0]['high'].replace('高温 ', '').replace('℃', ''))
        weather.weather_type = ans['data']['forecast'][0]['type']
        weather.pm25 = ans['data']['pm25']
        weather.pm10 = ans['data']['pm10']
        weather.air_quality = ans['data']['quality']
        weather.aqi = ans['data']['forecast'][0]['aqi']
        weather.wind_direction = ans['data']['forecast'][0]['fx']
        weather.wind_level = ans['data']['forecast'][0]['fl']
        weather.advice = ans['data']['ganmao']
        weather.comment = ans['data']['forecast'][0]['notice']
        
        weather.source = '气象局'
        return weather
    except ValueError as e:
        logger.error(e)
    except IndexError as e:
        logger.error(e)
    return None


def get_weather_com_cn(city_name: str, city_id: str, can_wait: bool = False) -> Weather or None:
    try:
        header = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        }
        url = "http://toy1.weather.com.cn/search?cityname=" + quote(
            city_name) + "&callback=success_jsonpCallback&_=1660895421896"
        timeout = random.choice(range(120, 240))
        query_city_index = requests.get(url, headers=header, timeout=timeout)
        query_city_index_text = query_city_index.text.strip().replace('success_jsonpCallback(', '').replace(')', '')
        city_list = json.loads(query_city_index_text)
        if len(city_list) == 0:
            return None
        city_index_data = city_list[0]['ref'].split('~')
        if len(city_index_data) == 0:
            return None
        city_index: str = city_index_data[0]
        
        url = 'http://www.weather.com.cn/data/sk/%s.html' % city_index
        res = get_html(url, can_wait)
        data1 = json.loads(res)
        url2 = 'http://www.weather.com.cn/data/cityinfo/%s.html' % city_index
        res = get_html(url2, can_wait)
        data2 = json.loads(res)
        
        weather: Weather = Weather()
        weather.city_id = city_id
        weather.city_name = city_name
        weather.min_temperature = int(data2['weatherinfo']['temp1'].replace('℃', ''))
        weather.max_temperature = int(data2['weatherinfo']['temp2'].replace('℃', ''))
        weather.humidity = int(data1['weatherinfo']['SD'].replace('%', ''))
        weather.weather_type = data2['weatherinfo']['weather']
        weather.wind_direction = data1['weatherinfo']['WD']
        weather.wind_level = data1['weatherinfo']['WS']
        weather.source = '天气网'
        return weather
    except ValueError as e:
        logger.error(e)
    except IndexError as e:
        logger.error(e)
    return None


lock_weather_method = {}
weather_method_list = [('气象局', get_weather_sojson), ('微软', get_bing_weather), ('百度', get_baidu_weather),
                       ('天气网', get_weather_com_cn)]


def timed_get_city_weather(city_name: str, city_id: str, can_wait: bool, method_name: str, func):
    global lock_weather_method
    # 对获取天气的行为进行计时，如果有某一个方法在5秒内未能返回，那么一个小时内就不再继续使用
    start_time = datetime.now()
    if method_name not in lock_weather_method or lock_weather_method[method_name] >= datetime.now() + timedelta(
            hours=1):
        weather = func(city_name, city_id, can_wait)
        if weather is not None:
            end_time = datetime.now()
            seconds: int = (end_time - start_time).seconds
            if seconds > 5:
                lock_weather_method[method_name] = datetime.now()
            logger.info('从%s获得%s的天气，耗时%d秒' % (method_name, city_name, seconds))
            return weather
    return None


def get_city_weather(city_name: str, city_id: str, can_wait: bool = False) -> Weather:
    global weather_method_list
    logger.info('获取天气：' + city_name)
    random.shuffle(weather_method_list)
    for method in weather_method_list:
        weather = timed_get_city_weather(city_name, city_id, can_wait, method[0], method[1])
        if weather is not None:
            return weather
    logger.error('未能获得%s的天气' % city_name)
    return Weather()


if __name__ == '__main__':
    w = get_city_weather('重庆', '')
    print(w)
