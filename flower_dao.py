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
mongo_mail = mongo_db['mail']  # 信件
mongo_achievement = mongo_db['achievement']  # 成就
mongo_buff = mongo_db['buff']  # buff

mongo_world_race = mongo_db['world_race']  # 种族
mongo_world_profession = mongo_db['world_profession']  # 职业
mongo_world_disease = mongo_db['world_disease']  # 疾病
mongo_world_terrain = mongo_db['world_terrain']  # 世界地形
mongo_world_area = mongo_db['world_area']  # 世界地区
mongo_kingdom = mongo_db['kingdom']  # 世界地区
mongo_relationship = mongo_db['relationship']  # 世界地区
mongo_person = mongo_db['person']  # npc
mongo_user_person = mongo_db['user_person']  # 玩家每天刷新的npc

mongo_sign_record = mongo_db['sign_record']  # 签到记录
mongo_user_statistics = mongo_db['user_statistics']  # 统计数据

mongo_person_last_name = mongo_db['person_last_name']  # npc姓氏
mongo_person_name = mongo_db['person_name']  # npc名

# Redis
redis_pool = ConnectionPool(host=global_config.redis_host, port=global_config.redis_port, db=global_config.redis_db,
                            password=global_config.redis_password, decode_responses=True)
redis_db = StrictRedis(connection_pool=redis_pool)

redis_global_prefix = 'flower_'  # redis全局前缀
redis_global_game_lock = redis_global_prefix + 'global_game_lock'  # 游戏锁前缀
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
redis_mail_prefix = redis_global_prefix + 'mail_'  # 信件redis前缀（信件id）
redis_mails_prefix = redis_global_prefix + 'mails'  # 正在投递中的mail
redis_buff_prefix = redis_global_prefix + 'buff_'  # BUFF
redis_achievement_prefix = redis_global_prefix + 'achievement_'  # 成就
redis_user_statistics = redis_global_prefix + 'user_statistics_'  # 统计数据

redis_world_race_prefix = redis_global_prefix + 'world_race_'  # 种族redis前缀
redis_world_profession_prefix = redis_global_prefix + 'world_profession_'  # 职业redis前缀
redis_world_disease_prefix = redis_global_prefix + 'world_disease_'  # 疾病redis前缀
redis_world_terrain_prefix = redis_global_prefix + 'world_terrain_'  # 世界地形redis前缀
redis_world_area_prefix = redis_global_prefix + 'world_area_'  # 世界地区redis前缀
redis_kingdom_prefix = redis_global_prefix + 'kingdom_'  # 国家redis前缀
redis_person_prefix = redis_global_prefix + 'person_'  # npc redis前缀
redis_relationship_prefix = redis_global_prefix + 'relationship_'  # 关系redis前缀
redis_all_person_prefix = redis_global_prefix + 'all_person_'  # npc redis前缀
redis_all_world_area = redis_global_prefix + 'all_world_area'  # 所有地区的redis前缀
redis_all_race = redis_global_prefix + 'all_race'  # 所有种族的redis前缀
redis_all_profession = redis_global_prefix + 'all_profession'  # 所有职业的redis前缀
redis_all_disease = redis_global_prefix + 'all_disease'  # 所有疾病的redis前缀
redis_all_kingdom = redis_global_prefix + 'all_kingdom'  # 所有帝国的redis前缀
redis_user_person_prefix = redis_global_prefix + 'user_person_'  # 用户-npc关系

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
        obj_dict = obj
    else:
        obj_dict = obj.__dict__
    for key in obj_dict:
        if key[0] == '_':
            continue
        elif isinstance(obj_dict[key], Enum):
            ans[key] = obj_dict[key].value
        elif isinstance(obj_dict[key], InnerClass):
            ans[key] = class_to_dict(obj_dict[key])
        elif isinstance(obj_dict[key], list):
            ans[key] = []
            if len(obj_dict[key]) > 0 and isinstance(obj_dict[key][0], InnerClass):
                for item in obj_dict[key]:
                    ans[key].append(class_to_dict(item))
            else:
                ans[key] = obj_dict[key]
        elif isinstance(obj_dict[key], dict):
            ans[key] = class_to_dict(obj_dict[key])
        else:
            ans[key] = obj_dict[key]
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
    elif d['class_type'] == 'DecorateBuff':
        return dict_to_class(d, DecorateBuff())
    elif d['class_type'] == 'DecorateAchievement':
        return dict_to_class(d, DecorateAchievement())
    elif d['class_type'] == 'DecorateHorse':
        return dict_to_class(d, DecorateHorse())
    elif d['class_type'] == 'DecorateDog':
        return dict_to_class(d, DecorateDog())
    elif d['class_type'] == 'DecorateCat':
        return dict_to_class(d, DecorateCat())
    elif d['class_type'] == 'Commodity':
        return dict_to_class(d, Commodity())
    elif d['class_type'] == 'PathModel':
        return dict_to_class(d, PathModel())
    elif d['class_type'] == 'Clothing':
        return dict_to_class(d, Clothing())
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
            # 如果是字典类型，需要判断其是否是一个子类类型
            if 'class_type' in d[key]:
                o.__dict__[key] = dict_to_inner_class(d[key])
            else:
                # 其value值可能是一个子类
                o.__dict__[key] = {}
                for dict_key in d[key]:
                    if isinstance(d[key][dict_key], dict) and 'class_type' in d[key][dict_key]:
                        o.__dict__[key][dict_key] = dict_to_inner_class(d[key][dict_key])
                    # 如果value是数组类型，那么需要检测其子类是否有嵌套内部类
                    elif isinstance(d[key][dict_key], list):
                        o.__dict__[key][dict_key] = []
                        if len(d[key][dict_key]) > 0:
                            if isinstance(d[key][dict_key][0], dict):
                                for item in d[key][dict_key]:
                                    inner_o = dict_to_inner_class(item)
                                    if inner_o is not None:
                                        o.__dict__[key][dict_key].append(inner_o)
                            else:
                                o.__dict__[key][dict_key] = d[key][dict_key]
                    else:
                        o.__dict__[key][dict_key] = d[key][dict_key]
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


