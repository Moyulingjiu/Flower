# coding=utf-8
"""
工具函数文件
"""
import asyncio
import copy
import random
from datetime import datetime, timedelta
from enum import Enum
from threading import Thread
from typing import List, Tuple, Dict

import flower_dao
import global_config
import weather_getter
from flower_exceptions import *
from global_config import logger
from model import *


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


def get_user(qq: int, username: str = '') -> User:
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
    if user.clothing is None:
        user.clothing = Clothing()
    # 将金币、经验值放入排行榜
    flower_dao.put_user_rank(user)
    # 计算耐久度
    calculation_farm_equipment(user)
    # 计算信箱
    calculation_mailbox(user)
    # 计算仓库
    calculation_warehouse(user)
    # 清理背包中过期的物品
    if user.warehouse.check_item():
        flower_dao.update_user_by_qq(user)
    return user


def get_user_statistics(qq: int) -> UserStatistics:
    """
    获取统计数据
    """
    user_statistics: UserStatistics = flower_dao.select_user_statistics_by_qq(qq)
    if user_statistics is None or user_statistics.qq == 0:
        get_user(qq)  # 尝试获取用户，如果获取不到，那么证明没有注册有异常，会有flower的handle方法捕获
        user_statistics: UserStatistics = UserStatistics()
        user_statistics.qq = qq
        flower_dao.insert_user_statistics(user_statistics)
        user_statistics: UserStatistics = flower_dao.select_user_statistics_by_qq(qq)
    return user_statistics


####################################################################################################

def get_soil_list(soil_id_list: List[str]) -> str:
    """
    根据土壤id列表获取土壤名列表
    :param soil_id_list: 土壤id列表
    :return: 名字
    """
    res = ''
    init: bool = False
    for soil_id in soil_id_list:
        if soil_id is None:
            continue
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


def show_items(item_list: List[DecorateItem]) -> str:
    """
    展示一组物品
    :param item_list:
    :return:
    """
    reply = ''
    for item in item_list:
        reply += str(item) + '、'
    return reply[:-1]


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
        if climate_id is None:
            continue
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


def show_gold(gold: int) -> str:
    if gold < 10000 * 100:
        return '%.2f' % (gold / 100)
    else:
        res = ''
        gold = gold
        number = gold // (100000000 * 100)
        if number > 0:
            res += '%d亿' % number
            gold %= 100000000 * 100
        number = gold // (10000 * 100)
        if number > 0:
            res += '%d万' % number
            gold %= 10000 * 100
        if gold > 0:
            res += '%.2f' % (gold / 100)
        return res


####################################################################################################

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
    item.rot_second = item_obj.rot_second  # 腐烂的秒数
    item.humidity = item_obj.humidity  # 湿度
    item.nutrition = item_obj.nutrition  # 营养
    item.temperature = item_obj.temperature  # 温度
    item.level = item_obj.level
    if not item_obj.valid():
        raise ItemNotFoundException('')
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
            copy_item: DecorateItem = copy.deepcopy(item)
            copy_item.create = item.create
            ans.append(copy.deepcopy(copy_item))
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
            item.item_name = item_obj.name
        else:
            item_obj: Item = flower_dao.select_item_by_name(item.item_name)
            create_item: bool = True
        if item_obj is None or item_obj.name == '':
            raise ItemNotFoundException('物品' + item.item_name + '不存在')
        if item.number <= 0:
            raise ItemNegativeNumberException('物品' + item_obj.name + '数量不能为负数或零')
        if create_item:
            item.item_id = item_obj.get_id()
            # 将不变的属性从item复制过来
            item.item_type = item_obj.item_type
            item.max_durability = item_obj.max_durability  # 最大耐久度
            if item.durability < 0:
                item.durability = item_obj.max_durability
            item.rot_second = item_obj.rot_second  # 腐烂的秒数
            item.humidity = item_obj.humidity  # 湿度
            item.nutrition = item_obj.nutrition  # 营养
            item.temperature = item_obj.temperature  # 温度
            item.level = item_obj.level
            if item_obj.item_type == ItemType.flower and item.flower_quality == FlowerQuality.not_flower:
                item.flower_quality = FlowerQuality.normal
            if item_obj.item_type == ItemType.accelerate and item.hour < 1:
                item.hour = 1
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


####################################################################################################

class UserRight(Enum):
    """
    用户权限
    """
    MASTER = 0
    ADMIN = 1
    USER = 2


def get_user_right(qq: int):
    """
    根据qq获取用户权限
    :param qq: qq
    :return: 用户权限
    """
    system_data: SystemData = get_system_data()
    if system_data.test_version:
        return UserRight.MASTER
    if qq in system_data.mater_right_qq:
        return UserRight.MASTER
    if qq in system_data.admin_right_qq:
        return UserRight.ADMIN
    return UserRight.USER


####################################################################################################

