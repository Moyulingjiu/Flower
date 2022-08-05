# coding=utf-8
import base64
from datetime import datetime, timedelta
import pickle
import random
import time
from enum import Enum
from typing import Dict, List, Tuple

import pymongo
from bson import ObjectId
from redis import ConnectionPool, StrictRedis

from flower_exceptions import *
from model import *
import global_config

# MongoDB
mongo_client = pymongo.MongoClient(global_config.mongo_connection)
mongo_db = mongo_client['xiaoqi']

mongo_system = mongo_db['system']  # 系统
mongo_announcement = mongo_db['announcement']  # 公告
mongo_region = mongo_db['region']  # 地区
mongo_terrain = mongo_db['terrain']  # 地形
mongo_climate = mongo_db['climate']  # 气候
mongo_soil = mongo_db['soil']  # 土壤
mongo_city = mongo_db['city']  # 城市
mongo_flower = mongo_db['flower']  # 花卉
mongo_user = mongo_db['user']  # 用户
mongo_item = mongo_db['item']  # 物品
mongo_weather = mongo_db['weather']  # 天气

mongo_sign_record = mongo_db['sign_record']  # 签到记录

# Redis
redis_pool = ConnectionPool(host=global_config.redis_host, port=global_config.redis_port, db=global_config.redis_db,
                            password=global_config.redis_password, decode_responses=True)
redis_db = StrictRedis(connection_pool=redis_pool)

redis_global_prefix = 'flower_'  # redis全局前缀
redis_system_data_prefix = redis_global_prefix + 'system_data'  # 系统数据前缀（有且仅有一个）
redis_announcement_prefix = redis_global_prefix + 'announcement'  # 公告数据前缀（有且仅有一个，为一个列表，表示当前有效的公告）
redis_region_prefix = redis_global_prefix + 'region_'  # 地区redis前缀（地区id）
redis_terrain_prefix = redis_global_prefix + 'terrain_'  # 地形redis前缀（地形id）
redis_climate_prefix = redis_global_prefix + 'climate_'  # 气候redis前缀（气候id）
redis_soil_prefix = redis_global_prefix + 'soil_'  # 土壤redis前缀（土壤id）
redis_city_prefix = redis_global_prefix + 'city_'  # 城市redis前缀（城市id）
redis_flower_prefix = redis_global_prefix + 'flower_'  # 花redis前缀（花id）
redis_user_prefix = redis_global_prefix + 'user_'  # 用户redis前缀（用户qq）
redis_username_prefix = redis_global_prefix + 'username_'  # 用户名redis前缀（用户qq）
redis_item_prefix = redis_global_prefix + 'item_'  # 物品redis前缀（物品id）
redis_weather_prefix = redis_global_prefix + 'weather_'  # 天气redis前缀（城市id+日期）

redis_all_city_prefix = redis_global_prefix + 'city_all'  # 所有城市的前缀
redis_city_like_prefix = redis_global_prefix + 'city_like_'  # 城市模糊匹配前缀
redis_item_like_prefix = redis_global_prefix + 'item_like_'  # 物品模糊匹配前缀
redis_warehouse_item_like_prefix = redis_global_prefix + 'warehouse_item_like_'  # 仓库内的物品匹配前缀

redis_user_lock_prefix = redis_global_prefix + 'user_lock_'  # 用户锁前缀
redis_username_lock_prefix = redis_global_prefix + 'username_lock_'  # 用户名锁前缀
redis_user_context_prefix = redis_global_prefix + 'user_context_'  # 用户上下文前缀

redis_user_gold_rank = redis_global_prefix + 'user_gold_rank'  # 用户金币排行榜
redis_user_exp_rank = redis_global_prefix + 'user_exp_rank'  # 用户经验排行榜

####################################################################################################
# 全局常量
expire_time_seconds: int = global_config.minute_second  # 很容易短期改变的值
long_expire_time_seconds: int = global_config.half_day_second  # 长期才会改变的值
context_expire_time_seconds: int = global_config.week_second  # 上下文的过期时间

lock_wait_time = 5000  # 锁等待时间（尝试五秒）
lock_try_interval = 500  # 锁等待时间（每五百毫秒尝试一次）