def be_locked(key: str) -> bool:
    """
    是否有被锁定
    :param key: key
    :return:
    """
    return redis_db.get(key) is not None


def unlock(key: str) -> int:
    """
    解锁
    :param key: 字段名
    :return: 是否解锁成功
    """
    return redis_db.delete(key)


####################################################################################################
def put_user_rank(user: User):
    put_gold_rank(user.qq, user.gold)
    put_exp_rank(user.qq, user.exp)


def put_gold_rank(qq: int, gold: int):
    """
    更新金币排行榜
    """
    mapping: Dict[str, int] = {str(qq): gold}
    redis_db.zadd(redis_user_gold_rank, mapping)


def get_gold_rank(qq: int) -> int:
    """
    获取某个人的金币排行
    """
    return redis_db.zrevrank(redis_user_gold_rank, str(qq))


def get_total_gold_rank() -> List[Tuple[str, float]]:
    """
    获取某个人的金币排行
    """
    return redis_db.zrevrange(redis_user_gold_rank, 0, 9, withscores=True)


def put_exp_rank(qq: int, exp: int):
    """
    更新经验排行榜
    """
    mapping: Dict[str, int] = {str(qq): exp}
    redis_db.zadd(redis_user_exp_rank, mapping)


def get_exp_rank(qq: int) -> int:
    """
    获取某个人的经验排行
    """
    return redis_db.zrevrank(redis_user_exp_rank, str(qq))


def get_total_exp_rank() -> List[Tuple[str, float]]:
    """
    获取某个人的金币排行
    """
    return redis_db.zrevrange(redis_user_exp_rank, 0, 9, withscores=True)


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
    return str(result.inserted_id)


def select_all_flower_number() -> int:
    """
    获取花的数量
    :return:
    """
    number = mongo_flower.count_documents({"is_delete": 0})
    return int(number)


def select_random_flower(level_list: List[FlowerLevel]) -> Flower:
    """
    随机获取一种花
    :return:
    """
    if level_list is None or len(level_list) == 0:
        number: int = select_all_flower_number()
        index: int = random.randint(0, number - 1)
        result = mongo_flower.find({"is_delete": 0}).skip(index).limit(1)
    else:
        level: FlowerLevel = random.choice(level_list)
        if level == FlowerLevel.S:
            level: str = 'S'
        if level == FlowerLevel.A:
            level: str = 'A'
        if level == FlowerLevel.B:
            level: str = 'B'
        if level == FlowerLevel.C:
            level: str = 'C'
        else:
            level: str = 'D'
        number: int = mongo_flower.count_documents({"is_delete": 0, "level": level})
        index: int = random.randint(0, number - 1)
        result = mongo_flower.find({"is_delete": 0, "level": level}).skip(index).limit(1)
    for flower_result in result:
        flower: Flower = Flower()
        dict_to_class(flower_result, flower)
        return flower
    return Flower()


def select_flower_by_id(_id: str) -> Flower:
    """
    根据id获取花卉
    :param _id: id
    :return: 花卉
    """
    if not ObjectId.is_valid(_id):
        return Flower()
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
        user.gender = Gender.get(user.gender)
        redis_db.set(redis_user_prefix + str(qq), serialization(user), ex=get_random_expire())
        return user


