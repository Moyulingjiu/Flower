# coding=utf-8
"""
存储与世界PCG演化相关的模型
"""
from datetime import datetime
from enum import Enum
from typing import Tuple, List

from model.base_model import *

__all__ = [
    "Disease", "Profession", "Race", "WorldTerrain", "WorldArea", "Kingdom", "Relationship",
    "Person", "Trait", "PersonName", "PersonLastName", "PathModel"
]


class PersonLastName(EntityClass):
    """
    姓氏
    """

    def __init__(self, value: str = '',
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)

        self.value = value  # 姓氏

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.__str__()


class PersonName(EntityClass):
    """
    名
    """

    def __init__(self, value: str = '', gender: Gender = Gender.male,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)

        self.value = value  # 姓氏
        self.gender = gender  # 性别

    def __str__(self):
        return self.value + '（%s）' % ('男' if self.gender == Gender.male else '女')

    def __repr__(self):
        return self.__str__()


class Disease(Enum):
    """
    疾病
    """

    def __init__(self, name: str = '', description: str = '', death_probability: int = 0,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)

        self.name = name  # 名字
        self.description = description  # 介绍
        self.death_probability = death_probability  # 死亡概率


class Profession(EntityClass):
    """
    职业
    """

    def __init__(self, name: str = '', description: str = '',
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)

        self.name = name  # 名字
        self.description = description  # 介绍


class Race(EntityClass):
    """
    种族
    """

    def __init__(self, name: str = '', description: str = '',
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)

        self.name = name  # 名字
        self.description = description  # 介绍

    def __str__(self):
        return '名字：%s\n介绍：%s' % (self.name, self.description)

    def __repr__(self):
        return self.__str__()


class WorldTerrain(EntityClass):
    """
    世界地区
    """

    def __init__(self, name: str = '',
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)

        self.name = name  # 世界地形名

    def __str__(self):
        return '地形：' + self.name

    def __repr__(self):
        return self.__str__()


class PathModel(InnerClass):
    """
    连通图
    """

    def __init__(self, target_area_id: str = '', distance: float = 0, driving_price: int = 0, sail_price: int = 0,
                 difficulty: int = 0, death_probability: float = 0.0):
        super().__init__('PathModel')

        self.target_area_id = target_area_id  # 目的地id
        self.distance = distance  # 距离
        self.driving_price = driving_price  # 陆行价格
        self.sail_price = sail_price  # 航行价格
        self.difficulty = difficulty  # 难度
        self.death_probability = death_probability  # 死亡概率


class WorldArea(EntityClass):
    """
    世界地区
    """

    def __init__(self, name: str = '', terrain_id: str = '', race_id: str = '', description: str = '',
                 path_list: List[PathModel] = None,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)

        self.name = name  # 地区名
        self.terrain_id = terrain_id  # 地形id
        self.description = description  # 描述
        self.race_id = race_id  # 主要种族
        if path_list is None:
            path_list = []
        self.path_list = path_list  # 联通路径

    def __str__(self):
        reply = '地区：%s' % self.name
        reply += '\n地形id：%s' % self.terrain_id
        reply += '\n描述：%s' % self.description
        reply += '\n连通地区id：'
        for area_path in self.path_list:
            reply += area_path + '、'
        if len(self.path_list) > 0:
            reply = reply[:-1]
        return reply

    def __repr__(self):
        return self.__str__()


class Kingdom(EntityClass):
    """
    王国
    """

    def __init__(self, name: str = '', area_id_list: List[str] = None,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)

        self.name = name  # 王国名
        if area_id_list is None:
            area_id_list = []
        self.area_id_list = area_id_list  # 地区id