def get_long_random_expire() -> int:
    """
    获取随机的过期时间，避免雪崩出现
    :return: 过期时间
    """
    # 返回1——2倍的过期时间
    return random.randint(long_expire_time_seconds, long_expire_time_seconds * 2)


def get_random_expire() -> int:
    """
    获取随机的过期时间，避免雪崩出现
    :return: 过期时间
    """
    # 返回1——2倍的过期时间
    return random.randint(expire_time_seconds, expire_time_seconds * 2)


def class_to_dict(obj) -> Dict:
    """
    将对象转换为字典
    :param obj: 对象
    :return: 字典
    """
    ans = {}
    if isinstance(obj, dict):
        return obj
    for key in obj.__dict__:
        if key[0] == '_':
            continue
        elif isinstance(obj.__dict__[key], Enum):
            ans[key] = obj.__dict__[key].value
        elif isinstance(obj.__dict__[key], InnerClass):
            ans[key] = class_to_dict(obj.__dict__[key])
        elif isinstance(obj.__dict__[key], list):
            ans[key] = []
            if len(obj.__dict__[key]) > 0 and isinstance(obj.__dict__[key][0], InnerClass):
                for item in obj.__dict__[key]:
                    ans[key].append(class_to_dict(item))
            else:
                ans[key] = obj.__dict__[key]
        elif isinstance(obj.__dict__[key], dict):
            ans[key] = class_to_dict(obj.__dict__[key])
        else:
            ans[key] = obj.__dict__[key]
    return ans


def dict_to_inner_class(d: Dict) -> object or None:
    if d['class_type'] == 'Condition':
        return dict_to_class(d, Condition())
    elif d['class_type'] == 'Conditions':
        return dict_to_class(d, Conditions())
    elif d['class_type'] == 'Farm':
        o = dict_to_class(d, Farm())
        o.flower_state = FlowerState.get_type(o.flower_state)
        return o
    elif d['class_type'] == 'DecorateItem':
        o = dict_to_class(d, DecorateItem())
        o.flower_quality = FlowerQuality.get_type(o.flower_quality)
        return o
    elif d['class_type'] == 'WareHouse':
        return dict_to_class(d, WareHouse())
    elif d['class_type'] == 'MailBox':
        return dict_to_class(d, MailBox())
    return None


def dict_to_class(d: Dict, o) -> object or None:
    """
    将字典转换为对象
    注意：原始对象也会被改变
    :param d: 字典
    :param o: 对象
    :return: 对象
    """
    if d is None:
        return None
    for key in d:
        if isinstance(d[key], ObjectId):
            o.__dict__[key] = str(d[key])
        elif isinstance(d[key], dict):
            if 'class_type' in d[key]:
                o.__dict__[key] = dict_to_inner_class(d[key])
            else:
                o.__dict__[key] = d[key]
        elif isinstance(d[key], list):
            o.__dict__[key] = []
            if len(d[key]) > 0:
                if isinstance(d[key][0], dict):
                    for item in d[key]:
                        inner_o = dict_to_inner_class(item)
                        if inner_o is not None:
                            o.__dict__[key].append(inner_o)
                else:
                    o.__dict__[key] = d[key]
        else:
            o.__dict__[key] = d[key]
    return o


def serialization(obj) -> str:
    """
    序列化对象
    :param obj: 对象
    :return: 序列化后的对象
    """
    return base64.b64encode(pickle.dumps(obj)).decode()


def deserialize(obj):
    """
    反序列化对象
    :param obj: 对象
    :return: 反序列化后的对象
    """
    return pickle.loads(base64.b64decode(obj.encode()))


def lock(key: str, wait_time: int = lock_wait_time, try_interval: int = lock_try_interval) -> None:
    """
    加锁
    :param key: 字段名
    :param wait_time: 等待时间（单位：毫秒）
    :param try_interval: 每次尝试的时间间隔（单位：毫秒）
    :return: 是否加锁成功
    """
    while wait_time > 0:
        if redis_db.setnx(key, 1):
            # 设置过期时间
            redis_db.expire(key, get_long_random_expire())
            return
        time.sleep(try_interval / 1000)
        wait_time -= try_interval
    raise ResBeLockedException('资源被锁定')


