# coding=utf-8
import copy
import random
from datetime import timedelta, datetime
from typing import Dict, List, Tuple

import flower_dao
import global_config
import util
import weather_getter
from flower_exceptions import *
from global_config import logger
from model import *
from util import UserRight, async_function


def handle(message: str, qq: int, username: str, bot_qq: int, bot_name: str, at_list: List[int]) -> Result:
    """
    入口函数
    :param message: 消息
    :param qq: qq号
    :param username: 用户名
    :param bot_qq: 机器人qq号
    :param bot_name: 机器人名
    :param at_list: @列表
    :return: 结果
    """
    try:
        # 处理上下文需要加锁，避免两个线程同时处理到一个上下文
        flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
        context_handler: ContextHandler = ContextHandler()
        result: Result = context_handler.handle(message, qq, username, bot_qq, bot_name, at_list)
        # 如果阻断传播就已经可以停止了
        if (len(result.context_reply_text) != 0 or len(
                result.context_reply_image) != 0) and context_handler.block_transmission:
            return result
        flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
        
        if len(at_list) == 0:
            # 数据查询部分
            if message[:4] == '查询城市' and message[4:].strip() != '':
                reply = FlowerService.query_city(message[4:].strip())
                result.reply_text.append(reply)
                return result
            elif message[:4] == '查询土壤' and message[4:].strip() != '':
                reply = FlowerService.query_soil(message[4:].strip())
                result.reply_text.append(reply)
                return result
            elif message[:3] == '查询花' and message[3:].strip() != '':
                reply = FlowerService.query_flower(message[3:].strip())
                result.reply_text.append(reply)
                return result
            elif message == '花店数据':
                reply = FlowerService.view_user_data(qq, username)
                result.reply_text.append(reply)
                return result
            elif message[:4] == '花店仓库':
                data = message[4:].strip()
                page = 0
                if data != '':
                    try:
                        page = int(data)
                    except ValueError:
                        raise TypeException('格式错误，格式“花店仓库【页码】”')
                reply, description = FlowerService.view_warehouse(qq, username, page)
                result.reply_text.append(reply)
                if description != '':
                    result.reply_text.append(description)
                return result
            elif message[:4] == '花店物品':
                data = message[4:].strip()
                reply = FlowerService.view_item(data)
                result.reply_text.append(reply)
                return result
            elif message[:4] == '花店天气':
                data = message[4:].strip()
                reply = FlowerService.view_weather(data)
                result.reply_text.append(reply)
                return result
            elif message == '花店农场设备':
                reply = FlowerService.view_user_farm_equipment(qq, username)
                result.reply_text.append(reply)
                return result
            elif message == '花店农场':
                reply = FlowerService.view_user_farm(qq, username)
                result.reply_text.append(reply)
                return result
            elif message == '花店信箱':
                reply = FlowerService.view_mailbox(qq, username)
                result.reply_text.append(reply)
                return result
            elif message[:4] == '花店信箱':
                try:
                    index = int(message[4:].strip())
                    reply = FlowerService.view_mail(qq, username, index)
                    result.reply_text.append(reply)
                    return result
                except ValueError:
                    raise TypeException('格式错误！格式“花店信箱 【序号】”，省略序号查看整个信箱')
            
            # 操作部分
            elif message == '初始化花店':
                reply = FlowerService.init_user(qq, username)
                result.reply_text.append(reply)
                return result
            elif message == '领取花店初始礼包':
                reply = FlowerService.receive_beginner_gifts(qq, username)
                result.reply_text.append(reply)
                return result
            elif message == '花店签到':
                reply = FlowerService.user_sign_in(qq, username)
                result.reply_text.append(reply)
                return result
            elif message[:2] == '转账':
                data: str = message[2:]
                if len(at_list) == 0:
                    raise AtListNullException('没有转账对象呢')
                try:
                    origin_gold: float = float(data)
                    origin_gold *= 100.0
                    gold: int = int(origin_gold)
                except ValueError:
                    raise TypeException('格式错误，格式“@xxx 转账 【数字】”')
                reply = FlowerService.transfer_accounts(qq, username, at_list, gold)
                result.reply_text.append(reply)
                return result
            elif message[:2] == '使用':
                data = message[2:]
                try:
                    flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
                    user: User = util.get_user(qq, username)
                    item: DecorateItem = util.analysis_item(data)
                    if (item.item_type == ItemType.flower and item.flower_quality != FlowerQuality.perfect) or (
                            item.max_durability > 0 and item.durability == 0) or item.rot_second > 0 or \
                            item.item_type == ItemType.accelerate:
                        item_list: List[DecorateItem] = util.find_items(user.warehouse, item.item_name)
                        choices: Dict[str, Choice] = {}
                        if len(item_list) > 1:
                            similar_items_name: List[DecorateItem] = []
                            reply = '你的仓库有多件相似物品，可能为以下物品：'
                            index: int = 0
                            for warehouse_item in item_list:
                                if warehouse_item not in similar_items_name:
                                    index += 1
                                    reply += '\n%d.' % index + warehouse_item.show_without_number()
                                    item.flower_quality = warehouse_item.flower_quality
                                    item.durability = warehouse_item.durability
                                    item.hour = warehouse_item.hour
                                    args = {
                                        'qq': qq,
                                        'username': username,
                                        'item': copy.deepcopy(item)
                                    }
                                    choices[str(index)] = Choice(args=args, callback=FlowerService.use_item)
                                    similar_items_name.append(warehouse_item)
                            reply += '\n请输入对应的序号，选择是哪一种物品。例如输入“1”选择第一种的物品。其余任意输入取消'
                            if len(similar_items_name) > 1:
                                flower_dao.insert_context(qq, ChooseContext(choices=choices))
                                result.reply_text.append(reply)
                                return result
                        # 如果只有一件物品，那么丢弃的应该是这件物品
                        item.durability = item_list[0].durability
                        item.flower_quality = item_list[0].flower_quality
                        item.hour = item_list[0].hour
                    flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
                    reply = FlowerService.use_item(qq, username, item)
                    result.reply_text.append(reply)
                    return result
                except TypeException:
                    raise TypeException('格式错误，格式“使用 【物品名字】 【数量】”')
                except ItemNotFoundException:
                    raise TypeException('该物品不存在！')
            elif message[:2] == '丢弃':
                data = message[2:]
                try:
                    flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
                    user: User = util.get_user(qq, username)
                    item: DecorateItem = util.analysis_item(data)
                    if (item.item_type == ItemType.flower and item.flower_quality != FlowerQuality.perfect) or (
                            item.max_durability > 0 and item.durability == 0) or item.rot_second > 0:
                        item_list: List[DecorateItem] = util.find_items(user.warehouse, item.item_name)
                        choices: Dict[str, Choice] = {}
                        if len(item_list) > 1:
                            similar_items_name: List[DecorateItem] = []
                            reply = '你的仓库有多件相似物品，可能为以下物品：'
                            index: int = 0
                            for warehouse_item in item_list:
                                if warehouse_item not in similar_items_name:
                                    index += 1
                                    reply += '\n%d.' % index + warehouse_item.show_without_number()
                                    item.flower_quality = warehouse_item.flower_quality
                                    item.durability = warehouse_item.durability
                                    args = {
                                        'qq': qq,
                                        'username': username,
                                        'item': copy.deepcopy(item)
                                    }
                                    choices[str(index)] = Choice(args=args, callback=FlowerService.throw_item)
                                    similar_items_name.append(warehouse_item)
                            reply += '\n请输入对应的序号，选择是哪一种物品。例如输入“1”选择第一种的物品。其余任意输入取消'
                            if len(similar_items_name) > 1:
                                flower_dao.insert_context(qq, ChooseContext(choices=choices))
                                result.reply_text.append(reply)
                                return result
                        # 如果只有一件物品，那么丢弃的应该是这件物品
                        item.durability = item_list[0].durability
                        item.flower_quality = item_list[0].flower_quality
                    flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
                    reply = FlowerService.throw_item(qq, username, item)
                    result.reply_text.append(reply)
                    return result
                except TypeException:
                    raise TypeException('格式错误，格式“丢弃 【物品名字】 【数量】”')
                except ItemNotFoundException:
                    raise TypeException('该物品不存在！')
            elif message == '清空花店仓库':
                reply = FlowerService.throw_all_items(qq, username)
                result.reply_text.append(reply)
                return result
            elif message[:2] == '种植':
                data = message[2:].strip()
                reply = FlowerService.plant_flower(qq, username, data)
                result.reply_text.append(reply)
                return result
            elif message[:2] == '浇水':
                data = message[2:].strip()
                try:
                    if len(data) > 0:
                        multiple: int = int(data)
                    else:
                        multiple: int = 1
                    reply = FlowerService.watering(qq, username, multiple)
                    result.reply_text.append(reply)
                    return result
                except ValueError:
                    raise TypeException('格式错误，格式“浇水 【次数】”。次数可以省略，默认一次。')
            elif message == '收获':
                reply = FlowerService.reward_flower(qq, username)
                result.reply_text.append(reply)
                return result
            elif message == '铲除花':
                reply = FlowerService.remove_flower(qq, username)
                result.reply_text.append(reply)
                return result
            elif message[:6] == '设置花店昵称':
                new_username = message[6:].strip()
                if len(new_username) == 0 or '_' in new_username:
                    raise TypeException('格式错误！格式“设置花店昵称 【新的昵称】”')
                system_data: SystemData = flower_dao.select_system_data()
                for word in system_data.username_screen_words:
                    if word in new_username:
                        raise TypeException('名字中含有违禁词或敏感词汇')
                reply = FlowerService.change_username(qq, username, new_username)
                result.reply_text.append(reply)
                return result
            elif message == '清除花店昵称':
                reply = FlowerService.clear_username(qq, username)
                result.reply_text.append(reply)
                return result
            elif message == '整理仓库':
                flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
                user: User = util.get_user(qq, username)
                util.sort_items(user.warehouse)
                flower_dao.update_user_by_qq(user)
                reply = '整理完成'
                result.reply_text.append(reply)
                return result
            elif message[:4] == '删除信件':
                try:
                    index = int(message[4:].strip())
                    reply = FlowerService.delete_mail(qq, username, index)
                    result.reply_text.append(reply)
                    return result
                except ValueError:
                    raise TypeException('格式错误！格式“删除信件 【序号】”')
            elif message == '清空信箱':
                reply = FlowerService.clear_mailbox(qq, username)
                result.reply_text.append(reply)
                return result
            elif message[:4] == '领取附件':
                try:
                    index = int(message[4:].strip())
                    reply = FlowerService.receive_appendix_mail(qq, username, index)
                    result.reply_text.append(reply)
                    return result
                except ValueError:
                    raise TypeException('格式错误！格式“领取附件 【序号】”，领取某一封信的附件')
        
        # 管理员操作
        if util.get_user_right(qq) == UserRight.ADMIN:
            reply: str = AdminHandler.handle(message, qq, username, at_list)
            if reply != '':
                result.reply_text.append(reply)
                return result
    except UserNotRegisteredException:
        return Result.init(reply_text='您还未初始化花店账号，请输入“初始化花店”进行初始化')
    except ResBeLockedException:
        logger.warning('用户被锁定%s<%d>@%s<%d>' % (username, qq, bot_name, bot_qq))
        return Result.init(
            reply_text='操作超时，请稍后再试\n出现的原因可能有：\n1.您的操作过于频繁，请稍后再试\n2.账号风险行为，耐心等待两小时重置\n3.网络波动')
    except AtListNullException as e:
        return Result.init(reply_text=e.message)
    except TypeException as e:
        return Result.init(reply_text=e.message)
    except PageOutOfRangeException as e:
        return Result.init(reply_text=e.message)
    except ItemNotFoundException as e:
        logger.error(e.message)
        return Result.init(reply_text='严重内部错误，请及时通知官方：\n%s' % e.message)
    except TypeError as e:
        logger.error(e)
        return Result.init()
    finally:
        flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
    return Result.init()