def select_all_user_number() -> int:
    """
    获取用户的数量
    :return:
    """
    number = mongo_user.count_documents({"is_delete": 0})
    return int(number)


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
        user.gender = Gender.get(user.gender)
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
        user.gender = Gender.get(user.gender)
        redis_db.set(redis_username_prefix + str(username), serialization(user), ex=get_random_expire())
        return user


def update_user_by_qq(user: User) -> int:
    """
    根据qq更新用户
    :param user: 用户
    :return: 更新结果
    """
    result = mongo_user.update_one({"qq": user.qq, "is_delete": 0}, {"$set": class_to_dict(user)})
    put_user_rank(user)
    redis_db.set(redis_user_prefix + str(user.qq), serialization(user), ex=get_random_expire())
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
    return str(result.inserted_id)


def select_user_statistics_by_qq(qq: int) -> UserStatistics:
    """
    查询统计数据
    """
    redis_ans = redis_db.get(redis_user_statistics + str(qq))
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_user_statistics.find_one({"qq": qq, "is_delete": 0})
        user_statistics: UserStatistics = UserStatistics()
        dict_to_class(result, user_statistics)
        redis_db.set(redis_user_statistics + str(qq), serialization(user_statistics), ex=get_random_expire())
        return user_statistics


def update_user_statistics(user_statistics: UserStatistics) -> int:
    """
    插入统计信息
    """
    result = mongo_user_statistics.update_one({"qq": user_statistics.qq, "is_delete": 0},
                                              {"$set": class_to_dict(user_statistics)})
    redis_db.delete(redis_user_statistics + str(user_statistics.qq))
    return result.modified_count


def insert_user_statistics(user_statistics: UserStatistics) -> str:
    """
    插入统计信息
    """
    result = mongo_user_statistics.insert_one(class_to_dict(user_statistics))
    redis_db.delete(redis_user_statistics + str(user_statistics.qq))
    return str(result.inserted_id)


def insert_sign_record(sign_record: SignRecord) -> str:
    """
    插入签到数据
    :param sign_record: 签到数据
    :return: id
    """
    result = mongo_sign_record.insert_one(class_to_dict(sign_record))
    return str(result.inserted_id)


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
    return str(result.inserted_id)


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
    return str(result.inserted_id)


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
    return str(result.inserted_id)


def select_valid_announcement() -> List[Announcement]:
    """
    查询所有有效的公告
    :return: 有效的公告列表
    """
    redis_ans = redis_db.get(redis_announcement_prefix)
    if redis_ans is not None:
        announcement_list: List[Announcement] = deserialize(redis_ans)
        announcement_list = [announcement for announcement in announcement_list if not announcement.is_expire()]
        redis_db.set(redis_announcement_prefix, serialization(announcement_list), ex=global_config.week_second)
        return announcement_list
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
    return str(result.inserted_id)


def select_mail_by_id(_id: str) -> Mail:
    """
    根据id获取信件
    :param _id: id
    :return: 信件
    """
    redis_ans = redis_db.get(redis_mail_prefix + _id)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_mail.find_one({"_id": ObjectId(_id)})
        mail: Mail = Mail()
        dict_to_class(result, mail)
        redis_db.set(redis_mail_prefix + _id, serialization(mail), ex=get_long_random_expire())
        return mail


def select_mail_not_arrived() -> List[Mail]:
    """
    获取没有到达的信件
    :return:
    """
    redis_ans = redis_db.get(redis_mails_prefix)
    if redis_ans is not None:
        mail_list: List[Mail] = deserialize(redis_ans)
        mail_list = [mail for mail in mail_list if not mail.arrived]
        redis_db.set(redis_mails_prefix, serialization(mail_list), ex=global_config.day_second)
        return mail_list
    else:
        result = mongo_announcement.find({"arrived": False, "is_delete": 0})
        mail_list: List[Mail] = []
        for mail_result in result:
            mail: Mail = Mail()
            dict_to_class(mail_result, mail)
            mail_list.append(mail)
        redis_db.set(redis_mails_prefix, serialization(mail_list), ex=global_config.day_second)
        return mail_list


def update_mail(mail: Mail) -> int:
    """
    修改信件
    :param mail: 信件
    :return: 修改的数量
    """
    result = mongo_mail.update_one({"_id": ObjectId(mail.get_id())}, {"$set": class_to_dict(mail)})
    redis_db.set(redis_mail_prefix + mail.get_id(), serialization(mail), ex=get_long_random_expire())
    redis_db.delete(redis_mails_prefix)
    return result.modified_count