def get_weather(city: City, can_wait: bool = False) -> Weather:
    """
    根据城市获取天气
    :param city: 城市
    :param can_wait: 爬虫是否等待以尝试再次爬取
    :return: 天气
    """
    weather: Weather = flower_dao.select_weather_by_city_id(city.get_id(), datetime.now())
    if weather.city_id != city.get_id():
        weather: Weather = weather_getter.get_city_weather(city.city_name, city.get_id(), can_wait=can_wait)
        weather.create_time = datetime.now()
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


def update_farm_soil(user: User, soil: Soil, cal_datetime: datetime) -> Soil:
    """
    更新农场的土壤
    :param user: 用户
    :param soil: 土壤
    :param cal_datetime: 计算的时间
    :return:
    """
    system_data: SystemData = get_system_data()
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

    # 改变土壤（如果被buff锁定了，那么就无法改变）
    total_buff: DecorateBuff = user.get_total_buff(cal_datetime)
    if not total_buff.lock_soil:
        if user.farm.soil_humidity_min_change_hour > system_data.soil_change_hour:
            if len(soil.min_change_humidity_soil_id) > 0:
                user.farm.soil_id = random.choice(soil.min_change_humidity_soil_id)
                soil = flower_dao.select_soil_by_id(user.farm.soil_id)
        elif user.farm.soil_humidity_max_change_hour > system_data.soil_change_hour:
            if len(soil.max_change_humidity_soil_id) > 0:
                user.farm.soil_id = random.choice(soil.max_change_humidity_soil_id)
                soil = flower_dao.select_soil_by_id(user.farm.soil_id)
        if user.farm.soil_nutrition_min_change_hour > system_data.soil_change_hour:
            if len(soil.min_change_nutrition_soil_id) > 0:
                user.farm.soil_id = random.choice(soil.min_change_nutrition_soil_id)
                soil = flower_dao.select_soil_by_id(user.farm.soil_id)
        elif user.farm.soil_nutrition_max_change_hour > system_data.soil_change_hour:
            if len(soil.max_change_nutrition_soil_id) > 0:
                user.farm.soil_id = random.choice(soil.max_change_nutrition_soil_id)
                soil = flower_dao.select_soil_by_id(user.farm.soil_id)
    return soil


def check_farm_soil_climate_condition(user: User, flower: Flower) -> None:
    """
    检查花是否符合这个条件种植
    :param user: 用户
    :param flower: 花
    :return:
    """
    # 如果花与土壤不符合那么直接枯萎（对于气候不做判断）
    if len(flower.soil_id) > 0:
        if user.farm.soil_id not in flower.soil_id:
            user.farm.flower_state = FlowerState.withered
    if len(flower.op_soil_id) > 0:
        if user.farm.soil_id in flower.op_soil_id:
            user.farm.flower_state = FlowerState.withered


def update_farm_condition(user: User, flower: Flower, weather: Weather, check_time: datetime, soil: Soil,
                          cal_datetime: datetime) -> None:
    """
    更新农场的条件
    :param user: 用户
    :param flower: 花
    :param weather: 天气
    :param check_time: 检查时间
    :param soil: 土壤
    :param cal_datetime: 计算的时间
    :return:
    """
    system_data: SystemData = get_system_data()
    now_temperature = ((12.0 - abs(check_time.hour - 12)) / 12.0) * (
            weather.max_temperature - weather.min_temperature) + weather.min_temperature
    origin_temperature: float = user.farm.temperature
    origin_humidity: float = user.farm.humidity
    origin_nutrition: float = user.farm.nutrition
    # 因为天气而改变的温度与湿度
    if user.farm.greenhouse.durability > 0 or user.farm.greenhouse.max_durability == 0:
        if user.farm.greenhouse.level == 4:
            user.farm.temperature += 0.05 * (now_temperature - user.farm.temperature)
            user.farm.humidity -= 0.1 * (1 - weather.humidity / 100)
        elif user.farm.greenhouse.level == 3:
            user.farm.temperature += 0.1 * (now_temperature - user.farm.temperature)
            user.farm.humidity -= 0.2 * (1 - weather.humidity / 100)
        elif user.farm.greenhouse.level == 2:
            user.farm.temperature += 0.2 * (now_temperature - user.farm.temperature)
            user.farm.humidity -= 0.5 * (1 - weather.humidity / 100)
        elif user.farm.greenhouse.level == 1:
            user.farm.temperature += 0.5 * (now_temperature - user.farm.temperature)
            user.farm.humidity -= 0.8 * (1 - weather.humidity / 100)
        else:
            user.farm.temperature += 0.8 * (now_temperature - user.farm.temperature)
            user.farm.humidity -= 1.0 * (1 - weather.humidity / 100)
    else:
        user.farm.temperature += 0.8 * (now_temperature - user.farm.temperature)
        user.farm.humidity -= 1.0 * (1 - weather.humidity / 100)
    # 天气所带来的湿度影响
    if weather.weather_type == '小雨':
        user.farm.humidity += 0.5
    elif weather.weather_type == '中雨':
        user.farm.humidity += 1.0
    elif weather.weather_type == '大雨' or '阵雨' in weather.weather_type:
        user.farm.humidity += 1.3
    elif weather.weather_type == '强雷暴':
        user.farm.humidity += 1.5
    # 花吸收的水分与营养
    if user.farm.flower_state != FlowerState.withered:
        user.farm.humidity -= flower.water_absorption
        user.farm.nutrition -= flower.nutrition_absorption
    # 增加buff所带来的水分与营养影响
    total_buff: DecorateBuff = user.get_total_buff(cal_datetime)
    user.farm.humidity += total_buff.change_humidity
    user.farm.nutrition += total_buff.change_nutrition
    user.farm.temperature += total_buff.change_temperature
    # 限制湿度与营养的土壤上下限
    if user.farm.humidity < soil.min_humidity:
        user.farm.humidity = soil.min_humidity
    elif user.farm.humidity > soil.max_humidity:
        user.farm.humidity = soil.max_humidity
    if user.farm.nutrition < soil.min_nutrition:
        user.farm.nutrition = soil.min_nutrition
    elif user.farm.nutrition > soil.max_nutrition:
        user.farm.nutrition = soil.max_nutrition
    # 如果buff有锁则不改变湿度等条件
    if total_buff.lock_humidity:
        user.farm.humidity = origin_humidity
    if total_buff.lock_nutrition:
        user.farm.nutrition = origin_nutrition
    if total_buff.lock_temperature:
        user.farm.temperature = origin_temperature
    # 限制湿度与营养的上下限
    if user.farm.humidity < system_data.soil_min_humidity:
        user.farm.humidity = system_data.soil_min_humidity
    elif user.farm.humidity > system_data.soil_max_humidity:
        user.farm.humidity = system_data.soil_max_humidity
    if user.farm.nutrition < system_data.soil_min_nutrition:
        user.farm.nutrition = system_data.soil_min_nutrition
    elif user.farm.nutrition > system_data.soil_max_nutrition:
        user.farm.nutrition = system_data.soil_max_nutrition