def unlock(key: str) -> int:
    """
    解锁
    :param key: 字段名
    :return: 是否解锁成功
    """
    return redis_db.delete(key)


####################################################################################################
def insert_region(region: Region) -> str:
    """
    插入地区
    :param region: 地区
    :return: id
    """
    result = mongo_region.insert_one(class_to_dict(region))
    redis_db.delete(redis_region_prefix + str(result.inserted_id))
    redis_db.delete(redis_region_prefix + region.name)
    return result.inserted_id


def select_region_by_id(_id: str) -> Region:
    """
    根据id查询地区
    :param _id: id
    :return: 地区
    """
    redis_ans = redis_db.get(redis_region_prefix + _id)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_region.find_one({"_id": ObjectId(_id)})
        region: Region = Region()
        dict_to_class(result, region)
        redis_db.set(redis_region_prefix + _id, serialization(region), ex=get_long_random_expire())
        return region


def insert_terrain(terrain: Terrain) -> str:
    """
    插入地形
    :param terrain: 地形
    :return: id
    """
    result = mongo_terrain.insert_one(class_to_dict(terrain))
    redis_db.delete(redis_terrain_prefix + str(result.inserted_id))
    redis_db.delete(redis_terrain_prefix + terrain.name)
    return result.inserted_id


def select_terrain_by_id(_id: str) -> Terrain:
    """
    根据id获取地形
    :param _id: id
    :return: 地形
    """
    redis_ans = redis_db.get(redis_terrain_prefix + _id)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_terrain.find_one({"_id": ObjectId(_id)})
        terrain: Terrain = Terrain()
        dict_to_class(result, terrain)
        redis_db.set(redis_terrain_prefix + _id, serialization(terrain), ex=get_long_random_expire())
        return terrain


def insert_climate(climate: Climate) -> str:
    """
    插入气候
    :param climate: 气候
    :return: id
    """
    result = mongo_climate.insert_one(class_to_dict(climate))
    redis_db.delete(redis_climate_prefix + climate.name)
    redis_db.delete(redis_climate_prefix + str(result.inserted_id))
    return result.inserted_id


def select_climate_by_id(_id: str) -> Climate:
    """
    根据id获取气候
    :param _id: id
    :return: 气候
    """
    redis_ans = redis_db.get(redis_climate_prefix + _id)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_climate.find_one({"_id": ObjectId(_id)})
        climate: Climate = Climate()
        dict_to_class(result, climate)
        redis_db.set(redis_climate_prefix + _id, serialization(climate), ex=get_long_random_expire())
        return climate


def select_climate_by_name(name: str) -> Climate:
    """
    根据名称获取气候
    :param name: 名称
    :return: 气候
    """
    redis_ans = redis_db.get(redis_climate_prefix + name)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_climate.find_one({"name": name})
        climate: Climate = Climate()
        dict_to_class(result, climate)
        redis_db.set(redis_climate_prefix + name, serialization(climate), ex=get_long_random_expire())
        return climate


def insert_soil(soil: Soil) -> str:
    """
    插入土壤
    :param soil: 土壤
    :return: id
    """
    result = mongo_soil.insert_one(class_to_dict(soil))
    redis_db.delete(redis_soil_prefix + soil.name)
    redis_db.delete(redis_soil_prefix + str(result.inserted_id))
    return result.inserted_id


def select_soil_by_id(_id: str) -> Soil:
    """
    根据id获取土壤
    :param _id: id
    :return: 土壤
    """
    redis_ans = redis_db.get(redis_soil_prefix + _id)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_soil.find_one({"_id": ObjectId(_id)})
        soil: Soil = Soil()
        dict_to_class(result, soil)
        redis_db.set(redis_soil_prefix + _id, serialization(soil), ex=get_long_random_expire())
        return soil


def select_soil_by_name(name: str) -> Soil:
    """
    根据名称获取土壤
    :param name: 名称
    :return: 土壤
    """
    redis_ans = redis_db.get(redis_soil_prefix + name)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_soil.find_one({"name": name})
        soil: Soil = Soil()
        dict_to_class(result, soil)
        redis_db.set(redis_soil_prefix + name, serialization(soil), ex=get_long_random_expire())
        return soil