class AdminHandler:
    """
    管理员指令处理器
    """
    
    @classmethod
    def handle(cls, message: str, qq: int, username: str, at_list: List[int]) -> str:
        if message[:4] == '给予金币':
            data: str = message[4:].strip()
            try:
                origin_gold: float = float(data)
                origin_gold *= 100.0
                gold: int = int(origin_gold)
            except ValueError:
                raise TypeException('格式错误，格式“@xxx 给予金币 【数字】”')
            update_number: int = 0
            if len(at_list) == 0:
                if cls.give_gold(qq, qq, gold):
                    update_number += 1
            else:
                for target_qq in at_list:
                    if cls.give_gold(target_qq, qq, gold):
                        update_number += 1
            if update_number > 0:
                return '成功给予金币给' + str(update_number) + '人'
            else:
                return '未能给予任何人金币'
        elif message[:4] == '给予物品':
            data: str = message[4:].strip()
            try:
                item: DecorateItem = util.analysis_item(data)
                if item.number < 1:
                    raise TypeException(
                        '格式错误，格式“@xxx 给予物品 【物品名字】 【数量】 （【小时】/【耐久度】/【花的品质】）”。数量需要大于0')
            except TypeException:
                raise TypeException(
                    '格式错误，格式“@xxx 给予物品 【物品名字】 【数量】 （【小时】/【耐久度】/【花的品质】）”。加速卡要跟小时，如果物品有耐久度，请跟耐久，如果有品质请跟品质，如果都没有省略')
            except ItemNotFoundException:
                raise TypeException('该物品不存在！')
            update_number: int = 0
            if len(at_list) == 0:
                if cls.give_item(qq, qq, item):
                    update_number += 1
            else:
                for target_qq in at_list:
                    if cls.give_item(target_qq, qq, item):
                        update_number += 1
            if update_number > 0:
                return '成功给予' + item.item_name + '给' + str(update_number) + '人'
            else:
                return '未能给予任何人' + item.item_name
        elif message[:4] == '修改湿度':
            data: str = message[4:].strip()
            try:
                humidity: float = float(data)
                if humidity > global_config.soil_max_humidity or humidity < global_config.soil_min_humidity:
                    raise TypeException('格式错误！湿度范围为%.2f~%.2f' % (
                        global_config.soil_min_humidity,
                        global_config.soil_max_humidity
                    ))
                update_number: int = 0
                if len(at_list) == 0:
                    if cls.edit_humidity_nutrition(qq, qq, humidity=humidity):
                        update_number += 1
                else:
                    for target_qq in at_list:
                        if cls.edit_humidity_nutrition(target_qq, qq, humidity=humidity):
                            update_number += 1
                if update_number > 0:
                    return '成功修改' + str(update_number) + '人'
                return '未能修改任何人的湿度'
            except ValueError:
                raise TypeException('格式错误！，格式“@xxx 修改湿度 【湿度】”。湿度为任意小数。')
        elif message[:4] == '修改营养':
            data: str = message[4:].strip()
            try:
                nutrition: float = float(data)
                if nutrition > global_config.soil_max_nutrition or nutrition < global_config.soil_min_nutrition:
                    raise TypeException('格式错误！营养范围为%.2f~%.2f' % (
                        global_config.soil_min_nutrition,
                        global_config.soil_max_nutrition
                    ))
                update_number: int = 0
                if len(at_list) == 0:
                    if cls.edit_humidity_nutrition(qq, qq, nutrition=nutrition):
                        update_number += 1
                else:
                    for target_qq in at_list:
                        if cls.edit_humidity_nutrition(target_qq, qq, nutrition=nutrition):
                            update_number += 1
                if update_number > 0:
                    return '成功修改' + str(update_number) + '人'
                return '未能修改任何人的营养'
            except ValueError:
                raise TypeException('格式错误！，格式“@xxx 修改营养 【营养】”。营养为任意小数。')
        elif message[:4] == '修改土壤':
            data: str = message[4:].strip()
            if len(data) == 0:
                raise TypeException('格式错误！格式“@xxx 修改土壤 【土壤名】”')
            soil: Soil = flower_dao.select_soil_by_name(data)
            if not soil.valid():
                raise TypeException('土壤' + data + '不存在')
            update_number: int = 0
            if len(at_list) == 0:
                if cls.edit_soil(qq, qq, soil_id=soil.get_id()):
                    update_number += 1
            else:
                for target_qq in at_list:
                    if cls.edit_soil(target_qq, qq, soil_id=soil.get_id()):
                        update_number += 1
            if update_number > 0:
                return '成功修改' + str(update_number) + '人的土壤到' + data
            return '未能修改任何人的土壤'
        elif message[:4] == '修改城市':
            data: str = message[4:].strip()
            if len(data) == 0:
                raise TypeException('格式错误！格式“@xxx 修改城市 【城市名】”')
            city: City = flower_dao.select_city_by_name(data)
            if not city.valid():
                raise TypeException('城市' + data + '不存在')
            update_number: int = 0
            if len(at_list) == 0:
                if cls.edit_city(qq, qq, city_id=city.get_id()):
                    update_number += 1
            else:
                for target_qq in at_list:
                    if cls.edit_city(target_qq, qq, city_id=city.get_id()):
                        update_number += 1
            if update_number > 0:
                return '成功修改' + str(update_number) + '人的城市到' + data
            return '未能修改任何人的城市'
        elif message[:4] == '修改气候':
            data: str = message[4:].strip()
            if len(data) == 0:
                raise TypeException('格式错误！格式“@xxx 修改气候 【气候名】”')
            climate: Climate = flower_dao.select_climate_by_name(data)
            if not climate.valid():
                raise TypeException('气候' + data + '不存在')
            update_number: int = 0
            if len(at_list) == 0:
                if cls.edit_climate(qq, qq, climate_id=climate.get_id()):
                    update_number += 1
            else:
                for target_qq in at_list:
                    if cls.edit_climate(target_qq, qq, climate_id=climate.get_id()):
                        update_number += 1
            if update_number > 0:
                return '成功修改' + str(update_number) + '人的农场气候到' + data
            return '未能修改任何人的农场气候'
        elif message == '移除农场的花':
            update_number: int = 0
            if len(at_list) == 0:
                if cls.remove_farm_flower(qq, qq):
                    update_number += 1
            else:
                for target_qq in at_list:
                    if cls.remove_farm_flower(target_qq, qq):
                        update_number += 1
            if update_number > 0:
                return '成功移除' + str(update_number) + '人农场的花'
            return '未能移除任何人农场的花'
        elif message[:10] == '添加花店用户名屏蔽词':
            word: str = message[10:].strip()
            if cls.append_username_screen_word(word):
                return '添加成功'
            return '添加失败，已有相同词汇或网络波动'
        elif message[:10] == '删除花店用户名屏蔽词':
            word: str = message[10:].strip()
            if cls.remove_username_screen_word(word):
                return '删除成功'
            return '删除失败，没有该词汇或网络波动'
        elif message[:10] == '查看花店用户名屏蔽词':
            data: str = message[10:].strip()
            try:
                if len(data) > 0:
                    page: int = int(data) - 1
                else:
                    page = 0
                reply = ''
                index = 0
                page_size = 20
                system_data: SystemData = flower_dao.select_system_data()
                for word in system_data.username_screen_words:
                    index += 1
                    if page * page_size <= index - 1 < (page + 1) * page_size:
                        reply += str(index) + '. ' + word + '\n'
                total_page = index // page_size
                if index % page_size > 0:
                    total_page += 1
                reply += '------\n当前页码：' + str(page + 1) + '，总计页码：' + str(total_page)
                if page >= total_page:
                    return '页码超限，总计页码：' + str(total_page)
                return reply
            except ValueError:
                raise TypeException('格式错误！格式“查看花店用户名屏蔽词 【页码】”。页码可省略。')
        elif message[:4] == '农场加速':
            data = message[4:]
            try:
                hour = int(data)
                update_number: int = 0
                if len(at_list) == 0:
                    if cls.accelerate_farm(qq, qq, hour):
                        update_number += 1
                else:
                    for target_qq in at_list:
                        if cls.accelerate_farm(target_qq, qq, hour):
                            update_number += 1
                if update_number > 0:
                    return '成功加速' + str(update_number) + '人的农场'
                return '未能加速任何人的农场'
            except ValueError:
                raise TypeException('格式错误！格式“农场加速 【小时】”。')
        elif message[:4] == '农场完美加速':
            data = message[4:]
            try:
                hour = int(data)
                update_number: int = 0
                if len(at_list) == 0:
                    if cls.perfect_accelerate_farm(qq, qq, hour):
                        update_number += 1
                else:
                    for target_qq in at_list:
                        if cls.perfect_accelerate_farm(target_qq, qq, hour):
                            update_number += 1
                if update_number > 0:
                    return '成功完美加速' + str(update_number) + '人的农场'
                return '未能完美加速任何人的农场'
            except ValueError:
                raise TypeException('格式错误！格式“农场完美加速 【小时】”。')
        elif message == '花店数据':
            if len(at_list) != 1:
                raise TypeException('格式错误！格式“@xxx 花店数据”')
            try:
                return FlowerService.view_user_data(at_list[0], '')
            except UserNotRegisteredException:
                return '对方未注册'
        elif message[:4] == '花店仓库':
            if len(at_list) != 1:
                raise TypeException('格式错误！格式“@xxx 花店仓库 【页码】”，页码为1可以省略')
            try:
                data: str = message[6:].strip()
                if len(data) == 0:
                    page: int = 0
                else:
                    page: int = int(data)
                reply, _ = FlowerService.view_warehouse(at_list[0], '', page, remove_description=False)
                return reply
            except ValueError:
                raise TypeException('格式错误！格式“@xxx 花店仓库 【页码】”，页码为1可以省略')
            except UserNotRegisteredException:
                return '对方未注册'
        elif message == '花店农场':
            if len(at_list) != 1:
                raise TypeException('格式错误，格式“@xxx 查看花店农场”，必须并且只能艾特一人')
            try:
                return FlowerService.view_user_farm(at_list[0], '')
            except UserNotRegisteredException:
                return '对方未注册'
        elif message == '花店农场设备':
            if len(at_list) != 1:
                raise TypeException('格式错误，格式“@xxx 查看花店农场设备”，必须并且只能艾特一人')
            try:
                return FlowerService.view_user_farm_equipment(at_list[0], '')
            except UserNotRegisteredException:
                return '对方未注册'
        elif message == '花店信箱':
            if len(at_list) != 1:
                raise TypeException('格式错误，格式“@xxx 花店信箱 【序号】”，省略序号查看整个信箱，必须并且只能艾特一人')
            try:
                return FlowerService.view_mailbox(at_list[0], '')
            except UserNotRegisteredException:
                return '对方未注册'
        elif message[:4] == '花店信箱':
            if len(at_list) != 1:
                raise TypeException('格式错误，格式“@xxx 花店信箱 【序号】”，省略序号查看整个信箱，必须并且只能艾特一人')
            try:
                index = int(message[4:].strip())
                return FlowerService.view_mail(at_list[0], '', index)
            except UserNotRegisteredException:
                return '对方未注册'
            except ValueError:
                raise TypeException('格式错误，格式“@xxx 花店信箱 【序号】”，省略序号查看整个信箱，必须并且只能艾特一人')
        elif message == '发送信件':
            context: AdminSendMailContext = AdminSendMailContext()
            flower_dao.insert_context(qq, context)
            return '请问信件的标题是什么？只可以包含文字。'
        elif message == '更新所有城市天气':
            @async_function
            def get_all_weather():
                logger.info('管理员%s<%d>开始更新所有城市天气' % (username, qq))
                util.get_all_weather()
            
            if global_config.get_all_weather:
                return '请勿重复发起获取请求，已经有更新请求正在运行，该行为会花费较长时间。'
            global_config.get_all_weather = True
            get_all_weather()
            return '预计需要3~5分钟获取爬取所有城市天气。该命令用于没有24小时运行时的手动更新，正常运行下请勿使用该命令！！！以免造成资源浪费'
        elif message == '更新所有城市天气的状态':
            if global_config.get_all_weather:
                return '线程仍然在进行“爬取所有城市天气”的活动'
            return '当前没有进行“爬取所有城市天气”'
        elif message == '发送公告':
            announcement_context: AnnouncementContext = AnnouncementContext()
            flower_dao.insert_context(qq, announcement_context)
            return '请问公告的正文是什么，只可以包含文字信息！'
        return ''
    
    @classmethod
    def give_gold(cls, qq: int, operator_id: int, gold: int) -> bool:
        """
        给予金币
        :param qq: qq号
        :param operator_id: 操作员id
        :param gold: 金币数量（单位：0.01）
        :return:
        """
        flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
        try:
            user: User = util.get_user(qq, '')
            user.gold += gold
            user.update(operator_id)
            flower_dao.update_user_by_qq(user)
            return True
        except UserNotRegisteredException:
            return False
        finally:
            flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
    
    @classmethod
    def give_item(cls, qq: int, operator_id: int, item: DecorateItem) -> bool:
        flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
        try:
            user: User = util.get_user(qq, '')
            util.insert_items(user.warehouse, [item])
            user.update(str(operator_id))
            flower_dao.update_user_by_qq(user)
            return True
        except UserNotRegisteredException:
            return False
        except ItemNotFoundException:
            return False
        except ItemNegativeNumberException:
            return False
        except WareHouseSizeNotEnoughException:
            return False
        finally:
            flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
    
    @classmethod
    def edit_humidity_nutrition(cls, qq: int, operator_id: int, humidity: float = -1.0,
                                nutrition: float = -1.0) -> bool:
        try:
            flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
            user: User = util.get_user(qq, '')
            if humidity >= 0.0:
                user.farm.humidity = humidity
            if nutrition >= 0.0:
                user.farm.nutrition = nutrition
            user.update(operator_id)
            flower_dao.update_user_by_qq(user)
            return True
        except UserNotRegisteredException:
            return False
        finally:
            flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
    
    @classmethod
    def edit_city(cls, qq: int, operator_id: int, city_id: str) -> bool:
        """
        修改城市
        :param qq: qq
        :param operator_id: 操作人员id
        :param city_id: 城市id
        :return: 结果
        """
        try:
            flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
            user: User = util.get_user(qq, '')
            user.city_id = city_id
            user.update(operator_id)
            flower_dao.update_user_by_qq(user)
            return True
        except UserNotRegisteredException:
            return False
        finally:
            flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
    
    @classmethod
    def edit_soil(cls, qq: int, operator_id: int, soil_id: str) -> bool:
        """
        修改土壤
        :param qq: qq
        :param operator_id: 操作人员id
        :param soil_id: 土壤id
        :return: 结果
        """
        try:
            flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
            user: User = util.get_user(qq, '')
            user.farm.soil_id = soil_id
            user.update(operator_id)
            flower_dao.update_user_by_qq(user)
            return True
        except UserNotRegisteredException:
            return False
        finally:
            flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
    
    @classmethod
    def edit_climate(cls, qq: int, operator_id: int, climate_id: str) -> bool:
        """
        修改土壤
        :param qq: qq
        :param operator_id: 操作人员id
        :param climate_id: 气候id
        :return: 结果
        """
        try:
            flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
            user: User = util.get_user(qq, '')
            user.farm.climate_id = climate_id
            user.update(operator_id)
            flower_dao.update_user_by_qq(user)
            return True
        except UserNotRegisteredException:
            return False
        finally:
            flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
    
    @classmethod
    def remove_farm_flower(cls, qq: int, operator_id: int) -> bool:
        try:
            flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
            user: User = util.get_user(qq, '')
            user.farm.flower_id = ''
            user.update(operator_id)
            flower_dao.update_user_by_qq(user)
            return True
        except UserNotRegisteredException:
            return False
        finally:
            flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
    
    @classmethod
    def append_username_screen_word(cls, screen_word: str) -> bool:
        # 对于系统数据是没有加锁的（因为管理员操作缓慢，系统设计只有一个管理员）
        system_data: SystemData = flower_dao.select_system_data()
        if screen_word not in system_data.username_screen_words:
            system_data.username_screen_words.append(screen_word)
            flower_dao.update_system_data(system_data)
            return True
        return False
    
    @classmethod
    def remove_username_screen_word(cls, screen_word: str) -> bool:
        # 对于系统数据是没有加锁的（因为管理员操作缓慢，系统设计只有一个管理员）
        system_data: SystemData = flower_dao.select_system_data()
        if screen_word in system_data.username_screen_words:
            system_data.username_screen_words.remove(screen_word)
            flower_dao.update_system_data(system_data)
            return True
        return False
    
    @classmethod
    def accelerate_farm(cls, qq: int, operator_id: int, hour: int) -> bool:
        """
        加速农场
        :param qq: qq
        :param operator_id: 操作员id
        :param hour: 小时数
        :return: 结果
        """
        try:
            flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
            user: User = util.get_user(qq, '')
            user.farm.last_check_time -= timedelta(hours=hour)
            user.update(operator_id)
            flower_dao.update_user_by_qq(user)
            return True
        except UserNotRegisteredException:
            return False
        finally:
            flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
    
    @classmethod
    def perfect_accelerate_farm(cls, qq: int, operator_id: int, hour: int) -> bool:
        """
        完美加速农场（直接增加不会计算水分营养）
        :param qq: qq
        :param operator_id: 操作员id
        :param hour: 小时数
        :return: 结果
        """
        try:
            flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
            user: User = util.get_user(qq, '')
            user.farm.hour += hour
            user.update(operator_id)
            flower_dao.update_user_by_qq(user)
            return True
        except UserNotRegisteredException:
            return False
        finally:
            flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))