def check_farm_condition(user: User, flower: Flower, seed_time: int, grow_time: int, mature_time: int,
                         overripe_time: int, cal_datetime: datetime):
    """
    检查农场的环境，修改花的状态
    :param user: 用户
    :param flower: 花
    :param seed_time: 0——seed_time种子
    :param grow_time: seed_time——grow_time幼苗
    :param mature_time: grow_time——mature_time成熟
    :param overripe_time: mature_time——overripe_time过熟
    :param cal_datetime: 计算的时间
    :return:
    """
    total_buff: DecorateBuff = user.get_total_buff(cal_datetime)
    logger.debug('total_buff：%s' % str(total_buff))
    logger.debug('hour：%d.perfect_hour:%d,bad_hour:%d' % (user.farm.hour, user.farm.perfect_hour, user.farm.bad_hour))
    if user.farm.hour <= overripe_time * 2:
        # 计算条件
        if user.farm.hour < seed_time:
            condition_level: ConditionLevel = flower.seed_condition.get_condition_level(user.farm.temperature,
                                                                                        user.farm.humidity,
                                                                                        user.farm.nutrition)
        elif user.farm.hour < grow_time:
            condition_level: ConditionLevel = flower.grow_condition.get_condition_level(user.farm.temperature,
                                                                                        user.farm.humidity,
                                                                                        user.farm.nutrition)
        elif user.farm.hour < mature_time:
            condition_level: ConditionLevel = flower.mature_condition.get_condition_level(user.farm.temperature,
                                                                                          user.farm.humidity,
                                                                                          user.farm.nutrition)
        else:
            condition_level: ConditionLevel = flower.mature_condition.get_condition_level(user.farm.temperature,
                                                                                          user.farm.humidity,
                                                                                          user.farm.nutrition)
        # 根据条件不同来计算完美时间和糟糕的时间
        if condition_level == ConditionLevel.PERFECT:
            user.farm.perfect_hour += 1 * (1.0 + total_buff.perfect_coefficient)
        elif condition_level == ConditionLevel.BAD:
            user.farm.perfect_hour = 0
            user.farm.bad_hour += 1 * (1.0 + total_buff.bad_hour_coefficient)
        else:
            user.farm.perfect_hour = 0

        # 根据条件不同，每小时增长的小时不同
        if condition_level == ConditionLevel.PERFECT:
            if flower.level == FlowerLevel.S:
                user.farm.hour += 1.2 * (1.0 + total_buff.hour_coefficient)
            elif flower.level == FlowerLevel.A:
                user.farm.hour += 1.6 * (1.0 + total_buff.hour_coefficient)
            elif flower.level == FlowerLevel.B:
                user.farm.hour += 1.8 * (1.0 + total_buff.hour_coefficient)
            elif flower.level == FlowerLevel.C:
                user.farm.hour += 2.0 * (1.0 + total_buff.hour_coefficient)
            else:
                user.farm.hour += 2.0 * (1.0 + total_buff.hour_coefficient)
        elif condition_level == ConditionLevel.SUITABLE:
            user.farm.hour += 1.0 * (1.0 + total_buff.hour_coefficient)
        elif condition_level == ConditionLevel.NORMAL:
            if flower.level == FlowerLevel.S:
                user.farm.hour += 0.5 * (1.0 + total_buff.hour_coefficient)
            else:
                user.farm.hour += 0.8 * (1.0 + total_buff.hour_coefficient)
        else:
            if flower.level == FlowerLevel.S:
                user.farm.hour += 0.3 * (1.0 + total_buff.hour_coefficient)
            elif flower.level == FlowerLevel.A:
                user.farm.hour += 0.4 * (1.0 + total_buff.hour_coefficient)
            elif flower.level == FlowerLevel.B:
                user.farm.hour += 0.5 * (1.0 + total_buff.hour_coefficient)
            elif flower.level == FlowerLevel.C:
                user.farm.hour += 0.6 * (1.0 + total_buff.hour_coefficient)
            else:
                user.farm.hour += 0.7 * (1.0 + total_buff.hour_coefficient)

        # 根据条件来查看花的状态
        if user.farm.bad_hour >= flower.withered_time:
            user.farm.flower_state = FlowerState.withered
        elif user.farm.perfect_hour >= flower.prefect_time > 0:
            user.farm.flower_state = FlowerState.perfect
        else:
            user.farm.flower_state = FlowerState.normal
    else:
        # 如果已经超过过熟的时间那么一定是枯萎了
        user.farm.flower_state = FlowerState.withered
    logger.debug('hour：%d.perfect_hour:%d,bad_hour:%d' % (user.farm.hour, user.farm.perfect_hour, user.farm.bad_hour))


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

    seed_time: int = flower.seed_time
    grow_time: int = seed_time + flower.grow_time
    mature_time: int = grow_time + flower.mature_time
    overripe_time: int = mature_time + flower.overripe_time

    real_time_weather: Weather = flower_dao.select_weather_by_city_id(city.get_id(), start_time)
    if real_time_weather.city_id != city.get_id():
        real_time_weather = weather
    while start_time <= now:
        soil = update_farm_soil(user, soil, start_time)
        if user.farm.flower_id != '':
            check_farm_soil_climate_condition(user, flower)

        update_farm_condition(user, flower, real_time_weather, start_time, soil, start_time)
        if user.farm.flower_id != '' and user.farm.flower_state != FlowerState.withered:
            check_farm_condition(user, flower, seed_time, grow_time, mature_time, overripe_time, start_time)

        start_time += timedelta(hours=1)
        if start_time.date() != weather.create_time.date():
            real_time_weather: Weather = flower_dao.select_weather_by_city_id(city.get_id(), start_time)
            if real_time_weather.city_id != city.get_id():
                real_time_weather = weather
    user.buff = [buff for buff in user.buff if buff.expired_time >= start_time]
    user.farm.last_check_time = start_time - timedelta(hours=1)


