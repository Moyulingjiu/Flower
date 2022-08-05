# coding=utf-8
"""
工具函数文件
"""

import copy
import random
import time
from datetime import datetime, timedelta
from enum import Enum
from threading import Thread
from typing import List, Tuple

import flower_dao
import global_config
from global_config import logger
from flower_exceptions import *
from model import *
import weather_getter


def async_function(f):
    """
    异步装饰器
    :param f: 函数
    :return: 包装之后的函数
    """
    
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    
    return wrapper


def get_user(qq: int, username: str) -> User:
    """
    获取用户
    :param qq: qq号
    :param username: 用户名
    :return: 用户
    """
    user = flower_dao.select_user_by_qq(qq)
    if user is None or user.qq == 0:
        raise UserNotRegisteredException('用户' + str(qq) + '未注册')
    if user.auto_get_name and username != '':
        user.username = username
    # 计算信箱
    calculation_mailbox(user)
    # 计算仓库
    calculation_warehouse(user)
    # 清理背包中过期的物品
    if user.warehouse.check_item():
        flower_dao.update_user_by_qq(user)
    return user


def get_soil_list(soil_id_list: List[str]) -> str:
    """
    根据土壤id列表获取土壤名列表
    :param soil_id_list: 土壤id列表
    :return: 名字
    """
    res = ''
    init: bool = False
    for soil_id in soil_id_list:
        if init:
            res += '、'
        else:
            init = True
        res += flower_dao.select_soil_by_id(soil_id).name
    return res


def show_cities_name(city_list: List[City]) -> str:
    """
    根据城市列表获取城市名列表
    :param city_list: 城市列表
    :return: 城市名
    """
    if len(city_list) == 0:
        return ''
    valid_data: bool = False  # 是否有有效的数据
    ans = '\n可能是'
    for city in city_list:
        if city.father_id != '0' and city.father_id != '':
            valid_data = True
            ans += city.city_name + '、'
    if valid_data:
        return ans[:-1]
    else:
        return ''


def show_items_name(item_list: List[Item]) -> str:
    """
    根据物品列表获取城市名列表
    :param item_list: 物品列表
    :return: 城市名
    """
    if len(item_list) == 0:
        return ''
    ans = '\n可能是'
    for item in item_list:
        ans += item.name + '、'
    return ans[:-1]


def get_climate_list(climate_ids: List[str]) -> str:
    """
    根据气候id列表获取气候名列表
    :param climate_ids: 气候ids
    :return: 气候名
    """
    res = ''
    for climate_id in climate_ids:
        climate = flower_dao.select_climate_by_id(climate_id)
        if climate is not None and climate.name != '':
            res += climate.name + '、'
    return res[:-1]


def show_condition(condition: Condition) -> str:
    """
    展示条件
    :param condition: 条件
    :return: 文本
    """
    res = '\n\t\t温度：' + str(condition.min_temperature) + '-' + str(condition.max_temperature)
    res += '\n\t\t湿度：' + str(condition.min_humidity) + '-' + str(condition.max_humidity)
    res += '\n\t\t营养：' + str(condition.min_nutrition) + '-' + str(condition.max_nutrition)
    return res


def show_conditions(conditions: Conditions) -> str:
    """
    展示一组条件
    :param conditions: 一组条件
    :return: 文本
    """
    res = '\n\t完美条件：'
    res += show_condition(conditions.perfect_condition)
    res += '\n\t适宜条件：'
    res += show_condition(conditions.suitable_condition)
    res += '\n\t正常条件：'
    res += show_condition(conditions.normal_condition)
    return res


