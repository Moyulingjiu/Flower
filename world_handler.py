# coding=utf-8
"""
世界管理器
"""
import random
from datetime import datetime, timedelta
from typing import List, Dict

import numpy as np

import flower_dao
import global_config
from global_config import logger
from model import *


def get_random_ratio(symbol: float = 1):
    return random.random() * 0.2 * symbol + 1.0


def random_kingdom_area(kingdom: Kingdom) -> WorldArea:
    if len(kingdom.area_id_list) > 0:
        area_id = random.choice(kingdom.area_id_list)
        area: WorldArea = flower_dao.select_world_area(area_id)
    else:
        area: WorldArea = random.choice(flower_dao.select_all_world_area())
    return area


def random_profession() -> Profession:
    rand = random.random()
    if rand <= 0.1:
        profession: Profession = flower_dao.select_profession_by_name('商人')
    elif rand <= 0.17:
        profession: Profession = flower_dao.select_profession_by_name('旅行商人')
    elif rand <= 0.27:
        profession: Profession = flower_dao.select_profession_by_name('农民')
    elif rand <= 0.37:
        profession: Profession = flower_dao.select_profession_by_name('渔夫')
    elif rand <= 0.38:
        profession: Profession = flower_dao.select_profession_by_name('建筑师')
    elif rand <= 0.43:
        profession: Profession = flower_dao.select_profession_by_name('猎人')
    elif rand <= 0.48:
        profession: Profession = flower_dao.select_profession_by_name('伐木工')
    elif rand <= 0.63:
        profession: Profession = flower_dao.select_profession_by_name('植物学家')
    elif rand <= 0.66:
        profession: Profession = flower_dao.select_profession_by_name('老师')
    elif rand <= 0.68:
        profession: Profession = flower_dao.select_profession_by_name('科学家')
    elif rand <= 0.73:
        profession: Profession = flower_dao.select_profession_by_name('探险家')
    elif rand <= 0.78:
        profession: Profession = flower_dao.select_profession_by_name('交易员')
    elif rand <= 0.83:
        profession: Profession = flower_dao.select_profession_by_name('工程师')
    elif rand <= 0.85:
        profession: Profession = flower_dao.select_profession_by_name('医生')
    elif rand <= 0.88:
        profession: Profession = flower_dao.select_profession_by_name('护士')
    elif rand <= 0.92:
        profession: Profession = flower_dao.select_profession_by_name('治安队')
    elif rand <= 0.95:
        profession: Profession = flower_dao.select_profession_by_name('邮递员')
    elif rand <= 0.97:
        profession: Profession = flower_dao.select_profession_by_name('小偷')
    else:
        profession: Profession = flower_dao.select_profession_by_name('无业')
    return profession


