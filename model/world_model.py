# coding=utf-8
"""
存储与世界PCG演化相关的模型
"""
from enum import Enum
from typing import Tuple

from model.base_model import *


class Disease(Enum):
    """
    疾病枚举类
    """

    none = 0

    @classmethod
    def view_level(cls, disease) -> str:
        pass

    @classmethod
    def get_level(cls, disease: str):
        pass


class Profession(Enum):
    """
    职业类
    """

    none = 0

    @classmethod
    def view_level(cls, profession) -> str:
        pass

    @classmethod
    def get_level(cls, profession: str):
        pass


class Race(Enum):
    """
    种族类
    """

    @classmethod
    def view_level(cls, race) -> str:
        pass

    @classmethod
    def get_level(cls, race: str):
        pass


class WorldArea(EntityClass):
    """
    世界地区
    """

    def __init__(self, name: str = '',
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)

        self.name = name  # 地区名


class Kingdom(EntityClass):
    """
    王国
    """

    def __init__(self, name: str = '',
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)

        self.name = name  # 王国名


class Relationship(EntityClass):
    """
    人际关系
    人物src_person->des_person的好感为value，value为0表示不喜欢也不讨厌，小于0讨厌，大于0喜欢
    """

    def __init__(self, src_person: str = '', des_person: str = '', value: int = 0,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
        self.src_person = src_person  # 人物1
        self.des_person = des_person  # 人物2
        self.value = value  # 关系水平


class Gender(Enum):
    """
    性别
    """

    male = 0  # 男
    female = 1  # 女
    intersex = 2  # 双性
    unknown = 3  # 未知


class Person(EntityClass):
    """
    人物模型
    """

    def __init__(self, name: str = '', gender: Gender = Gender.male, sexual_orientation: Gender = Gender.female,
                 spouse_id: str = '', predecessor: List[Tuple[str, datetime]] = None, relationships: List[str] = None,
                 children: List[str] = None, father_id: str = '', mother_id: str = '',
                 world_area_id: str = '', born_area_id: str = '', born_time: datetime = datetime.now(),
                 gold: int = 0, disease: Disease = Disease.none, profession: Profession = Profession.none,
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

        self.gold = gold  # 金币
        self.disease = disease  # 疾病
        self.profession = profession  # 职业

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


####################################################################################################
class Trait:
    """
    特质，用于描述npc的性格
    """
