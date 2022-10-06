# coding=utf-8

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Tuple

from model.base_model import *

__all__ = [
    "Region", "Terrain", "Climate", "Soil", "City", "Conditions", "Condition", "ConditionLevel",
    "FlowerLevel", "Flower", "FlowerGroup", "Weather", "ItemType", "FlowerQuality", "Item", "DecorateItem",
    "WareHouse", "Horse", "DecorateHorse", "Dog", "DecorateDog", "Cat", "DecorateCat", "FlowerState",
    "Farm", "SignRecord", "Mail", "MailBox", "Buff", "DecorateBuff", "Achievement", "DecorateAchievement",
    "User", "SystemData", "Announcement", "Commodity", "UserPerson", "Clothing", "UserStatistics"
]


class Region(EntityClass):
    """
    地区（沿海、内陆、近陆、岛）
    """
    
    def __init__(self, name: str = '', create_time: datetime = datetime.now(), create_id: str = '0',
                 update_time: datetime = datetime.now(), update_id: str = '0', is_delete: int = 0,
                 _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
        self.name = name


class Terrain(EntityClass):
    """
    地形（平原、高原等）
    """
    
    def __init__(self, name: str = '',
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
        self.name = name


class Climate(EntityClass):
    """
    气候
    """
    
    def __init__(self, name: str = '',
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
        self.name = name
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.__str__()


class Soil(EntityClass):
    """
    土壤
    """
    
    def __init__(self, name: str = '',
                 min_humidity: int = 0, max_humidity: int = 0,
                 min_change_humidity: int = 0, min_change_humidity_soil_id: List[str] = None,
                 max_change_humidity: int = 0, max_change_humidity_soil_id: List[str] = None,
                 min_nutrition: int = 0, max_nutrition: int = 0,
                 min_change_nutrition: int = 0, min_change_nutrition_soil_id: List[str] = None,
                 max_change_nutrition: int = 0, max_change_nutrition_soil_id: List[str] = None,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
        self.name = name
        
        self.min_humidity = min_humidity  # 湿度下限
        self.max_humidity = max_humidity  # 湿度上限
        self.min_change_humidity = min_change_humidity  # 湿度转变下限（高于此值一定时间会导致土壤转变）
        if min_change_humidity_soil_id is None:
            min_change_humidity_soil_id = []
        self.min_change_humidity_soil_id = min_change_humidity_soil_id  # 湿度转变下限对应的土壤
        self.max_change_humidity = max_change_humidity  # 湿度转变上限
        if max_change_humidity_soil_id is None:
            max_change_humidity_soil_id = []
        self.max_change_humidity_soil_id = max_change_humidity_soil_id  # 湿度转变上限对应的土壤
        self.min_nutrition = min_nutrition  # 营养下限
        self.max_nutrition = max_nutrition  # 营养上限
        self.min_change_nutrition = min_change_nutrition  # 营养转变下限
        if min_change_nutrition_soil_id is None:
            min_change_nutrition_soil_id = []
        self.min_change_nutrition_soil_id = min_change_nutrition_soil_id  # 营养转变下限对应的土壤
        self.max_change_nutrition = max_change_nutrition  # 营养转变上限
        if max_change_nutrition_soil_id is None:
            max_change_nutrition_soil_id = []
        self.max_change_nutrition_soil_id = max_change_nutrition_soil_id  # 营养转变上限对应的土壤


class City(EntityClass):
    """
    地点类
    """
    
    def __init__(self, city_name: str = '', father_id: str = '', region_id: str = '', terrain_id: str = '',
                 description: str = '', climate_id: str = '', soil_id: str = '',
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
        self.city_name = city_name
        self.father_id = father_id  # 父地点，只有子地点才拥有下面的属性
        self.description = description  # 描述
        
        # 地区属性
        self.region_id = region_id  # 地区
        self.terrain_id = terrain_id  # 地形
        self.climate_id = climate_id  # 气候
        self.soil_id = soil_id  # 土壤
    
    def __str__(self):
        return self.city_name
    
    def __repr__(self):
        return self.__str__()


class Condition(InnerClass):
    """
    条件
    """
    
    def __init__(self, min_humidity: int = 0, max_humidity: int = 0, min_nutrition: int = 0, max_nutrition: int = 0,
                 min_temperature: int = 0, max_temperature: int = 0
                 ):
        super().__init__('Condition')
        self.min_humidity = min_humidity
        self.max_humidity = max_humidity
        self.min_nutrition = min_nutrition
        self.max_nutrition = max_nutrition
        self.min_temperature = min_temperature
        self.max_temperature = max_temperature


class ConditionLevel(Enum):
    """
    条件级别
    """
    BAD = 0
    NORMAL = 1
    SUITABLE = 2
    PERFECT = 3


class Conditions(InnerClass):
    """
    一组条件
    """
    
    def __init__(self, normal_condition: Condition = None, suitable_condition: Condition = None,
                 perfect_condition: Condition = None):
        super().__init__('Conditions')
        if isinstance(normal_condition, dict):
            normal_condition = Condition(**normal_condition)
        elif normal_condition is None:
            normal_condition = Condition()
        self.normal_condition = normal_condition  # 普通条件
        if isinstance(suitable_condition, dict):
            suitable_condition = Condition(**suitable_condition)
        elif suitable_condition is None:
            suitable_condition = Condition()
        self.suitable_condition = suitable_condition  # 适宜条件
        if isinstance(perfect_condition, dict):
            perfect_condition = Condition(**perfect_condition)
        elif perfect_condition is None:
            perfect_condition = Condition()
        self.perfect_condition = perfect_condition  # 完美条件
    
    def get_condition_level(self, temperature: float = 0.0, humidity: float = 0.0,
                            nutrition: float = 0.0) -> ConditionLevel:
        """
        获取条件级别
        :param temperature: 温度
        :param humidity: 湿度
        :param nutrition: 营养
        :return: 级别
        """
        if self.perfect_condition.min_humidity <= humidity <= self.perfect_condition.max_humidity and \
                self.perfect_condition.min_nutrition <= nutrition <= self.perfect_condition.max_nutrition and \
                self.perfect_condition.min_temperature <= temperature <= self.perfect_condition.max_temperature:
            return ConditionLevel.PERFECT
        elif self.suitable_condition.min_humidity <= humidity <= self.suitable_condition.max_humidity and \
                self.suitable_condition.min_nutrition <= nutrition <= self.suitable_condition.max_nutrition and \
                self.suitable_condition.min_temperature <= temperature <= self.suitable_condition.max_temperature:
            return ConditionLevel.SUITABLE
        elif self.normal_condition.min_humidity <= humidity <= self.normal_condition.max_humidity and \
                self.normal_condition.min_nutrition <= nutrition <= self.normal_condition.max_nutrition and \
                self.normal_condition.min_temperature <= temperature <= self.normal_condition.max_temperature:
            return ConditionLevel.NORMAL
        return ConditionLevel.BAD


class FlowerLevel(Enum):
    """
    花的等级
    """
    S = 'S'
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'
    
    @classmethod
    def view_level(cls, level) -> str:
        if level == cls.S:
            return 'S'
        elif level == cls.A:
            return 'A'
        elif level == cls.B:
            return 'B'
        elif level == cls.C:
            return 'C'
        return 'D'
    
    @classmethod
    def get_level(cls, level: str):
        if not level.startswith('FlowerLevel.'):
            level = 'FlowerLevel.' + level
        if level == str(cls.S):
            return cls.S
        elif level == str(cls.A):
            return cls.A
        elif level == str(cls.B):
            return cls.B
        elif level == str(cls.C):
            return cls.C
        return cls.D


class FlowerGroup(EntityClass):
    """
    花的专辑
    """
    
    def __init__(self, name: str = '', description: str = '', is_activity: bool = False,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
        self.name = name  # 名字
        self.description = description  # 描述
        self.is_activity = is_activity  # 是否是活动

    def __str__(self):
        return '专辑：%s\n介绍：%s' % (self.name, self.description)


class Flower(EntityClass):
    """
    花类
    """
    
    def __init__(self, name: str = '', level: FlowerLevel = FlowerLevel.D,
                 climate_id: List[str] = None, soil_id: List[str] = None,
                 op_climate_id: List[str] = None, op_soil_id: List[str] = None,
                 description: str = '', groups: List[str] = None,
                 seed_condition: Conditions = Conditions(), grow_condition: Conditions = Conditions(),
                 mature_condition: Conditions = Conditions(),
                 water_absorption: int = 0, nutrition_absorption: int = 0,
                 seed_time: int = 0, grow_time: int = 0, mature_time: int = 0,
                 overripe_time: int = 0, withered_time: int = 0, prefect_time: int = 0, flower_yield: int = 1,
                 first_user_qq: int = 0, first_user_time: datetime = datetime.now(),
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
        self.name = name  # 花名
        self.level = level  # 花的等级
        if groups is None:
            groups = []
        self.groups = groups  # 专辑列表
        self.description = description  # 描述
        
        if climate_id is None:
            climate_id = []
        self.climate_id = climate_id  # 适宜的气候id（如果适宜气候id和不适宜都为空，那么表示适宜所有环境）
        if soil_id is None:
            soil_id = []
        self.soil_id = soil_id  # 适宜的土壤id
        if op_climate_id is None:
            op_climate_id = []
        self.op_climate_id = op_climate_id  # 不适宜的气候id（不能与适宜气候id并存，可能导致bug）
        if op_soil_id is None:
            op_soil_id = []
        self.op_soil_id = op_soil_id  # 不适宜的土壤id（不能与适宜的土壤id并存）
        
        # 条件
        self.seed_condition = seed_condition  # 种子的条件
        self.grow_condition = grow_condition  # 种植的条件
        self.mature_condition = mature_condition  # 成熟的条件
        
        # 水分、营养的吸收
        self.water_absorption = water_absorption  # 水分吸收速率（每小时）
        self.nutrition_absorption = nutrition_absorption  # 营养吸收（每小时）
        
        # 每个阶段的时间
        self.seed_time = seed_time  # 种子的时间
        self.grow_time = grow_time  # 种植的时间
        self.mature_time = mature_time  # 成熟的时间
        self.overripe_time = overripe_time  # 过熟的时间
        self.withered_time = withered_time  # 枯萎的时间（这个是累计一定时间后将会枯萎）
        self.prefect_time = prefect_time  # 完美的时间（这个累计一定时间后将会变为完美）
        
        self.flower_yield = flower_yield  # 花的产量
        
        self.first_user_qq = first_user_qq  # 第一个种出来的人
        self.first_user_time = first_user_time  # 第一次种出完美的时间

    def valid_climate(self, climate_id: str) -> bool:
        """
        检查是否适宜气候
        :param climate_id:
        :return:
        """
        if len(self.climate_id) != 0:
            return climate_id in self.climate_id
        elif len(self.op_climate_id) != 0:
            return climate_id not in self.op_climate_id
        return True
    
    def valid_soil(self, soil_id: str) -> bool:
        """
        检查是否适宜土壤
        :param soil_id:
        :return:
        """
        if len(self.soil_id) != 0:
            return soil_id in self.soil_id
        elif len(self.op_soil_id) != 0:
            return soil_id not in self.op_soil_id
        return True


class Weather(EntityClass):
    """
    天气类（每个城市的天气）
    """
    
    def __init__(self, city_id: str = '', city_name: str = '', weather_type: str = '', min_temperature: int = 0,
                 max_temperature: int = 0, humidity: int = 0,
                 pm25: float = 0.0, pm10: float = 0.0, air_quality: str = '', air_quality_number: int = 0,
                 wind_direction: str = '', wind_level: str = '',
                 source: str = '', aqi: int = 0, advice: str = '', comment: str = '',
                 create_time: datetime = datetime.now(), create_id: str = '0',
                 update_time: datetime = datetime.now(), update_id: str = '0', is_delete: int = 0,
                 _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
        self.city_id = city_id  # 城市id
        self.city_name = city_name  # 城市名
        self.weather_type = weather_type  # 天气类型
        self.min_temperature = min_temperature  # 最低温度
        self.max_temperature = max_temperature  # 最高温度
        self.humidity = humidity  # 湿度
        self.pm25 = pm25  # PM 2.5
        self.pm10 = pm10  # PM 10
        self.air_quality = air_quality  # 空气质量
        self.air_quality_number = air_quality_number  # 空气质量数值
        self.wind_direction = wind_direction  # 风方向
        self.wind_level = wind_level  # 风的级别
        self.aqi = aqi  # 污染程度
        self.advice = advice  # 出行建议（对于空气）
        self.comment = comment  # 天气说明（需要注意什么）
        self.source = source  # 来源
    
    def __str__(self):
        reply = self.city_name + '，' + self.weather_type
        reply += '\n最低气温：' + str(self.min_temperature) + '℃'
        reply += '\n最高气温：' + str(self.max_temperature) + '℃'
        reply += '\n湿度：' + str(self.humidity) + '%'
        if self.pm25 != 0.0:
            reply += '\nPM 2.5：%.1f' % self.pm25
        if self.pm10 != 0.0:
            reply += '\nPM 10：%.1f' % self.pm10
        if self.air_quality != '':
            reply += '\n空气质量：' + self.air_quality
            if self.air_quality_number > 0:
                reply += '（%d）' % self.air_quality_number
        if self.wind_direction != '' and self.wind_level != '':
            reply += '\n风：' + self.wind_direction + self.wind_level
        if self.advice != '':
            reply += '\n感冒易发程度：' + self.advice
        if self.comment != '':
            reply += '\n说明：' + self.comment
        if self.source != '':
            reply += '\n来源：' + self.source
        return reply
    
    def __repr__(self):
        return self.__str__()


class ItemType(Enum):
    """
    物品类型枚举类
    """
    unknown = 'unknown'  # 未知物品
    seed = 'seed'  # 种子
    flower = 'flower'  # 花
    fertilizer = 'fertilizer'  # 化肥
    accelerate = 'accelerate'  # 加速卡
    props = 'props'  # 特殊道具
    thermometer = 'thermometer'  # 温度计（用于农场）
    soil_monitoring_station = 'soil_monitoring_station'  # 土壤检测站（用于农场）
    watering_pot = 'watering_pot'  # 浇水壶（用于农场）
    weather_station = 'weather_station'  # 气象监控站（适用于农场）
    mailbox = 'mailbox'  # 信箱（适用于农场）
    greenhouse = 'greenhouse'  # 温室（适用于农场）
    warehouse = 'warehouse'  # 仓库（适用于农场）
    air_condition = 'air_condition'  # 空调（适用于农场）
    
    hat = 'hat'  # 帽子
    clothes = 'clothes'  # 衣服
    dress = 'dress'  # 连衣裙
    trousers = 'trousers'  # 裤子
    shoes = 'shoes'  # 鞋子
    glove = 'glove'  # 手套
    necklace = 'necklace'  # 项链
    bracelet = 'bracelet'  # 手链
    foot_ring = 'foot_ring'  # 脚链
    cape = 'cape'  # 披风
    coat = 'coat'  # 外套
    
    @classmethod
    def view_name(cls, item_type) -> str:
        if item_type == cls.unknown:
            return '未知物品'
        elif item_type == cls.seed:
            return '种子'
        elif item_type == cls.flower:
            return '花'
        elif item_type == cls.fertilizer:
            return '营养液'
        elif item_type == cls.accelerate:
            return '加速卡'
        elif item_type == cls.props:
            return '特殊道具'
        elif item_type == cls.thermometer:
            return '温度计'
        elif item_type == cls.soil_monitoring_station:
            return '土壤监测站'
        elif item_type == cls.watering_pot:
            return '浇水壶'
        elif item_type == cls.weather_station:
            return '气象监控站'
        elif item_type == cls.air_condition:
            return '空调'
        elif item_type == cls.mailbox:
            return '信箱'
        elif item_type == cls.greenhouse:
            return '温室'
        elif item_type == cls.warehouse:
            return '仓库'
        elif item_type == cls.hat:
            return '帽子'
        elif item_type == cls.clothes:
            return '衣服'
        elif item_type == cls.dress:
            return '连衣裙'
        elif item_type == cls.trousers:
            return '裤子'
        elif item_type == cls.shoes:
            return '鞋子'
        elif item_type == cls.glove:
            return '手套'
        elif item_type == cls.necklace:
            return '项链'
        elif item_type == cls.bracelet:
            return '手链'
        elif item_type == cls.foot_ring:
            return '脚链'
        elif item_type == cls.cape:
            return '披风'
        elif item_type == cls.coat:
            return '外套'
        return ''
    
    @classmethod
    def get_type(cls, item_type: str):
        if not item_type.startswith('ItemType.'):
            item_type = 'ItemType.' + item_type
        if item_type == str(cls.seed):
            return cls.seed
        elif item_type == str(cls.flower):
            return cls.flower
        elif item_type == str(cls.fertilizer):
            return cls.fertilizer
        elif item_type == str(cls.accelerate):
            return cls.accelerate
        elif item_type == str(cls.props):
            return cls.props
        elif item_type == str(cls.thermometer):
            return cls.thermometer
        elif item_type == str(cls.soil_monitoring_station):
            return cls.soil_monitoring_station
        elif item_type == str(cls.watering_pot):
            return cls.watering_pot
        elif item_type == str(cls.weather_station):
            return cls.weather_station
        elif item_type == str(cls.mailbox):
            return cls.mailbox
        elif item_type == str(cls.greenhouse):
            return cls.greenhouse
        elif item_type == str(cls.warehouse):
            return cls.warehouse
        elif item_type == str(cls.air_condition):
            return cls.air_condition
        elif item_type == str(cls.hat):
            return cls.hat
        elif item_type == str(cls.clothes):
            return cls.clothes
        elif item_type == str(cls.dress):
            return cls.dress
        elif item_type == str(cls.trousers):
            return cls.trousers
        elif item_type == str(cls.shoes):
            return cls.shoes
        elif item_type == str(cls.glove):
            return cls.glove
        elif item_type == str(cls.necklace):
            return cls.necklace
        elif item_type == str(cls.bracelet):
            return cls.bracelet
        elif item_type == str(cls.foot_ring):
            return cls.foot_ring
        elif item_type == str(cls.cape):
            return cls.cape
        elif item_type == str(cls.coat):
            return cls.coat
        return cls.unknown


class FlowerQuality(Enum):
    """
    花的品质枚举类
    """
    
    not_flower = 'not_flower'
    perfect = 'perfect'
    normal = 'normal'
    
    @classmethod
    def view_name(cls, flower_quality) -> str:
        if flower_quality == cls.not_flower:
            return '不是花'
        elif flower_quality == cls.perfect:
            return '完美'
        elif flower_quality == cls.normal:
            return '正常'
        return ''
    
    @classmethod
    def get_type(cls, flower_quality: str):
        if not flower_quality.startswith('FlowerQuality.'):
            flower_quality = 'FlowerQuality.' + flower_quality
        if flower_quality == str(cls.perfect):
            return cls.perfect
        elif flower_quality == str(cls.normal):
            return cls.normal
        return cls.not_flower


class Item(EntityClass):
    """
    物品类
    """
    
    def __init__(self, name: str = '', item_type: ItemType = ItemType.unknown, description: str = '',
                 max_stack: int = 0, max_durability: int = 0, rot_second: int = 0,
                 humidity: float = 0.0, nutrition: float = 0.0, temperature: float = 0.0, level: int = 0,
                 gold: int = 0,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
        self.name = name
        self.item_type = item_type  # 物品类型
        self.description = description  # 描述
        self.max_stack = max_stack  # 最大叠加数量
        self.max_durability = max_durability  # 最大耐久度
        self.rot_second = rot_second  # 腐烂的秒数
        
        self.humidity = humidity  # 湿度
        self.nutrition = nutrition  # 营养
        self.temperature = temperature  # 温度
        self.level = level  # 级别（用于检测农场的气象站等）
        self.gold = gold  # 基准价格
    
    def __str__(self):
        result = '名字：' + self.name
        result += '\n类别：' + ItemType.view_name(self.item_type)
        result += '\n最大堆叠：' + str(self.max_stack)
        if self.level > 0:
            result += '\n级别：' + str(self.level)
        if self.max_durability > 0:
            result += '\n耐久：' + str(self.max_durability)
        if self.rot_second > 0:
            result += '\n腐烂：'
            left_second = self.rot_second
            if left_second >= 86400:
                result += str(left_second // 86400) + '天'
                left_second %= 86400
            if left_second >= 3600:
                result += str(left_second // 3600) + '小时'
                left_second %= 3600
            if left_second >= 60:
                result += str(left_second // 60) + '分钟'
                left_second %= 60
            if left_second > 0:
                result += str(left_second) + '秒'
        result += '\n描述：' + self.description
        return result
    
    def __repr__(self):
        return self.__str__()


class DecorateItem(InnerClass):
    """
    物品栈类
    """
    
    def __init__(self, item_id: str = '', item_type: ItemType = ItemType.unknown, item_name: str = '', number: int = 0,
                 durability: int = 0, max_durability: int = 0, rot_second: int = 0,
                 flower_quality: FlowerQuality = FlowerQuality.not_flower, hour: int = 0,
                 humidity: float = 0.0, nutrition: float = 0.0, temperature: float = 0.0, level: int = 0,
                 create: datetime = datetime.now(), update: datetime = datetime.now()):
        super().__init__('DecorateItem')
        self.item_id = item_id  # 物品id
        self.item_name = item_name  # 物品名字
        self.item_type = item_type  # 物品类型
        self.number = number  # 数量
        
        self.durability = durability  # 耐久度
        self.max_durability = max_durability  # 最大耐久度
        self.rot_second = rot_second  # 腐烂的秒
        self.flower_quality = flower_quality  # 花的品质
        self.humidity = humidity  # 湿度
        self.nutrition = nutrition  # 营养
        self.temperature = temperature  # 温度
        self.hour = hour  # 加速的时间
        self.level = level  # 级别（用于检测农场的气象站等）
        self.create = create  # 创建时间（用于一些物品失效检测）
        self.update = update  # 修改时间（用于耐久度检测，装备的耐久度都是时间）
    
    def show_without_number(self):
        ans: str = self.__str__()
        if 'x' in ans:
            ans = ans[:ans.rindex('x')]
        return ans
    
    def __str__(self):
        if self.item_id == '' and self.item_name == '' and self.item_id is not None and self.item_name is not None:
            return '无'
        if self.number <= 0:
            return '无'
        ans = self.item_name
        if self.flower_quality != FlowerQuality.not_flower:
            ans += '—' + FlowerQuality.view_name(self.flower_quality)
        if self.max_durability > 0:
            ans += '（耐久' + '%d/%d）' % (self.durability, self.max_durability)
        if self.rot_second > 0:
            critical_time: datetime = self.create + timedelta(seconds=self.rot_second)
            ans += '（将在' + critical_time.strftime('%Y-%m-%d %H:%M:%S') + '腐烂）'
        if self.hour > 0:
            ans += '（%d小时）' % self.hour
        if self.number > 1:
            ans += 'x' + str(self.number)
        return ans
    
    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, other):
        if not isinstance(other, DecorateItem):
            return False
        if other.item_id != '' and self.item_id != '' and self.item_id is not None and self.item_name is not None and \
                self.item_id != other.item_id:
            return False
        if self.item_name != other.item_name:
            return False
        if self.max_durability != 0 and self.durability != other.durability:
            return False
        if self.rot_second != 0 and self.create != other.create:
            return False
        if self.flower_quality != other.flower_quality:
            return False
        if self.hour != other.hour:
            return False
        return True
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __gt__(self, other):
        if not isinstance(other, DecorateItem):
            raise TypeError('不可以比较')
        if self.item_name == other.item_name:
            if self.max_durability > 0:
                return self.durability > other.durability
            if self.flower_quality != FlowerQuality.not_flower:
                return self.flower_quality > other.flower_quality
            if self.hour > 0 or other.hour > 0:
                return self.hour < other.hour
            return self.number < other.number
        if self.item_type != other.item_type:
            return self.item_type > other.item_type
        return self.item_name > other.item_name
    
    def __ge__(self, other):
        return self.__eq__(other) or self.__gt__(other)
    
    def __lt__(self, other):
        if not isinstance(other, DecorateItem):
            raise TypeError('不可以比较')
        if self.item_name == other.item_name:
            if self.max_durability > 0:
                return self.durability < other.durability
            if self.flower_quality != FlowerQuality.not_flower:
                return self.flower_quality < other.flower_quality
            if self.hour > 0 or other.hour > 0:
                return self.hour > other.hour
            return self.number > other.number
        if self.item_type != other.item_type:
            return self.item_type < other.item_type
        return self.item_name < other.item_name
    
    def __le__(self, other):
        return self.__eq__(other) or self.__lt__(other)
    
    def is_valid(self) -> bool:
        # 没有东西
        if self.number < 1:
            return False
        # 腐烂了
        if self.rot_second > 0:
            now: datetime = datetime.now()
            critical_time: datetime = self.create + timedelta(seconds=self.rot_second)
            if now >= critical_time:
                return False
        # 耐久度没了
        if self.max_durability > 0:
            if self.durability <= 0:
                return False
        return True


class WareHouse(InnerClass):
    """
    仓库类
    """
    
    def __init__(self, items: List[DecorateItem] = None, max_size: int = 30, description: str = ''):
        super().__init__('WareHouse')
        if items is None:
            items = []
        self.items = items
        self.max_size = max_size  # 仓库容量
        self.description = description  # 描述
    
    def check_item(self) -> bool:
        """
        检查物品有效性
        :return: none
        """
        result: bool = False
        remove_item: List[DecorateItem] = []
        for item in self.items:
            if not item.is_valid():
                remove_item.append(item)
                result = True
        for item in remove_item:
            # 如果是用完的就没必要提醒
            if item.number > 0:
                self.description += '物品失效：' + str(item) + '\n'
            self.items.remove(item)
        
        return result


class Horse(EntityClass):
    """
    马
    """
    
    def __init__(self, name: str = '', speed: float = 0.0, strength: float = 0.0, playful: float = 0.0,
                 description: str = '', max_age: int = 0,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
        
        self.name = name  # 马的名字
        self.speed = speed  # 速度
        self.strength = strength  # 体力
        self.playful = playful  # 贪玩
        self.description = description  # 描述
        self.max_age = max_age  # 最大年龄


class DecorateHorse(InnerClass):
    """
    农场的马
    """
    
    def __init__(self, name: str = '', nickname: str = '', speed: float = 0.0, strength: float = 0.0,
                 playful: float = 0.0, description: str = '', last_race: datetime = datetime.now(), max_age: int = 0,
                 born_time: datetime = datetime.now()):
        super().__init__('DecorateHorse')
        
        self.name = name  # 马的名字
        self.nickname = nickname  # 昵称
        self.speed = speed  # 速度
        self.strength = strength  # 体力
        self.playful = playful  # 贪玩
        self.description = description  # 描述
        self.last_race = last_race  # 上一次比赛的时间（会影响体力的恢复情况）
        self.max_age = max_age  # 最大年龄
        self.born_time = born_time  # 出生日期


class Dog(EntityClass):
    """
    狗
    """
    
    def __init__(self, name: str = '', force: float = 0.0, affinity: float = 0.0, strength: float = 0.0,
                 description: str = '', max_age: int = 0,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
        
        self.name = name  # 名字
        self.force = force  # 武力
        self.affinity = affinity  # 亲和力
        self.strength = strength  # 体力（影响是否能捉到小偷）
        self.description = description  # 描述
        self.max_age = max_age  # 最大年龄


class DecorateDog(InnerClass):
    """
    农场的狗
    """
    
    def __init__(self, name: str = '', force: float = 0.0, affinity: float = 0.0, favorability: float = 0.0,
                 strength: float = 0.0, description: str = '', max_age: int = 0, nickname: str = '',
                 born_time: datetime = datetime.now()):
        super().__init__('DecorateDog')
        
        self.name = name  # 名字
        self.nickname = nickname  # 昵称
        self.force = force  # 武力
        self.affinity = affinity  # 亲和力
        self.favorability = favorability  # 好感度（决定狗是否会帮助主人）
        self.strength = strength  # 体力（影响是否能捉到小偷）
        self.description = description  # 描述
        self.max_age = max_age  # 最大年龄
        self.born_time = born_time  # 出生日期


class Cat(EntityClass):
    """
    猫
    """
    
    def __init__(self, name: str = '', affinity: float = 0.0, playful: float = 0.0,
                 description: str = '', max_age: int = 0,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
        
        self.name = name  # 名字
        self.affinity = affinity  # 亲和力（刷好感度的速度）
        self.playful = playful  # 贪玩
        self.description = description  # 描述
        self.max_age = max_age  # 最大年龄


class DecorateCat(InnerClass):
    """
    农场的猫
    """
    
    def __init__(self, name: str = '', affinity: float = 0.0, favorability: float = 0.0, playful: float = 0.0,
                 description: str = '', max_age: int = 0, nickname: str = '',
                 born_time: datetime = datetime.now()):
        super().__init__('DecorateCat')
        
        self.name = name  # 名字
        self.nickname = nickname  # 昵称
        self.affinity = affinity  # 亲和力（刷好感度的速度）
        self.favorability = favorability  # 好感度（决定猫咪是否会外出）
        self.playful = playful  # 贪玩
        self.description = description  # 描述
        self.max_age = max_age  # 最大年龄
        self.born_time = born_time  # 出生日期


class FlowerState(Enum):
    not_flower = 'not_flower'  # 不是花
    perfect = 'perfect'  # 完美
    normal = 'normal'  # 正常
    withered = 'withered'  # 枯萎
    
    @classmethod
    def view_name(cls, flower_state) -> str:
        if flower_state == cls.not_flower:
            return '未种植花'
        elif flower_state == cls.perfect:
            return '完美'
        elif flower_state == cls.normal:
            return '正常'
        elif flower_state == cls.withered:
            return '枯萎'
        return ''
    
    @classmethod
    def get_type(cls, flower_state: str):
        if not flower_state.startswith('FlowerState.'):
            flower_state = 'FlowerState.' + flower_state
        if flower_state == str(cls.perfect):
            return cls.perfect
        elif flower_state == str(cls.normal):
            return cls.normal
        elif flower_state == str(cls.withered):
            return cls.withered
        return cls.not_flower


class Farm(InnerClass):
    """
    用户-花类（农场）
    """
    
    def __init__(self, soil_id: str = '', climate_id: str = '', flower_id: str = '',
                 flower_state: FlowerState = FlowerState.not_flower,
                 reality_hour: int = 0,
                 hour: float = 0.0, perfect_hour: float = 0.0, stop_prefect: int = 0, non_perfect_hour: int = 0,
                 bad_hour: float = 0.0, humidity: float = 0.0, nutrition: float = 0.0, temperature: float = 0.0,
                 last_check_time: datetime = datetime.now(), thermometer: DecorateItem = DecorateItem(),
                 soil_monitoring_station: DecorateItem = DecorateItem(), watering_pot: DecorateItem = DecorateItem(),
                 mailbox: DecorateItem = DecorateItem(), greenhouse: DecorateItem = DecorateItem(),
                 warehouse: DecorateItem = DecorateItem(), air_condition: DecorateItem = DecorateItem(),
                 horse: DecorateHorse = DecorateHorse(), dog: DecorateDog = DecorateDog(),
                 cat: DecorateCat = DecorateCat(),
                 soil_humidity_min_change_hour: int = 0, soil_humidity_max_change_hour: int = 0,
                 soil_nutrition_min_change_hour: int = 0, soil_nutrition_max_change_hour: int = 0):
        super().__init__('Farm')
        self.soil_id = soil_id  # 土壤id
        self.climate_id = climate_id  # 气候id
        self.flower_id = flower_id  # 花的id
        self.flower_state = flower_state  # 花的状态
        self.reality_hour = reality_hour  # 真实的时间（不吃任何加成，每种植一个小时就是一个小时）
        self.hour = hour  # 植物生长的小时数
        self.perfect_hour = perfect_hour  # 累计的完美的小时数
        self.stop_prefect = stop_prefect  # 停止完美计时的次数
        self.non_perfect_hour = non_perfect_hour  # 非完美的小时数
        self.bad_hour = bad_hour  # 糟糕的小时数
        self.humidity = humidity  # 上一次检查的湿度
        self.nutrition = nutrition  # 上一次检查的营养
        self.temperature = temperature  # 上一次检查的温度
        self.last_check_time = last_check_time  # 上一次检查时间
        
        self.thermometer = thermometer  # 农场的温度计
        self.soil_monitoring_station = soil_monitoring_station  # 农场的土壤检测站
        self.watering_pot = watering_pot  # 农场的浇水壶
        self.mailbox = mailbox  # 信箱
        self.greenhouse = greenhouse  # 温室
        self.warehouse = warehouse  # 仓库
        self.air_condition = air_condition  # 空调
        
        self.horse = horse  # 农场的马
        self.dog = dog  # 农场的狗
        self.cat = cat  # 农场的猫
        
        # 土壤改变的累计小时
        self.soil_humidity_min_change_hour = soil_humidity_min_change_hour  # 营养不合格累计的小时数
        self.soil_humidity_max_change_hour = soil_humidity_max_change_hour  # 营养不合格累计的小时数
        self.soil_nutrition_min_change_hour = soil_nutrition_min_change_hour  # 湿度不合格累计的小时数
        self.soil_nutrition_max_change_hour = soil_nutrition_max_change_hour  # 湿度不合格累计的小时数


class SignRecord(EntityClass):
    """
    签到记录
    """
    
    def __init__(self, qq: int = 0, create_time: datetime = datetime.now(), create_id: str = '0',
                 update_time: datetime = datetime.now(), update_id: str = '0', is_delete: int = 0,
                 _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
        self.qq = qq


class Mail(EntityClass):
    """
    邮件类
    """
    
    def __init__(self, role_id: str = '', from_qq: int = 0, target_qq: int = 0, title: str = '', text: str = '',
                 appendix: List[DecorateItem] = None, place_id: str = '', arrived: bool = False, status: str = '',
                 received: bool = False, username: str = '', gold: int = 0,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
        self.role_id = role_id  # npc的id
        self.from_qq = from_qq  # 谁寄出来的（用户和npc只能有一个）
        self.username = username  # 寄件人，可能会用名义去送（而不会实名）
        self.target_qq = target_qq  # 谁收到这封
        self.title = title  # 标题
        self.text = text  # 正文
        if not isinstance(appendix, list):
            appendix = []
        self.appendix = appendix  # 附件
        self.gold = gold  # 随信赠送的金币
        self.received = received  # 是否已经领取了附件
        self.place_id = place_id  # 地点id（当前所在的地点）
        self.arrived = arrived  # 是否已到达（无论是损坏还是咋样都应该到达或者没有送到）
        self.status = status  # 信件的状态描述（描述信件是已经送达，还是出了意外）


class MailBox(InnerClass):
    """
    邮箱类
    """
    
    def __init__(self, mail_list: List[str] = None, max_size: int = 0):
        super().__init__('MailBox')
        if not isinstance(mail_list, list):
            mail_list = []
        self.mail_list = mail_list  # 信件的id
        self.max_size = max_size


class Buff(EntityClass):
    """
    增益or减益
    """
    
    def __init__(self, name: str = '', lock_humidity: bool = False, lock_nutrition: bool = False,
                 lock_soil: bool = False, lock_temperature: bool = False, description: str = '',
                 change_humidity: float = 0.0, change_nutrition: float = 0.0, change_temperature: float = 0.0,
                 perfect_coefficient: float = 0.0, hour_coefficient: float = 0.0, bad_hour_coefficient: float = 0.0,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
        
        self.name = name  # buff名字
        self.description = description  # 描述
        self.lock_humidity = lock_humidity  # 是否锁定湿度
        self.lock_nutrition = lock_nutrition  # 是否锁定营养
        self.lock_temperature = lock_temperature  # 是否锁定温度
        self.lock_soil = lock_soil  # 是否锁定土壤，不让转变
        self.change_humidity = change_humidity  # 每小时改变的湿度
        self.change_nutrition = change_nutrition  # 每小时改变的营养
        self.change_temperature = change_temperature  # 每小时改变的温度
        self.perfect_coefficient = perfect_coefficient  # 完美小时的系数
        self.hour_coefficient = hour_coefficient  # 生长小时的系数
        self.bad_hour_coefficient = bad_hour_coefficient  # 糟糕小时的系数
    
    def __str__(self):
        reply: str = 'BUFF：' + str(self.name)
        reply += '\n描述：' + self.description
        decorate_buff: DecorateBuff = DecorateBuff().generate(buff=self)
        reply += '\n效果：' + decorate_buff.show_effect()
        return reply
    
    def __repr__(self):
        return self.__str__()


class DecorateBuff(InnerClass):
    """
    装饰的buff
    """
    
    def __init__(self, name: str = '', lock_humidity: bool = False, lock_nutrition: bool = False,
                 lock_soil: bool = False, lock_temperature: bool = False,
                 change_humidity: float = 0.0, change_nutrition: float = 0.0, change_temperature: float = 0.0,
                 perfect_coefficient: float = 0.0, hour_coefficient: float = 0.0, bad_hour_coefficient: float = 0.0,
                 expired_time: datetime = datetime.now()):
        super().__init__('DecorateBuff')
        
        self.name = name  # buff名字
        self.lock_humidity = lock_humidity  # 是否锁定湿度
        self.lock_nutrition = lock_nutrition  # 是否锁定营养
        self.lock_temperature = lock_temperature  # 是否锁定温度
        self.lock_soil = lock_soil  # 是否锁定土壤，不让转变
        self.change_humidity = change_humidity  # 每小时改变的湿度
        self.change_nutrition = change_nutrition  # 每小时改变的营养
        self.change_temperature = change_temperature  # 每小时改变的温度
        self.change_temperature = change_temperature  # 每小时改变的温度
        self.perfect_coefficient = perfect_coefficient  # 完美小时的系数
        self.hour_coefficient = hour_coefficient  # 生长小时的系数
        self.bad_hour_coefficient = bad_hour_coefficient  # 糟糕小时的系数
        
        self.expired_time = expired_time  # 过期时间
    
    def show_effect(self) -> str:
        reply: str = ''
        if self.lock_humidity:
            reply += '、锁定湿度'
        if self.lock_nutrition:
            reply += '、锁定营养'
        if self.lock_temperature:
            reply += '、锁定温度'
        if self.lock_soil:
            reply += '、锁定土壤'
        if self.change_humidity != 0.0:
            if self.change_humidity > 0:
                reply += '、湿度+%.2f/小时' % self.change_humidity
            else:
                reply += '、湿度%.2f/小时' % self.change_humidity
        if self.change_nutrition != 0.0:
            if self.change_nutrition > 0:
                reply += '、营养+%.2f/小时' % self.change_nutrition
            else:
                reply += '、营养%.2f/小时' % self.change_nutrition
        if self.change_temperature != 0.0:
            if self.change_temperature > 0:
                reply += '、温度+%.2f/小时' % self.change_temperature
            else:
                reply += '、温度%.2f/小时' % self.change_temperature
        if self.perfect_coefficient != 0.0:
            if self.perfect_coefficient > 0:
                reply += '、完美时长增幅+%.2f%%' % (self.perfect_coefficient * 100)
            else:
                reply += '、完美时长增幅%.2f%%' % (self.perfect_coefficient * 100)
        if self.hour_coefficient != 0.0:
            if self.hour_coefficient > 0:
                reply += '、生长时长增幅+%.2f%%' % (self.hour_coefficient * 100)
            else:
                reply += '、生长时长增幅%.2f%%' % (self.hour_coefficient * 100)
        if self.bad_hour_coefficient != 0.0:
            if self.bad_hour_coefficient > 0:
                reply += '、糟糕时长增幅+%.2f%%' % (self.bad_hour_coefficient * 100)
            else:
                reply += '、糟糕时长增幅%.2f%%' % (self.bad_hour_coefficient * 100)
        if reply == '':
            return '无效果或者拥有特殊效果'
        return reply[1:]
    
    def __str__(self):
        return self.name + '（到期时间：%s）：%s' % (self.expired_time.strftime('%Y-%m-%d %H:%M:%S'), self.show_effect())
    
    def __repr__(self):
        return self.__str__()
    
    def generate(self, buff: Buff):
        """
        将buff的数据填入自己
        :param buff: buff.txt
        :return:
        """
        self.name = buff.name
        self.lock_humidity = buff.lock_humidity
        self.lock_nutrition = buff.lock_nutrition
        self.lock_temperature = buff.lock_temperature
        self.lock_soil = buff.lock_soil
        self.change_humidity = buff.change_humidity
        self.change_nutrition = buff.change_nutrition
        self.change_temperature = buff.change_temperature
        return self
    
    def expired(self, now: datetime = datetime.now()):
        return self.expired_time < now


class Achievement(EntityClass):
    """
    成就类
    """
    
    def __init__(self, name: str = '', value_list: List[int] = None, description: str = '',
                 award_list: List[List[DecorateItem] or int] = None, collection: List[str] = None,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
        
        self.name = name  # 成就名
        if value_list is None:
            value_list = []
        self.value_list = value_list  # 用来暂存某一个维度升级的值，例如种花的成就就是种出来的花的个数
        if award_list is None:
            award_list = []
        self.award_list = award_list  # 奖励列表（可以是一组物品，也可以是金币）
        if collection is None:
            collection = []
        self.collection = collection  # 收集品
        self.description = description  # 描述
    
    def __str__(self):
        reply = '成就名：' + self.name
        reply += '\n描述：' + self.description
        reply += '\n最大等级：%d' % len(self.value_list)
        return reply
    
    def __repr__(self):
        return self.__str__()


class DecorateAchievement(InnerClass):
    """
    装饰的成就类
    """
    
    def __init__(self, name: str = '', achievement_time: datetime = datetime.now(), value: int = 0,
                 collection: List[str] = None, level: int = 0):
        super().__init__('DecorateAchievement')
        
        self.name = name
        self.achievement_time = achievement_time
        self.value = value  # 用于记录某个维度的值的个数
        if collection is None:
            collection = []
        self.collection = collection  # 收集类成就
        self.level = level
    
    @classmethod
    def show_level(cls, level: int):
        if level == 1:
            return 'I'
        elif level == 2:
            return 'II'
        elif level == 3:
            return 'III'
        elif level == 4:
            return 'IV'
        elif level == 5:
            return 'V'
        elif level == 6:
            return 'VI'
        elif level == 7:
            return 'VII'
        elif level == 8:
            return 'VIII'
        elif level == 9:
            return 'IX'
        elif level == 10:
            return 'X'
        return 'O'
    
    def __str__(self):
        return '%s %s（获取于%s）' % (
            self.name,
            self.show_level(self.level),
            self.achievement_time.strftime('%Y-%m-%d %H:%M:%S')
        )
    
    def __repr__(self):
        return self.__str__()
    
    def __gt__(self, other):
        if not isinstance(other, DecorateAchievement):
            raise TypeError('不可比较')
        if self.level != other.level:
            return self.level > other.level
        return self.name > other.name
    
    def __lt__(self, other):
        if not isinstance(other, DecorateAchievement):
            raise TypeError('不可比较')
        if self.level != other.level:
            return self.level < other.level
        return self.name < other.name
    
    def __eq__(self, other):
        if not isinstance(other, DecorateAchievement):
            raise TypeError('不可比较')
        return self.level == other.level and self.name == other.name
    
    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)
    
    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)


class Clothing(InnerClass):
    """
    衣服
    """
    
    def __init__(self, hat: DecorateItem = DecorateItem(), clothes: DecorateItem = DecorateItem(),
                 trousers: DecorateItem = DecorateItem(), shoes: DecorateItem = DecorateItem(),
                 glove: DecorateItem = DecorateItem(), necklace: DecorateItem = DecorateItem(),
                 bracelet: DecorateItem = DecorateItem(), foot_ring: DecorateItem = DecorateItem(),
                 cape: DecorateItem = DecorateItem(), coat: DecorateItem = DecorateItem()):
        super().__init__('Clothing')
        self.hat = hat  # 帽子
        self.clothes = clothes  # 衣服
        self.trousers = trousers  # 裤子
        self.shoes = shoes  # 鞋子
        self.glove = glove  # 手套
        self.necklace = necklace  # 项链
        self.bracelet = bracelet  # 手链
        self.foot_ring = foot_ring  # 脚链
        self.cape = cape  # 披风
        self.coat = coat  # 外套


class UserStatistics(EntityClass):
    """
    统计数据
    """
    
    def __init__(self, qq: int = 0, watering: int = 0, remove_flower: int = 0,
                 use_item: Dict[str, int] = None,
                 plant_flower: Dict[str, int] = None, plant_perfect_flower: Dict[str, int] = None,
                 draw_times: int = 0, success_draw_times: int = 0, all_draw_times: int = 0,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
        
        self.qq = qq  # QQ号
        self.watering = watering  # 浇水次数
        self.remove_flower = remove_flower  # 铲除次数
        if use_item is None:
            use_item = {}
        self.use_item = use_item  # 使用过的物品
        if plant_flower is None:
            plant_flower = {}
        self.plant_flower = plant_flower  # 种植的植物
        if plant_perfect_flower is None:
            plant_perfect_flower = {}
        self.plant_perfect_flower = plant_perfect_flower  # 种植的完美植物
        
        self.draw_times = draw_times  # 抽卡次数
        self.success_draw_times = success_draw_times  # 成功抽到的次数
        self.all_draw_times = all_draw_times  # 抽到全部的物品


class User(EntityClass):
    """
    用户类
    """
    
    def __init__(self, qq: int = 0, username: str = '', gender: Gender = Gender.unknown, auto_get_name: bool = True,
                 gold: int = 0, exp: int = 0, level: int = 0, total_gold: int = 0,
                 last_sign_date: datetime = datetime.today() - timedelta(days=1), sign_count: int = 0,
                 sign_continuous: int = 0, draw_card_number: int = 5, beginner_pack: bool = False,
                 beginner_pack_finish: bool = False,
                 warehouse: WareHouse = WareHouse(), farm: Farm = Farm(), mailbox: MailBox = MailBox(),
                 buff: List[DecorateBuff] = None, achievement: Dict[str, DecorateAchievement] = None,
                 born_city_id: str = '', city_id: str = '', knowledge: Dict[str, int] = None,
                 clothing: Clothing = Clothing(),
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
        self.qq = qq
        self.username = username
        self.gender = gender
        self.auto_get_name = auto_get_name  # 是否自动获取用户名
        self.gold = gold
        self.total_gold = total_gold  # 总计金币
        self.exp = exp  # 经验值
        self.level = level  # 当前等级（避免从头搜索经验数组）
        
        self.last_sign_date = last_sign_date  # 上次签到日期
        self.sign_count = sign_count  # 签到次数
        self.sign_continuous = sign_continuous  # 连续签到次数
        self.draw_card_number = draw_card_number  # 抽卡次数，每日签到刷新
        
        self.beginner_pack = beginner_pack  # 是否领取了初始礼包
        self.beginner_pack_finish = beginner_pack_finish  # 是否领完了新手礼包
        
        self.warehouse = warehouse  # 仓库
        self.farm = farm  # 农场
        self.mailbox = mailbox  # 信箱
        if buff is None:
            buff = []
        self.buff = buff  # Buff
        if achievement is None:
            achievement = {}
        self.achievement = achievement  # 成就
        
        self.born_city_id = born_city_id  # 出生城市id
        self.city_id = city_id  # 当前城市id
        
        if knowledge is None:
            knowledge = {}
        self.knowledge = knowledge  # 花的知识
        self.clothing = clothing  # 衣服
    
    def get_gold(self, gold):
        """
        增加金币
        """
        self.gold += gold
        self.total_gold += gold
    
    def get_total_buff(self, cal_datetime: datetime) -> DecorateBuff:
        total_buff: DecorateBuff = DecorateBuff()
        for buff in self.buff:
            # 对于在某一时间过期的buff不作处理
            if buff.expired_time < cal_datetime:
                continue
            if buff.lock_soil:
                total_buff.lock_soil = True
            if buff.lock_humidity:
                total_buff.lock_humidity = True
            if buff.lock_nutrition:
                total_buff.lock_nutrition = True
            if buff.lock_temperature:
                total_buff.lock_temperature = True
            total_buff.change_humidity += buff.change_humidity
            total_buff.change_temperature += buff.change_temperature
            total_buff.change_nutrition += buff.change_nutrition
            total_buff.perfect_coefficient += buff.perfect_coefficient
            total_buff.hour_coefficient += buff.hour_coefficient
            total_buff.bad_hour_coefficient += buff.bad_hour_coefficient
        return total_buff
    
    def accelerate_buff(self, seconds: int = 0):
        """
        加速buff
        :param seconds: 加速时间
        """
        for buff in self.buff:
            buff.expired_time -= timedelta(seconds=seconds)


class Commodity(InnerClass):
    """
    商品类
    """
    
    def __init__(self, item_id: str = '', gold: int = 0, stock: int = 0):
        super().__init__('Commodity')
        self.item_id = item_id  # 物品名
        self.gold = gold  # 售价
        self.stock = stock  # 库存


class UserPerson(EntityClass):
    """
    用户每天刷新的人物
    """
    
    def __init__(self, qq: int = 0, person_id: str = '', commodities: List[Commodity] = None, news: List[str] = None,
                 send_mail_price: int = -1, knowledge: Dict[str, Tuple[int, int]] = None, ban_item: List[str] = None,
                 cancel_sell_times: Dict[str, int] = None, can_create_market_account: bool = False,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
        self.qq = qq  # qq
        self.person_id = person_id  # 人物id
        if commodities is None:
            commodities = []
        self.commodities = commodities  # 商品
        if news is None:
            news = []
        self.news = news  # 小道消息
        self.send_mail_price = send_mail_price  # 发送mail的手续费百分比
        if knowledge is None:
            knowledge = {}
        self.knowledge = knowledge  # 知识 {花名： (等级，价格)}
        if ban_item is None:
            ban_item = []
        self.ban_item = ban_item  # 拒绝出售的商品
        if cancel_sell_times is None:
            cancel_sell_times = {}
        self.cancel_sell_times = cancel_sell_times  # 取消出售的次数
        self.can_create_market_account = can_create_market_account  # 是否可以开户


class SystemData:
    """
    系统数据类
    """
    
    def __init__(self, exp_level: List[int] = None, username_screen_words: List[str] = None,
                 soil_change_hour: int = 8, remove_farm_flower_cost_gold: int = 500, watering_cost_gold: int = 50,
                 soil_max_humidity: float = 100.0, soil_min_humidity: float = 0.0, soil_max_nutrition: float = 50.0,
                 soil_min_nutrition: float = 0.0, draw_card_max_number: int = 5,
                 draw_card_probability_unit: int = 10000, draw_card_probability: List[int] = None,
                 merchant_seed_pool: Dict[str, int] = None, merchant_item_pool: Dict[str, int] = None,
                 draw_seed_pool: Dict[str, int] = None, draw_item_pool: Dict[str, int] = None,
                 explorer_seed_pool: Dict[str, int] = None, explorer_item_pool: Dict[str, int] = None,
                 architect_item_pool: Dict[str, int] = None,
                 mater_right_qq: List[int] = None, admin_right_qq: List[int] = None, test_version: bool = False,
                 white_token_list: List[str] = None, allow_trading_flower_list: List[str] = None,
                 is_delete: int = 0, _id: str or None = None):
        self._id = _id
        self.is_delete = is_delete
        
        if exp_level is None:
            exp_level = []
        self.exp_level = exp_level  # 经验等级
        if username_screen_words is None:
            username_screen_words = []
        self.username_screen_words = username_screen_words
        
        self.soil_change_hour = soil_change_hour  # 土壤改变的小时数（超过此小时，土壤将会转变）
        self.remove_farm_flower_cost_gold = remove_farm_flower_cost_gold  # 铲除花所需要花费的金币数
        self.watering_cost_gold = watering_cost_gold  # 每次浇水所花费的金币
        
        # 土壤的湿度、营养上下限
        self.soil_max_humidity = soil_max_humidity
        self.soil_min_humidity = soil_min_humidity
        self.soil_max_nutrition = soil_max_nutrition
        self.soil_min_nutrition = soil_min_nutrition
        
        self.draw_card_max_number = draw_card_max_number  # 每日抽卡上限
        self.draw_card_probability_unit = draw_card_probability_unit  # 概率单位为万分之一
        if draw_card_probability is None:
            draw_card_probability = [5000, 2000, 1000, 100, 10]
        self.draw_card_probability = draw_card_probability
        
        if merchant_seed_pool is None:
            merchant_seed_pool = {}
        self.merchant_seed_pool = merchant_seed_pool  # 商人的种子池
        if merchant_item_pool is None:
            merchant_item_pool = {}
        self.merchant_item_pool = merchant_item_pool  # 商人的道具池
        
        if draw_seed_pool is None:
            draw_seed_pool = {}
        self.draw_seed_pool = draw_seed_pool  # 抽卡的种子池
        if draw_item_pool is None:
            draw_item_pool = {}
        self.draw_item_pool = draw_item_pool  # 抽卡的道具池
        
        if explorer_seed_pool is None:
            explorer_seed_pool = {}
        self.explorer_seed_pool = explorer_seed_pool  # 探险家的种子池
        if explorer_item_pool is None:
            explorer_item_pool = {}
        self.explorer_item_pool = explorer_item_pool  # 探险家的道具池
        
        if architect_item_pool is None:
            architect_item_pool = {}
        self.architect_item_pool = architect_item_pool  # 建筑师的道具池
        
        if mater_right_qq is None:
            mater_right_qq = []
        self.mater_right_qq = mater_right_qq  # 拥有master权限的QQ
        if admin_right_qq is None:
            admin_right_qq = []
        self.admin_right_qq = admin_right_qq  # 拥有admin权限的QQ
        self.test_version = test_version  # 是否在测试版本（如果在测试版本，那么所有人都拥有master权限）
        
        if white_token_list is None:
            white_token_list = []
        self.white_token_list = white_token_list  # 允许访问的token白名单

        if allow_trading_flower_list is None:
            allow_trading_flower_list = []
        self.allow_trading_flower_list = allow_trading_flower_list  # 允许交易的花名单
    
    def get_id(self) -> str:
        return self._id


class Announcement:
    """
    公告
    """
    
    def __init__(self, qq: int = -0, username: str = '', text: str = '', release_time: datetime = datetime.now(),
                 expire_time: datetime = datetime.now(),
                 is_delete: int = 0, _id: str or None = None):
        self._id = _id
        self.is_delete = is_delete
        
        self.qq = qq  # 发布人
        self.username = username  # 发布人名
        self.text = text  # 公告正文
        self.release_time = release_time  # 发布时间
        self.expire_time = expire_time  # 过期时间
        self.read_list: Dict[str, int] = {}  # 阅读的人的QQ号
    
    def get_id(self) -> str:
        return self._id
    
    def is_expire(self):
        """
        公告是否过期
        """
        return datetime.now() > self.expire_time