def update_soil(soil: Soil) -> int:
    """
    更新土壤
    :param soil: 土壤
    :return: id
    """
    result = mongo_soil.update_one({"_id": ObjectId(soil.get_id())}, {"$set": class_to_dict(soil)})
    redis_db.set(redis_soil_prefix + soil.get_id(), serialization(soil), ex=get_long_random_expire())
    return result.modified_count


def insert_city(city: City) -> str:
    """
    插入城市
    :param city: 城市
    :return: id
    """
    result = mongo_city.insert_one(class_to_dict(city))
    redis_db.delete(redis_city_prefix + str(result.inserted_id))
    redis_db.delete(redis_city_prefix + city.city_name)
    return result.inserted_id


def select_city_by_id(_id: str) -> City:
    """
    根据id获取城市
    :param _id: id
    :return: 城市
    """
    redis_ans = redis_db.get(redis_city_prefix + _id)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_city.find_one({"_id": ObjectId(_id)})
        city: City = City()
        dict_to_class(result, city)
        redis_db.set(redis_city_prefix + _id, serialization(city), ex=get_long_random_expire())
        return city


def select_city_by_name(name: str) -> City:
    """
    根据名称获取城市
    :param name: 名称
    :return: 城市
    """
    redis_ans = redis_db.get(redis_city_prefix + name)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_city.find_one({"city_name": name, "is_delete": 0})
        city: City = City()
        dict_to_class(result, city)
        redis_db.set(redis_city_prefix + name, serialization(city), ex=get_long_random_expire())
        return city


def select_all_city() -> List[City]:
    """
    获取所有城市
    :return: 所有城市
    """
    redis_ans = redis_db.get(redis_all_city_prefix)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_city.find({"is_delete": 0})
        city_list: List[City] = []
        for city_result in result:
            city: City = City()
            dict_to_class(city_result, city)
            city_list.append(city)
        redis_db.set(redis_all_city_prefix, serialization(city_list), ex=global_config.week_second)
        return city_list


def select_city_by_name_like(name: str) -> List[City]:
    """
    模糊查询城市名
    :param name: 城市名
    :return: 城市
    """
    redis_ans = redis_db.get(redis_city_like_prefix + name)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_city.find({"city_name": {"$regex": name}, "is_delete": 0})
        city_list: List[City] = []
        for city_result in result:
            city: City = City()
            dict_to_class(city_result, city)
            city_list.append(city)
        redis_db.set(redis_city_like_prefix + name, serialization(city_list), ex=get_long_random_expire())
        return city_list


def insert_flower(flower: Flower) -> str:
    """
    插入花卉
    :param flower: 花卉
    :return: id
    """
    result = mongo_flower.insert_one(class_to_dict(flower))
    redis_db.delete(redis_flower_prefix + str(result.inserted_id))
    redis_db.delete(redis_flower_prefix + flower.name)
    return result.inserted_id


def select_flower_by_id(_id: str) -> Flower:
    """
    根据id获取花卉
    :param _id: id
    :return: 花卉
    """
    redis_ans = redis_db.get(redis_flower_prefix + _id)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_flower.find_one({"_id": ObjectId(_id)})
        flower: Flower = Flower()
        dict_to_class(result, flower)
        flower.level = FlowerLevel.get_level(str(flower.level))
        redis_db.set(redis_flower_prefix + _id, serialization(flower), ex=get_long_random_expire())
        return flower


def select_flower_by_name(name: str) -> Flower:
    """
    根据名称获取花卉
    :param name: 名称
    :return: 花卉
    """
    redis_ans = redis_db.get(redis_flower_prefix + name)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_flower.find_one({"name": name, "is_delete": 0})
        flower: Flower = Flower()
        dict_to_class(result, flower)
        flower.level = FlowerLevel.get_level(str(flower.level))
        redis_db.set(redis_flower_prefix + name, serialization(flower), ex=get_long_random_expire())
        return flower


def select_user_by_qq(qq: int) -> User:
    """
    根据qq查询用户
    :param qq: qq
    :return: 用户
    """
    redis_ans = redis_db.get(redis_user_prefix + str(qq))
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_user.find_one({"qq": qq, "is_delete": 0})
        user: User = User()
        dict_to_class(result, user)
        redis_db.set(redis_user_prefix + str(qq), serialization(user), ex=get_random_expire())
        return user