def add_nutrition(farm: Farm, nutrition: float) -> float:
    """
    修改营养
    :param farm: 农场
    :param nutrition: 改变的值
    :return: 实际改变的值
    """
    system_data: SystemData = get_system_data()
    farm.nutrition += nutrition
    if farm.nutrition > system_data.soil_max_nutrition:
        nutrition -= farm.nutrition - system_data.soil_max_nutrition
        farm.nutrition = system_data.soil_max_nutrition
    elif farm.nutrition < system_data.soil_min_nutrition:
        nutrition += system_data.soil_min_nutrition - farm.nutrition
        farm.nutrition = system_data.soil_min_nutrition
    return nutrition


def add_humidity(farm: Farm, humidity: float) -> float:
    """
    修改湿度
    :param farm: 农场
    :param humidity: 湿度
    :return: 实际更改的湿度
    """
    system_data: SystemData = get_system_data()
    farm.humidity += humidity
    if farm.humidity > system_data.soil_max_humidity:
        humidity -= farm.humidity - system_data.soil_max_humidity
        farm.humidity = system_data.soil_max_humidity
    elif farm.humidity < system_data.soil_min_humidity:
        humidity += system_data.soil_min_humidity - farm.humidity
        farm.humidity = system_data.soil_min_humidity
    return humidity


####################################################################################################

def get_update_right() -> None:
    """
    尝试获取更新数据的权限
    :return:
    """
    try:
        logger.info('尝试获取更新数据的权限')
        lock_the_world()
        global_config.get_right_update_data = True
        logger.info('成功获取更新权限')
    except ResBeLockedException:
        logger.warning('获取更新权限失败')
        return


def release_update_right() -> None:
    """
    释放更新数据的权限
    :return:
    """
    if not global_config.get_right_update_data:
        return
    logger.info('已释放更新权限')
    unlock_the_world()