def update_world():
    """
    更新世界
    :return:
    """
    if not global_config.get_right_update_data:
        return
    now: datetime = datetime.now()
    total_number: int = flower_dao.select_all_person_number()
    alive_number: int = flower_dao.select_all_alive_person_number()
    die_number = total_number - alive_number
    profession_list: List[Profession] = flower_dao.select_all_profession()
    profession_dict: Dict[str, Profession] = {}
    for profession in profession_list:
        profession_dict[profession.get_id()] = profession
    page: int = -1
    page_size: int = 20
    logger.info('遍历所有人口，总计数量：%d，页面大小：%d' % (total_number, page_size))
    while alive_number > 0:
        alive_number -= page_size
        page += 1
        logger.info('当前页：%d，剩余人数：%d' % (page, alive_number))
        person_list: List[Person] = flower_dao.select_all_alive_person(page, page_size)
        for person in person_list:
            age: int = int((now - person.born_time).total_seconds() // global_config.day_second)
            
            # 对当前职业进行判断（如果是无业或者学生那么就有概率变成有职业的人）
            profession: Profession = profession_dict[person.profession_id]
            if not profession.valid():
                profession = random_profession()
                logger.info('npc<%s>(%s)原职业已失效获得新职业：%s' % (person.name, person.get_id(), profession.name))
            if (profession.name == '无业' or profession.name == '学生') and 25 >= age >= 20:
                profession = random_profession()
                logger.info('npc<%s>(%s)从无业或学生获得新职业：%s' % (person.name, person.get_id(), profession.name))
            elif profession.name == '无业' and age > 25:
                rand = random.random()
                if rand < 0.05:
                    profession = random_profession()
                    logger.info('npc<%s>(%s)从无业获得新职业：%s' % (person.name, person.get_id(), profession.name))
            elif 20 > age >= 7:
                profession = flower_dao.select_profession_by_name('学生')
                logger.info('npc<%s>(%s)到达上学年纪获得新职业：%s' % (person.name, person.get_id(), profession.name))
            if profession.valid():
                person.profession_id = profession.get_id()
            
            # 对适合生育年龄的人进行判断
            if 22 <= age <= 35 and person.gender == Gender.male:
                rand = random.random()
                children_number: int = len(person.children)
                # 每年有30%概率生第一胎
                if children_number < 1 and rand < 0.5:
                    new_child(person)
                elif children_number < 2 and rand < 0.3:
                    new_child(person)
                elif children_number < 3 and rand < 0.01:
                    new_child(person)
                elif rand < 0.00001:
                    new_child(person)

            # 如果年龄太大，就有概率死亡（并且不死人也不会死亡）
            if age >= person.max_age and not person.immortal:
                rand = random.random()
                if rand < 0.3:
                    person.die_time = datetime.now()
                    person.die = True
                    person.die_reason = '衰老'


def new_child(person: Person):
    area: WorldArea = flower_dao.select_world_area(person.born_area_id)
    child: Person = random_person(born_area=area, age=0)
    child_id: str = flower_dao.insert_person(child)
    person.children.append(child_id)
    logger.info('npc<%s>(%s)生了一个孩子' % (person.name, person.get_id()))


def random_generate_world() -> int:
    """
    随机生成世界
    :return: 总人口
    """
    logger.info('开始生成世界！')
    area_list: List[WorldArea] = flower_dao.select_all_world_area()
    kingdom_list: List[Kingdom] = flower_dao.select_all_kingdom()
    terrain_cache = {}
    total_population: int = 0
    for area in area_list:
        if area.terrain_id in terrain_cache:
            terrain: WorldTerrain = terrain_cache[area.terrain_id]
        else:
            terrain: WorldTerrain = flower_dao.select_world_terrain(area.terrain_id)
            terrain_cache[area.terrain_id] = terrain
        population: int = 1
        if terrain.name == '冰盖':
            population: int = 10
        elif terrain.name == '草原':
            population: int = 50
        elif terrain.name == '岛':
            population: int = 20
        elif terrain.name == '港口':
            population: int = 50
        elif terrain.name == '高原':
            population: int = 20
        elif terrain.name == '海洋':
            population: int = 0
        elif terrain.name == '禁地':
            population: int = 0
        elif terrain.name == '胡泊':
            population: int = 20
        elif terrain.name == '林地':
            population: int = 20
        elif terrain.name == '平原':
            population: int = 100
        elif terrain.name == '丘陵':
            population: int = 50
        elif terrain.name == '盆地':
            population: int = 20
        elif terrain.name == '沙漠':
            population: int = 10
        elif terrain.name == '山脉':
            population: int = 10
        elif terrain.name == '山地':
            population: int = 20
        elif terrain.name == '峡谷':
            population: int = 20
        elif terrain.name == '雨林':
            population: int = 4
        elif terrain.name == '海峡':
            population: int = 0
        logger.info('生成地区“%s”的人口“%d”' % (area.name, population))
        total_population += population
        for i in range(population):
            if random.random() < 0.9:
                rand = random.random()
                if rand <= 0.1:
                    profession: Profession = flower_dao.select_profession_by_name('商人')
                elif rand <= 0.17:
                    profession: Profession = flower_dao.select_profession_by_name('旅行商人')
                elif rand <= 0.27:
                    profession: Profession = flower_dao.select_profession_by_name('农民')
                elif rand <= 0.37:
                    profession: Profession = flower_dao.select_profession_by_name('渔夫')
                elif rand <= 0.38:
                    profession: Profession = flower_dao.select_profession_by_name('建筑师')
                elif rand <= 0.43:
                    profession: Profession = flower_dao.select_profession_by_name('猎人')
                elif rand <= 0.48:
                    profession: Profession = flower_dao.select_profession_by_name('伐木工')
                elif rand <= 0.63:
                    profession: Profession = flower_dao.select_profession_by_name('学生')
                elif rand <= 0.66:
                    profession: Profession = flower_dao.select_profession_by_name('老师')
                elif rand <= 0.68:
                    profession: Profession = flower_dao.select_profession_by_name('科学家')
                elif rand <= 0.78:
                    profession: Profession = flower_dao.select_profession_by_name('探险家')
                elif rand <= 0.83:
                    profession: Profession = flower_dao.select_profession_by_name('交易员')
                elif rand <= 0.88:
                    profession: Profession = flower_dao.select_profession_by_name('工程师')
                elif rand <= 0.9:
                    profession: Profession = flower_dao.select_profession_by_name('医生')
                elif rand <= 0.93:
                    profession: Profession = flower_dao.select_profession_by_name('护士')
                elif rand <= 0.97:
                    profession: Profession = flower_dao.select_profession_by_name('治安队')
                else:
                    profession: Profession = flower_dao.select_profession_by_name('无业')
            else:
                rand = random.random()
                if rand < 0.5:
                    profession: Profession = flower_dao.select_profession_by_name('骑士')
                elif rand < 0.8:
                    profession: Profession = flower_dao.select_profession_by_name('男爵')
                elif rand < 0.9:
                    profession: Profession = flower_dao.select_profession_by_name('子爵')
                elif rand < 0.97:
                    profession: Profession = flower_dao.select_profession_by_name('伯爵')
                elif rand < 0.99:
                    profession: Profession = flower_dao.select_profession_by_name('侯爵')
                else:
                    profession: Profession = flower_dao.select_profession_by_name('公爵')
            person: Person = random_person(born_profession=profession)
            # 如果不是学生那么不能太小
            if profession.name != '学生' and \
                    (datetime.now() - person.born_time).total_seconds() // global_config.day_second < 20:
                person.born_time = datetime.now() - timedelta(days=random.randint(20, 25))
            flower_dao.insert_person(person)
    for kingdom in kingdom_list:
        logger.info('生成国家“%s”的政要' % kingdom.name)
        profession: Profession = flower_dao.select_profession_by_name('国王')
        person: Person = random_person(
            born_area=random_kingdom_area(kingdom),
            born_profession=profession,
            min_age=20
        )
        kingdom.king_id = flower_dao.insert_person(person)
        kingdom.governance_level = person.leadership  # 治理水平
        kingdom.financial_level = person.wisdom  # 财政水平
        kingdom.military_level = person.force  # 军事水平
        flower_dao.update_kingdom(kingdom)
        profession: Profession = flower_dao.select_profession_by_name('陆军军事大臣')
        person: Person = random_person(
            born_area=random_kingdom_area(kingdom),
            born_profession=profession,
            min_age=30
        )
        flower_dao.insert_person(person)
        profession: Profession = flower_dao.select_profession_by_name('海军军事大臣')
        person: Person = random_person(
            born_area=random_kingdom_area(kingdom),
            born_profession=profession,
            min_age=30
        )
        flower_dao.insert_person(person)
        profession: Profession = flower_dao.select_profession_by_name('财政大臣')
        person: Person = random_person(
            born_area=random_kingdom_area(kingdom),
            born_profession=profession,
            min_age=50
        )
        flower_dao.insert_person(person)
        profession: Profession = flower_dao.select_profession_by_name('治理大臣')
        person: Person = random_person(
            born_area=random_kingdom_area(kingdom),
            born_profession=profession,
            min_age=50
        )
        flower_dao.insert_person(person)
        profession: Profession = flower_dao.select_profession_by_name('教育大臣')
        person: Person = random_person(
            born_area=random_kingdom_area(kingdom),
            born_profession=profession,
            min_age=50
        )
        flower_dao.insert_person(person)
        profession: Profession = flower_dao.select_profession_by_name('科技大臣')
        person: Person = random_person(
            born_area=random_kingdom_area(kingdom),
            born_profession=profession,
            min_age=50
        )
        flower_dao.insert_person(person)
        profession: Profession = flower_dao.select_profession_by_name('外交大臣')
        person: Person = random_person(
            born_area=random_kingdom_area(kingdom),
            born_profession=profession,
            min_age=50
        )
        flower_dao.insert_person(person)
        profession: Profession = flower_dao.select_profession_by_name('国安大臣')
        person: Person = random_person(
            born_area=random_kingdom_area(kingdom),
            born_profession=profession,
            min_age=50
        )
        flower_dao.insert_person(person)
        total_population += 10
    logger.info('生成世界结束！总计人口%d' % total_population)
    return total_population


def random_person(born_area: WorldArea = None, born_profession: Profession = None, age: int = -1,
                  min_age: int = 0) -> Person:
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
    if born_area is None:
        area_list: List[WorldArea] = flower_dao.select_all_world_area()
        area: WorldArea = random.choice(area_list)
    else:
        area: WorldArea = born_area
    person.born_area_id = area.get_id()
    person.world_area_id = area.get_id()
    # 有80%的概率为该地区的主要种族
    if random.randint(1, 100) > 80 or area.race_id == '':
        race_list: List[Race] = flower_dao.select_all_world_race()
        race: Race = random.choice(race_list)
        person.race_id = race.get_id()
    else:
        race: Race = flower_dao.select_world_race(area.race_id)
        person.race_id = area.race_id
    
    # 该地区所在的帝国为其祖国
    kingdom_list: List[Kingdom] = flower_dao.select_all_kingdom()
    for kingdom in kingdom_list:
        if area.get_id() in kingdom.area_id_list:
            person.motherland = kingdom.get_id()
            break
    if person.motherland == '':
        person.motherland = random.choice(kingdom_list).get_id()
    
    # 获取职业，随机职业
    if born_profession is None:
        profession_list: List[Profession] = flower_dao.select_all_profession()
        profession = random.choice(profession_list)
    else:
        profession = born_profession
    person.profession_id = profession.get_id()
    
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
    # 根据种族来特质化
    if race.name == '格克雷登':
        # 好战，游牧民族，不懂经商，武力强大但不团结
        person.force = person.force * get_random_ratio()
        person.wisdom = person.wisdom * get_random_ratio(-1)
        person.selfish_or_generous = person.selfish_or_generous * get_random_ratio(-1)
    elif race.name == '达尔伊':
        # 友善，爱好和平，务农民族，擅长防守，团结一致
        person.affinity = person.affinity * get_random_ratio()
        person.selfish_or_generous = person.selfish_or_generous * get_random_ratio()
    elif race.name == '早柠':
        # 女强男弱，勤劳有力，犹豫不决，墨守成规
        person.hedonic_or_computation = person.hedonic_or_computation * get_random_ratio()
        person.ambition = person.ambition * get_random_ratio(-1)
    elif race.name == '立渊臣':
        #  武德充沛，善于谋略，内斗，狡诈
        person.force = person.force * get_random_ratio()
        person.wisdom = person.wisdom * get_random_ratio()
        person.rational_or_sensual = person.rational_or_sensual * get_random_ratio()
        person.justice_or_evil = person.justice_or_evil * get_random_ratio(-1)
        person.ambition = person.ambition * get_random_ratio()
    elif race.name == '尼酋格':
        # 游手好闲，身体极其健壮，部落制，内斗，多为奴隶
        person.force = person.force * get_random_ratio(1.2)
        person.hedonic_or_computation = person.hedonic_or_computation * get_random_ratio()
        person.ambition = person.ambition * get_random_ratio()
    elif race.name == '浩斯特':
        # 善于经商，精明算计，身体柔弱，没有野心，贪财
        person.wisdom = person.wisdom * get_random_ratio(1.2)
        person.rational_or_sensual = person.rational_or_sensual * get_random_ratio(1.2)
    elif race.name == '梅兰尼亚':
        # 热爱征战，内部团结，不善经营，智商高，高傲
        person.wisdom = person.wisdom * get_random_ratio(1.2)
        person.bravery_or_cowardly = person.bravery_or_cowardly * get_random_ratio()
        person.leadership = person.leadership * get_random_ratio(-1)
    elif race.name == '甘星道辰':
        # 长寿亲和，智商高，与世无争，懒惰
        person.wisdom = person.wisdom * get_random_ratio(1.2)
        person.health = person.health * get_random_ratio(1.5)
        person.ambition = person.ambition * get_random_ratio(-1.5)
    elif race.name == '固彦霖':
        # 浪漫，热爱思考，爱好旅游，颜值高
        person.rational_or_sensual = person.rational_or_sensual * get_random_ratio(-1)
        person.hedonic_or_computation = person.hedonic_or_computation * get_random_ratio()
        person.appearance = person.appearance * get_random_ratio(1.5)
    elif race.name == '忏彻':
        # 不爱争斗，智商高，热爱手工制作一些机器，喜欢与外族交流
        person.wisdom = person.wisdom * get_random_ratio(1.2)
        person.extroversion_or_introversion = person.extroversion_or_introversion * get_random_ratio()
        person.bravery_or_cowardly = person.bravery_or_cowardly * get_random_ratio()
        person.affinity = person.affinity * get_random_ratio(-1.2)
    elif race.name == '魏温':
        # 文武双全，制度森明，友好，聪慧，过于谨慎，略有自卑
        person.force = person.force * get_random_ratio(0.8)
        person.wisdom = person.wisdom * get_random_ratio(0.8)
        person.affinity = person.affinity * get_random_ratio(1.2)
        person.bravery_or_cowardly = person.bravery_or_cowardly * get_random_ratio(-0.8)
    
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
    if age == -1:
        age: int = random.randint(0, person.max_age - 1)
        if age < min_age:
            age = min_age
    if person.max_age < age:
        person.max_age = age + 5
    person.born_time = datetime.now() - timedelta(days=age)
    return person
