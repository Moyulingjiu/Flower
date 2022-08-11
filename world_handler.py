# coding=utf-8
"""
世界管理器
"""
import random
from typing import List

import flower_dao
import global_config
from global_config import logger
from model import *


def update_world():
    """
    更新世界
    :return:
    """
    if not global_config.get_right_update_data:
        return
    logger.info('开始更新世界')


def random_generate_world():
    """
    随机生成世界
    :return:
    """


def random_person() -> Person:
    """
    随机凭空生成一个人物（没有父母）
    """
    area_list: List[WorldArea] = flower_dao.select_all_world_area()
    person: Person = Person()
    person.gender = random.choice([Gender.male, Gender.female])
    # 有3%的概率性取向异常
    if random.randint(0, 100) > 95:
        person.sexual_orientation = random.choice([Gender.male, Gender.female, Gender.intersex])
    else:
        if person.gender == Gender.female:
            person.sexual_orientation = Gender.male
        else:
            person.sexual_orientation = Gender.female
    # 赋予姓名
    last_name_list: List[PersonLastName] = flower_dao.select_all_person_last_name()
    person_name: PersonName = flower_dao.select_random_person_name(Gender.male)
    person.name = random.choice(last_name_list).value + person_name.value
    
    # 出生地
    area = random.choice(area_list)
    person.born_area_id = area.get_id()
    person.world_area_id = area.get_id()
    # 角色的各项属性
    person.wisdom = random.randint(0, 101)
    person.leadership = random.randint(0, 101)
    person.force = random.randint(0, 101)
    person.affinity = random.randint(0, 101)
    person.ambition = random.randint(0, 101)
    person.health = random.randint(0, 101)
    person.appearance = random.randint(0, 101)
    # 角色的性格
    person.justice_or_evil = random.randint(0, 101)
    person.extroversion_or_introversion = random.randint(0, 101)
    person.bravery_or_cowardly = random.randint(0, 101)
    person.rational_or_sensual = random.randint(0, 101)
    person.hedonic_or_computation = random.randint(0, 101)
    person.selfish_or_generous = random.randint(0, 101)
    # 根据健康值来确定角色的最大年龄
    if person.health < 20:
        person.max_age = random.randint(1, 30)
    elif person.health < 40:
        person.max_age = random.randint(20, 60)
    elif person.health < 60:
        person.max_age = random.randint(40, 90)
    elif person.health < 80:
        person.max_age = random.randint(60, 100)
    else:
        person.max_age = random.randint(60, 125)
    return person