def get_all_weather(force: bool = False) -> None:
    """
    获取所有城市的天气
    :param force: 强制执行
    :return: none
    """
    if not global_config.get_right_update_data and not force:
        global_config.get_all_weather = False
        return
    logger.info('开始获取所有城市的天气')
    city_list: List[City] = flower_dao.select_all_city()
    index = 0
    fail_number = 0
    total = len(city_list)
    for city in city_list:
        if city.father_id == '':
            continue
        index += 1
        weather: Weather = get_weather(city, can_wait=True)
        if weather.city_id != city.get_id():
            fail_number += 1
            logger.error('%.2f%%' % (index * 100 / total) + ' ' + city.city_name + '天气获取失败')
        else:
            logger.info('%.2f%%' % (index * 100 / total) + ' ' + city.city_name + '天气获取成功')
        asyncio.sleep(0.5)
    logger.info('天气获取结果，总计城市：%d，有效城市：%d，获取失败：%d' % (total, index, fail_number))
    # 解除获取获取天气的锁
    global_config.get_all_weather = False


def update_all_user() -> None:
    """
    更新所有用户
    :return: none
    """
    if not global_config.get_right_update_data:
        return
    logger.info('开始更新所有用户数据')
    total_user_number: int = flower_dao.select_all_user_number()
    page_size: int = 20
    page: int = -1
    while total_user_number > 0:
        total_user_number -= page_size
        page += 1
        user_list: List[User] = flower_dao.select_all_user(page=page, page_size=page_size)
        for user in user_list:
            logger.info('更新用户<%s>(%d)的农场' % (user.username, user.qq))
            city: City = flower_dao.select_city_by_id(user.city_id)
            soil: Soil = flower_dao.select_soil_by_id(user.farm.soil_id)
            weather: Weather = get_weather(city)
            flower: Flower = flower_dao.select_flower_by_id(user.farm.flower_id)
            update_farm(user, city, soil, weather, flower)
            flower_dao.update_user_by_qq(user)
    logger.info('更新用户数据完成')


def lock_the_world() -> None:
    """
    锁住整个游戏
    :return:
    """
    flower_dao.lock(flower_dao.redis_global_game_lock)


def unlock_the_world() -> None:
    """
    解锁整个游戏
    :return:
    """
    flower_dao.unlock(flower_dao.redis_global_game_lock)


def get_global_lock() -> bool:
    return flower_dao.be_locked(flower_dao.redis_global_game_lock)


####################################################################################################

def calculation_mailbox(user: User):
    """
    计算信箱的容积
    :param user: 用户
    :return: none
    """
    if user.farm.mailbox.max_durability > 0 and user.farm.mailbox.durability == 0:
        return
    if user.farm.mailbox.level == 1:
        user.mailbox.max_size = 3
    elif user.farm.mailbox.level == 2:
        user.mailbox.max_size = 5
    elif user.farm.mailbox.level == 3:
        user.mailbox.max_size = 7
    elif user.farm.mailbox.level == 4:
        user.mailbox.max_size = 10
    else:
        user.mailbox.max_size = 0


def calculation_warehouse(user: User):
    """
    计算仓库容积
    :param user: 用户
    :return: none
    """
    if user.farm.warehouse.max_durability > 0 and user.farm.warehouse.durability == 0:
        return
    if user.farm.warehouse.level == 1:
        user.warehouse.max_size = 30
    elif user.farm.warehouse.level == 2:
        user.warehouse.max_size = 50
    elif user.farm.warehouse.level == 3:
        user.warehouse.max_size = 80
    elif user.farm.warehouse.level == 4:
        user.warehouse.max_size = 120
    elif user.farm.warehouse.level == 5:
        user.warehouse.max_size = 200
    else:
        user.warehouse.max_size = 20