class Relationship(EntityClass):
    """
    人际关系
    人物src_person->des_person的好感为value，value为0表示不喜欢也不讨厌，小于0讨厌，大于0喜欢
    """

    def __init__(self, src_person: str = '', dst_person: str = '', value: int = 0,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
        self.src_person = src_person  # 人物1
        self.dst_person = dst_person  # 人物2
        self.value = value  # 关系水平

    def __str__(self):
        return '%s 对 %s 的关系为：%d' % (self.src_person, self.dst_person, self.value)

    def __repr__(self):
        return self.__str__()


class Person(EntityClass):
    """
    人物模型
    """

    def __init__(self, name: str = '', gender: Gender = Gender.male, sexual_orientation: Gender = Gender.female,
                 spouse_id: str = '', predecessor: List[Tuple[str, datetime]] = None, relationships: List[str] = None,
                 children: List[str] = None, father_id: str = '', mother_id: str = '', motherland: str = '',
                 die: bool = False, die_time: datetime = datetime.now(), max_age: int = 0, die_reason: str = '',
                 world_area_id: str = '', born_area_id: str = '', born_time: datetime = datetime.now(),
                 gold: int = 0, disease_id: str = '', profession_id: str = '', race_id: str = '',
                 wisdom: int = 0, leadership: int = 0, force: int = 0, affinity: int = 0, ambition: int = 0,
                 health: int = 0, appearance: int = 0, appearance_description: str = '',
                 justice_or_evil: int = 0, extroversion_or_introversion: int = 0, bravery_or_cowardly: int = 0,
                 rational_or_sensual: int = 0, hedonic_or_computation: int = 0, selfish_or_generous: int = 0,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)

        self.name = name  # 名字
        self.gender = gender  # 性别
        self.sexual_orientation = sexual_orientation  # 性取向
        self.spouse_id = spouse_id  # 伴侣
        if predecessor is None:
            predecessor = []
        self.predecessor = predecessor  # 前任伴侣（id，时间）
        if relationships is None:
            relationships = []
        self.relationships = relationships  # 人际关系（id列表）
        if children is None:
            children = []
        self.children = children  # 子女（id列表）
        self.father_id = father_id  # 父亲
        self.mother_id = mother_id  # 母亲
        self.world_area_id = world_area_id  # 当前所在地
        self.born_area_id = born_area_id  # 出生地
        self.born_time = born_time  # 出生时间（现实中每一天是其一年）
        self.max_age = max_age  # 最大年龄
        self.motherland = motherland  # 祖国

        self.gold = gold  # 金币
        self.disease_id = disease_id  # 疾病
        self.profession_id = profession_id  # 职业
        self.race_id = race_id  # 种族

        self.die = die  # 是否死亡
        self.die_time = die_time  # 死亡时间
        self.die_reason = die_reason  # 死亡原因

        self.wisdom = wisdom  # 智慧
        self.leadership = leadership  # 领导力
        self.force = force  # 武力
        self.affinity = affinity  # 亲和力
        self.ambition = ambition  # 野心
        self.health = health  # 健康（健康与疾病不同，健康影响的是患疾病的概率，而不是直接有病，病还可能是外伤）
        self.appearance = appearance  # 外貌
        self.appearance_description = appearance_description  # 外貌描述

        self.justice_or_evil = justice_or_evil  # 正义/邪恶：（0~100）：影响是否会帮助弱小，是否会欺骗别人。
        self.extroversion_or_introversion = extroversion_or_introversion  # 外向/内向：（0~100）：影响是否愿意出门，是否愿意和其他人交朋友。
        self.bravery_or_cowardly = bravery_or_cowardly  # 勇敢/胆怯：（0~100）：影响是否会上战场，遇见危机的情况。
        self.rational_or_sensual = rational_or_sensual  # 理智/感性：（0~100）：影响处事方式，一个理智的国王不会因为孩子被绑架而发动战争，一个感性的会。
        self.hedonic_or_computation = hedonic_or_computation  # 享乐/计较：（0~100）：影响是否会超前消费，是否会存钱。
        self.selfish_or_generous = selfish_or_generous  # 自私/大方：（0~100）：影响其对自己的喜爱程度，是否会给朋友、孩子、父母花钱。

    def __setattr__(self, key, value):
        if key in ['wisdom', 'leadership', 'force', 'leadership', 'force', 'affinity', 'ambition', 'health',
                   'appearance', 'justice_or_evil', 'extroversion_or_introversion', 'bravery_or_cowardly',
                   'rational_or_sensual', 'hedonic_or_computation', 'selfish_or_generous']:
            if value < 0:
                value = 0
            elif value > 100:
                value = 100
        object.__setattr__(self, key, value)

    def __str__(self):
        reply = 'id:%s' % self.get_id()
        reply += '\n名字：%s' % self.name
        reply += '\n年龄：%d/%d岁' % (((datetime.now() - self.born_time).total_seconds() // (24 * 3600)), self.max_age)
        if self.die:
            reply += '（已于%s死亡）' % self.die_time.strftime('%Y-%m-%d %H:%M:%S')
            reply += '\n死亡原因：%s' % self.die_reason
        reply += '\n性别：%s，性取向：%s' % (self.gender.show(), self.sexual_orientation.show())
        reply += '\n父亲：%s，母亲：%s' % (self.father_id, self.mother_id)
        reply += '\n出生地：%s，现在所在地：%s' % (self.born_area_id, self.world_area_id)
        reply += '\n祖国：%s' % self.motherland
        reply += '\n种族：%s' % self.race_id
        reply += '\n疾病：%s' % self.disease_id
        reply += '\n职业：%s' % self.profession_id
        reply += '\n' + ('-' * 6)
        reply += '\n基础属性：'
        reply += '\n智慧：%d，领导力：%d，武力：%d，亲和力：%d，野心：%d，健康：%d，外貌：%d' % (
            self.wisdom, self.leadership, self.force, self.affinity, self.ambition, self.health, self.appearance
        )
        reply += '\n外貌描述：%s' % self.appearance_description
        reply += '\n' + ('-' * 6)
        reply += '\n性格（以下描述词越小越靠近左边的词，越大越靠近右边的词）'
        reply += '\n邪恶/正义：%d' % self.justice_or_evil
        reply += '\n内向/外向：%d' % self.extroversion_or_introversion
        reply += '\n胆怯/勇敢：%d' % self.bravery_or_cowardly
        reply += '\n感性/理智：%d' % self.rational_or_sensual
        reply += '\n节俭/享乐：%d' % self.hedonic_or_computation
        reply += '\n自私/大方：%d' % self.selfish_or_generous
        return reply

    def __repr__(self):
        return self.__str__()


####################################################################################################
class Trait:
    """
    特质，用于描述npc的性格
    """