def analysis_item(data: str) -> DecorateItem:
    """
    分析item
    :param data: 字段
    :return: item
    """
    data_list: List[str] = data.split(' ')
    if len(data_list) < 1 or len(data_list) > 3:
        raise TypeException('')
    item_name = data_list[0]
    if '—' in item_name:
        name_list = item_name.split('—')
        if len(name_list) == 2:
            item_name = name_list[0]
            data_list.append(name_list[1])
    if '-' in item_name:
        name_list = item_name.split('-')
        if len(name_list) == 2:
            item_name = name_list[0]
            data_list.append(name_list[1])
    if '（' in item_name:
        item_name = item_name[:item_name.rindex('（')]
    if len(data_list) == 1:
        item_number = 1
    else:
        try:
            item_number = int(data_list[1])
        except ValueError:
            raise TypeException('')
    item: DecorateItem = DecorateItem()
    item.item_name = item_name
    item.number = item_number
    
    item_obj: Item = flower_dao.select_item_by_name(item.item_name)
    item.item_type = item_obj.item_type
    if item_obj.item_type == ItemType.flower:
        item.flower_quality = FlowerQuality.normal
        if len(data_list) == 3:
            if data_list[2] == '完美':
                item.flower_quality = FlowerQuality.perfect
    elif item_obj.item_type == ItemType.accelerate:
        item.hour = 1
        if len(data_list) == 3:
            try:
                item.hour = int(data_list[2])
            except ValueError:
                pass
    elif item_obj.max_durability != 0:
        item.durability = item_obj.max_durability
        item.max_durability = item_obj.max_durability
        if len(data_list) == 3:
            try:
                item.durability = int(data_list[2])
            except ValueError:
                raise TypeException('')
    elif len(data_list) == 3:
        raise TypeException('')
    return item


def find_items(warehouse: WareHouse, item_name: str) -> List[DecorateItem]:
    """
    查找可能是的物品
    :param warehouse: 仓库
    :param item_name: 物品名
    :return: none
    """
    ans: List[DecorateItem] = []
    for item in warehouse.items:
        if item.item_name == item_name:
            ans.append(copy.deepcopy(item))
    return ans


def sort_items(warehouse: WareHouse):
    """
    整理仓库
    :param warehouse: 仓库
    :return: none
    """
    warehouse.items.sort()


def insert_items(warehouse: WareHouse, items: List[DecorateItem]):
    """
    往仓库添加物品
    :param warehouse: 仓库
    :param items: 物品
    :return: none
    """
    copy_items = copy.deepcopy(warehouse.items)
    for item in items:
        # 物体是否是新创建的
        create_item: bool = False
        if item.item_id != '' and item.item_id is not None:
            item_obj: Item = flower_dao.select_item_by_id(item.item_id)
        else:
            item_obj: Item = flower_dao.select_item_by_name(item.item_name)
            create_item: bool = True
        if item_obj is None or item_obj.name == '':
            raise ItemNotFoundException('物品' + item.item_name + '不存在')
        if item.number <= 0:
            raise ItemNegativeNumberException('物品' + item_obj.name + '数量不能为负数或零')
        if create_item:
            item.item_id = item_obj.get_id()
            item.item_type = item_obj.item_type
            # 将不变的属性从item复制过来
            item.item_type = item_obj.item_type
            item.max_stack = item_obj.max_stack  # 最大叠加数量
            item.max_durability = item_obj.max_durability  # 最大耐久度
            item.rot_second = item_obj.rot_second  # 腐烂的秒数
            item.humidity = item_obj.humidity  # 湿度
            item.nutrition = item_obj.nutrition  # 营养
            item.temperature = item_obj.temperature  # 温度
            item.level = item_obj.level
            if item_obj.item_type == ItemType.flower and item.flower_quality == FlowerQuality.not_flower:
                item.flower_quality = FlowerQuality.normal
        for i in copy_items:
            if i == item:
                if i.number + item.number <= item_obj.max_stack:
                    i.number += item.number
                    item.number = 0
                    break
                else:
                    temp: int = item_obj.max_stack - i.number
                    i.number += temp
                    item.number -= temp
        while item.number > 0:
            if len(copy_items) >= warehouse.max_size:
                raise WareHouseSizeNotEnoughException('背包容量不足')
            if item.number > item_obj.max_stack:
                append_item = copy.deepcopy(item)
                append_item.number = item_obj.max_stack
                copy_items.append(append_item)
                item.number -= item_obj.max_stack
            else:
                copy_items.append(copy.deepcopy(item))
                item.number = 0
    warehouse.items = copy_items