class ContextHandler:
    """
    上下文处理器
    """
    
    def __init__(self):
        self.block_transmission: bool = True  # 是否阻断消息继续传递，默认阻断
    
    def handle(self, message: str, qq: int, username: str, bot_qq: int, bot_name: str, at_list: List[int]) -> Result:
        """
        上下文处理
        :param message: 消息
        :param qq: qq
        :param username: 用户名
        :param bot_qq: 机器人qq
        :param bot_name: 机器人名
        :param at_list: 艾特列表
        :return: 结果
        """
        self.block_transmission = True
        origin_list, context_list = flower_dao.get_context(qq)
        del_context_list: List = []
        index: int = -1
        for context in context_list:
            index += 1
            if context.is_expired():
                del_context_list.append(origin_list[index])
        result: Result = Result.init()
        if len(context_list) == 0:
            return result
        index: int = -1
        for context in context_list:
            index += 1
            if context in del_context_list:
                continue
            # 账号注册
            if isinstance(context, RegisterContext):
                if message == '取消':
                    del_context_list.append(origin_list[index])
                    reply = '已为您取消注册'
                    result.context_reply_text.append(reply)
                    continue
                if context.step == 0:
                    city: City = flower_dao.select_city_by_name(message)
                    if city is None or city.city_name != message:
                        reply = FlowerService.query_city(message) + '\n请选择一座城市，只支持地级市（你可以输入“取消”来取消初始化账户）。'
                        result.context_reply_text.append(reply)
                        continue
                    flower_dao.remove_context(qq, origin_list[index])
                    context.step += 1
                    context.city = city
                    flower_dao.insert_context(qq, context)
                    reply = bot_name + '已选择城市“%s”\n请为你的角色选择一个性别：男/女' % message
                    result.context_reply_text.append(reply)
                elif context.step == 1:
                    gender: Gender = Gender.unknown
                    if message == '男':
                        gender = Gender.male
                    elif message == '女':
                        gender = Gender.female
                    if gender == Gender.unknown:
                        reply = bot_name + '请为你的角色选择一个性别：男/女（你可以输入“取消”来取消初始化账户）'
                        result.context_reply_text.append(reply)
                        continue
                    user: User = User()
                    user.qq = qq
                    user.username = username
                    user.gender = gender
                    user.create_id = str(bot_qq)
                    user.update(bot_qq)
                    
                    city: City = context.city
                    user.city_id = city.get_id()
                    user.born_city_id = city.get_id()
                    
                    # 农场的处
                    util.init_user_farm(user, city)
                    
                    flower_dao.insert_user(user)
                    del_context_list.append(origin_list[index])
                    reply = bot_name + '已为您初始化花店\n' \
                                       '免责声明：本游戏一切内容与现实无关（包括但不限于城市、人物、事件），城市只是为了方便计算天气！\n' \
                                       '现在输入“领取花店初始礼包”试试吧'
                    result.context_reply_text.append(reply)
            # 新手指引
            elif isinstance(context, BeginnerGuideContext):
                if message == '关闭新手指引':
                    del_context_list.append(origin_list[index])
                    reply = '已为您关闭新手指引'
                    result.context_reply_text.append(reply)
                if context.step == 0:
                    if message == '花店签到':
                        self.block_transmission = False
                        flower_dao.remove_context(qq, origin_list[index])
                        context.step += 1
                        flower_dao.insert_context(qq, context)
                        reply = '很好你已经完成了签到！每日签到可以获取金币。接下来试试“花店数据”。\n您可以输入“关闭新手指引”来取消指引。'
                        result.context_reply_text.append(reply)
                elif context.step == 1:
                    if message == '花店数据':
                        self.block_transmission = False
                        flower_dao.remove_context(qq, origin_list[index])
                        context.step += 1
                        flower_dao.insert_context(qq, context)
                        reply = '在这里你可以看见一些玩家的基本数据，接下来试试“花店仓库”。\n您可以输入“关闭新手指引”来取消指引。'
                        result.context_reply_text.append(reply)
                elif context.step == 2:
                    if message == '花店仓库':
                        self.block_transmission = False
                        del_context_list.append(origin_list[index])
                        reply = '在这里你可以看见你的新手物资。新手指引结束了（这句话后面再改）。'
                        result.context_reply_text.append(reply)
            # 丢弃所有物品
            elif isinstance(context, ThrowAllItemContext):
                del_context_list.append(origin_list[index])
                # context 会自动lock无需手动加锁
                user: User = util.get_user(qq, username)
                if message != '确认':
                    reply = user.username + '，已取消清空花店仓库'
                    result.context_reply_text.append(reply)
                    continue
                user.warehouse.items = []
                flower_dao.update_user_by_qq(user)
                reply = user.username + '，已为您清空花店仓库'
                result.context_reply_text.append(reply)
            # 铲除农场的花
            elif isinstance(context, RemoveFlowerContext):
                del_context_list.append(origin_list[index])
                user: User = util.get_user(qq, username)
                if message != '确认':
                    reply = user.username + '，已取消铲除花'
                    result.context_reply_text.append(reply)
                    continue
                if user.gold < global_config.remove_farm_flower_cost_gold:
                    reply = user.username + '，金币不足' + '%.2f' % (
                            global_config.remove_farm_flower_cost_gold / 100) + '枚'
                    result.context_reply_text.append(reply)
                    continue
                user.gold -= global_config.remove_farm_flower_cost_gold
                user.farm.flower_id = ''
                flower_dao.update_user_by_qq(user)
                reply = user.username + '，成功花费' + '%.2f' % (
                        global_config.remove_farm_flower_cost_gold / 100) + '金币为您铲除花'
                result.context_reply_text.append(reply)
            # 选择的回调
            elif isinstance(context, ChooseContext):
                if context.auto_cancel:
                    flower_dao.remove_context(qq, origin_list[index])
                elif message == context.cancel_command:
                    del_context_list.append(origin_list[index])
                    continue
                get_answer: bool = False
                for command in context.choices:
                    if message == command:
                        flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
                        reply = context.choices[command].callback(**context.choices[command].args)
                        flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
                        result.context_reply_text.append(reply)
                        get_answer = True
                if not get_answer:
                    if context.auto_cancel:
                        reply = '已取消'
                    else:
                        reply = '没有该选择，你可以输入“%s”来取消' % context.cancel_command
                    result.context_reply_text.append(reply)
            # 随机旅行
            elif isinstance(context, RandomTravelContext):
                flower_dao.remove_context(qq, origin_list[index])
                user: User = util.get_user(qq, username)
                if message != '确认':
                    item: DecorateItem = DecorateItem()
                    item.item_name = '随机旅行卡'
                    item.number = 1
                    item.item_type = ItemType.props
                    util.insert_items(user.warehouse, [item])
                    flower_dao.update_user_by_qq(user)
                    reply = '已为你取消旅行'
                    result.context_reply_text.append(reply)
                    continue
                city_list: List[City] = [city for city in flower_dao.select_all_city() if city.father_id != '']
                city: City = random.choice(city_list)
                user.city_id = city.get_id()
                user.farm = Farm()
                util.init_user_farm(user, city)
                flower_dao.update_user_by_qq(user)
                reply = username + '，旅行到了%s，来这里开始新的冒险吧~' % city.city_name
                result.context_reply_text.append(reply)
            # 定向旅行
            elif isinstance(context, RandomTravelContext):
                flower_dao.remove_context(qq, origin_list[index])
                user: User = util.get_user(qq, username)
                if message == '取消':
                    item: DecorateItem = DecorateItem()
                    item.item_name = '定向旅行卡'
                    item.number = 1
                    item.item_type = ItemType.props
                    util.insert_items(user.warehouse, [item])
                    flower_dao.update_user_by_qq(user)
                    reply = '已为你取消旅行'
                    result.context_reply_text.append(reply)
                    continue
                city: City = flower_dao.select_city_by_name(message)
                if city is None or city.city_name != message:
                    reply = FlowerService.query_city(message) + '\n请选择一座城市，输入“取消”来取消本次旅行。'
                    result.context_reply_text.append(reply)
                    continue
                user.city_id = city.get_id()
                user.farm = Farm()
                util.init_user_farm(user, city)
                flower_dao.update_user_by_qq(user)
                reply = username + '，旅行到了%s，来这里开始新的冒险吧~' % city.city_name
                result.context_reply_text.append(reply)
            # 发送公告
            elif isinstance(context, AnnouncementContext):
                if message == '取消':
                    del_context_list.append(origin_list[index])
                    reply = '已为您取消发送公告'
                    result.context_reply_text.append(reply)
                    continue
                if context.step == 0:
                    if len(message) == 0:
                        reply = '公告的内容不可以为空哦~你可以输入“取消”来取消发送'
                        result.context_reply_text.append(reply)
                        continue
                    flower_dao.remove_context(qq, origin_list[index])
                    context.step += 1
                    context.text = message
                    flower_dao.insert_context(qq, context)
                    reply = '请问公告的有效期是多久呢？格式“x天y小时z分钟s秒”不要的单位可以省略'
                    result.context_reply_text.append(reply)
                elif context.step == 1:
                    second: int = util.analysis_time(message)
                    if second < 1:
                        reply = '格式错误！格式“x天y小时z分钟s秒”不要的单位可以省略。你可以输入“取消”来取消发送'
                        result.context_reply_text.append(reply)
                        continue
                    flower_dao.remove_context(qq, origin_list[index])
                    context.step += 1
                    context.valid_second = second
                    flower_dao.insert_context(qq, context)
                    reply = '请问发送的名义是谁？'
                    result.context_reply_text.append(reply)
                elif context.step == 2:
                    if len(message.strip()) == 0:
                        reply = '发送名义不能为空~你可以输入“取消”来取消发送'
                        result.context_reply_text.append(reply)
                        continue
                    flower_dao.remove_context(qq, origin_list[index])
                    context.step += 1
                    context.username = message.strip()
                    flower_dao.insert_context(qq, context)
                    
                    reply = '最后检查\n------\n' + context.text + '\n------\n截止日期（预估，以确定时间为准）：'
                    reply += (datetime.now() + timedelta(seconds=context.valid_second)).strftime('%Y-%m-%d %H:%M:%S')
                    reply += '\n发件人名义：' + context.username
                    reply += '\n输入“确认”发送公告，输入“取消”取消发送'
                    result.context_reply_text.append(reply)
                elif context.step == 3:
                    if message != '确认':
                        reply = '请“确认”或者“取消”'
                        result.context_reply_text.append(reply)
                        continue
                    announcement: Announcement = Announcement()
                    announcement.text = context.text
                    announcement.release_time = datetime.now()
                    announcement.expire_time = datetime.now() + timedelta(seconds=context.valid_second)
                    announcement.qq = qq
                    announcement.username = context.username
                    flower_dao.insert_announcement(announcement)
                    del_context_list.append(origin_list[index])
                    reply = '公告已推送'
                    result.context_reply_text.append(reply)
            # 发送信件
            elif isinstance(context, AdminSendMailContext):
                if message == '取消' and context.step != 4:
                    del_context_list.append(origin_list[index])
                    reply = '已为您取消发送信件'
                    result.context_reply_text.append(reply)
                    continue
                if context.step == 0:
                    title = message.strip()
                    if len(title) == 0:
                        reply = '信件的标题不能为空哦！（你可以输入“取消”来取消发送信件）'
                        result.context_reply_text.append(reply)
                        continue
                    flower_dao.remove_context(qq, origin_list[index])
                    context.step += 1
                    context.title = title
                    flower_dao.insert_context(qq, context)
                    reply = '请问信件的正文内容是什么？只可以包含文字。'
                    result.context_reply_text.append(reply)
                elif context.step == 1:
                    text = message.strip()
                    if len(text) == 0:
                        reply = '信件的正文不能为空哦！（你可以输入“取消”来取消发送信件）'
                        result.context_reply_text.append(reply)
                        continue
                    flower_dao.remove_context(qq, origin_list[index])
                    context.step += 1
                    context.text = text
                    flower_dao.insert_context(qq, context)
                    reply = '请问信件的发送名义是什么？只可以包含文字。'
                    result.context_reply_text.append(reply)
                elif context.step == 2:
                    mail_username: str = message.strip()
                    if len(mail_username) == 0:
                        reply = '发送的名义不能为空哦！（你可以输入“取消”来取消发送信件）'
                        result.context_reply_text.append(reply)
                        continue
                    flower_dao.remove_context(qq, origin_list[index])
                    context.step += 1
                    context.username = mail_username
                    flower_dao.insert_context(qq, context)
                    reply = '很好！你可以输入以下内容：\n' \
                            '1.“追加附件 物品 数量 【小时数/品质/耐久】”来追加物品\n' \
                            '2.“删除附件 序号”来删除一个附件\n' \
                            '2.“追加收件人 QQ号”来追加一个收件人\n' \
                            '3.“删除收件人 QQ号”来删除一个收件人\n' \
                            '4.“发送给所有人”来发送信件给所有人\n' \
                            '5.“取消发送给所有人”来取消发送信件给所有人\n' \
                            '6.“预览信件”来预览整个信件\n' \
                            '7.“确认”发送信件，注意必须要有一个收件人！\n' \
                            '8.“取消”来取消发送'
                    result.context_reply_text.append(reply)
                elif context.step == 3:
                    if message == '确认':
                        if len(context.addressee) == 0 and not context.send_all_user:
                            reply = '没有任何收件人！请追加收件人'
                            result.context_reply_text.append(reply)
                            continue
                        del_context_list.append(origin_list[index])
                        mail: Mail = Mail()
                        mail.from_qq = qq
                        mail.title = context.title
                        mail.text = context.text
                        mail.username = context.username
                        mail.appendix = context.appendix
                        mail.arrived = True  # 已经抵达
                        mail.status = '由系统直接送达'
                        reply = ''
                        update_number: int = 0
                        if context.send_all_user:
                            reply = '暂未实现'
                        else:
                            for target_qq in context.addressee:
                                try:
                                    if target_qq != qq:
                                        flower_dao.lock(flower_dao.redis_user_lock_prefix + str(target_qq))
                                    user: User = util.get_user(target_qq)
                                    mail.target_qq = target_qq
                                    mail_id: str = flower_dao.insert_mail(mail)
                                    user.mailbox.mail_list.append(mail_id)
                                    flower_dao.update_user_by_qq(user)
                                    update_number += 1
                                    reply += str(target_qq) + '，发送成功\n'
                                except UserNotRegisteredException:
                                    reply += str(target_qq) + '，未注册\n'
                                except ResBeLockedException:
                                    reply += str(target_qq) + '，无法发送信件\n'
                                finally:
                                    if target_qq != qq:
                                        flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(target_qq))
                        reply += '成功把信件发送给%d个人' % update_number
                        result.context_reply_text.append(reply)
                        continue
                    elif message == '预览信件':
                        reply = context.title
                        reply += '\n------\n'
                        reply += context.text
                        reply += '\n------\n'
                        reply += '来自：%s' % context.username
                        if len(context.appendix) > 0:
                            reply += '\n附件：' + util.show_items(context.appendix)
                        reply += '\n收件人：'
                        if context.send_all_user:
                            reply += '所有人'
                        elif len(context.addressee) > 0:
                            for target_qq in context.addressee:
                                reply += str(target_qq) + ' '
                            reply = reply[:-1]
                        else:
                            reply += '暂无'
                        result.context_reply_text.append(reply)
                        continue
                    elif message == '发送给所有人':
                        flower_dao.remove_context(qq, origin_list[index])
                        context.step = 4
                        flower_dao.insert_context(qq, context)
                        reply = '确认要把信件发送给所有人吗？输入“确认”来确认，其余表示取消'
                        result.context_reply_text.append(reply)
                    elif message == '取消发送给所有人':
                        flower_dao.remove_context(qq, origin_list[index])
                        context.send_all_user = False
                        flower_dao.insert_context(qq, context)
                        reply = '已取消发送给所有人'
                        result.context_reply_text.append(reply)
                    elif message[:5] == '追加收件人':
                        try:
                            target_qq = int(message[5:].strip())
                            flower_dao.remove_context(qq, origin_list[index])
                            if target_qq not in context.addressee:
                                reply = '成功追加收件人！'
                                context.addressee.append(target_qq)
                            else:
                                reply = '追加失败！该人已在名单中'
                            flower_dao.insert_context(qq, context)
                            result.context_reply_text.append(reply)
                        except ValueError:
                            reply = '格式错误！格式“追加收件人 QQ号”'
                            result.context_reply_text.append(reply)
                    elif message[:5] == '删除收件人':
                        try:
                            target_qq = int(message[5:].strip())
                            flower_dao.remove_context(qq, origin_list[index])
                            if target_qq in context.addressee:
                                reply = '成功删除收件人！'
                                context.addressee.remove(target_qq)
                            else:
                                reply = '删除失败！该人不在名单中'
                            flower_dao.insert_context(qq, context)
                            result.context_reply_text.append(reply)
                        except ValueError:
                            reply = '格式错误！格式“删除收件人 QQ号”'
                            result.context_reply_text.append(reply)
                    elif message[:4] == '追加附件':
                        try:
                            data = message[4:].strip()
                            item: DecorateItem = util.analysis_item(data)
                            if item.number < 1:
                                reply = '格式错误！格式“追加附件 物品 数量 【小时数/品质/耐久】”。加速卡要跟小时，如果物品有耐久度，请跟耐久，如果有品质请跟品质，如果都没有省略'
                                result.context_reply_text.append(reply)
                                continue
                            flower_dao.remove_context(qq, origin_list[index])
                            context.appendix.append(item)
                            flower_dao.insert_context(qq, context)
                            reply = '成功追加物品：%s' % str(item)
                            result.context_reply_text.append(reply)
                        except TypeException:
                            raise '格式错误！格式“追加附件 物品 数量 【小时数/品质/耐久】”'
                        except ItemNotFoundException:
                            raise '格式错误！物品不存在'
                    elif message[:4] == '删除附件':
                        data = message[4:].strip()
                        try:
                            item_index: int = int(data)
                            if item_index > 0:
                                item_index -= 1
                            if item_index < 0 or item_index >= len(context.appendix):
                                reply = '格式错误！格式“删除附件 【附件序号】”，序号超出范围'
                                result.context_reply_text.append(reply)
                                continue
                            flower_dao.remove_context(qq, origin_list[index])
                            item = context.appendix[item_index]
                            del context.appendix[item_index]
                            flower_dao.insert_context(qq, context)
                            reply = '成功删除物品：%s' % str(item)
                            result.context_reply_text.append(reply)
                        except ValueError:
                            reply = '格式错误！格式“删除附件 【附件序号】”'
                            result.context_reply_text.append(reply)
                            continue
                elif context.step == 4:
                    flower_dao.remove_context(qq, origin_list[index])
                    context.step = 3
                    if message == '确认':
                        context.send_all_user = True
                        reply = '成功切换为把信件发给所有用户'
                        result.context_reply_text.append(reply)
                    else:
                        reply = '已取消把信件发送给所有人'
                        result.context_reply_text.append(reply)
                    flower_dao.insert_context(qq, context)
            # 删除信件
            elif isinstance(context, DeleteMailContext):
                del_context_list.append(origin_list[index])
                # context 会自动lock无需手动加锁
                user: User = util.get_user(qq, username)
                if message != '确认':
                    reply = user.username + '，已取消删除信件'
                    result.context_reply_text.append(reply)
                    continue
                if context.index < 0 or context.index >= len(user.mailbox.mail_list):
                    reply = user.username + '，序号超出范围'
                    result.context_reply_text.append(reply)
                    continue
                mail_id = user.mailbox.mail_list[context.index]
                mail: Mail = flower_dao.select_mail_by_id(mail_id)
                del user.mailbox.mail_list[context.index]
                mail.is_delete = 1
                flower_dao.update_mail(mail)
                flower_dao.update_user_by_qq(user)
                reply = user.username + '，成功删除信件“%s”' % mail.title
                result.context_reply_text.append(reply)
            # 清空信箱
            elif isinstance(context, ClearMailBoxContext):
                del_context_list.append(origin_list[index])
                # context 会自动lock无需手动加锁
                user: User = util.get_user(qq, username)
                if message != '确认':
                    reply = user.username + '，已取消清空信箱'
                    result.context_reply_text.append(reply)
                    continue
                user.mailbox.mail_list = []
                flower_dao.update_user_by_qq(user)
                reply = user.username + '，成功清空信箱'
                result.context_reply_text.append(reply)
        for context in del_context_list:
            flower_dao.remove_context(qq, context)
        return result


