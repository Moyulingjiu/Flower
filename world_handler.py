# coding=utf-8
"""
世界管理器
"""
import random
from datetime import datetime, timedelta
from typing import List

import numpy as np

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

    # 给予身高
    if person.gender == Gender.male:
        person.height = random.random() * (2.1 - 1.5) + 1.5
    else:
        person.height = random.random() * (1.9 - 1.3) + 1.3
    # 有30%的概率过瘦或肥胖
    if random.randint(1, 100) >= 70:
        bmi: float = random.random() * (35 - 15) + 15
    else:
        bmi: float = random.random() * (27 - 18) + 18
    person.weight = bmi * (person.height * person.height)

    # 出生地
    area_list: List[WorldArea] = flower_dao.select_all_world_area()
    area: WorldArea = random.choice(area_list)
    person.born_area_id = area.get_id()
    person.world_area_id = area.get_id()
    # 有80%的概率为该地区的主要种族
    if random.randint(1, 100) > 80 or area.race_id == '':
        race_list: List[Race] = flower_dao.select_all_world_race()
        race: Race = random.choice(race_list)
        person.race_id = race.get_id()
    else:
        person.race_id = area.race_id
    # 该地区所在的帝国为其祖国
    kingdom_list: List[Kingdom] = flower_dao.select_all_kingdom()
    for kingdom in kingdom_list:
        if area.get_id() in kingdom.area_id_list:
            person.motherland = kingdom.get_id()
            break
    if person.motherland == '':
        person.motherland = random.choice(kingdom_list).get_id()

    # 角色的各项属性
    person.wisdom = int(np.random.normal(50, 15, 1)[0])
    person.leadership = int(np.random.normal(50, 15, 1)[0])
    person.force = int(np.random.normal(50, 15, 1)[0])
    person.affinity = int(np.random.normal(50, 15, 1)[0])
    person.ambition = int(np.random.normal(50, 15, 1)[0])
    person.health = int(np.random.normal(50, 15, 1)[0])
    person.appearance = int(np.random.normal(50, 15, 1)[0])
    # 角色的性格
    person.justice_or_evil = int(np.random.normal(50, 15, 1)[0])
    person.extroversion_or_introversion = int(np.random.normal(50, 15, 1)[0])
    person.bravery_or_cowardly = int(np.random.normal(50, 15, 1)[0])
    person.rational_or_sensual = int(np.random.normal(50, 15, 1)[0])
    person.hedonic_or_computation = int(np.random.normal(50, 15, 1)[0])
    person.selfish_or_generous = int(np.random.normal(50, 15, 1)[0])
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
    age: int = random.randint(0, person.max_age - 1)
    person.born_time = datetime.now() - timedelta(days=age)
    return person