def remove_items(warehouse: WareHouse, items: List[DecorateItem]):
    """
    从仓库移除物品
    :param warehouse: 仓库
    :param items: 物品
    :return: none
    """
    copy_items = copy.deepcopy(warehouse.items)
    for item in items:
        item_obj: Item = flower_dao.select_item_by_name(item.item_name)
        if item_obj is None or item_obj.name == '':
            raise ItemNotFoundException('物品' + item.item_name + '不存在')
        for i in copy_items[::-1]:
            if i == item:
                if i.number >= item.number:
                    i.number -= item.number
                    item.number = 0
                    break
                else:
                    item.number -= i.number
                    i.number = 0
        if item.number > 0:
            raise ItemNotEnoughException('物品' + item.item_name + '不足')
    warehouse.items = [item for item in copy_items if item.number > 0]


class UserRight(Enum):
    """
    用户权限
    """
    ADMIN = 1
    USER = 2


def get_user_right(qq: int):
    """
    根据qq获取用户权限
    :param qq: qq
    :return: 用户权限
    """
    # todo: 根据qq获取用户权限（连接远程服务器）
    # 如果qq号是0表示系统查询，肯定是管理员
    if qq == 0:
        return UserRight.ADMIN
    return UserRight.ADMIN


def get_weather(city: City) -> Weather:
    """
    根据城市获取天气
    :param city: 城市
    :return: 天气
    """
    weather: Weather = flower_dao.select_weather_by_city_id(city.get_id())
    if weather.city_id != city.get_id():
        weather: Weather = weather_getter.get_city_weather(city.city_name, city.get_id())
        if weather.city_id == city.get_id():
            flower_dao.insert_weather(weather)
    return weather


def get_now_temperature(weather: Weather) -> float:
    """
    获取当前的温度
    :param weather: 天气
    :return: 当前温度
    """
    now: datetime = datetime.now()
    return ((12.0 - abs(now.hour - 12)) / 12.0) * (
            weather.max_temperature - weather.min_temperature) + weather.min_temperature


def get_farm_information(qq: int, username: str) -> Tuple[User, City, Soil, Climate, Weather, Flower]:
    """
    获取农场的所有信息
    :param qq: qq
    :param username: 用户名
    :return: 用户、城市、土地、天气、气候、花
    """
    user: User = get_user(qq, username)
    city: City = flower_dao.select_city_by_id(user.city_id)
    soil: Soil = flower_dao.select_soil_by_id(user.farm.soil_id)
    climate: Climate = flower_dao.select_climate_by_id(user.farm.climate_id)
    weather: Weather = get_weather(city)
    flower: Flower = Flower()
    if user.farm.flower_id != '':
        flower: Flower = flower_dao.select_flower_by_id(user.farm.flower_id)
    return user, city, soil, climate, weather, flower


def update_farm_soil(user: User, soil: Soil) -> None:
    """
    更新农场的土壤
    :param user: 用户
    :param soil: 土壤
    :return:
    """
    # 计算不符合条件的时间
    if user.farm.humidity < soil.min_change_humidity:
        user.farm.soil_humidity_min_change_hour += 1
        user.farm.soil_humidity_max_change_hour = 0
    elif user.farm.humidity > soil.max_change_humidity:
        user.farm.soil_humidity_max_change_hour += 1
        user.farm.soil_humidity_min_change_hour = 0
    else:
        user.farm.soil_humidity_max_change_hour = 0
        user.farm.soil_humidity_min_change_hour = 0
    
    if user.farm.nutrition < soil.min_change_nutrition:
        user.farm.soil_nutrition_min_change_hour += 1
        user.farm.soil_nutrition_max_change_hour = 0
    elif user.farm.nutrition > soil.max_change_nutrition:
        user.farm.soil_nutrition_max_change_hour += 1
        user.farm.soil_nutrition_min_change_hour = 0
    else:
        user.farm.soil_nutrition_max_change_hour = 0
        user.farm.soil_nutrition_min_change_hour = 0
    
    # 改变土壤
    if user.farm.soil_humidity_min_change_hour > global_config.soil_change_hour:
        if len(soil.min_change_humidity_soil_id) > 0:
            user.farm.soil_id = random.choice(soil.min_change_humidity_soil_id)
    elif user.farm.soil_humidity_max_change_hour > global_config.soil_change_hour:
        if len(soil.max_change_humidity_soil_id) > 0:
            user.farm.soil_id = random.choice(soil.max_change_humidity_soil_id)
    if user.farm.soil_nutrition_min_change_hour > global_config.soil_change_hour:
        if len(soil.min_change_nutrition_soil_id) > 0:
            user.farm.soil_id = random.choice(soil.min_change_nutrition_soil_id)
    elif user.farm.soil_nutrition_max_change_hour > global_config.soil_change_hour:
        if len(soil.max_change_nutrition_soil_id) > 0:
            user.farm.soil_id = random.choice(soil.max_change_nutrition_soil_id)


