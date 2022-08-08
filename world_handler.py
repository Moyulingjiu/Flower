# coding=utf-8
"""
世界管理器
"""
import random

from global_config import logger
from model import *


def update_world():
    """
    更新世界
    :return:
    """
    logger.info('开始更新世界')


def random_person() -> Person:
    """
    随机生成一个人物
    """
    person: Person = Person()
    person.gender = random.choice([Gender.male, Gender.female])
    # 有3%的概率性取向异常
    if random.randint(0, 100) > 96:
        person.sexual_orientation = random.choice([Gender.male, Gender.female, Gender.intersex])
    else:
        if person.gender == Gender.female:
            person.sexual_orientation = Gender.male
        else:
            person.sexual_orientation = Gender.female
    person.wisdom = random.randint(0, 101)
    person.leadership = random.randint(0, 101)
    person.force = random.randint(0, 101)
    person.affinity = random.randint(0, 101)
    person.ambition = random.randint(0, 101)
    person.wisdom = random.randint(0, 101)
    return person