def insert_mail(mail: Mail) -> str:
    """
    插入信件
    :param mail: 信件
    :return: id
    """
    result = mongo_mail.insert_one(class_to_dict(mail))
    redis_db.delete(redis_mail_prefix + str(result.inserted_id))
    redis_db.delete(redis_mails_prefix)
    return str(result.inserted_id)


####################################################################################################
# 世界模型

def select_all_disease() -> List[Disease]:
    """
    查询所有疾病
    :return: 疾病的数组
    """
    redis_ans = redis_db.get(redis_all_disease)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_world_disease.find({"is_delete": 0})
        disease_list: List[Disease] = []
        for disease_result in result:
            disease: Disease = Disease()
            dict_to_class(disease_result, disease)
            disease_list.append(disease)
        redis_db.set(redis_all_disease, serialization(disease_list),
                     ex=get_long_random_expire())
        return disease_list


def select_disease(_id: str) -> Disease:
    """
    根据id查询职业
    :param _id: id
    :return: 职业
    """
    redis_ans = redis_db.get(redis_world_disease_prefix + _id)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_world_disease.find_one({"_id": ObjectId(_id)})
        disease: Disease = Disease()
        dict_to_class(result, disease)
        redis_db.set(redis_world_disease_prefix + _id, serialization(disease), ex=get_long_random_expire())
        return disease


def select_disease_by_name(name: str) -> Disease:
    """
    根据名字查询疾病
    :param name: 疾病
    :return:
    """
    redis_ans = redis_db.get(redis_world_disease_prefix + name)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_world_disease.find_one({"name": name})
        disease: Disease = Disease()
        dict_to_class(result, disease)
        redis_db.set(redis_world_disease_prefix + name, serialization(disease), ex=get_long_random_expire())
        return disease


def insert_disease(disease: Disease) -> str:
    """
    插入职业
    :param disease: 疾病
    :return: id
    """
    result = mongo_world_disease.insert_one(class_to_dict(disease))
    redis_db.delete(redis_world_disease_prefix + str(result.inserted_id))
    redis_db.delete(redis_world_disease_prefix + disease.name)
    redis_db.delete(redis_all_disease)
    return str(result.inserted_id)


def select_all_profession() -> List[Profession]:
    """
    查询所有职业
    :return: 职业的数组
    """
    redis_ans = redis_db.get(redis_all_profession)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_world_profession.find({"is_delete": 0})
        profession_list: List[Profession] = []
        for profession_result in result:
            profession: Profession = Profession()
            dict_to_class(profession_result, profession)
            profession_list.append(profession)
        redis_db.set(redis_all_profession, serialization(profession_list),
                     ex=get_long_random_expire())
        return profession_list


def select_profession(_id: str) -> Profession:
    """
    根据id查询职业
    :param _id: id
    :return: 职业
    """
    redis_ans = redis_db.get(redis_world_profession_prefix + _id)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_world_profession.find_one({"_id": ObjectId(_id)})
        profession: Profession = Profession()
        dict_to_class(result, profession)
        redis_db.set(redis_world_profession_prefix + _id, serialization(profession), ex=get_long_random_expire())
        return profession


def select_profession_by_name(name: str) -> Profession:
    """
    根据名字查询职业
    :param name: 职业
    :return:
    """
    redis_ans = redis_db.get(redis_world_profession_prefix + name)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_world_profession.find_one({"name": name})
        profession: Profession = Profession()
        dict_to_class(result, profession)
        redis_db.set(redis_world_profession_prefix + name, serialization(profession), ex=get_long_random_expire())
        return profession


def insert_profession(profession: Profession) -> str:
    """
    插入职业
    :param profession: 职业
    :return: id
    """
    result = mongo_world_profession.insert_one(class_to_dict(profession))
    redis_db.delete(redis_world_profession_prefix + str(result.inserted_id))
    redis_db.delete(redis_world_profession_prefix + profession.name)
    redis_db.delete(redis_all_profession)
    return str(result.inserted_id)


def select_all_world_race() -> List[Race]:
    """
    查询所有种族
    :return: 种族 的 数组
    """
    redis_ans = redis_db.get(redis_all_race)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_world_race.find({"is_delete": 0})
        race_list: List[Race] = []
        for race_result in result:
            race: Race = Race()
            dict_to_class(race_result, race)
            race_list.append(race)
        redis_db.set(redis_all_race, serialization(race_list),
                     ex=get_long_random_expire())
        return race_list