def check_farm_soil_climate_condition(user: User, flower: Flower) -> None:
    """
    检查花是否符合这个条件种植
    :param user: 用户
    :param flower: 花
    :return:
    """
    # 如果花与土壤不符合那么直接枯萎
    if len(flower.soil_id) > 0:
        if user.farm.soil_id not in flower.soil_id:
            user.farm.flower_state = FlowerState.withered
    if len(flower.op_soil_id) > 0:
        if user.farm.soil_id in flower.op_soil_id:
            user.farm.flower_state = FlowerState.withered
    if len(flower.climate_id) > 0:
        if user.farm.climate_id not in flower.climate_id:
            user.farm.flower_state = FlowerState.withered
    if len(flower.op_climate_id) > 0:
        if user.farm.climate_id in flower.op_climate_id:
            user.farm.flower_state = FlowerState.withered


def update_farm_condition(user: User, flower: Flower, weather: Weather, check_time: datetime) -> None:
    """
    更新农场的条件
    :param user: 用户
    :param flower: 花
    :param weather: 天气
    :param check_time: 检查时间
    :return:
    """
    now_temperature = ((12.0 - abs(check_time.hour - 12)) / 12.0) * (
            weather.max_temperature - weather.min_temperature) + weather.min_temperature
    # todo: 特殊道具会影响数据变动
    if user.farm.temperature < now_temperature:
        user.farm.temperature += 0.8
    elif user.farm.temperature > now_temperature:
        user.farm.temperature -= 0.8
    user.farm.humidity -= flower.water_absorption
    user.farm.nutrition -= flower.nutrition_absorption


def check_farm_condition(user: User, flower: Flower, seed_time: int, grow_time: int, mature_time: int,
                         overripe_time: int):
    """
    检查农场的环境，修改花的状态
    :param user: 用户
    :param flower: 花
    :param seed_time: 0——seed_time种子
    :param grow_time: seed_time——grow_time幼苗
    :param mature_time: grow_time——mature_time成熟
    :param overripe_time: mature_time——overripe_time过熟
    :return:
    """
    if user.farm.hour <= overripe_time:
        if user.farm.hour <= seed_time:
            condition_level: ConditionLevel = flower.seed_condition.get_condition_level(user.farm.temperature,
                                                                                        user.farm.humidity,
                                                                                        user.farm.nutrition)
        elif user.farm.hour <= grow_time:
            condition_level: ConditionLevel = flower.grow_condition.get_condition_level(user.farm.temperature,
                                                                                        user.farm.humidity,
                                                                                        user.farm.nutrition)
        elif user.farm.hour <= mature_time:
            condition_level: ConditionLevel = flower.mature_condition.get_condition_level(user.farm.temperature,
                                                                                          user.farm.humidity,
                                                                                          user.farm.nutrition)
        else:
            condition_level: ConditionLevel = flower.mature_condition.get_condition_level(user.farm.temperature,
                                                                                          user.farm.humidity,
                                                                                          user.farm.nutrition)
        if condition_level == ConditionLevel.PERFECT:
            user.farm.perfect_hour += 1
        elif condition_level == ConditionLevel.BAD:
            user.farm.perfect_hour = 0
            user.farm.bad_hour += 1
        else:
            user.farm.perfect_hour = 0
            user.farm.hour += 1
        
        if user.farm.bad_hour > flower.withered_time:
            user.farm.flower_state = FlowerState.withered
        elif user.farm.perfect_hour > flower.prefect_time > 0:
            user.farm.flower_state = FlowerState.perfect
        else:
            user.farm.flower_state = FlowerState.normal
    else:
        user.farm.flower_state = FlowerState.withered