def select_all_user(page: int = 0, page_size: int = 20) -> List[User]:
    """
    查找全部user
    :param page: 页码（从0开始）
    :param page_size: 页码大小
    :return: 用户的列表
    """
    result = mongo_user.find({"is_delete": 0}).limit(page_size).skip(page * page_size)
    user_list: List[User] = []
    for result_user in result:
        user: User = User()
        dict_to_class(result_user, user)
        user_list.append(user)
    return user_list


def select_user_by_username(username: str) -> User:
    """
    根据用户名查询用户
    :param username: 用户名
    :return: 用户
    """
    redis_ans = redis_db.get(redis_username_prefix + str(username))
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_user.find_one({"username": username, "auto_get_name": False, "is_delete": 0})
        user: User = User()
        dict_to_class(result, user)
        redis_db.set(redis_username_prefix + str(username), serialization(user), ex=get_random_expire())
        return user


def update_user_by_qq(user: User) -> int:
    """
    根据qq更新用户
    :param user: 用户
    :return: 更新结果
    """
    result = mongo_user.update_one({"qq": user.qq, "is_delete": 0}, {"$set": class_to_dict(user)})
    redis_db.delete(redis_user_prefix + str(user.qq))
    redis_db.delete(redis_username_prefix + str(user.username))
    return result.modified_count


def insert_user(user: User) -> str:
    """
    插入用户
    :param user: 用户
    :return: id
    """
    result = mongo_user.insert_one(class_to_dict(user))
    redis_db.delete(redis_user_prefix + str(user.qq))
    redis_db.delete(redis_username_prefix + str(user.username))
    return result.inserted_id


def insert_sign_record(sign_record: SignRecord) -> str:
    """
    插入签到数据
    :param sign_record: 签到数据
    :return: id
    """
    result = mongo_sign_record.insert_one(class_to_dict(sign_record))
    return result.inserted_id


def select_item_by_id(item_id: str) -> Item:
    """
    根据id查询物品
    :param item_id: id
    :return: 物品
    """
    redis_ans = redis_db.get(redis_item_prefix + item_id)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_item.find_one({"_id": ObjectId(item_id)})
        item: Item = Item()
        dict_to_class(result, item)
        item.item_type = ItemType.get_type(str(item.item_type))
        redis_db.set(redis_item_prefix + item_id, serialization(item), ex=get_long_random_expire())
        return item


def select_item_by_name(name: str) -> Item:
    """
    根据名称查询物品
    :param name: 名称
    :return: 物品
    """
    redis_ans = redis_db.get(redis_item_prefix + name)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_item.find_one({"name": name, "is_delete": 0})
        item: Item = Item()
        dict_to_class(result, item)
        item.item_type = ItemType.get_type(str(item.item_type))
        redis_db.set(redis_item_prefix + name, serialization(item), ex=get_long_random_expire())
        return item


def select_item_like_name(name: str) -> List[Item]:
    """
    模糊查询物品名
    :param name: 名称
    :return: 物品
    """
    redis_ans = redis_db.get(redis_item_like_prefix + name)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_item.find({"name": {"$regex": name}, "is_delete": 0})
        item_list: List[Item] = []
        for item_result in result:
            item: Item = Item()
            dict_to_class(item_result, item)
            item.item_type = ItemType.get_type(str(item.item_type))
            item_list.append(item)
        redis_db.set(redis_item_like_prefix + name, serialization(item_list), ex=get_long_random_expire())
        return item_list


def insert_item(item: Item) -> str:
    """
    插入物品
    :param item: 物品
    :return: id
    """
    result = mongo_item.insert_one(class_to_dict(item))
    redis_db.delete(redis_item_prefix + str(result.inserted_id))
    return result.inserted_id


def select_system_data() -> SystemData:
    """
    获取系统数据
    :return: 系统数据
    """
    redis_ans = redis_db.get(redis_system_data_prefix)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_system.find_one({"is_delete": 0})
        system_data: SystemData = SystemData()
        dict_to_class(result, system_data)
        redis_db.set(redis_system_data_prefix, serialization(system_data), ex=get_long_random_expire())
        return system_data


