"""
工具函数文件
"""

from enum import Enum
from typing import List
import copy
from model import *
from exceptions import *
import flower_dao


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


def insert_items(warehouse: WareHouse, items: List[DecorateItem]):
    """
    往仓库添加物品
    :param warehouse: 仓库
    :param items: 物品
    :return: none
    """
    copy_items = copy.deepcopy(warehouse.items)
    for item in items:
        item_obj: Item = flower_dao.select_item_by_id(item.item_id)
        if item_obj is None or item_obj.name == '':
            raise ItemNotFoundException('物品' + item.item_name + '不存在')
        if item.number < 0:
            raise ItemNegativeNumberException('物品' + item_obj.name + '数量不能为负数')
        for i in copy_items:
            if i.item_id == item.item_id:
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
                copy_items.append(DecorateItem(item_id=item.item_id, number=item_obj.max_stack))
                item.number -= item_obj.max_stack
            else:
                copy_items.append(DecorateItem(item_id=item.item_id, number=item.number))
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
        item_obj: Item = flower_dao.select_item_by_id(item.item_id)
        for i in copy_items:
            if i.item_id == item.item_id:
                if i.number >= item.number:
                    i.number -= item.number
                    item.number = 0
                    break
                else:
                    temp: int = item.number - i.number
                    i.number = 0
                    item.number -= temp
        if item.number > 0:
            raise ItemNotEnoughException('物品' + item_obj.name + '不足')
    warehouse.items = copy_items


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
    if qq == 0 or qq == 1597867839:
        return UserRight.ADMIN
    return UserRight.ADMIN