def update_farm(user: User, city: City, soil: Soil, weather: Weather, flower: Flower) -> None:
    """
    更新农场
    :param user: 用户
    :param city: 城市
    :param soil: 泥土
    :param weather: 天气
    :param flower: 花
    :return: none
    """
    now: datetime = datetime.now()
    start_time: datetime = user.farm.last_check_time + timedelta(hours=1)
    user.farm.last_check_time = now
    if user.farm.flower_id == '':
        return
    if user.farm.flower_state == FlowerState.not_flower or user.farm.flower_state == FlowerState.withered:
        return
    
    seed_time: int = flower.seed_time
    grow_time: int = seed_time + flower.grow_time
    mature_time: int = grow_time + flower.mature_time
    overripe_time: int = mature_time + flower.overripe_time
    
    real_time_weather: Weather = flower_dao.select_weather_by_city_id(city.get_id(), start_time)
    if real_time_weather.city_id != city.get_id():
        real_time_weather = weather
    while start_time < now:
        update_farm_soil(user, soil)
        check_farm_soil_climate_condition(user, flower)
        if user.farm.flower_state == FlowerState.withered:
            break
        update_farm_condition(user, flower, real_time_weather, start_time)
        user.farm.hour += 1
        
        check_farm_condition(user, flower, seed_time, grow_time, mature_time, overripe_time)
        if user.farm.flower_state == FlowerState.withered:
            break
        
        start_time += timedelta(hours=1)
        if start_time.date() != weather.create_time.date():
            real_time_weather: Weather = flower_dao.select_weather_by_city_id(city.get_id(), start_time)
            if real_time_weather.city_id != city.get_id():
                real_time_weather = weather


def get_all_weather() -> None:
    """
    获取所有城市的天气
    :return: none
    """
    logger.info('开始获取所有城市的天气')
    city_list: List[City] = flower_dao.select_all_city()
    index = 0
    fail_number = 0
    total = len(city_list)
    for city in city_list:
        if city.father_id == '':
            continue
        index += 1
        weather: Weather = get_weather(city)
        if weather.city_id != city.get_id():
            fail_number += 1
            logger.error('%.2f%%' % (index * 100 / total) + ' ' + city.city_name + '天气获取失败')
        else:
            logger.info('%.2f%%' % (index * 100 / total) + ' ' + city.city_name + '天气获取成功')
        time.sleep(0.5)
    logger.info('天气获取结果，总计城市：%d，有效城市：%d，获取失败：%d' % (total, index, fail_number))
    # 解除获取获取天气的锁
    global_config.get_all_weather = False


def calculation_mailbox(user: User):
    """
    计算信箱的容积
    :param user: 用户
    :return: none
    """
    if user.farm.mailbox.level == 1:
        user.mailbox.max_size = 3
    elif user.farm.mailbox.level == 2:
        user.mailbox.max_size = 5
    elif user.farm.mailbox.level == 3:
        user.mailbox.max_size = 7
    elif user.farm.mailbox.level == 4:
        user.mailbox.max_size = 10
    user.mailbox.max_size = 0


def calculation_warehouse(user: User):
    """
    计算仓库容积
    :param user: 用户
    :return: none
    """
    if user.farm.warehouse.level == 1:
        user.warehouse.max_size = 30
    elif user.farm.warehouse.level == 2:
        user.warehouse.max_size = 50
    elif user.farm.warehouse.level == 3:
        user.warehouse.max_size = 80
    elif user.farm.warehouse.level == 4:
        user.warehouse.max_size = 120
    user.warehouse.max_size = 20