def update_system_data(system_data: SystemData) -> int:
    """
    修改系统数据
    :param system_data: 系统数据
    :return: id
    """
    result = mongo_system.update_one({"_id": ObjectId(system_data.get_id()), "is_delete": 0},
                                     {"$set": class_to_dict(system_data)})
    redis_db.delete(redis_system_data_prefix)
    return result.modified_count


def insert_system_data(system_data: SystemData) -> str:
    """
    插入系统数据
    :param system_data: 系统数据
    :return: id
    """
    result = mongo_system.insert_one(class_to_dict(system_data))
    redis_db.delete(redis_system_data_prefix)
    return result.inserted_id


def select_weather_by_city_id(city_id: str, weather_time: datetime = datetime.now()):
    """
    获取天气
    :param city_id: 城市id
    :param weather_time: 日期
    :return: 结果
    """
    # 根据城市id和日期时间戳来获取
    redis_ans = redis_db.get(redis_weather_prefix + city_id + '_' + weather_time.strftime('%Y_%m_%d'))
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        today: datetime = datetime(weather_time.year, weather_time.month, weather_time.day)
        tomorrow: datetime = today + timedelta(days=1)
        result = mongo_weather.find_one(
            {"city_id": city_id, "create_time": {'$gte': today, '$lt': tomorrow}, "is_delete": 0})
        weather: Weather = Weather()
        dict_to_class(result, weather)
        redis_db.set(redis_weather_prefix + city_id + '_' + weather_time.strftime('%Y_%m_%d'), serialization(weather),
                     ex=get_long_random_expire())
        return weather


def insert_weather(weather: Weather) -> str:
    """
    插入天气
    :param weather: 天气
    :return: id
    """
    result = mongo_weather.insert_one(class_to_dict(weather))
    redis_db.delete(redis_weather_prefix + weather.city_id + '_' + weather.create_time.strftime('%Y_%m_%d'))
    return result.inserted_id


def select_valid_announcement() -> List[Announcement]:
    """
    查询所有有效的公告
    :return: 有效的公告列表
    """
    redis_ans = redis_db.get(redis_announcement_prefix)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        now: datetime = datetime.now()
        result = mongo_announcement.find(
            {"expire_time": {'$gte': now}, "is_delete": 0})
        
        announcement_list: List[Announcement] = []
        for announcement_result in result:
            announcement: Announcement = Announcement()
            dict_to_class(announcement_result, announcement)
            announcement_list.append(announcement)
        redis_db.set(redis_announcement_prefix, serialization(announcement_list), ex=global_config.week_second)
        return announcement_list


def update_announcement(announcement: Announcement) -> int:
    """
    更新公告
    :param announcement: 公告
    :return: id
    """
    result = mongo_announcement.update_one({"_id": ObjectId(announcement.get_id()), "is_delete": 0},
                                   {"$set": class_to_dict(announcement)})
    redis_db.delete(redis_announcement_prefix)
    return result.modified_count


def insert_announcement(announcement: Announcement) -> str:
    """
    插入公告
    :param announcement: 公告
    :return: id
    """
    result = mongo_announcement.insert_one(class_to_dict(announcement))
    redis_db.delete(redis_announcement_prefix)
    return result.inserted_id


####################################################################################################
# 上下文处理
def insert_context(qq: int, context) -> bool:
    """
    插入上下文
    :param qq:
    :param context:
    :return:
    """
    if not isinstance(context, BaseContext):
        return False
    redis_db.lpush(redis_user_context_prefix + str(qq), serialization(context))
    redis_db.expire(redis_user_context_prefix + str(qq), context_expire_time_seconds)
    return True


def remove_context(qq: int, context):
    """
    删除上下文
    :param qq: qq号
    :param context: 上下文
    :return: none
    """
    redis_db.lrem(redis_user_context_prefix + str(qq), 0, context)


def get_context(qq: int) -> Tuple[List, List]:
    """
    查询某个人的上下文
    :param qq: QQ号
    :return: 上下文列表
    """
    context_list = redis_db.lrange(redis_user_context_prefix + str(qq), 0, -1)
    ans = [deserialize(context) for context in context_list]
    return context_list, ans