class FlowerService:
    @classmethod
    def query_city(cls, name: str) -> str:
        """
        查询城市
        :param name: 城市名
        :return:
        """
        if len(name) > 30:
            return '城市名过长'
        city = flower_dao.select_city_by_name(name)
        if city is None or city.city_name != name:
            ans = '没有找到城市' + name
            cities = flower_dao.select_city_by_name_like(name)
            if len(cities) > 0:
                ans += util.show_cities_name(cities)
            else:
                length: int = len(name) - 1
                init: bool = False
                while length > 0:
                    for i in range(len(name) - length):
                        cities = flower_dao.select_city_by_name_like(name[i:i + length])
                        cities_name = util.show_cities_name(cities)
                        if len(cities_name) > 0:
                            ans += cities_name
                            init = True
                    if init:
                        break
                    length -= 1
            return ans
        if city.region_id == '0':
            return '名字：' + city.city_name
        father = City()
        if city.father_id != '':
            father = flower_dao.select_city_by_id(city.father_id)
        region = flower_dao.select_region_by_id(city.region_id)
        terrain = flower_dao.select_terrain_by_id(city.terrain_id)
        climate = flower_dao.select_climate_by_id(city.climate_id)
        soil = flower_dao.select_soil_by_id(city.soil_id)
        return '名字：' + city.city_name + '\n' + \
               '省份：' + father.city_name + '\n' + \
               '地区：' + region.name + '\n' + \
               '地形：' + terrain.name + '\n' + \
               '气候：' + climate.name + '\n' + \
               '土壤：' + soil.name
    
    @classmethod
    def query_soil(cls, name: str) -> str:
        """
        查询土壤
        :param name: 土壤名
        :return: 结果
        """
        if len(name) > 30:
            return '土壤名过长'
        soil = flower_dao.select_soil_by_name(name)
        if soil is None or soil.name != name:
            return '没有找到土壤' + name
        res = '名字：' + soil.name
        res += '\n营养：' + str(soil.min_nutrition) + '-' + str(soil.max_nutrition) + '（' + str(
            soil.min_change_nutrition) + '-' + str(soil.max_change_nutrition) + '）'
        res += '\n湿度：' + str(soil.min_humidity) + '-' + str(soil.max_humidity) + '（' + str(
            soil.min_change_humidity) + '-' + str(soil.max_change_humidity) + '）'
        if len(soil.min_change_humidity_soil_id) != 0:
            res += '\n最低湿度变化土壤：' + util.get_soil_list(soil.min_change_humidity_soil_id)
        if len(soil.max_change_humidity_soil_id) != 0:
            res += '\n最高湿度变化土壤：' + util.get_soil_list(soil.max_change_humidity_soil_id)
        if len(soil.min_change_nutrition_soil_id) != 0:
            res += '\n最低营养变化土壤：' + util.get_soil_list(soil.min_change_nutrition_soil_id)
        if len(soil.max_change_nutrition_soil_id) != 0:
            res += '\n最高营养变化土壤：' + util.get_soil_list(soil.max_change_nutrition_soil_id)
        return res
    
    @classmethod
    def query_flower(cls, name: str) -> str:
        """
        查询花
        :param name: 花名
        :return: 结果
        """
        if len(name) > 30:
            return '花名过长'
        flower = flower_dao.select_flower_by_name(name)
        if flower is None or flower.name != name:
            return '没有找到花名' + name
        res = '名字：' + flower.name
        res += '\n等级：' + FlowerLevel.view_level(flower.level)
        if len(flower.climate_id) > 0:
            res += '\n适宜气候：' + util.get_climate_list(flower.climate_id)
        elif len(flower.op_climate_id) > 0:
            res += '\n不适宜气候：' + util.get_climate_list(flower.op_climate_id)
        elif len(flower.climate_id) == 0 and len(flower.op_climate_id) == 0:
            res += '\n适宜气候：所有气候'
        if len(flower.soil_id) > 0:
            res += '\n适宜土壤：' + util.get_soil_list(flower.soil_id)
        elif len(flower.op_soil_id) > 0:
            res += '\n不适宜土壤：' + util.get_soil_list(flower.op_soil_id)
        elif len(flower.soil_id) == 0 and len(flower.op_soil_id) == 0:
            res += '\n适宜土壤：所有土壤'
        
        res += '\n吸收水分：' + str(flower.water_absorption) + '/小时'
        res += '\n吸收营养：' + str(flower.nutrition_absorption) + '/小时'
        res += '\n能忍受恶劣条件：' + str(flower.withered_time) + '小时'
        
        res += '\n种子：'
        res += '\n\t周期：' + str(flower.seed_time) + '小时'
        res += util.show_conditions(flower.seed_condition)
        res += '\n幼苗：'
        res += '\n\t周期：' + str(flower.grow_time) + '小时'
        res += util.show_conditions(flower.grow_condition)
        res += '\n成熟：'
        res += '\n\t成熟周期：' + str(flower.mature_time) + '小时'
        res += '\n\t过熟周期：' + str(flower.overripe_time) + '小时'
        res += util.show_conditions(flower.mature_condition)
        
        return res
    
    @classmethod
    def view_user_data(cls, qq: int, username: str) -> str:
        """
        查询用户数据
        :param qq: qq
        :param username: 用户名
        :return: 结果
        """
        user: User = util.get_user(qq, username)
        born_city: City = flower_dao.select_city_by_id(user.born_city_id)
        city: City = flower_dao.select_city_by_id(user.city_id)
        res = '用户名：' + user.username
        if user.auto_get_name:
            res += '（自动获取）'
        res += '\n等级：'
        level = 0
        system_data = flower_dao.select_system_data()
        for i in range(len(system_data.exp_level)):
            if user.exp >= system_data.exp_level[i]:
                level = i
        res += str(level + 1)
        res += '\n角色性别：' + user.gender.show()
        res += '\n出生地：' + born_city.city_name
        res += '\n所在城市：' + city.city_name
        res += '\n金币：' + '%.2f' % (user.gold / 100)
        res += '\n仓库：' + str(len(user.warehouse.items)) + '/' + str(user.warehouse.max_size)
        return res
    
    @classmethod
    def view_user_farm_equipment(cls, qq: int, username: str) -> str:
        """
        根据用户查询其农场设备
        :param qq: qq号
        :param username: 用户名
        :return: 农场信息
        """
        flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
        user, city, soil, climate, _, _ = util.get_farm_information(qq, username)
        flower_dao.update_user_by_qq(user)
        flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
        
        reply = user.username + '的农场设备：'
        reply += '\n所在地：' + city.city_name
        reply += '\n气候：' + climate.name
        reply += '\n土壤：' + soil.name
        
        reply += '\n温度计：' + str(user.farm.thermometer)
        reply += '\n气象检测站：' + str(user.farm.weather_station)
        reply += '\n土壤监控站：' + str(user.farm.soil_monitoring_station)
        reply += '\n浇水壶：' + str(user.farm.watering_pot)
        reply += '\n信箱：' + str(user.farm.mailbox)
        reply += '\n温室：' + str(user.farm.greenhouse)
        return reply
    
    @classmethod
    def view_user_farm(cls, qq: int, username: str) -> str:
        """
        查看用户农场
        :param qq: QQ
        :param username: 用户名
        :return:
        """
        flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
        user, city, soil, climate, weather, flower = util.get_farm_information(qq, username)
        now_temperature = util.get_now_temperature(weather)
        util.update_farm(user, city, soil, weather, flower)
        flower_dao.update_user_by_qq(user)
        flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
        
        reply = user.username + '的农场：'
        reply += '\n种植的花：'
        if user.farm.flower_id != '':
            reply += flower.name
            reply += '\n花的状态：' + FlowerState.view_name(user.farm.flower_state)
            
            seed_time: int = flower.seed_time
            grow_time: int = seed_time + flower.grow_time
            mature_time: int = grow_time + flower.mature_time
            overripe_time: int = mature_time + flower.overripe_time
            if user.farm.hour <= seed_time:
                reply += '\n阶段：种子'
            elif user.farm.hour <= grow_time:
                reply += '\n阶段：幼苗'
            elif user.farm.hour <= mature_time:
                reply += '\n阶段：成熟'
            elif user.farm.hour <= overripe_time:
                reply += '\n阶段：过熟'
            else:
                reply += '\n阶段：枯萎'
            total_hour: int = flower.seed_time + flower.grow_time
            reply += '\n成长度：' + '%.1f%%' % (user.farm.hour * 100.0 / total_hour)
        else:
            reply += '无'
        reply += '\n天气：' + weather.weather_type
        reply += '\n气温：' + util.show_temperature(user)
        if user.farm.temperature > now_temperature:
            reply += '（↓）'
        elif user.farm.temperature < now_temperature:
            reply += '（↑）'
        else:
            reply += '（=）'
        reply += '\n土壤湿度：' + util.show_humidity(user)
        reply += '\n土壤营养：' + util.show_nutrition(user)
        
        return reply
    
    @classmethod
    def view_mailbox(cls, qq: int, username: str) -> str:
        """
        查看信箱
        :param qq:
        :param username:
        :return:
        """
        user: User = util.get_user(qq, username)
        total_number = len(user.mailbox.mail_list)
        reply: str = '%s，你的信箱如下：%d/%d' % (user.username, total_number, user.mailbox.max_size)
        if total_number == 0:
            reply += '\n暂无'
            reply += '\n------'
            reply += '\n有些时候有太多的信件也不是一件好事情呢~'
            return reply
        index = 0
        for mail_id in user.mailbox.mail_list:
            index += 1
            mail: Mail = flower_dao.select_mail_by_id(mail_id)
            if not mail.valid():
                reply += '\n%d.信件已损坏' % index
                continue
            reply += '\n%d.%s' % (index, mail.title)
            if len(mail.status) > 0:
                reply += '（%s）' % mail.status
        return reply
    
    @classmethod
    def view_mail(cls, qq: int, username: str, mail_index: int) -> str:
        """
        查看信件
        :param qq:
        :param username:
        :param mail_index:
        :return:
        """
        user: User = util.get_user(qq, username)
        if mail_index > 0:
            mail_index -= 1
        if mail_index < 0 or mail_index >= len(user.mailbox.mail_list):
            return user.username + '，超出范围'
        mail_id = user.mailbox.mail_list[mail_index]
        mail: Mail = flower_dao.select_mail_by_id(mail_id)
        if not mail.valid():
            return user.username + '，信件已损坏'
        reply = mail.title
        reply += '\n------\n'
        reply += mail.text
        reply += '\n------\n'
        mail_username: str = '【匿名】'
        if mail.username != '':
            # 如果有名义寄件人，直接采用名义寄件人
            mail_username = mail.username
        elif mail.from_qq != 0:
            try:
                from_user: User = util.get_user(mail.from_qq)
                mail_username = from_user.username
            except UserNotRegisteredException:
                mail_username = '【玩家已注销】'
        elif mail.role_id != '':
            # todo: 接入npc
            mail_username = 'npc'
        reply += '来自：%s，日期：%s' % (mail_username, mail.create_time.strftime('%Y-%m-%d %H:%M:%S'))
        if len(mail.appendix) > 0:
            reply += '\n附件：' + util.show_items(mail.appendix)
        if mail.received:
            reply += '（已领取附件）'
        return reply
    
    @classmethod
    def delete_mail(cls, qq: int, username: str, mail_index: int = 0) -> str:
        """
        删除信件
        :param qq:
        :param username:
        :param mail_index:
        :return:
        """
        user: User = util.get_user(qq, username)
        if mail_index > 0:
            mail_index -= 1
        if mail_index < 0 or mail_index >= len(user.mailbox.mail_list):
            flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
            return user.username + '，超出范围'
        context: DeleteMailContext = DeleteMailContext(index=mail_index)
        flower_dao.insert_context(qq, context)
        return user.username + '，输入“确认”删除信件，其余输入取消'
    
    @classmethod
    def clear_mailbox(cls, qq: int, username: str) -> str:
        """
        删除信件
        :param qq:
        :param username:
        :return:
        """
        user: User = util.get_user(qq, username)
        if len(user.mailbox.mail_list) == 0:
            return user.username + '，你的信箱空空如也呢'
        context: ClearMailBoxContext = ClearMailBoxContext()
        flower_dao.insert_context(qq, context)
        return user.username + '，输入“确认”清空信箱，其余输入取消'
    
    @classmethod
    def receive_appendix_mail(cls, qq: int, username: str, mail_index: int = 0) -> str:
        """
        领取附件
        :param qq:
        :param username:
        :param mail_index:
        :return:
        """
        flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
        user: User = util.get_user(qq, username)
        try:
            if mail_index > 0:
                mail_index -= 1
            if mail_index < 0 or mail_index >= len(user.mailbox.mail_list):
                return user.username + '，超出范围'
            mail_id = user.mailbox.mail_list[mail_index]
            mail: Mail = flower_dao.select_mail_by_id(mail_id)
            if len(mail.appendix) == 0:
                return user.username + '，该信件没有附件可以领取。'
            if mail.received:
                return user.username + '，你已经领取过该附件了。'
            util.insert_items(user.warehouse, copy.deepcopy(mail.appendix))
            mail.received = True
            flower_dao.update_mail(mail)
            flower_dao.update_user_by_qq(user)
            return user.username + '，领取成功，信件“%s”的附件%s' % (mail.title, util.show_items(mail.appendix))
        except WareHouseSizeNotEnoughException:
            return user.username + '，领取失败，仓库空间不足！'
        except ItemNegativeNumberException:
            return user.username + '，领取失败！该附件可能在送信的路上已损坏。人生命途总是充满了变数。'
        except ItemNotFoundException:
            return user.username + '，领取失败！该附件可能在送信的路上已损坏。人生命途总是充满了变数。'
        finally:
            flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
    
    @classmethod
    def init_user(cls, qq: int, username: str) -> str:
        """
        初始化用户
        :param qq: qq
        :param username: 用户名
        :return: 结果
        """
        try:
            user: User = util.get_user(qq, username)
            return user.username + '您已经有账号了'
        except UserNotRegisteredException:
            context = RegisterContext(qq, username)
            flower_dao.insert_context(qq, context)
            return username + '，请选择一座城市，只支持地级市。'
    
    @classmethod
    def user_sign_in(cls, qq: int, username: str) -> str:
        """
        签到
        :param qq: qq
        :param username: 用户名
        :return: 结果
        """
        flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
        user: User = util.get_user(qq, username)
        today: datetime = datetime.today()
        if user.last_sign_date.date() == today.date():
            flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
            return user.username + '，今天已经签到过了'
        if user.last_sign_date + timedelta(days=1) == today:
            user.sign_continuous += 1
        else:
            user.sign_continuous = 1
        user.sign_count += 1
        user.last_sign_date = today
        gold = random.randint(100, 500)
        user.gold += gold
        # 只对于不足次数的补足，有可能有活动之类的额外增加了每日的抽卡次数
        if user.draw_card_number < global_config.draw_card_max_number:
            user.draw_card_number = global_config.draw_card_max_number
        user.update(user.qq)
        res = user.username + '，签到成功！'
        res += '\n获得金币：' + '%.2f' % (gold / 100)
        res += '\n剩余金币：' + '%.2f' % (user.gold / 100)
        res += '\n连续签到：' + str(user.sign_continuous) + '天'
        res += '\n累计签到：' + str(user.sign_count) + '天'
        flower_dao.update_user_by_qq(user)
        sign_record: SignRecord = SignRecord()
        sign_record.qq = user.qq
        sign_record.update(user.qq)
        flower_dao.insert_sign_record(sign_record)
        flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
        return res
    
    @classmethod
    def transfer_accounts(cls, qq: int, username: str, at_list: List[int], gold: int) -> str:
        """
        转账
        :param qq: qq
        :param username: 用户名
        :param at_list:@列表
        :param gold: 金币
        :return:
        """
        flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
        user: User = util.get_user(qq, username)
        reply = '转账结果如下：'
        for target_qq in at_list:
            try:
                flower_dao.lock(flower_dao.redis_user_lock_prefix + str(target_qq))
                target_user: User = util.get_user(target_qq, '')
                if user.gold < gold:
                    reply += '\n对' + str(target_qq) + '转账失败，余额不足'
                else:
                    user.gold -= gold
                    target_user.gold += int(gold * 0.8)
                    target_user.update(qq)
                    flower_dao.update_user_by_qq(target_user)
                    reply += '\n对' + str(target_qq) + '转账成功，余额：' + '%.2f' % (user.gold / 100)
            except ResBeLockedException:
                reply += '\n对' + str(target_qq) + '转账失败，无法转账或网络波动'
            except UserNotRegisteredException:
                reply += '\n对' + str(target_qq) + '转账失败，还未注册'
            finally:
                flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(target_qq))
        flower_dao.update_user_by_qq(user)
        flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
        reply += '\n转账有20%手续费'
        return reply
    
    @classmethod
    def view_warehouse(cls, qq: int, username: str, page: int, page_size: int = 30,
                       remove_description: bool = True) -> Tuple[str, str]:
        """
        查看仓库
        无需加锁，只读！
        :param qq: qq
        :param username: 用户名
        :param page: 页码
        :param page_size: 页面大小
        :param remove_description: 是否移除描述
        :return: 结果
        """
        user: User = util.get_user(qq, username)
        total_number = len(user.warehouse.items)
        reply = user.username + '，你的花店仓库如下：' + str(total_number) + '/' + str(user.warehouse.max_size)
        if total_number == 0:
            reply += '\n暂无'
        else:
            total_page = int(total_number / page_size)
            if total_number % page_size != 0:
                total_page += 1
            if page < 0 or page > total_page:
                raise PageOutOfRangeException('背包页码超限，总计：' + str(total_page))
            index = 0
            for item in user.warehouse.items:
                if index < page * page_size:
                    continue
                if index > (page + 1) * page_size:
                    break
                reply += '\n' + str(item)
                index += 1
            reply += '\n------'
            reply += '\n总计页码：' + str(total_page)
        description = ''
        if user.warehouse.description != '' and remove_description:
            flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
            description = user.warehouse.description[:-1]
            user.warehouse.description = ''
            flower_dao.update_user_by_qq(user)
            flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
        return reply, description
    
    @classmethod
    def view_item(cls, item_name: str) -> str:
        """
        查询物品
        :param item_name: 物品名字
        :return: 物品
        """
        item: Item = flower_dao.select_item_by_name(item_name)
        if item.name == item_name:
            return str(item)
        
        ans = '没有找到物品：' + item_name
        item_list: List[Item] = flower_dao.select_item_like_name(item_name)
        if len(item_list) > 0:
            ans += util.show_items_name(item_list)
        else:
            length: int = len(item_name) - 1
            init: bool = False
            while length > 0:
                for i in range(len(item_name) - length):
                    item_list: List[Item] = flower_dao.select_item_like_name(item_name[i:i + length])
                    items_name: str = util.show_items_name(item_list)
                    if len(item_list) > 0:
                        ans += items_name
                        init = True
                        if len(ans) > 200:
                            break
                if init:
                    break
                length -= 1
        return ans
    
    @classmethod
    def receive_beginner_gifts(cls, qq: int, username: str) -> str:
        """
        领取初始礼包
        :param qq: qq
        :param username: 用户名
        :return: 结果
        """
        flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
        user: User = util.get_user(qq, username)
        if user.beginner_pack:
            return user.username + '，你已经领取过初始礼包了'
        user.beginner_pack = True
        flower_dao.update_user_by_qq(user)
        flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
        item: DecorateItem = DecorateItem()
        item_list: List[DecorateItem] = []
        
        # 初始获取初始种子
        seed_list = ['野草种子', '野花种子', '小黄花种子', '小红花种子']
        for seed in seed_list:
            item.item_name = seed
            item.number = 5
            item_list.append(copy.deepcopy(item))
        # 领取化肥
        item.item_name = '初级化肥'
        item.number = 5
        item_list.append(copy.deepcopy(item))
        # 新手道具
        item.item_name = '新手水壶'
        item.number = 1
        item_list.append(copy.deepcopy(item))
        item.item_name = '随机旅行卡'
        item.number = 1
        item_list.append(copy.deepcopy(item))
        item.item_name = '加速卡'
        item.number = 1
        item.hour = 10
        item_list.append(copy.deepcopy(item))
        item.item_name = '完美加速卡'
        item.number = 1
        item.hour = 36
        item_list.append(copy.deepcopy(item))
        
        util.insert_items(user.warehouse, item_list)
        flower_dao.update_user_by_qq(user)
        
        context: BeginnerGuideContext = BeginnerGuideContext()
        flower_dao.insert_context(qq, context)
        return '领取成功！接下来输入“花店签到”试试'
    
    @classmethod
    def view_weather(cls, city_name: str) -> str:
        """
        查看天气
        :param city_name: 城市名
        :return: 结果
        """
        city: City = flower_dao.select_city_by_name(city_name)
        if city.city_name != city_name:
            weather: Weather = weather_getter.get_city_weather(city_name, 'none')
        else:
            weather: Weather = util.get_weather(city)
        reply = weather.city_name + '，' + weather.weather_type
        reply += '\n最低气温：' + str(weather.min_temperature) + '℃'
        reply += '\n最高气温：' + str(weather.max_temperature) + '℃'
        reply += '\n湿度：' + str(weather.humidity) + '%'
        return reply
    
    @classmethod
    def throw_item(cls, qq: int, username: str, item: DecorateItem) -> str:
        """
        丢弃一件物品
        :param qq: qq
        :param username: 用户名
        :param item: 物品
        :return: 结果
        """
        flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
        user: User = util.get_user(qq, username)
        try:
            util.remove_items(user.warehouse, [item])
            flower_dao.update_user_by_qq(user)
            return user.username + '，丢弃成功'
        except ItemNotFoundException:
            return user.username + '，没有该物品'
        except ItemNotEnoughException:
            return user.username + '，物品不足'
        finally:
            flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
    
    @classmethod
    def throw_all_items(cls, qq: int, username: str) -> str:
        """
        丢弃所有物品
        :param qq: qq
        :param username: 用户名
        :return: 结果
        """
        user: User = util.get_user(qq, username)
        if len(user.warehouse.items) == 0:
            return user.username + '，你的花店仓库没有物品'
        context: ThrowAllItemContext = ThrowAllItemContext()
        flower_dao.insert_context(qq, context)
        return user.username + '，请输入“确认”丢弃所有花店仓库的物品，其余任何回复视为取消'
    
    @classmethod
    def plant_flower(cls, qq: int, username: str, flower_name: str) -> str:
        """
        种植植物
        :param qq:
        :param username:
        :param flower_name:
        :return:
        """
        flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
        user: User = util.get_user(qq, username)
        try:
            if user.farm.flower_id != '':
                return user.username + '，您的农场已经有花了'
            flower: Flower = flower_dao.select_flower_by_name(flower_name)
            if flower.name != flower_name:
                return user.username + '，不存在这种花'
            item: DecorateItem = DecorateItem()
            item.item_name = flower_name + '种子'
            item.number = 1
            util.remove_items(user.warehouse, [item])
            user.farm.flower_id = flower.get_id()
            user.farm.flower_state = FlowerState.normal
            user.farm.last_check_time = datetime.now()
            user.farm.hour = 0
            user.farm.bad_hour = 0
            user.farm.perfect_hour = 0
            flower_dao.update_user_by_qq(user)
            return user.username + '，种植' + flower_name + '成功！'
        except ItemNotFoundException:
            return user.username + '，没有' + flower_name + '种子'
        except ItemNotEnoughException:
            return user.username + '，没有足够的' + flower_name + '种子'
        finally:
            flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
    
    @classmethod
    def watering(cls, qq: int, username: str, multiple: int) -> str:
        flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
        user: User = util.get_user(qq, username)
        
        humidity_change: float = 0.0
        watering_pot: DecorateItem = user.farm.watering_pot
        if watering_pot.level == 1:
            humidity_change = 5.0 * multiple
            user.farm.humidity += humidity_change
        elif watering_pot.level == 2:
            humidity_change = 2.5 * multiple
            user.farm.humidity += humidity_change
        elif watering_pot.level == 3:
            humidity_change = 1.0 * multiple
            user.farm.humidity += humidity_change
        elif watering_pot.level == 4:
            humidity_change = 0.1 * multiple
            user.farm.humidity += humidity_change
        cost_gold: int = global_config.watering_cost_gold * multiple
        # 设置湿度的上限
        if user.farm.humidity > global_config.soil_max_humidity:
            humidity_change -= user.farm.humidity - global_config.soil_max_humidity
            user.farm.humidity = global_config.soil_max_humidity
        # 金币消耗
        if user.gold < cost_gold:
            return user.username + '，浇水失败！金币不足！\n每浇水一次，需要金币%.2f' % (
                    global_config.watering_cost_gold / 100)
        user.gold -= cost_gold
        flower_dao.update_user_by_qq(user)
        flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
        if humidity_change == 0.0:
            return user.username + '，浇水失败！当前可能没有浇水壶。'
        return user.username + '，浇水成功！湿度增加%.2f，花费金币%.2f' % (humidity_change, cost_gold / 100)
    
    @classmethod
    def remove_flower(cls, qq: int, username: str) -> str:
        user: User = util.get_user(qq, username)
        if user.farm.flower_id == '':
            return user.username + '，你的农场没有种花'
        context: RemoveFlowerContext = RemoveFlowerContext()
        flower_dao.insert_context(qq, context)
        return user.username + '，请输入“确认”铲除农场的花，其余任何回复视为取消'
    
    @classmethod
    def change_username(cls, qq: int, username: str, new_username: str) -> str:
        """
        改变用户名
        :param qq: qq
        :param username: 自动获取的用户名
        :param new_username: 新的用户名
        :return: 结果
        """
        flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
        # 把名字一起锁定了
        flower_dao.lock(flower_dao.redis_username_lock_prefix + new_username)
        user: User = util.get_user(qq, username)
        old_user: User = flower_dao.select_user_by_username(new_username)
        if old_user.valid():
            flower_dao.unlock(flower_dao.redis_username_lock_prefix + new_username)
            return '该名字已被别人使用！'
        user.username = new_username
        user.auto_get_name = False
        flower_dao.update_user_by_qq(user)
        flower_dao.unlock(flower_dao.redis_username_lock_prefix + new_username)
        return '已成功更改你的游戏名'
    
    @classmethod
    def clear_username(cls, qq: int, username: str) -> str:
        """
        清除用户名
        :param qq: qq
        :param username: 自动获取的用户名
        :return: 结果
        """
        flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
        user: User = util.get_user(qq, username)
        if user.auto_get_name:
            return user.username + '，你本来就没有设定名字。'
        user.auto_get_name = True
        flower_dao.update_user_by_qq(user)
        return username + '，已为你清除名字'
    
    @classmethod
    def use_item(cls, qq: int, username: str, item: DecorateItem) -> str:
        """
        使用物品
        :param qq: qq
        :param username: 自动获取的用户名
        :param item: 物品
        :return: 结果
        """
        flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
        user: User = util.get_user(qq, username)
        try:
            if item.number == 0:
                return '数量不能为0'
            item_obj: Item = flower_dao.select_item_by_name(item.item_name)
            item.item_type = item_obj.item_type
            item.max_stack = item_obj.max_stack  # 最大叠加数量
            item.max_durability = item_obj.max_durability  # 最大耐久度
            item.rot_second = item_obj.rot_second  # 腐烂的秒数
            item.humidity = item_obj.humidity  # 湿度
            item.nutrition = item_obj.nutrition  # 营养
            item.temperature = item_obj.temperature  # 温度
            item.level = item_obj.level
            if item_obj.item_type == ItemType.flower and item.flower_quality == FlowerQuality.not_flower:
                item.flower_quality = FlowerQuality.normal
            util.remove_items(user.warehouse, [copy.deepcopy(item)])
            # 花
            if item.item_type == ItemType.flower:
                raise UseFailException(user.username + '，花不可以使用')
            # 种子
            elif item.item_type == ItemType.seed:
                raise UseFailException(user.username + '，种子请使用命令“种植 【花名】”')
            # 加速卡
            elif item.item_type == ItemType.accelerate:
                if item.item_name == '加速卡':
                    hour: int = item.hour * item.number
                    user.farm.last_check_time -= timedelta(hours=hour)
                    return user.username + '，成功加速农场%d小时' % hour
                elif item.item_name == '完美加速卡':
                    hour: int = item.hour * item.number
                    user.farm.hour += hour
                    return user.username + '，成功完美加速农场%d小时' % hour
            # 化肥
            elif item.item_type == ItemType.fertilizer:
                nutrition: float = item.nutrition * item.number
                nutrition = user.farm.add_nutrition(nutrition)
                return user.username + '，成功增加营养%.2f' % nutrition
            # 温度计
            elif item.item_type == ItemType.thermometer:
                if item.number == 1:
                    if user.farm.thermometer.item_name != '':
                        util.insert_items(user.warehouse, [user.farm.thermometer])
                    item.update = datetime.now()
                    user.farm.thermometer = item
                    return user.username + '，成功使用%s' % str(item)
                else:
                    raise UseFailException(user.username + '，该类型物品只能使用一个')
            # 土壤检测站
            elif item.item_type == ItemType.soil_monitoring_station:
                if item.number == 1:
                    if user.farm.soil_monitoring_station.item_name != '':
                        util.insert_items(user.warehouse, [user.farm.soil_monitoring_station])
                    item.update = datetime.now()
                    user.farm.soil_monitoring_station = item
                    return user.username + '，成功使用%s' % str(item)
                else:
                    raise UseFailException(user.username + '，该类型物品只能使用一个')
            # 浇水壶
            elif item.item_type == ItemType.watering_pot:
                if item.number == 1:
                    if user.farm.watering_pot.item_name != '':
                        util.insert_items(user.warehouse, [user.farm.watering_pot])
                    item.update = datetime.now()
                    user.farm.watering_pot = item
                    return user.username + '，成功使用%s' % str(item)
                else:
                    raise UseFailException(user.username + '，该类型物品只能使用一个')
            # 气象监控站
            elif item.item_type == ItemType.weather_station:
                if item.number == 1:
                    if user.farm.weather_station.item_name != '':
                        util.insert_items(user.warehouse, [user.farm.weather_station])
                    item.update = datetime.now()
                    user.farm.weather_station = item
                    return user.username + '，成功使用%s' % str(item)
                else:
                    raise UseFailException(user.username + '，该类型物品只能使用一个')
            # 信箱
            elif item.item_type == ItemType.mailbox:
                if item.number == 1:
                    if user.farm.mailbox.item_name != '':
                        util.insert_items(user.warehouse, [user.farm.mailbox])
                    item.update = datetime.now()
                    user.farm.mailbox = item
                    return user.username + '，成功使用%s' % str(item)
                else:
                    raise UseFailException(user.username + '，该类型物品只能使用一个')
            # 温室
            elif item.item_type == ItemType.greenhouse:
                if item.number == 1:
                    if user.farm.greenhouse.item_name != '':
                        util.insert_items(user.warehouse, [user.farm.greenhouse])
                    item.update = datetime.now()
                    user.farm.greenhouse = item
                    return user.username + '，成功使用%s' % str(item)
                else:
                    raise UseFailException(user.username + '，该类型物品只能使用一个')
            # 仓库
            elif item.item_type == ItemType.warehouse:
                if item.number == 1:
                    if user.farm.warehouse.item_name != '':
                        util.insert_items(user.warehouse, [user.farm.warehouse])
                    item.update = datetime.now()
                    user.farm.warehouse = item
                    return user.username + '，成功使用%s' % str(item)
                else:
                    raise UseFailException(user.username + '，该类型物品只能使用一个')
            # 特殊道具
            elif item.item_type == ItemType.props:
                if item.item_name == '随机旅行卡':
                    if item.number != 1:
                        raise UseFailException(user.username + '，该类型物品只能使用一个')
                    context: RandomTravelContext = RandomTravelContext()
                    flower_dao.insert_context(qq, context)
                    return user.username + '，请输入“确认”来随机旅行，输入“取消”取消旅行，旅行后你将会失去农场的所有设备（包括仓库）'
                elif item.item_name == '定向旅行卡':
                    if item.number != 1:
                        raise UseFailException(user.username + '，该类型物品只能使用一个')
                    context: TravelContext = TravelContext()
                    flower_dao.insert_context(qq, context)
                    return user.username + '，请输入一个城市名前往，输入“取消”取消旅行，旅行后你将会失去农场的所有设备（包括仓库）'
                if item.item_name == '小金币卡':
                    gold = random.randint(50 * item.number, 501 * item.number)
                    user.gold += gold
                    return user.username + '，获得%.2f金币' % (gold / 100)
                elif item.item_name == '大金币卡':
                    gold = random.randint(50 * item.number, 1000001 * item.number)
                    user.gold += gold
                    return user.username + '，获得%.2f金币' % (gold / 100)
                elif item.item_name == '铲除卡':
                    if user.farm.flower_id == '':
                        raise UseFailException(user.username + '，你的农场没有花')
                    user.farm.flower_id = ''
                    return user.username + '，获得%.2f金币' % int(user.gold / 100)
                elif item.item_name == '升温卡':
                    temperature = item.temperature * item.number
                    user.farm.temperature += temperature
                    return user.username + '，温度+%.2f℃' % temperature
                elif item.item_name == '降温卡':
                    temperature = item.temperature * item.number
                    user.farm.temperature += temperature
                    return user.username + '，温度%.2f℃' % temperature
                elif item.item_name == '小施肥卡' or item.item_name == '大施肥卡':
                    nutrition: float = item.nutrition * item.number
                    nutrition = user.farm.add_nutrition(nutrition)
                    return user.username + '，营养+%.2f' % nutrition
                elif item.item_name == '小浇水卡' or item.item_name == '大浇水卡':
                    humidity: float = item.humidity * item.number
                    humidity = user.farm.add_humidity(humidity)
                    return user.username + '，湿度+%.2f' % humidity
            raise UseFailException(user.username + '，该物品不可以使用')
        except ItemNotFoundException:
            return user.username + '，没有该物品'
        except ItemNotEnoughException:
            return user.username + '，物品不足'
        except UseFailException as e:
            util.insert_items(user.warehouse, [copy.deepcopy(item)])
            return e.message
        except WareHouseSizeNotEnoughException as e:
            util.insert_items(user.warehouse, [copy.deepcopy(item)])
            return user.username + '，' + e.message
        finally:
            flower_dao.update_user_by_qq(user)
            flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
    
    @classmethod
    def reward_flower(cls, qq: int, username: str) -> str:
        """
        收获
        :param qq: qq
        :param username: 用户名
        :return: 收获
        """
        flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
        try:
            user, city, soil, _, weather, flower = util.get_farm_information(qq, username)
            util.update_farm(user, city, soil, weather, flower)
            if user.farm.flower_id == '':
                return user.username + '，当前农场没有种植任何花。'
            if user.farm.flower_state == FlowerState.withered:
                return user.username + '，你的花已枯萎。'
            
            seed_time: int = flower.seed_time
            grow_time: int = seed_time + flower.grow_time
            mature_time: int = grow_time + flower.mature_time
            overripe_time: int = mature_time + flower.overripe_time
            if user.farm.hour <= grow_time:
                return user.username + '，你的花还未成熟。'
            elif user.farm.hour <= overripe_time:
                item: DecorateItem = DecorateItem()
                item_obj: Item = flower_dao.select_item_by_name(flower.name)
                if item_obj.name == '':
                    raise ItemNotFoundException('物品' + flower.name + '不存在')
                item.item_name = flower.name
                # 产量需要根据bad hour进行计算（最坏的情况产量只有50%）
                item.number = flower.flower_yield
                if flower.withered_time > 0:
                    ratio: float = user.farm.bad_hour / (flower.withered_time * 2)
                    item.number = int(flower.flower_yield * (1.0 - ratio))
                    if item.number == 0:
                        item.number = 1
                item.item_type = item_obj.item_type
                item.flower_quality = FlowerQuality.normal
                # 过熟阶段没法拿到完美的花
                if user.farm.flower_state == FlowerState.perfect and user.farm.hour <= mature_time:
                    item.flower_quality = FlowerQuality.perfect
                try:
                    number = item.number
                    util.insert_items(user.warehouse, [item])
                    user.farm.flower_id = ''
                    flower_dao.update_user_by_qq(user)
                    return user.username + '，收获成功，获得%s-%sx%d' % (flower.name,
                                                                 FlowerQuality.view_name(item.flower_quality),
                                                                 number)
                except WareHouseSizeNotEnoughException:
                    return user.username + '，收获失败，仓库空间不足。'
            else:
                return user.username + '，你的花已枯萎。'
        finally:
            flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))


class DrawCard:
    """
    抽卡类
    """
    
    @classmethod
    def draw_card(cls, qq: int, username: str) -> str:
        """
        抽卡
        :param qq: qq名
        :param username: 用户名
        :return:
        """
        flower_dao.lock(flower_dao.redis_user_lock_prefix + str(qq))
        try:
            user: User = util.get_user(qq, username)
            if user.draw_card_number <= 0:
                return ''
            rand: int = random.randint(0, global_config.draw_card_probability_unit)
            # 对于当天次数大于5次的，多余的部分按照第1个物品的概率去抽取，剩余的按照0、1、2、3、4依次类推
            draw_probability_index: int = global_config.draw_card_max_number - user.draw_card_number
            if draw_probability_index < 0:
                draw_probability_index = 0
            if rand < global_config.draw_card_probability[draw_probability_index]:
                # todo: 抽到物品（这部分需要在物品表完善之后完成）
                return '抽到物品'
            return ''
        except UserNotRegisteredException:
            return ''
        finally:
            flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))


if __name__ == '__main__':
    pass