def calculation_farm_equipment(user: User):
    """
    计算农场装备的耐久
    :param user: 用户
    :return: none
    """
    now: datetime = datetime.now()
    if user.farm.thermometer.max_durability > 0 and user.farm.thermometer.durability > 0:
        user.farm.thermometer.durability -= int((now - user.farm.thermometer.update).days)
        if user.farm.thermometer.durability < 0:
            user.farm.thermometer.durability = 0
            user.farm.thermometer = DecorateItem()
        user.farm.thermometer.update = now
    if user.farm.weather_station.max_durability > 0 and user.farm.weather_station.durability > 0:
        user.farm.weather_station.durability -= int((now - user.farm.weather_station.update).days)
        if user.farm.weather_station.durability < 0:
            user.farm.weather_station.durability = 0
            user.farm.weather_station = DecorateItem()
        user.farm.weather_station.update = now
    if user.farm.watering_pot.max_durability > 0 and user.farm.watering_pot.durability > 0:
        user.farm.watering_pot.durability -= int((now - user.farm.watering_pot.update).days)
        if user.farm.watering_pot.durability < 0:
            user.farm.watering_pot.durability = 0
            user.farm.watering_pot = DecorateItem()
        user.farm.watering_pot.update = now
    if user.farm.mailbox.max_durability > 0 and user.farm.mailbox.durability > 0:
        user.farm.mailbox.durability -= int((now - user.farm.mailbox.update).days)
        if user.farm.mailbox.durability < 0:
            user.farm.mailbox.durability = 0
            user.farm.mailbox = DecorateItem()
        user.farm.mailbox.update = now
    if user.farm.greenhouse.max_durability > 0 and user.farm.greenhouse.durability > 0:
        user.farm.greenhouse.durability -= int((now - user.farm.greenhouse.update).days)
        if user.farm.greenhouse.durability < 0:
            user.farm.greenhouse.durability = 0
            user.farm.greenhouse = DecorateItem()
        user.farm.greenhouse.update = now
    if user.farm.warehouse.max_durability > 0 and user.farm.warehouse.durability > 0:
        user.farm.warehouse.durability -= int((now - user.farm.warehouse.update).days)
        if user.farm.warehouse.durability < 0:
            user.farm.warehouse.durability = 0
            user.farm.warehouse = DecorateItem()
        user.farm.warehouse.update = now
    if user.farm.air_condition.max_durability > 0 and user.farm.air_condition.durability > 0:
        user.farm.air_condition.durability -= int((now - user.farm.air_condition.update).days)
        if user.farm.air_condition.durability < 0:
            user.farm.air_condition.durability = 0
            user.farm.air_condition = DecorateItem()
        user.farm.air_condition.update = now


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
            return '适中'
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
            return '适中'
    if humidity > 66:
        return '湿润'
    if humidity < 33:
        return '干燥'
    return '适中'


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
            return '适中'
    if nutrition > 32:
        return '营养丰富'
    if nutrition < 17:
        return '营养匮乏'
    return '适中'


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
    user.farm.temperature = (weather.max_temperature - weather.min_temperature) * 3 / 4 + weather.min_temperature


####################################################################################################
__system_data: SystemData = SystemData()  # 系统数据
__last_update_system_data: datetime = datetime.now() - timedelta(days=1)  # 上一次更新系统数据的时间


def get_system_data() -> SystemData:
    """
    获取系统数据
    """
    global __last_update_system_data, __system_data
    now: datetime = datetime.now()
    # 如果数据超出十分钟了那么更新数据
    if (now - __last_update_system_data).total_seconds() > global_config.ten_minute_second:
        __system_data = flower_dao.select_system_data()
        __last_update_system_data = now
    return __system_data


def analysis_time(message: str) -> int:
    """
    分析时间
    :param message: 原始消息（x天y小时z分钟s秒）
    :return: 秒数
    """
    message = message.strip()
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


####################################################################################################
def lock_user(qq: int):
    """
    锁定QQ
    """
    flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))


def unlock_user(qq: int):
    """
    解锁QQ
    """
    flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))


def lock_username(username: str):
    """
    锁定用户名
    """
    flower_dao.lock(flower_dao.redis_username_lock_prefix + username)


def unlock_username(username: str):
    """
    解锁用户名
    """
    flower_dao.unlock(flower_dao.redis_username_lock_prefix + username)


####################################################################################################
def send_system_mail(user: User, title: str, text: str, appendix: List[DecorateItem], gold: int):
    mail: Mail = Mail()
    mail.from_qq = 0
    mail.username = '系统'
    mail.target_qq = user.qq
    mail.title = title
    mail.text = text + '\n（系统邮件可以无视邮箱最大上限送达）'
    mail.appendix = appendix
    mail.gold = gold
    mail.arrived = True
    mail.status = '由系统直接送达'
    mail_id: str = flower_dao.insert_mail(mail)
    user.mailbox.mail_list.append(mail_id)


def send_award(user: User, title: str, text: str, award: List[DecorateItem] or int):
    """
    发送奖品
    """
    if isinstance(award, int):
        send_system_mail(user, title, text, [], award)
    elif isinstance(award, list):
        send_system_mail(user, title, text, award, 0)