def select_world_race(_id: str) -> Race:
    """
    根据id查询世界地形
    :param _id: id
    :return: 世界地形
    """
    redis_ans = redis_db.get(redis_world_race_prefix + _id)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_world_race.find_one({"_id": ObjectId(_id)})
        race: Race = Race()
        dict_to_class(result, race)
        redis_db.set(redis_world_race_prefix + _id, serialization(race), ex=get_long_random_expire())
        return race


def select_world_race_by_name(name: str) -> Race:
    """
    根据名字查询种族
    :param name: 种族名
    :return:
    """
    redis_ans = redis_db.get(redis_world_terrain_prefix + name)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_world_race.find_one({"name": name})
        race: Race = Race()
        dict_to_class(result, race)
        redis_db.set(redis_world_race_prefix + name, serialization(race), ex=get_long_random_expire())
        return race


def insert_world_race(world_race: Race) -> str:
    """
    插入地形
    :param world_race: 种族
    :return: id
    """
    result = mongo_world_race.insert_one(class_to_dict(world_race))
    redis_db.delete(redis_world_race_prefix + str(result.inserted_id))
    redis_db.delete(redis_world_race_prefix + world_race.name)
    redis_db.delete(redis_all_race)
    return str(result.inserted_id)


def select_world_terrain(_id: str) -> WorldTerrain:
    """
    根据id查询世界地形
    :param _id: id
    :return: 世界地形
    """
    redis_ans = redis_db.get(redis_world_terrain_prefix + _id)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_world_terrain.find_one({"_id": ObjectId(_id)})
        world_terrain: WorldTerrain = WorldTerrain()
        dict_to_class(result, world_terrain)
        redis_db.set(redis_world_terrain_prefix + _id, serialization(world_terrain), ex=get_long_random_expire())
        return world_terrain


def select_world_terrain_by_name(name: str) -> WorldTerrain:
    """
    根据id查询世界地形
    :param name: 地形名
    :return: 世界地形
    """
    redis_ans = redis_db.get(redis_world_terrain_prefix + name)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_world_terrain.find_one({"name": name})
        world_terrain: WorldTerrain = WorldTerrain()
        dict_to_class(result, world_terrain)
        redis_db.set(redis_world_terrain_prefix + name, serialization(world_terrain), ex=get_long_random_expire())
        return world_terrain


def insert_world_terrain(world_terrain: WorldTerrain) -> str:
    """
    插入地形
    :param world_terrain: 世界地形
    :return: id
    """
    result = mongo_world_terrain.insert_one(class_to_dict(world_terrain))
    redis_db.delete(redis_world_terrain_prefix + str(result.inserted_id))
    redis_db.delete(redis_world_terrain_prefix + world_terrain.name)
    return str(result.inserted_id)


def select_world_area(_id: str) -> WorldArea:
    """
    根据id查询世界地区
    :param _id: id
    :return: 世界地区
    """
    redis_ans = redis_db.get(redis_world_area_prefix + _id)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_world_area.find_one({"_id": ObjectId(_id)})
        world_area: WorldArea = WorldArea()
        dict_to_class(result, world_area)
        redis_db.set(redis_world_area_prefix + _id, serialization(world_area), ex=get_long_random_expire())
        return world_area


def select_all_world_area() -> List[WorldArea]:
    """
    查询所有地区
    :return: 世界地区 的 数组
    """
    redis_ans = redis_db.get(redis_all_world_area)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_world_area.find({"is_delete": 0})
        world_area_list: List[WorldArea] = []
        for world_area_result in result:
            world_area: WorldArea = WorldArea()
            dict_to_class(world_area_result, world_area)
            world_area_list.append(world_area)
        redis_db.set(redis_all_world_area, serialization(world_area_list),
                     ex=get_long_random_expire())
        return world_area_list


def select_world_area_by_name(name: str) -> WorldArea:
    """
    根据名字查询世界地区
    :param name: 地区名
    :return: 世界地区
    """
    redis_ans = redis_db.get(redis_world_area_prefix + name)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_world_area.find_one({"name": name})
        world_area: WorldArea = WorldArea()
        dict_to_class(result, world_area)
        redis_db.set(redis_world_area_prefix + name, serialization(world_area), ex=get_long_random_expire())
        return world_area


def insert_world_area(world_area: WorldArea) -> str:
    """
    插入地形
    :param world_area: 世界地区
    :return: id
    """
    result = mongo_world_area.insert_one(class_to_dict(world_area))
    redis_db.delete(redis_world_area_prefix + str(result.inserted_id))
    redis_db.delete(redis_all_world_area)
    return str(result.inserted_id)