def show_temperature(user: User) -> str:
    """
    显示温度
    :param user: 用户
    :return: 结果
    """
    temperature: float = user.farm.temperature
    if user.farm.thermometer.max_durability == 0 or user.farm.thermometer.durability > 0:
        if user.farm.thermometer.level == 4:
            return '%.2f' % temperature
        elif user.farm.thermometer.level == 3:
            return '%d' % int(temperature)
        elif user.farm.thermometer.level == 2:
            return '%d' % ((int(temperature) // 5) * 5)
        elif user.farm.thermometer.level == 1:
            if temperature > 35:
                return '炎热'
            if temperature > 25:
                return '热'
            if temperature < 15:
                return '冷'
            if temperature < 5:
                return '寒冷'
            return '适宜'
    if temperature > 30:
        return '热'
    if temperature < 10:
        return '冷'
    return '不冷不热'


def show_humidity(user: User) -> str:
    """
    显示土壤湿度
    :param user: 用户
    :return: 结果
    """
    humidity: float = user.farm.humidity
    if user.farm.soil_monitoring_station.max_durability == 0 or user.farm.soil_monitoring_station.durability > 0:
        if user.farm.soil_monitoring_station.level == 4:
            return '%.2f' % humidity
        elif user.farm.soil_monitoring_station.level == 3:
            return '%d' % int(humidity)
        elif user.farm.soil_monitoring_station.level == 2:
            return '%d' % ((int(humidity) // 5) * 5)
        elif user.farm.soil_monitoring_station.level == 1:
            if humidity > 80:
                return '极其湿润'
            if humidity > 60:
                return '湿润'
            if humidity < 40:
                return '干燥'
            if humidity < 20:
                return '极其干燥'
            return '适宜'
    if humidity > 66:
        return '湿润'
    if humidity < 33:
        return '干燥'
    return '适宜'


def show_nutrition(user: User) -> str:
    """
    显示土壤湿度
    :param user: 用户
    :return: 结果
    """
    nutrition: float = user.farm.nutrition
    if user.farm.soil_monitoring_station.max_durability == 0 or user.farm.soil_monitoring_station.durability > 0:
        if user.farm.soil_monitoring_station.level == 4:
            return '%.2f' % nutrition
        elif user.farm.soil_monitoring_station.level == 3:
            return '%d' % int(nutrition)
        elif user.farm.soil_monitoring_station.level == 2:
            return '%d' % ((int(nutrition) // 5) * 5)
        elif user.farm.soil_monitoring_station.level == 1:
            if nutrition > 40:
                return '营养极其丰富'
            if nutrition > 30:
                return '营养丰富'
            if nutrition < 20:
                return '营养匮乏'
            if nutrition < 10:
                return '营养极其匮乏'
            return '适宜'
    if nutrition > 32:
        return '营养丰富'
    if nutrition < 17:
        return '营养匮乏'
    return '适宜'


def init_user_farm(user: User, city: City) -> None:
    """
    初始化用户农场
    :param user: 用户
    :param city: 城市
    :return: none
    """
    user.farm.soil_id = city.soil_id
    user.farm.climate_id = city.climate_id
    soil: Soil = flower_dao.select_soil_by_id(city.soil_id)
    user.farm.humidity = (soil.max_humidity + soil.min_humidity) / 2
    user.farm.nutrition = (soil.max_nutrition + soil.min_nutrition) / 2
    weather: Weather = get_weather(city)
    user.farm.temperature = (weather.max_temperature - weather.min_temperature) \
                            * 3 / 4 + weather.min_temperature


def analysis_time(message: str) -> int:
    """
    分析时间
    :param message: 原始消息（x天y小时z分钟s秒）
    :return: 秒数
    """
    try:
        second: int = 0
        if '天' in message:
            index: int = message.index('天')
            second += global_config.day_second * int(message[:index])
            message = message[index + 1:]
        if '小时' in message:
            index: int = message.index('小时')
            second += global_config.hour_second * int(message[:index])
            message = message[index + 2:]
        if '分钟' in message:
            index: int = message.index('分钟')
            second += global_config.minute_second * int(message[:index])
            message = message[index + 2:]
        if message.endswith('秒'):
            second += int(message[:-1])
        return second
    except ValueError:
        return 0