def give_achievement(user: User, achievement_name: str, value: int = 1, cover_old_value: bool = False,
                     collection: List[str] = None) -> None:
    """
    给予成就
    """
    achievement: Achievement = flower_dao.select_achievement_by_name(achievement_name)
    if not achievement.valid():
        logger.error('未能找到成就：%s' % achievement_name)
        return
    if achievement_name not in user.achievement:
        user.achievement[achievement_name] = DecorateAchievement()
        user.achievement[achievement_name].name = achievement_name
        user.achievement[achievement_name].value = 0
        user.achievement[achievement_name].level = 0
        user.achievement[achievement_name].collection = collection
    user_achievement: DecorateAchievement = user.achievement[achievement_name]
    if cover_old_value:
        user_achievement.value = value
    else:
        user_achievement.value += value
    # 常规计算类的成就
    if user_achievement.level < len(achievement.value_list):
        if user_achievement.value >= achievement.value_list[user_achievement.level]:
            send_award(
                user,
                '获得成就%s' % achievement_name,
                '恭喜你！获得成就“%s”。这是我们为你准备的礼品。\n%s' % (achievement_name, achievement.description),
                achievement.award_list[user_achievement.level]
            )
            user_achievement.achievement_time = datetime.now()
            user_achievement.level += 1
    # 收集类成就
    elif len(achievement.collection) != 0 and collection is not None:
        # 收集类成就需要将收集转为
        achievement.collection = set(achievement.collection)
        user_achievement.collection = set(user_achievement.collection)
        for item in collection:
            user_achievement.collection.add(item)
        if user_achievement.collection == achievement.collection and user_achievement.level != 1:
            send_award(
                user,
                '获得成就%s' % achievement_name,
                '恭喜你！获得收集类成就“%s”。这是我们为你准备的礼品。\n%s' % (achievement_name, achievement.description),
                achievement.award_list[0]
            )
            user_achievement.achievement_time = datetime.now()
            user_achievement.level = 1
        else:
            user_achievement.level = 0
        user_achievement.collection = list(user_achievement.collection)


def leave_message(qq: int, message: str):
    """
    留言
    :param qq: qq
    :param message: 消息
    :return:
    """
    if qq in global_config.message_board:
        global_config.message_board[qq].append(message)
    else:
        global_config.message_board[qq] = [message]


def show_appearance(appearance: int, age: int) -> int:
    """
    显示颜值
    :param appearance:
    :param age:
    :return:
    """
    if age <= 5:
        return appearance
    if age <= 18:
        return int(appearance * (1.0 - 0.3 * (18 - age) / 13))
    if age <= 30:
        return appearance
    elif age <= 40:
        return int(appearance * (0.7 + 0.3 * (40 - age) / 10))
    elif age <= 70:
        return int(appearance * (0.3 + 0.4 * (70 - age) / 30))
    else:
        return int(appearance * 0.3)


def random_choice_pool(pool: Dict[str, int], relationship: Relationship) -> Commodity:
    """
    从池子里抽取东西
    :param pool:
    :param relationship:
    :return:
    """
    if len(pool) == 0:
        return Commodity()
    total: int = 0
    for item_id in pool:
        total += pool[item_id]
    rand: int = random.randint(0, total)
    for item_id in pool:
        rand -= pool[item_id]
        if rand < 0:
            commodity: Commodity = Commodity()
            commodity.item_id = item_id
            item: Item = flower_dao.select_item_by_id(item_id)
            if not item.valid():
                commodity.item_id = ''
                logger.error('商店池中物品不存在！')
            commodity.gold = int(item.gold * (1.0 - 0.3 * (relationship.value - 50 + random.randint(-5, 5)) / 50))
            if commodity.gold <= 10 * 100:
                commodity.stock = random.randint(1, 30)
            elif commodity.gold <= 50 * 100:
                commodity.stock = random.randint(1, 10)
            elif commodity.gold <= 50 * 500:
                commodity.stock = random.randint(1, 5)
            else:
                commodity.stock = 1
            return commodity
    return Commodity()


def get_today_person(qq: int) -> List[UserPerson]:
    """
    获取今日人物
    """
    user_person_list: List[UserPerson] = flower_dao.select_user_person_by_qq(qq, datetime.now())
    if len(user_person_list) == 0:
        generate_today_person(qq)
        user_person_list: List[UserPerson] = flower_dao.select_user_person_by_qq(qq, datetime.now())
    return user_person_list