def select_all_kingdom() -> List[Kingdom]:
    """
    查询所有种族
    :return: 种族 的 数组
    """
    redis_ans = redis_db.get(redis_all_kingdom)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_kingdom.find({"is_delete": 0})
        kingdom_list: List[Kingdom] = []
        for kingdom_result in result:
            kingdom: Kingdom = Kingdom()
            dict_to_class(kingdom_result, kingdom)
            kingdom_list.append(kingdom)
        redis_db.set(redis_all_kingdom, serialization(kingdom_list),
                     ex=get_long_random_expire())
        return kingdom_list


def select_kingdom(_id: str) -> Kingdom:
    """
    根据id查询帝国
    :param _id: id
    :return: 帝国
    """
    redis_ans = redis_db.get(redis_kingdom_prefix + _id)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_kingdom.find_one({"_id": ObjectId(_id)})
        kingdom: Kingdom = Kingdom()
        dict_to_class(result, kingdom)
        redis_db.set(redis_kingdom_prefix + _id, serialization(kingdom), ex=get_long_random_expire())
        return kingdom


def select_kingdom_by_name(name: str) -> Kingdom:
    """
    根据名字查询帝国
    :param name: 帝国名
    :return: 帝国
    """
    redis_ans = redis_db.get(redis_kingdom_prefix + name)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_kingdom.find_one({"name": name})
        kingdom: Kingdom = Kingdom()
        dict_to_class(result, kingdom)
        redis_db.set(redis_kingdom_prefix + name, serialization(kingdom), ex=get_long_random_expire())
        return kingdom


def update_kingdom(kingdom: Kingdom) -> int:
    """
    更新帝国
    :param kingdom: 国家
    :return: id
    """
    result = mongo_kingdom.update_one({"_id": ObjectId(kingdom.get_id())}, {"$set": class_to_dict(kingdom)})
    redis_db.delete(redis_kingdom_prefix + kingdom.get_id())
    redis_db.delete(redis_all_kingdom)
    return result.modified_count


def insert_kingdom(kingdom: Kingdom) -> str:
    """
    插入帝国
    :param kingdom: 国家
    :return: id
    """
    result = mongo_kingdom.insert_one(class_to_dict(kingdom))
    redis_db.delete(redis_kingdom_prefix + str(result.inserted_id))
    redis_db.delete(redis_all_kingdom)
    return str(result.inserted_id)


def select_relationship(_id: str) -> Relationship:
    """
    根据id查询关系
    :param _id: id
    :return: 关系
    """
    redis_ans = redis_db.get(redis_relationship_prefix + _id)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_relationship.find_one({"_id": ObjectId(_id)})
        relationship: Relationship = Relationship()
        dict_to_class(result, relationship)
        redis_db.set(redis_relationship_prefix + _id, serialization(relationship), ex=get_random_expire())
        return relationship


def select_relationship_by_pair(src_person: str, dst_person: str) -> Relationship:
    """
    根据人物查询关系
    :param src_person: 人物1
    :param dst_person: 人物2
    :return: 关系
    """
    redis_ans = redis_db.get(redis_relationship_prefix + src_person + '_' + dst_person)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_relationship.find_one({"src_person": src_person, 'dst_person': dst_person})
        relationship: Relationship = Relationship()
        dict_to_class(result, relationship)
        redis_db.set(redis_relationship_prefix + src_person + '_' + dst_person, serialization(relationship),
                     ex=get_random_expire())
        return relationship


def update_relationship(relationship: Relationship) -> int:
    """
    更新关系
    :param relationship: 关系
    :return: id
    """
    result = mongo_relationship.update_one({"_id": ObjectId(relationship.get_id())},
                                           {"$set": class_to_dict(relationship)})
    redis_db.delete(redis_relationship_prefix + relationship.get_id())
    redis_db.delete(redis_relationship_prefix + relationship.src_person + '_' + relationship.dst_person)
    return result.modified_count


def insert_relationship(relationship: Relationship) -> str:
    """
    插入关系
    :param relationship: 关系
    :return: id
    """
    result = mongo_relationship.insert_one(class_to_dict(relationship))
    redis_db.delete(redis_relationship_prefix + str(result.inserted_id))
    redis_db.delete(redis_relationship_prefix + relationship.src_person + '_' + relationship.dst_person)
    return str(result.inserted_id)


def select_all_person_number() -> int:
    number: int = mongo_person.count_documents({"is_delete": 0})
    return number


def select_all_alive_person_number() -> int:
    number: int = mongo_person.count_documents({"is_delete": 0, "die": False})
    return number


def select_age_range_person_number(min_age: int, max_age: int) -> int:
    """
    查询一个年龄区间有多少人
    :param min_age: 最小年龄
    :param max_age: 最大年龄
    :return:
    """
    now: datetime = datetime.now()
    min_born_time = now - timedelta(days=max_age)
    max_born_time = now - timedelta(days=min_age)
    number: int = mongo_person.count_documents(
        {"is_delete": 0, "die": False, "born_time": {'$gte': min_born_time, '$lt': max_born_time}})
    return number


def select_all_profession_person_number(profession_id: str) -> int:
    number: int = mongo_person.count_documents({"is_delete": 0, "profession_id": profession_id, "die": False})
    return number


def select_all_person(page: int, page_size: int = 30) -> List[Person]:
    """
    查询所有npc
    :param page: 页码
    :param page_size: 页面大小
    :return: npc 的 id数组
    """
    redis_ans = redis_db.get(redis_all_person_prefix + '%d_%d' % (page, page_size))
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_person.find({"is_delete": 0}).limit(page_size).skip(page * page_size)
        person_list: List[Person] = []
        for person_result in result:
            person: Person = Person()
            dict_to_class(person_result, person)
            person_list.append(person)
        redis_db.set(redis_all_person_prefix + '%d_%d' % (page, page_size), serialization(person_list),
                     ex=get_long_random_expire())
        return person_list


def select_random_person_by_profession(profession_id: str) -> Person:
    """
    随机选择一位某职业人
    :param profession_id:
    :return:
    """
    number: int = select_all_profession_person_number(profession_id)
    index: int = random.randint(0, number - 1)
    result = mongo_person.find({"is_delete": 0, "profession_id": profession_id, "die": False}).skip(index).limit(1)
    for person_result in result:
        person: Person = Person()
        dict_to_class(person_result, person)
        return person
    return Person()


def select_person(_id: str) -> Person:
    """
    根据id查询npc
    :param _id: id
    :return: npc
    """
    redis_ans = redis_db.get(redis_person_prefix + _id)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_person.find_one({"_id": ObjectId(_id)})
        person: Person = Person()
        dict_to_class(result, person)
        person.gender = Gender.get(person.gender)
        redis_db.set(redis_person_prefix + _id, serialization(person), ex=get_long_random_expire())
        return person


def update_person(person: Person) -> int:
    """
    更新npc
    :param person: npc
    :return: id
    """
    result = mongo_person.update_one({"_id": ObjectId(person.get_id())}, {"$set": class_to_dict(person)})
    redis_db.delete(redis_person_prefix + person.get_id())
    return result.modified_count


def insert_person(person: Person) -> str:
    """
    插入npc
    :param person: npc
    :return: id
    """
    result = mongo_person.insert_one(class_to_dict(person))
    redis_db.delete(redis_person_prefix + str(result.inserted_id))
    return str(result.inserted_id)


def select_user_person(_id: str) -> UserPerson:
    """
    根据id查询用户-npc关系
    :param _id: id
    :return: user_person
    """
    redis_ans = redis_db.get(redis_user_person_prefix + _id)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_user_person.find_one({"_id": ObjectId(_id)})
        user_person: UserPerson = UserPerson()
        dict_to_class(result, user_person)
        redis_db.set(redis_user_person_prefix + _id, serialization(user_person), ex=get_random_expire())
        return user_person


def select_user_person_by_qq(qq: int, select_time: datetime = datetime.now()) -> List[UserPerson]:
    """
    查询用户-npc关联关系
    """
    redis_ans = redis_db.get(redis_user_person_prefix + str(qq) + '_' + select_time.strftime('%Y_%m_%d'))
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        today: datetime = datetime(select_time.year, select_time.month, select_time.day)
        tomorrow: datetime = today + timedelta(days=1)
        result = mongo_user_person.find(
            {"qq": qq, "create_time": {'$gte': today, '$lt': tomorrow}, "is_delete": 0}).sort([('create_time', 1)])
        user_person_list: List[UserPerson] = []
        for user_person_result in result:
            user_person: UserPerson = UserPerson()
            dict_to_class(user_person_result, user_person)
            user_person_list.append(user_person)
        redis_db.set(redis_user_person_prefix + str(qq) + '_' + select_time.strftime('%Y_%m_%d'),
                     serialization(user_person_list), ex=global_config.day_second)
        return user_person_list


def update_user_person(user_person: UserPerson) -> int:
    """
    更新玩家-npc关联
    :param user_person: npc
    :return:
    """
    result = mongo_user_person.update_one({"_id": ObjectId(user_person.get_id())}, {"$set": class_to_dict(user_person)})
    redis_db.delete(redis_user_person_prefix + str(user_person.qq) + '_' + user_person.create_time.strftime('%Y_%m_%d'))
    redis_db.delete(redis_user_person_prefix + user_person.get_id())
    return result.modified_count