def generate_today_person(qq: int):
    logger.info('开始更新每日npc@%d' % qq)
    system_data: SystemData = get_system_data()
    for _ in range(3):
        # 商人80%，探险家30%，建筑师10%
        rand: float = random.random()
        if rand < 0.9:
            profession: Profession = flower_dao.select_profession_by_name('商人')
            item_pool: Dict[str, int] = system_data.merchant_item_pool
        elif rand < 0.95:
            profession: Profession = flower_dao.select_profession_by_name('探险家')
            item_pool: Dict[str, int] = system_data.explorer_item_pool
        elif rand < 0.97:
            profession: Profession = flower_dao.select_profession_by_name('农民')
            item_pool: Dict[str, int] = {}
        else:
            profession: Profession = flower_dao.select_profession_by_name('建筑师')
            item_pool: Dict[str, int] = system_data.architect_item_pool
        person: Person = flower_dao.select_random_person_by_profession(profession.get_id())
        if not person.valid():
            continue
        user_person: UserPerson = UserPerson()
        user_person.qq = qq
        user_person.person_id = person.get_id()
        user_person.create_time = datetime.now()

        relationship: Relationship = flower_dao.select_relationship_by_pair(person.get_id(), str(qq))
        if not relationship.valid():
            relationship: Relationship = Relationship()
            relationship.src_person = person.get_id()
            relationship.dst_person = str(qq)
            relationship.value = person.affinity
            flower_dao.insert_relationship(relationship)
        # 总计最多有7件商品
        item_number: int = random.randint(1, 7)
        for _ in range(item_number):
            commodity: Commodity = random_choice_pool(item_pool, relationship)
            if commodity.item_id != '':
                user_person.commodities.append(commodity)
        if profession.name == '商人':
            seed_number = random.randint(1, 12 - item_number)
            for _ in range(seed_number):
                commodity: Commodity = random_choice_pool(system_data.merchant_seed_pool, relationship)
                if commodity.item_id != '':
                    user_person.commodities.append(commodity)
        elif profession.name == '探险家':
            seed_number = random.randint(1, 12 - item_number)
            for _ in range(seed_number):
                commodity: Commodity = random_choice_pool(system_data.explorer_seed_pool, relationship)
                if commodity.item_id != '':
                    user_person.commodities.append(commodity)
        elif profession.name == '农民':
            for _ in range(random.randint(1, 3)):
                if random.random() < 0.3:
                    flower: Flower = flower_dao.select_random_flower([FlowerLevel.D, FlowerLevel.C, FlowerLevel.B])
                else:
                    flower: Flower = flower_dao.select_random_flower([FlowerLevel.D, FlowerLevel.C])
                if not flower.valid():
                    continue
                if random.random() < 0.6:
                    level: int = 1
                elif random.random() < 0.9:
                    level: int = 2
                elif random.random() < 0.97:
                    level: int = 3
                else:
                    level: int = 4
                if flower.level == FlowerLevel.S:  # S级基准价格1级500金币
                    gold: int = int(50000 * level * (level + 1) / 2 * (
                            1.0 - 0.3 * (relationship.value - 50 + random.randint(-5, 5)) / 50))
                elif flower.level == FlowerLevel.A:  # A级基准价格1级250金币
                    gold: int = int(25000 * level * (level + 1) / 2 * (
                            1.0 - 0.3 * (relationship.value - 50 + random.randint(-5, 5)) / 50))
                elif flower.level == FlowerLevel.B:  # B级基准价格1级50金币
                    gold: int = int(5000 * level * (level + 1) / 2 * (
                            1.0 - 0.3 * (relationship.value - 50 + random.randint(-5, 5)) / 50))
                elif flower.level == FlowerLevel.C:  # C级基准价格1级10金币
                    gold: int = int(1000 * level * (level + 1) / 2 * (
                            1.0 - 0.3 * (relationship.value - 50 + random.randint(-5, 5)) / 50))
                else:  # D级知识不随等级波动
                    gold: int = int(1000 * (
                            1.0 - 0.3 * (relationship.value - 50 + random.randint(-5, 5)) / 50))
                user_person.knowledge[flower.name] = (level, gold)

        flower_dao.insert_user_person(user_person)


def calculate_item_gold(item: DecorateItem, item_obj: Item, relationship: Relationship,
                        random_ratio: float = 0.1) -> int:
    """
    计算商品价格
    """
    if relationship.value < 10:
        gold: int = 1
    else:
        if item_obj.item_type == ItemType.flower:
            ratio: float = 1.0
            if item.flower_quality == FlowerQuality.perfect:
                flower: Flower = flower_dao.select_flower_by_name(item_obj.name)
                if flower.level == FlowerLevel.S:
                    ratio: float = 2.0
                elif flower.level == FlowerLevel.A:
                    ratio: float = 1.5
                elif flower.level == FlowerLevel.B:
                    ratio: float = 1.2
                elif flower.level == FlowerLevel.C:
                    ratio: float = 1.15
                else:
                    ratio: float = 1.1
        else:
            ratio: float = 0.6
        if relationship.value > 90:
            random_ratio += 0.1
        if item_obj.max_durability > 0:
            duration_ratio: float = item.durability / item_obj.max_durability
        else:
            duration_ratio: float = 1.0
        # 0.7（非花）+0.2关系+0.1的随机数
        total_ratio: float = (ratio + 0.2 * (relationship.value - 50) / 50 + random_ratio * (random.random() - 0.5))
        gold: int = int(item_obj.gold * total_ratio * duration_ratio)
    return gold


def show_knowledge_level(level: int) -> str:
    """
    显示知识等级
    """
    if level >= 4:
        return '大师'
    elif level == 3:
        return '熟悉'
    elif level == 2:
        return '了解'
    elif level == 1:
        return '菜鸟'
    else:
        return '不认识'


def calculate_user_level(user: User):
    """
    计算用户等级
    """
    level = user.level
    system_data = get_system_data()
    for i in range(level, len(system_data.exp_level)):
        if user.exp >= system_data.exp_level[i]:
            level = i + 1
            if level != 1:
                send_system_mail(user, '升级奖励', '玩家角色达到%d级' % level, [], i * 10 * 100)
            user.level = level
            flower_dao.update_user_by_qq(user)