def insert_user_person(user_person: UserPerson) -> str:
    """
    插入玩家-npc关联
    :param user_person: npc
    :return: id
    """
    now: datetime = datetime.now()
    result = mongo_user_person.insert_one(class_to_dict(user_person))
    redis_db.delete(redis_user_person_prefix + str(user_person.qq) + '_' + now.strftime('%Y_%m_%d'))
    return str(result.inserted_id)


def select_buff(_id: str) -> Buff:
    """
    根据id查询buff
    :param _id: id
    :return: buff
    """
    redis_ans = redis_db.get(redis_buff_prefix + _id)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_buff.find_one({"_id": ObjectId(_id)})
        buff: Buff = Buff()
        dict_to_class(result, buff)
        redis_db.set(redis_buff_prefix + _id, serialization(buff), ex=get_long_random_expire())
        return buff


def select_buff_by_name(name: str) -> Buff:
    """
    根据name查询buff
    :param name: name
    :return: buff
    """
    redis_ans = redis_db.get(redis_buff_prefix + name)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_buff.find_one({"name": name})
        buff: Buff = Buff()
        dict_to_class(result, buff)
        redis_db.set(redis_buff_prefix + name, serialization(buff), ex=get_long_random_expire())
        return buff


def insert_buff(buff: Buff) -> str:
    """
    插入buff
    :param buff: buff
    :return: id
    """
    result = mongo_buff.insert_one(class_to_dict(buff))
    redis_db.delete(redis_buff_prefix + str(result.inserted_id))
    return str(result.inserted_id)


def select_achievement(_id: str) -> Achievement:
    """
    根据id查询成就
    :param _id: id
    :return: 成就
    """
    redis_ans = redis_db.get(redis_achievement_prefix + _id)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_achievement.find_one({"_id": ObjectId(_id)})
        achievement: Achievement = Achievement()
        dict_to_class(result, achievement)
        redis_db.set(redis_achievement_prefix + _id, serialization(achievement), ex=get_long_random_expire())
        return achievement


def select_achievement_by_name(name: str) -> Achievement:
    """
    根据name查询成就
    :param name: name
    :return: 成就
    """
    redis_ans = redis_db.get(redis_achievement_prefix + name)
    if redis_ans is not None:
        return deserialize(redis_ans)
    else:
        result = mongo_achievement.find_one({"name": name})
        achievement: Achievement = Achievement()
        dict_to_class(result, achievement)
        redis_db.set(redis_achievement_prefix + name, serialization(achievement), ex=get_long_random_expire())
        return achievement


def insert_achievement(achievement: Achievement) -> str:
    """
    插入成就
    :param achievement: 成就
    :return: id
    """
    result = mongo_achievement.insert_one(class_to_dict(achievement))
    redis_db.delete(redis_achievement_prefix + str(result.inserted_id))
    return str(result.inserted_id)


####################################################################################################
# 姓氏与名字（底层支持）

def select_all_person_last_name() -> List[PersonLastName]:
    """
    查询所有姓氏，访问量很小，没必要加缓存
    :return:
    """
    result = mongo_person_last_name.find(class_to_dict({"is_delete": 0}))
    person_last_name_list: List[PersonLastName] = []
    for single_result in result:
        person_last_name: PersonLastName = PersonLastName()
        dict_to_class(single_result, person_last_name)
        person_last_name_list.append(person_last_name)
    return person_last_name_list


def insert_person_last_name(person_last_name: PersonLastName) -> str:
    """
    插入姓氏
    :param person_last_name: 姓氏
    :return: id
    """
    result = mongo_person_last_name.insert_one(class_to_dict(person_last_name))
    return str(result.inserted_id)


def select_random_person_name(gender: Gender) -> PersonName:
    """
    随机抽取姓名（访问量比较低）
    :param gender: 性别
    :return:
    """
    if gender == Gender.female:
        gender_value = 1
    else:
        gender_value = 0
    number: int = mongo_person_name.count_documents({"is_delete": 0, "gender": gender_value})
    index: int = random.randint(0, number - 1)
    result = mongo_person_name.find({"is_delete": 0, "gender": gender_value}).skip(index).limit(1)
    for person_name_result in result:
        person_name: PersonName = PersonName()
        dict_to_class(person_name_result, person_name)
        person_name.gender = Gender.get(person_name.gender)
        return person_name
    return PersonName()


def insert_person_name(person_name: PersonName) -> str:
    """
    插入名
    :param person_name: 名
    :return: id
    """
    result = mongo_person_name.insert_one(class_to_dict(person_name))
    return str(result.inserted_id)


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
