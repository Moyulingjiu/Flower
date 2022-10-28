# coding=utf-8
import copy
import os.path
import shutil
import random
from datetime import timedelta, datetime, date
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
from matplotlib import font_manager

from bson import ObjectId

# 引入所有组件
import flower_dao
import global_config
import util
import weather_getter
import world_handler
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
        # 面对极端情况可以清除缓存
        if len(at_list) == 0 and message == '花店清除缓存':
            util.lock_user(qq)
            origin_list, context_list = flower_dao.get_context(qq)
            for context in origin_list:
                flower_dao.remove_context(qq, context)
            util.unlock_user(qq)
            reply: str = '清除成功！'
            return Result.init(reply_text=reply)

        # 处理上下文需要加锁，避免两个线程同时处理到一个上下文
        util.lock_user(qq)
        context_handler: ContextHandler = ContextHandler()
        result: Result = context_handler.handle(message, qq, username, bot_qq, bot_name)
        # 如果阻断传播就已经可以停止了
        if (len(result.context_reply_text) != 0 or len(
                result.context_reply_image) != 0) and context_handler.block_transmission:
            return result
        util.unlock_user(qq)
        system_data: SystemData = util.get_system_data()

        if len(at_list) == 0:
            # 数据查询部分
            if message[:4] == '查询城市':
                name: str = message[4:].strip()
                if len(name) == 0 or ObjectId.is_valid(name):
                    raise TypeException('格式错误！格式“查询城市 名字”')
                reply = FlowerService.query_city(name)
                result.reply_text.append(reply)
                return result
            elif message[:4] == '查询土壤':
                name: str = message[4:].strip()
                if len(name) == 0 or ObjectId.is_valid(name):
                    raise TypeException('格式错误！格式“查询土壤 名字”')
                reply = FlowerService.query_soil(name)
                result.reply_text.append(reply)
                return result
            elif message[:5] == '查询花专辑':
                name: str = message[5:].strip()
                if len(name) > 0:
                    reply = FlowerService.view_flower_group(name)
                    result.reply_text.append(reply)
                    return result
            elif message[:3] == '查询花':
                name: str = message[3:].strip()
                if len(name) == 0 or ObjectId.is_valid(name):
                    raise TypeException('格式错误！格式“查询花 名字”')
                reply = FlowerService.query_flower(qq, username, name)
                result.reply_text.append(reply)
                return result
            elif message[:4] == '查询成就':
                name: str = message[4:].strip()
                if len(name) == 0 or ObjectId.is_valid(name):
                    raise TypeException('格式错误！格式“查询成就 名字”')
                reply = FlowerService.view_achievement(name)
                result.reply_text.append(reply)
                return result
            elif message[:6].lower() == '查询buff':
                name: str = message[6:].strip()
                if len(name) == 0 or ObjectId.is_valid(name):
                    raise TypeException('格式错误！格式“查询buff 名字”')
                reply = FlowerService.view_buff(name)
                result.reply_text.append(reply)
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
            elif message == '花店金币排行榜':
                reply = FlowerService.view_gold_rank()
                result.reply_text.append(reply)
                return result
            elif message == '花店赚取金币排行榜':
                reply = FlowerService.view_total_gold_rank()
                result.reply_text.append(reply)
                return result
            elif message == '花店等级排行榜':
                reply = FlowerService.view_exp_rank()
                result.reply_text.append(reply)
                return result
            elif message == '花店抽卡排行榜':
                reply = FlowerService.view_draw_card_rank()
                result.reply_text.append(reply)
                return result
            elif message == '花店签到排行榜':
                reply = FlowerService.view_sign_rank()
                result.reply_text.append(reply)
                return result
            elif message[:6] == '花店期货列表':
                data = message[6:].strip()
                if len(data) > 0:
                    try:
                        page: int = int(data)
                        page -= 1
                    except ValueError:
                        raise TypeException('格式错误！格式“花店期货列表 页码”，页码为1可以省略')
                else:
                    page: int = 0
                reply = FlowerService.view_all_trading_flower(page)
                result.reply_text.append(reply)
                return result
            elif message == '花店股市规则':
                reply = '1.股市一切内容与现实无关，现实投资有风险！\n' \
                        '2.你的交易请求不会立马完成！必须要有其他玩家或者npc买卖才能完成你的订单。\n' \
                        '3.交易税从当天买当天卖1%开始，到持仓15天20%线性增长。\n' \
                        '4.花店每天会提供部分贷款选项，记得及时还款，否则将会强制还款，若金币不足，将会强制破产清算，失去所有东西。'
                result.reply_text.append(reply)
                return result
            elif message == '花店股市帮助':
                if not os.path.exists('cache/股市帮助.png'):
                    try:
                        shutil.copyfile('doc/股市帮助.png', 'cache/股市帮助.png')
                    except IOError:
                        logger.error('错误！无权复制文件！')
                        result.reply_text.append(
                            '系统内部错误！请及时告知管理员检查日志，发生时间：%s' % datetime.now().strftime(
                                '%Y-%m-%d %H:%M:%S'))
                        return result
                result.reply_image.append('股市帮助.png')
                return result
            elif message[:6] == '花店价格走势':
                data = message[6:].strip()
                reply = FlowerService.generate_price_map(qq, username, data)
                if reply.endswith('.png'):
                    result.reply_image.append(reply)
                else:
                    result.reply_text.append(reply)
                return result
            elif message[:6] == '花店月度价格走势':
                data = message[6:].strip()
                # todo: 生成月度k线
            elif message == '花店上一期获奖情况':
                system_data: SystemData = util.get_system_data()
                reply = system_data.winning_lottery_info
                if reply == '':
                    reply = '上一期无人中奖'
                result.reply_text.append(reply)
                return result
            elif message == '花店奖金池':
                system_data: SystemData = util.get_system_data()
                reply = '当前奖金：' + util.show_gold(system_data.lottery_prize_pool)
                result.reply_text.append(reply)
                return result

            # 查看自己数据的部分
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
            elif message[:4] == '花店成就':
                data = message[4:].strip()
                try:
                    if len(data) > 0:
                        page: int = int(data) - 1
                    else:
                        page: int = 0
                    reply = FlowerService.view_user_achievement(qq, username, page)
                    result.reply_text.append(reply)
                    return result
                except ValueError:
                    raise '格式错误！格式“花店成就 【页码】”页码可省略。'
            elif message[:6] == '花店精简成就':
                data = message[6:].strip()
                try:
                    if len(data) > 0:
                        page: int = int(data) - 1
                    else:
                        page: int = 0
                    reply = FlowerService.view_user_simple_achievement(qq, username, page)
                    result.reply_text.append(reply)
                    return result
                except ValueError:
                    raise '格式错误！格式“花店精简成就 【页码】”页码可省略。'
            elif message[:6].lower() == '花店buff':
                data = message[6:].strip()
                try:
                    if len(data) > 0:
                        page: int = int(data) - 1
                    else:
                        page: int = 0
                    reply = FlowerService.view_user_buff(qq, username, page)
                    result.reply_text.append(reply)
                    return result
                except ValueError:
                    raise '格式错误！格式“花店buff 【页码】”页码可省略。'
            elif message[:4] == '花店知识':
                data = message[4:].strip()
                try:
                    if len(data) > 0:
                        page: int = int(data) - 1
                    else:
                        page: int = 0
                    reply = FlowerService.view_knowledge(qq, username, page)
                    result.reply_text.append(reply)
                    return result
                except ValueError:
                    raise '格式错误！格式“花店知识 【页码】”页码可省略。'
            elif message == '花店时装':
                reply = FlowerService.view_user_clothing(qq, username)
                result.reply_text.append(reply)
                return result
            elif message == '花店人物':
                reply = FlowerService.view_today_person(qq, username)
                result.reply_text.append(reply)
                return result
            elif message[:4] == '花店人物':
                data = message[4:].strip()
                try:
                    index: int = int(data)
                    reply = FlowerService.view_today_person_index(qq, username, index)
                    result.reply_text.append(reply)
                    return result
                except ValueError:
                    raise TypeException('格式错误！格式“花店人物 序号”来查看某个具体的人')
            elif message == '花店统计数据':
                reply = FlowerService.view_user_statistics(qq, username)
                result.reply_text.append(reply)
                return result
            elif message == '花店账户':
                reply = FlowerService.view_user_account(qq, username)
                result.reply_text.append(reply)
                return result
            elif message[:6] == '花店交易状态':
                page: int = util.get_page(message[6:].strip(), '格式错误！格式“花店交易状态 页码”')
                reply = FlowerService.view_trade_states(qq, username, page)
                result.reply_text.append(reply)
                return result
            elif message[:6] == '花店持仓状态':
                page: int = util.get_page(message[6:].strip(), '格式错误！格式“花店持仓状态 页码”')
                reply = FlowerService.view_hold_stock(qq, username, page)
                result.reply_text.append(reply)
                return result
            elif message == '花店贷款状态':
                reply = FlowerService.view_debt(qq)
                result.reply_text.append(reply)
                return result
            elif message == '花店可选贷款':
                reply: str = FlowerService.view_all_today_debt_choice(qq)
                result.reply_text.append(reply)
                return result
            elif message[:6] == '花店可选贷款':
                index: int = util.get_page(message[6:].strip(), '格式错误！格式“花店可选贷款 页码”')
                reply: str = FlowerService.view_today_debt_choice(qq, index)
                result.reply_text.append(reply)
                return result

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
            elif message[:4] == '花店使用':
                data = message[4:].strip()
                try:
                    util.lock_user(qq)
                    user: User = util.get_user(qq, username)
                    item: DecorateItem = util.analysis_item(data)
                    if (item.item_type == ItemType.flower and item.flower_quality != FlowerQuality.perfect) or \
                            item.max_durability > 0 or item.rot_second > 0 or item.item_type == ItemType.accelerate:
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
                                    number: int = item.number
                                    item = copy.deepcopy(warehouse_item)
                                    item.number = number
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
                        number: int = item.number
                        item = copy.deepcopy(item_list[0])
                        item.number = number
                    util.unlock_user(qq)
                    reply = FlowerService.use_item(qq, username, item)
                    result.reply_text.append(reply)
                    return result
                except TypeException:
                    raise TypeException('格式错误，格式“使用 【物品名字】 【数量】”')
                except ItemNotFoundException:
                    raise TypeException('该物品不存在！')
            elif message[:4] == '花店丢弃':
                data = message[4:].strip()
                try:
                    util.lock_user(qq)
                    user: User = util.get_user(qq, username)
                    item: DecorateItem = util.analysis_item(data)
                    if (item.item_type == ItemType.flower and item.flower_quality != FlowerQuality.perfect) or \
                            item.max_durability > 0 or item.rot_second > 0 or item.item_type == ItemType.accelerate:
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
                                    number: int = item.number
                                    item = copy.deepcopy(warehouse_item)
                                    item.number = number
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
                        number: int = item.number
                        item = copy.deepcopy(item_list[0])
                        item.number = number
                    util.unlock_user(qq)
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
            elif message == '花店收获':
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
                for word in system_data.username_screen_words:
                    if word in new_username:
                        raise TypeException('名字中含有违禁词或敏感词汇')
                if '_' in new_username:
                    raise TypeException('不能包含下划线')
                if not (1 < len(new_username) < global_config.object_id_length):
                    raise TypeException('名字长度不符合规范，必须按在2~%d内' % (global_config.object_id_length - 1))
                reply = FlowerService.change_username(qq, username, new_username)
                result.reply_text.append(reply)
                return result
            elif message == '清除花店昵称':
                reply = FlowerService.clear_username(qq, username)
                result.reply_text.append(reply)
                return result
            elif message == '整理花店仓库':
                util.lock_user(qq)
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
            elif message[:6] == '花店购买商品':
                data = message[6:].strip()
                data_list = data.split(' ')
                if len(data_list) < 2 or len(data_list) > 3:
                    raise TypeException('格式错误！格式“花店购买商品 人物序号 商品序号 数量”数量为1可以省略，'
                                        '人物序号可以通过命令“花店人物”查看')
                try:
                    user_person_id: int = int(data_list[0])
                    commodity_id: int = int(data_list[1])
                    if len(data_list) == 3:
                        number: int = int(data_list[2])
                    else:
                        number: int = 1
                    reply = FlowerService.buy_commodity(qq, username, user_person_id, commodity_id, number)
                    result.reply_text.append(reply)
                    return result
                except ValueError:
                    raise TypeException('格式错误！格式“花店购买商品 人物序号 商品序号 数量”数量为1可以省略，'
                                        '人物序号可以通过命令“花店人物”查看')
            elif message[:6] == '花店购买知识':
                data = message[6:].strip()
                data_list = data.split(' ')
                if len(data_list) != 2:
                    raise TypeException('格式错误！格式“花店购买知识 人物序号 花名”，人物序号可以通过命令“花店人物”查看')
                try:
                    user_person_id: int = int(data_list[0])
                    flower_name: str = data_list[1]
                    if '-' in flower_name:
                        flower_name = flower_name[:flower_name.rindex('-')]
                    reply = FlowerService.buy_knowledge(qq, username, user_person_id, flower_name)
                    result.reply_text.append(reply)
                    return result
                except ValueError:
                    raise TypeException('格式错误！格式“花店购买知识 人物序号 花名”，人物序号可以通过命令“花店人物”查看')
            elif message[:6] == '花店出售商品':
                data = message[6:].strip()
                data_list = data.split(' ')
                try:
                    if len(data_list) < 1:
                        raise TypeException('')
                    person_index: int = int(data_list[0])
                    if len(data_list) == 2:
                        item_origin_name: str = data_list[1]
                    elif len(data_list) == 3:
                        item_origin_name: str = data_list[1] + ' ' + data_list[2]
                    else:
                        raise TypeException('')
                    util.lock_user(qq)
                    user: User = util.get_user(qq, username)
                    item: DecorateItem = util.analysis_item(item_origin_name)
                    if (item.item_type == ItemType.flower and item.flower_quality != FlowerQuality.perfect) or \
                            item.max_durability > 0 or item.rot_second > 0 or item.item_type == ItemType.accelerate:
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
                                    number: int = item.number
                                    item = copy.deepcopy(warehouse_item)
                                    item.number = number
                                    args = {
                                        'qq': qq,
                                        'username': username,
                                        'person_index': person_index,
                                        'item': copy.deepcopy(item)
                                    }
                                    choices[str(index)] = Choice(args=args, callback=FlowerService.sell_commodity)
                                    similar_items_name.append(warehouse_item)
                            reply += '\n请输入对应的序号，选择是哪一种物品。例如输入“1”选择第一种的物品。其余任意输入取消'
                            if len(similar_items_name) > 1:
                                flower_dao.insert_context(qq, ChooseContext(choices=choices))
                                result.reply_text.append(reply)
                                return result
                        # 如果只有一件物品，出售的只能是它
                        number: int = item.number
                        item = copy.deepcopy(item_list[0])
                        item.number = number
                    util.unlock_user(qq)
                    reply = FlowerService.sell_commodity(qq, username, person_index, item)
                    result.reply_text.append(reply)
                    return result
                except TypeException or ValueError:
                    raise TypeException('格式错误，格式“花店出售商品 【人物序号】 【物品名字】 【数量】”数量为1可以省略')
                except ItemNotFoundException:
                    raise TypeException('该物品不存在！')
            elif message[:4] == '花店送信':
                data = message[4:].strip()
                try:
                    person_number: int = int(data)
                    reply = FlowerService.send_mail(qq, username, person_number)
                    result.reply_text.append(reply)
                    return result
                except ValueError:
                    raise TypeException('格式错误，格式“花店送信 【人物序号】”')
            elif message[:4] == '花店开户':
                data = message[4:].strip()
                try:
                    person_index: int = int(data)
                    reply = FlowerService.create_account(qq, username, person_index)
                    result.reply_text.append(reply)
                    return result
                except ValueError:
                    raise TypeException('格式错误，格式“花店开户 【人物序号】”')
            elif message[:6] == '花店买入期货':
                data = message[6:].strip()
                try:
                    data_list = data.split(' ')
                    if len(data_list) == 2:
                        name = data_list[0]
                        price: int = int(float(data_list[1]) * 100)
                        number = 1
                    elif len(data_list) == 3:
                        name = data_list[0]
                        price: int = int(float(data_list[1]) * 100)
                        number = int(data_list[2])
                    else:
                        raise TypeException('')
                except ValueError or TypeException:
                    raise TypeException('格式错误，格式“花店买入期货 货品名 最高交易价格 数量”，数量为1可以省略')
                reply = FlowerService.buy_futures(qq, username, name, price, number)
                result.reply_text.append(reply)
                return result
            elif message[:6] == '花店卖出期货':
                data = message[6:].strip()
                try:
                    data_list = data.split(' ')
                    if len(data_list) == 2:
                        name = data_list[0]
                        price: int = int(float(data_list[1]) * 100)
                        number = 1
                    elif len(data_list) == 3:
                        name = data_list[0]
                        price: int = int(float(data_list[1]) * 100)
                        number = int(data_list[2])
                    else:
                        raise TypeException('')
                except ValueError or TypeException:
                    raise TypeException('格式错误，格式“花店卖出期货 货品名 最高交易价格 数量”，数量为1可以省略')
                reply = FlowerService.sell_futures(qq, username, name, price, number)
                result.reply_text.append(reply)
                return result
            elif message[:6] == '花店转入金币':
                data = message[6:]
                try:
                    gold_float: float = float(data)
                    gold: int = int(gold_float * 100)
                except ValueError:
                    raise TypeException('格式错误！格式“花店转入金币 金币数量”')
                reply = FlowerService.transfer_in(qq, username, gold)
                result.reply_text.append(reply)
                return result
            elif message[:6] == '花店转出金币':
                data = message[6:]
                try:
                    gold_float: float = float(data)
                    gold: int = int(gold_float * 100)
                except ValueError:
                    raise TypeException('格式错误！格式“花店转出金币 金币数量”')
                reply = FlowerService.transfer_out(qq, username, gold)
                result.reply_text.append(reply)
                return result
            elif message[:4] == '花店贷款':
                index: int = util.get_page(message[4:].strip(), '格式错误！格式“花店贷款 序号”', no_default_number=True)
                reply = FlowerService.get_debt(qq, index)
                result.reply_text.append(reply)
                return result
            elif message[:4] == '花店还款':
                index: int = util.get_page(message[4:].strip())
                reply = FlowerService.repayment_debt(qq, username, index)
                result.reply_text.append(reply)
                return result
            elif message == '花店购买彩票':
                reply = FlowerService.buy_lottery(qq, username)
                result.reply_text.append(reply)
                return result
        else:
            if message[:4] == '花店转账':
                data: str = message[4:]
                try:
                    origin_gold: float = float(data)
                    origin_gold *= 100.0
                    gold: int = int(origin_gold)
                except ValueError:
                    raise TypeException('格式错误，格式“@xxx 花店转账 【数字】”')
                if gold <= 0:
                    raise TypeException('格式错误，格式“@xxx 花店转账 【数字】”，数字不可以小于等于0')
                reply = FlowerService.transfer_accounts(qq, username, at_list, gold)
                result.reply_text.append(reply)
                return result

        # 管理员（admin、master）操作
        user_right: UserRight = util.get_user_right(qq)
        if user_right == UserRight.ADMIN or user_right == UserRight.MASTER:
            get_reply: bool = False
            reply: str = AdminHandler.handle(message, qq, username, at_list)
            if reply != '':
                get_reply = True
                result.reply_text.append(reply)
            reply: str = WorldControlHandler.handle(message, qq)
            if reply != '':
                get_reply = True
                result.reply_text.append(reply)
            if get_reply:
                return result
    except UserNotRegisteredException:
        return Result.init(reply_text='您还未初始化花店账号，请输入“初始化花店”进行初始化')
    except ResBeLockedException:
        logger.warning('用户被锁定%s<%d>@%s<%d>' % (username, qq, bot_name, bot_qq))
        return Result.init(
            reply_text='操作超时，请稍后再试\n'
                       '出现的原因可能有：\n'
                       '1.您的操作过于频繁，请稍后再试\n'
                       '2.账号风险行为，耐心等待两小时重置\n'
                       '3.网络波动'
        )
    except NoAccount:
        return Result.init(reply_text='您没有花店账户，需要在交易员处进行开户才能进行交易')
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
    except ResourceNotFound as e:
        return Result.init(reply_text=e.message)
    except Exception as e:
        logger.error('未知错误，触发原因：%s@<%s>(%d)' % (message, username, qq))
        logger.error(str(e))
    finally:
        util.unlock_user(qq)
    return Result.init()


class AdminHandler:
    """
    管理员指令处理器
    """

    @classmethod
    def handle(cls, message: str, qq: int, username: str, at_list: List[int]) -> str:
        system_data: SystemData = util.get_system_data()
        # 排行榜部分
        if message == '调试花店金币排行榜':
            return FlowerService.view_gold_rank(debug=True)
        elif message == '调试花店赚取金币排行榜':
            return FlowerService.view_total_gold_rank(debug=True)
        elif message == '调试花店等级排行榜':
            return FlowerService.view_exp_rank(debug=True)
        elif message == '调试花店抽卡排行榜':
            return FlowerService.view_draw_card_rank(debug=True)
        elif message == '调试花店签到排行榜':
            return FlowerService.view_sign_rank(debug=True)
        # 修改他人数据
        elif message == '花店时间':
            return '当前服务器时间：' + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        elif message[:4] == '给予金币':
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
                return '未能给予任何人金币，请检查是否注册'
        elif message[:4] == '修改金币':
            data: str = message[4:].strip()
            try:
                origin_gold: float = float(data)
                origin_gold *= 100.0
                gold: int = int(origin_gold)
            except ValueError:
                raise TypeException('格式错误，格式“@xxx 修改金币 【数字】”')
            update_number: int = 0
            if len(at_list) == 0:
                if cls.give_gold(qq, qq, gold, replace=True):
                    update_number += 1
            else:
                for target_qq in at_list:
                    if cls.give_gold(target_qq, qq, gold, replace=True):
                        update_number += 1
            if update_number > 0:
                return '成功修改金币' + str(update_number) + '人'
            else:
                return '未能修改任何人金币，请检查是否注册'
        elif message[:4] == '给予物品':
            data: str = message[4:].strip()
            try:
                item: DecorateItem = util.analysis_item(data)
                item.create = datetime.now()
                item.update = datetime.now()
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
                return '未能给予任何人' + item.item_name + '，请检查是否注册'
        elif message[:4] == '修改温度':
            data: str = message[4:].strip()
            try:
                temperature: float = float(data)
                update_number: int = 0
                if len(at_list) == 0:
                    if cls.edit_temperature(qq, qq, temperature=temperature):
                        update_number += 1
                else:
                    for target_qq in at_list:
                        if cls.edit_temperature(target_qq, qq, temperature=temperature):
                            update_number += 1
                if update_number > 0:
                    return '成功修改' + str(update_number) + '人'
                return '未能修改任何人的温度，请检查是否注册'
            except ValueError:
                raise TypeException('格式错误！，格式“@xxx 修改湿度 【湿度】”。湿度为任意小数。')
        elif message[:4] == '修改湿度':
            data: str = message[4:].strip()
            try:
                humidity: float = float(data)
                if humidity > system_data.soil_max_humidity or humidity < system_data.soil_min_humidity:
                    raise TypeException('格式错误！湿度范围为%.2f~%.2f' % (
                        system_data.soil_min_humidity,
                        system_data.soil_max_humidity
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
                return '未能修改任何人的湿度，请检查是否注册'
            except ValueError:
                raise TypeException('格式错误！，格式“@xxx 修改湿度 【湿度】”。湿度为任意小数。')
        elif message[:4] == '修改营养':
            data: str = message[4:].strip()
            try:
                nutrition: float = float(data)
                if nutrition > system_data.soil_max_nutrition or nutrition < system_data.soil_min_nutrition:
                    raise TypeException('格式错误！营养范围为%.2f~%.2f' % (
                        system_data.soil_min_nutrition,
                        system_data.soil_max_nutrition
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
                return '未能修改任何人的营养，请检查是否注册'
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
            return '未能修改任何人的土壤，请检查是否注册'
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
            return '未能修改任何人的城市，请检查是否注册'
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
            return '未能修改任何人的农场气候，请检查是否注册'
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
            return '未能移除任何人农场的花，请检查是否注册'
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
        elif message == '给予buff':
            context: GiveBuffContext = GiveBuffContext()
            if len(at_list) > 0:
                context.target_qq_list = at_list
            else:
                context.target_qq_list.append(qq)
            flower_dao.insert_context(qq, context)
            return '请问buff名字是什么？（输入“取消”来取消）'
        elif message[:8] == '删除花店buff':
            data = message[8:].strip()
            if len(data) == 0:
                index = -1
            else:
                try:
                    index = int(data) - 1
                except ValueError:
                    raise TypeException('格式错误！格式“@xxx 清除花店buff 序号”，序号省略表示清除全部')
            update_number: int = 0
            if len(at_list) == 0:
                if cls.remove_user_buff(qq, qq, index):
                    update_number += 1
            else:
                for target_qq in at_list:
                    if cls.remove_user_buff(target_qq, qq, index):
                        update_number += 1
            if update_number > 0:
                return '成功清除' + str(update_number) + '人的buff'
            return '未能清除任何人的buff，请检查是否注册或者序号越界'
        elif message[:4] == '给予知识':
            try:
                data: List[str] = message[4:].strip().split()
                if len(data) != 2:
                    raise TypeException('格式错误！格式“@xxx 给予知识 花名 级别”，最低1级，最高4级')
                flower_name = data[0]
                level: int = int(data[1])
                if level < 1 or level > 4:
                    raise TypeException('格式错误！格式“@xxx 给予知识 花名 级别”，最低1级，最高4级')
                update_number: int = 0
                if len(at_list) == 0:
                    if cls.give_knowledge(qq, qq, flower_name, level):
                        update_number += 1
                else:
                    for target_qq in at_list:
                        if cls.give_knowledge(target_qq, qq, flower_name, level):
                            update_number += 1
                if update_number > 0:
                    return '成功修改' + str(update_number) + '人的知识'
                return '未能修改任何人的知识'
            except ValueError:
                raise TypeException('格式错误！格式“@xxx 给予知识 花名 级别”，最低1级，最高4级')
        elif message[:4] == '删除知识':
            data = message[4:].strip()
            if len(data) == 0:
                raise TypeException('格式错误！格式“@xxx 删除知识 花名”')
            update_number: int = 0
            if len(at_list) == 0:
                if cls.remove_knowledge(qq, qq, data):
                    update_number += 1
            else:
                for target_qq in at_list:
                    if cls.remove_knowledge(target_qq, qq, data):
                        update_number += 1
            if update_number > 0:
                return '成功删除' + str(update_number) + '人的知识'
            return '未能删除任何人的知识\n' \
                   '可能是：目标没有该知识、目标没有注册'

        # 查看他人数据
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
        elif message == '调试花店农场':
            if len(at_list) > 1:
                raise TypeException('格式错误，格式“@xxx 调试花店农场”，艾特省略查看自己，最多艾特一人')
            target_qq: int = qq
            if len(at_list) == 1:
                target_qq = at_list[0]
            return cls.debug_user_farm(target_qq)
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
        elif message[:4] == '花店成就':
            if len(at_list) != 1:
                raise TypeException('格式错误，格式“@xxx 花店成就 【页码】”，页码可省略')
            data = message[4:].strip()
            try:
                if len(data) > 0:
                    page: int = int(data) - 1
                else:
                    page: int = 0
                return FlowerService.view_user_achievement(at_list[0], '', page)
            except ValueError:
                raise '格式错误！格式“@xxx 花店成就 【页码】”页码可省略。'
            except UserNotRegisteredException:
                return '对方未注册'
        elif message[:6] == '花店精简成就':
            if len(at_list) != 1:
                raise TypeException('格式错误，格式“@xxx 花店精简成就 【页码】”，页码可省略')
            data = message[6:].strip()
            try:
                if len(data) > 0:
                    page: int = int(data) - 1
                else:
                    page: int = 0
                return FlowerService.view_user_simple_achievement(at_list[0], '', page)
            except ValueError:
                raise '格式错误！格式“@xxx 花店精简成就 【页码】”页码可省略。'
            except UserNotRegisteredException:
                return '对方未注册'
        elif message[:6].lower() == '花店buff':
            if len(at_list) != 1:
                raise TypeException('格式错误，格式“@xxx 花店信箱 【序号】”，省略序号查看整个信箱，必须并且只能艾特一人')
            data = message[6:].strip()
            try:
                if len(data) > 0:
                    page: int = int(data) - 1
                else:
                    page: int = 0
                return FlowerService.view_user_buff(at_list[0], '', page)
            except ValueError:
                raise '格式错误！格式“@xxx 花店buff 【页码】”页码可省略。'
            except UserNotRegisteredException:
                return '对方未注册'
        elif message[:4] == '花店知识':
            if len(at_list) != 1:
                raise TypeException('格式错误，格式“@xxx 花店知识 【页码】”，必须并且只能艾特一人')
            data = message[4:].strip()
            try:
                if len(data) > 0:
                    page: int = int(data) - 1
                else:
                    page: int = 0
                return FlowerService.view_knowledge(at_list[0], '', page)
            except ValueError:
                raise '格式错误！格式“@xxx 花店知识 【页码】”页码可省略。'
            except UserNotRegisteredException:
                return '对方未注册'
        elif message == '花店人物':
            if len(at_list) != 1:
                raise TypeException('格式错误，格式“@xxx 花店人物”，必须并且只能艾特一人')
            return FlowerService.view_today_person(at_list[0], '')
        elif message[:4] == '花店人物':
            if len(at_list) != 1:
                raise TypeException('格式错误，格式“@xxx 花店人物 序号”，必须并且只能艾特一人')
            data = message[4:].strip()
            try:
                index: int = int(data)
                return FlowerService.view_today_person_index(at_list[0], '', index)
            except ValueError:
                raise TypeException('格式错误，格式“@xxx 花店人物 序号”，必须并且只能艾特一人')
        elif message == '花店统计数据':
            if len(at_list) != 1:
                raise TypeException('格式错误，格式“@xxx 花店统计数据”，必须并且只能艾特一人')
            return FlowerService.view_user_statistics(at_list[0], '')

        # 游戏管理部分
        elif message == '发送信件':
            context: AdminSendMailContext = AdminSendMailContext()
            flower_dao.insert_context(qq, context)
            return '请问信件的标题是什么？只可以包含文字。'
        elif message == '发送公告':
            announcement_context: AnnouncementContext = AnnouncementContext()
            flower_dao.insert_context(qq, announcement_context)
            return '请问公告的正文是什么，只可以包含文字信息！'
        elif message[:9] == '在该机器人留言花店':
            data: List[str] = message[9:].strip().split(' ')
            if len(data) != 2 or len(data[1]) == 0:
                raise TypeException('格式错误！格式“在该机器人留言花店 QQ号 留言内容”留言内容只可以是文字')
            try:
                target_qq: int = int(data[0])
                util.leave_message(target_qq, data[1])
                return '留言成功！'
            except ValueError:
                raise TypeException('格式错误！格式“在该机器人留言花店 QQ号 留言内容”留言内容只可以是文字')
        # 系统操作部分
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
                system_data: SystemData = util.get_system_data()
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
        elif message == '更新所有城市天气':
            @async_function
            def get_all_weather():
                logger.info('管理员%s<%d>开始更新所有城市天气' % (username, qq))
                util.get_all_weather(force=True)

            if global_config.get_all_weather:
                return '请勿重复发起获取请求，已经有更新请求正在运行，该行为会花费较长时间。'
            global_config.get_all_weather = True
            get_all_weather()
            return '预计需要3~5分钟获取爬取所有城市天气。该命令用于没有24小时运行时的手动更新，正常运行下请勿使用该命令！！！以免造成资源浪费'
        elif message == '更新所有城市天气的状态':
            if global_config.get_all_weather:
                return '线程仍然在进行“爬取所有城市天气”的活动'
            return '当前没有进行“爬取所有城市天气”'
        elif message == '花店玩家数量':
            number: int = flower_dao.select_all_user_number()
            return '玩家总数：%d' % number
        elif message == '锁定花店':
            util.lock_the_world()
            return '锁定后，需要手动重启！'
        return ''

    @classmethod
    def give_gold(cls, qq: int, operator_id: int, gold: int, replace: bool = False) -> bool:
        """
        给予金币
        :param qq: qq号
        :param operator_id: 操作员id
        :param gold: 金币数量（单位：0.01）
        :param replace: 是否为替换
        :return:
        """
        util.lock_user(qq)
        try:
            user: User = util.get_user(qq, '')
            if not replace:
                user.get_gold(gold)
            else:
                user.gold = gold
            user.update(operator_id)
            flower_dao.update_user_by_qq(user)
            return True
        except UserNotRegisteredException:
            return False
        finally:
            util.unlock_user(qq)

    @classmethod
    def give_item(cls, qq: int, operator_id: int, item: DecorateItem) -> bool:
        util.lock_user(qq)
        try:
            user: User = util.get_user(qq, '')
            util.insert_items(user.warehouse, [copy.deepcopy(item)])
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
            util.unlock_user(qq)

    @classmethod
    def edit_temperature(cls, qq: int, operator_id: int, temperature: float):
        try:
            util.lock_user(qq)
            user: User = util.get_user(qq, '')
            user.farm.temperature = temperature
            user.update(operator_id)
            flower_dao.update_user_by_qq(user)
            return True
        except UserNotRegisteredException:
            return False
        finally:
            util.unlock_user(qq)

    @classmethod
    def edit_humidity_nutrition(cls, qq: int, operator_id: int, humidity: float = -1.0,
                                nutrition: float = -1.0) -> bool:
        try:
            util.lock_user(qq)
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
            util.unlock_user(qq)

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
            util.lock_user(qq)
            user: User = util.get_user(qq, '')
            user.city_id = city_id
            user.update(operator_id)
            flower_dao.update_user_by_qq(user)
            return True
        except UserNotRegisteredException:
            return False
        finally:
            util.unlock_user(qq)

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
            util.lock_user(qq)
            user: User = util.get_user(qq, '')
            user.farm.soil_id = soil_id
            user.update(operator_id)
            flower_dao.update_user_by_qq(user)
            return True
        except UserNotRegisteredException:
            return False
        finally:
            util.unlock_user(qq)

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
            util.lock_user(qq)
            user: User = util.get_user(qq, '')
            user.farm.climate_id = climate_id
            user.update(operator_id)
            flower_dao.update_user_by_qq(user)
            return True
        except UserNotRegisteredException:
            return False
        finally:
            util.unlock_user(qq)

    @classmethod
    def remove_farm_flower(cls, qq: int, operator_id: int) -> bool:
        try:
            util.lock_user(qq)
            user: User = util.get_user(qq, '')
            user.farm.flower_id = ''
            user_statistics: UserStatistics = util.get_user_statistics(qq)
            user_statistics.remove_flower += 1
            flower_dao.update_user_statistics(user_statistics)
            user.update(operator_id)
            flower_dao.update_user_by_qq(user)
            return True
        except UserNotRegisteredException:
            return False
        finally:
            util.unlock_user(qq)

    @classmethod
    def append_username_screen_word(cls, screen_word: str) -> bool:
        # 对于系统数据是没有加锁的（因为管理员操作缓慢，系统设计只有一个管理员）
        system_data: SystemData = util.get_system_data()
        if screen_word not in system_data.username_screen_words:
            system_data.username_screen_words.append(screen_word)
            flower_dao.update_system_data(system_data)
            return True
        return False

    @classmethod
    def remove_username_screen_word(cls, screen_word: str) -> bool:
        # 对于系统数据是没有加锁的（因为管理员操作缓慢，系统设计只有一个管理员）
        system_data: SystemData = util.get_system_data()
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
            util.lock_user(qq)
            user: User = util.get_user(qq, '')
            user.farm.last_check_time -= timedelta(hours=hour)
            user.accelerate_buff(seconds=global_config.hour_second * hour)
            city: City = flower_dao.select_city_by_id(user.city_id)
            flower: Flower = flower_dao.select_flower_by_id(user.farm.flower_id)
            soil: Soil = flower_dao.select_soil_by_id(user.farm.soil_id)
            weather: Weather = util.get_weather(city)
            util.update_farm(user, city, soil, weather, flower)
            user.update(operator_id)
            flower_dao.update_user_by_qq(user)
            return True
        except UserNotRegisteredException:
            return False
        finally:
            util.unlock_user(qq)

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
            util.lock_user(qq)
            user: User = util.get_user(qq, '')
            user.farm.hour += hour
            user.update(operator_id)
            flower_dao.update_user_by_qq(user)
            return True
        except UserNotRegisteredException:
            return False
        finally:
            util.unlock_user(qq)

    @classmethod
    def debug_user_farm(cls, qq: int) -> str:
        """
        查看用户农场
        :param qq: QQ
        :return:
        """
        util.lock_user(qq)
        user, city, soil, climate, weather, flower = util.get_farm_information(qq, '')
        now_temperature = util.get_now_temperature(weather)
        util.update_farm(user, city, soil, weather, flower)
        flower_dao.update_user_by_qq(user)
        util.unlock_user(qq)

        reply = user.username + '的农场：'
        reply += '\n种植的花：'
        if user.farm.flower_id != '':
            reply += flower.name
            reply += '\n花的状态：' + FlowerState.view_name(user.farm.flower_state)

            seed_time: int = flower.seed_time
            grow_time: int = seed_time + flower.grow_time
            mature_time: int = grow_time + flower.mature_time
            overripe_time: int = mature_time + flower.overripe_time
            if user.farm.hour < seed_time:
                reply += '\n阶段：种子'
            elif user.farm.hour < grow_time:
                reply += '\n阶段：幼苗'
            elif user.farm.hour < mature_time:
                reply += '\n阶段：成熟'
            elif user.farm.hour < overripe_time:
                reply += '\n阶段：过熟'
            else:
                reply += '\n阶段：枯萎'
            total_hour: int = flower.seed_time + flower.grow_time
            reply += '\n成长度：' + '%.1f%%' % (user.farm.hour * 100.0 / total_hour)
            reply += '\n成长小时数：%.1f/%d' % (user.farm.hour, total_hour)
            reply += '\n完美小时数：%d/%d' % (user.farm.perfect_hour, flower.prefect_time)
            reply += '\n糟糕小时数：%d/%d' % (user.farm.bad_hour, flower.withered_time)
            reply += '\n上一次计算时间：%s' % user.farm.last_check_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            reply += '无'
        reply += '\n天气：' + weather.weather_type
        reply += '\n气温：%.2f' % user.farm.temperature
        if user.farm.temperature > now_temperature:
            reply += '（↓）'
        elif user.farm.temperature < now_temperature:
            reply += '（↑）'
        else:
            reply += '（=）'
        reply += '\n土壤湿度：%.2f' % user.farm.humidity
        reply += '\n土壤营养：%.2f' % user.farm.nutrition

        reply += '\n马：'
        if user.farm.horse.name != '':
            reply += user.farm.horse.name
            reply += '（%d/%d岁）' % (
                (datetime.now() - user.farm.horse.born_time).total_seconds() * 2 // global_config.day_second,
                user.farm.horse.max_age
            )
        else:
            reply += '暂无'
        reply += '\n狗：'
        if user.farm.dog.name != '':
            reply += user.farm.dog.name
            reply += '（%d/%d岁）' % (
                (datetime.now() - user.farm.dog.born_time).total_seconds() * 2 // global_config.day_second,
                user.farm.dog.max_age
            )
        else:
            reply += '暂无'
        reply += '\n猫：'
        if user.farm.cat.name != '':
            reply += user.farm.cat.name
            reply += '（%d/%d岁）' % (
                (datetime.now() - user.farm.cat.born_time).total_seconds() * 2 // global_config.day_second,
                user.farm.cat.max_age
            )
        else:
            reply += '暂无'

        return reply

    @classmethod
    def remove_user_buff(cls, qq: int, operator_id: int, index: int = -1) -> bool:
        """
        清除用户buff
        :param qq: qq
        :param operator_id: 操作员id
        :param index: 序号
        :return: 结果
        """
        try:
            util.lock_user(qq)
            user: User = util.get_user(qq, '')
            if index == -1:
                user.buff = []
            else:
                if 0 <= index < len(user.buff):
                    del user.buff[index]
            user.update(operator_id)
            flower_dao.update_user_by_qq(user)
            return True
        except UserNotRegisteredException:
            return False
        finally:
            util.unlock_user(qq)

    @classmethod
    def give_knowledge(cls, qq: int, operator_id: int, flower_name: str, level: int) -> bool:
        """
        修改知识
        :param qq: qq
        :param operator_id: 操作人员id
        :param flower_name: 花名
        :param level: 级别
        :return: 结果
        """
        try:
            util.lock_user(qq)
            user: User = util.get_user(qq, '')
            user.knowledge[flower_name] = level
            user.update(operator_id)
            flower_dao.update_user_by_qq(user)
            return True
        except UserNotRegisteredException:
            return False
        finally:
            util.unlock_user(qq)

    @classmethod
    def remove_knowledge(cls, qq: int, operator_id: int, flower_name: str) -> bool:
        """
        删除知识
        :param qq: qq
        :param operator_id: 操作人员id
        :param flower_name: 花名
        :return: 结果
        """
        try:
            util.lock_user(qq)
            user: User = util.get_user(qq, '')
            if flower_name in user.knowledge:
                del user.knowledge[flower_name]
                user.update(operator_id)
                flower_dao.update_user_by_qq(user)
                return True
            else:
                return False
        except UserNotRegisteredException:
            return False
        finally:
            util.unlock_user(qq)


class WorldControlHandler:
    """
    世界控制入口
    """

    @classmethod
    def handle(cls, message: str, qq: int) -> str:
        if message == '创建人物':
            person: Person = world_handler.random_person()
            reply = 'id:%s' % person.get_id()
            reply += '\n名字：%s' % person.name
            reply += '\n年龄：%d/%d岁' % (
                ((datetime.now() - person.born_time).total_seconds() // (24 * 3600)), person.max_age)
            if person.die:
                reply += '（已于%s死亡）' % person.die_time.strftime('%Y-%m-%d %H:%M:%S')
                reply += '\n死亡原因：%s' % person.die_reason
            reply += '\n性别：%s，性取向：%s' % (person.gender.show(), person.sexual_orientation.show())
            reply += '\n身高：%.2fm，体重：%.2fkg' % (person.height, person.weight)
            father_name: str = ''
            if person.father_id != '':
                father: Person = flower_dao.select_person(person.father_id)
                father_name = father.name
            mother_name: str = ''
            if person.father_id != '':
                mother: Person = flower_dao.select_person(person.mother_id)
                mother_name = mother.name
            reply += '\n父亲：%s（%s），母亲：%s（%s）' % (father_name, person.father_id, mother_name, person.mother_id)
            born_area: WorldArea = flower_dao.select_world_area(person.born_area_id)
            area: WorldArea = flower_dao.select_world_area(person.world_area_id)
            reply += '\n出生地：%s，现在所在地：%s' % (born_area.name, area.name)
            kingdom: Kingdom = flower_dao.select_kingdom(person.motherland)
            reply += '\n祖国：%s' % kingdom.name
            race: Race = flower_dao.select_world_race(person.race_id)
            reply += '\n种族：%s' % race.name
            reply += '\n疾病：%s' % person.disease_id
            reply += '\n职业：%s' % person.profession_id
            reply += '\n' + ('-' * 6)
            reply += '\n基础属性：'
            reply += '\n智慧：%d，领导力：%d，武力：%d，亲和力：%d，野心：%d，健康：%d，外貌：%d' % (
                person.wisdom, person.leadership, person.force, person.affinity, person.ambition, person.health,
                person.appearance
            )
            reply += '\n外貌描述：%s' % person.appearance_description
            reply += '\n' + ('-' * 6)
            reply += '\n性格（以下描述词越小越靠近左边的词，越大越靠近右边的词）'
            reply += '\n邪恶/正义：%d' % person.justice_or_evil
            reply += '\n内向/外向：%d' % person.extroversion_or_introversion
            reply += '\n胆怯/勇敢：%d' % person.bravery_or_cowardly
            reply += '\n感性/理智：%d' % person.rational_or_sensual
            reply += '\n节俭/享乐：%d' % person.hedonic_or_computation
            reply += '\n自私/大方：%d' % person.selfish_or_generous
            return reply
        elif message[:5] == '花店npc':
            data = message[5:].strip()
            if not ObjectId.is_valid(data):
                raise TypeException('格式错误！格式“花店npc npc的id”，id一般为一长串字母英文混合')
            person: Person = flower_dao.select_person(data)
            if not person.valid():
                return '人物不存在'
            reply = 'id:%s' % person.get_id()
            reply += '\n名字：%s' % person.name
            age: int = int((datetime.now() - person.born_time).total_seconds() // global_config.day_second)
            reply += '\n年龄：%d/%d岁' % (
                age, person.max_age)
            if person.die:
                reply += '（已于%s死亡）' % person.die_time.strftime('%Y-%m-%d %H:%M:%S')
                reply += '\n死亡原因：%s' % person.die_reason
            reply += '\n性别：%s，性取向：%s' % (person.gender.show(), person.sexual_orientation.show())
            reply += '\n身高：%.2fm，体重：%.2fkg' % (person.height, person.weight)
            father_name: str = ''
            if person.father_id != '':
                father: Person = flower_dao.select_person(person.father_id)
                father_name = father.name
            mother_name: str = ''
            if person.father_id != '':
                mother: Person = flower_dao.select_person(person.mother_id)
                mother_name = mother.name
            reply += '\n父亲：%s（%s），母亲：%s（%s）' % (father_name, person.father_id, mother_name, person.mother_id)
            born_area: WorldArea = flower_dao.select_world_area(person.born_area_id)
            area: WorldArea = flower_dao.select_world_area(person.world_area_id)
            reply += '\n出生地：%s，现在所在地：%s' % (born_area.name, area.name)
            kingdom: Kingdom = flower_dao.select_kingdom(person.motherland)
            reply += '\n祖国：%s' % kingdom.name
            race: Race = flower_dao.select_world_race(person.race_id)
            reply += '\n种族：%s' % race.name
            reply += '\n疾病：%s' % person.disease_id
            reply += '\n职业：%s' % person.profession_id
            reply += '\n' + ('-' * 6)
            reply += '\n基础属性：'
            reply += '\n智慧：%d，领导力：%d，武力：%d，亲和力：%d，野心：%d，健康：%d，外貌：%d/%d' % (
                person.wisdom, person.leadership, person.force, person.affinity, person.ambition, person.health,
                util.show_appearance(person.appearance, age), person.appearance
            )
            reply += '\n外貌描述：%s' % person.appearance_description
            reply += '\n' + ('-' * 6)
            reply += '\n性格（以下描述词越小越靠近左边的词，越大越靠近右边的词）'
            reply += '\n邪恶/正义：%d' % person.justice_or_evil
            reply += '\n内向/外向：%d' % person.extroversion_or_introversion
            reply += '\n胆怯/勇敢：%d' % person.bravery_or_cowardly
            reply += '\n感性/理智：%d' % person.rational_or_sensual
            reply += '\n节俭/享乐：%d' % person.hedonic_or_computation
            reply += '\n自私/大方：%d' % person.selfish_or_generous
            return reply
        elif message == '创建世界':
            person_number = flower_dao.select_all_person_number()
            if person_number != 0:
                return '当前世界已经创建过了或正在创建'

            @async_function
            def create_world():
                population: int = world_handler.random_generate_world()
                util.leave_message(qq, '世界生成已经完成，总计人口：%d' % population)

            create_world()
            return '当前开始创建世界，预估需要十分钟~请勿重复发起命令'
        elif message[:4] == '世界种族':
            data = message[4:].strip()
            if ObjectId.is_valid(data):
                race: Race = flower_dao.select_world_race(data)
            else:
                race: Race = flower_dao.select_world_race_by_name(data)
            if not race.valid():
                raise ResourceNotFound('不存在世界种族“%s”' % data)
            return str(race)
        elif message[:4] == '世界地形':
            data = message[4:].strip()
            if ObjectId.is_valid(data):
                world_terrain: WorldTerrain = flower_dao.select_world_terrain(data)
            else:
                world_terrain: WorldTerrain = flower_dao.select_world_terrain_by_name(data)
            if not world_terrain.valid():
                raise ResourceNotFound('不存在世界地形“%s”，既不是id也不是名字' % data)
            return str(world_terrain)
        elif message[:4] == '世界地区':
            data = message[4:].strip()
            if ObjectId.is_valid(data):
                world_area: WorldArea = flower_dao.select_world_area(data)
            else:
                world_area: WorldArea = flower_dao.select_world_area_by_name(data)
            if not world_area.valid():
                raise ResourceNotFound('不存在世界地区“%s”，既不是id也不是名字' % data)
            reply: str = '地区名：' + world_area.name
            reply += '\n描述：' + world_area.description
            reply += '\n地形：'
            terrain: WorldTerrain = flower_dao.select_world_terrain(world_area.terrain_id)
            reply += terrain.name
            reply += '\n主要种族：'
            if world_area.race_id == '':
                reply += '无'
            else:
                race: Race = flower_dao.select_world_race(world_area.race_id)
                reply += race.name
            reply += '\n连通地区：'
            for path in world_area.path_list:
                target_area: WorldArea = flower_dao.select_world_area(path.target_area_id)
                reply += '\n%s，距离：%.2f，陆行价格：%.2f，航行价格：%.2f，行程难易：%d' % (
                    target_area.name,
                    path.distance,
                    path.driving_price / 100,
                    path.sail_price / 100,
                    path.difficulty
                )
            return reply
        elif message[:4] == '世界帝国':
            data = message[4:].strip()
            if ObjectId.is_valid(data):
                kingdom: Kingdom = flower_dao.select_kingdom(data)
            else:
                kingdom: Kingdom = flower_dao.select_kingdom_by_name(data)
            if not kingdom.valid():
                raise ResourceNotFound('不存在世界帝国“%s”，既不是id也不是名字' % data)
            reply: str = '名字：' + kingdom.name
            reply += '\n控制地区：'
            for area_id in kingdom.area_id_list:
                target_area: WorldArea = flower_dao.select_world_area(area_id)
                reply += '\n%s' % target_area.name
            return reply
        elif message == '世界人口':
            number: int = flower_dao.select_all_person_number()
            return '世界总人口：%d' % number
        elif message == '世界活人人口':
            number: int = flower_dao.select_all_alive_person_number()
            return '世界活人人口：%d' % number
        elif message == '世界人口分析':
            logger.info('管理员%d开启了世界人口分析')
            total_number: int = flower_dao.select_all_person_number()
            alive_number: int = flower_dao.select_all_alive_person_number()
            die_number = total_number - alive_number
            age_range: List = [0 for _ in range(11)]
            profession_number: Dict[str or None, int] = {}
            page: int = -1
            page_size: int = 20
            now: datetime = datetime.now()
            logger.info('遍历所有人口，总计数量：%d，页面大小：%d' % (total_number, page_size))
            while total_number > 0:
                total_number -= page_size
                page += 1
                logger.info('当前页：%d，剩余人数：%d' % (page, total_number))
                person_list: List[Person] = flower_dao.select_all_person(page, page_size)
                for person in person_list:
                    age: int = int((now - person.born_time).total_seconds() // global_config.day_second)
                    if age >= 100:
                        age_range[10] += 1
                    else:
                        age_range[int(age // 10)] += 1
                    if person.profession_id not in profession_number:
                        profession_number[person.profession_id] = 1
                    else:
                        profession_number[person.profession_id] += 1
            logger.info('统计完成！')
            reply: str = '世界总人口：%d（死亡：%d）' % (alive_number, die_number)
            reply += '\n' + '-' * 6
            reply += '\n各年龄阶段：'
            for i in range(10):
                reply += '\n%d岁~%d岁：%d' % (i * 10, (i + 1) * 10, age_range[i])
            reply += '\n大于100岁：%d' % age_range[10]
            reply += '\n' + '-' * 6
            reply += '\n职业分析：'
            for profession_id in profession_number:
                if profession_id is None:
                    reply += '\n无业：%d' % profession_number[profession_id]
                    continue
                profession: Profession = flower_dao.select_profession(profession_id)
                reply += '\n%s：%d' % (profession.name, profession_number[profession_id])
            return reply
        elif message[:7] == '花店投放npc':
            data = message[7:].strip()
            data_list = data.split(' ')
            if len(data_list) == 1:
                number: int = 1
            elif len(data_list) == 2 and data_list[1].isdigit():
                number: int = int(data_list[1])
            else:
                raise TypeException('格式错误！格式“花店投放npc 职业名 数量”')
            profession: Profession = flower_dao.select_profession_by_name(data_list[0])
            if not profession.valid():
                raise TypeException('格式错误！%s不存在' % data_list[0])
            logger.info('管理员%d创建了npc：%sx%d' % (qq, data_list[0], number))
            for i in range(number):
                person: Person = world_handler.random_person(born_profession=profession, min_age=20)
                flower_dao.insert_person(person)
            return '创建完成！'
        return ''


class ContextHandler:
    """
    上下文处理器
    """

    def __init__(self):
        self.block_transmission: bool = True  # 是否阻断消息继续传递，默认阻断

    def handle(self, message: str, qq: int, username: str, bot_qq: int, bot_name: str) -> Result:
        """
        上下文处理
        :param message: 消息
        :param qq: qq
        :param username: 用户名
        :param bot_qq: 机器人qq
        :param bot_name: 机器人名
        :return: 结果
        """
        system_data: SystemData = util.get_system_data()
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
                    if city is None or city.city_name != message or not city.valid():
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
                    user.create_time = datetime.now()
                    user.update(bot_qq)

                    city: City = context.city
                    user.city_id = city.get_id()
                    user.born_city_id = city.get_id()

                    # 农场的初始化
                    util.init_user_farm(user, city)

                    flower_dao.insert_user(user)
                    del_context_list.append(origin_list[index])
                    reply = bot_name + '已为您初始化花店\n' \
                                       '免责声明：本游戏一切内容与现实无关（包括但不限于城市、人物、事件），城市只是为了方便计算天气！\n' \
                                       '现在输入“领取花店初始礼包”试试吧'
                    result.context_reply_text.append(reply)
            # 新手指引
            elif isinstance(context, BeginnerGuideContext):
                user: User = util.get_user(qq, username)
                if message == '关闭新手指引':
                    del_context_list.append(origin_list[index])
                    reply = user.username + '，已为您关闭新手指引'
                    result.context_reply_text.append(reply)
                if context.step == 0:
                    if message == '花店签到':
                        self.block_transmission = False
                        flower_dao.remove_context(qq, origin_list[index])
                        context.step += 1
                        flower_dao.insert_context(qq, context)
                        reply = user.username + '，很好你已经完成了签到！每日签到可以获取一定数量的金币。如果破产了，' \
                                                '可以通过签到回血。\n' \
                                                '接下来试试“花店数据”。\n' \
                                                '您可以输入“关闭新手指引”来取消指引。'
                        result.context_reply_text.append(reply)
                elif context.step == 1:
                    if message == '花店数据':
                        self.block_transmission = False
                        flower_dao.remove_context(qq, origin_list[index])
                        context.step += 1
                        flower_dao.insert_context(qq, context)
                        reply = user.username + '，在这里你可以看见一些玩家的基本数据，包括玩家等级、金币数量等等\n' \
                                                '接下来试试“花店仓库”。\n' \
                                                '您可以输入“关闭新手指引”来取消指引。'
                        result.context_reply_text.append(reply)
                elif context.step == 2:
                    if message == '花店仓库':
                        self.block_transmission = False
                        flower_dao.remove_context(qq, origin_list[index])
                        context.step += 1
                        flower_dao.insert_context(qq, context)
                        reply = user.username + '，在这里你可以看见刚刚我们发给你的杂草种子、新手水壶、加速卡。\n' \
                                                '接下来试试“种植杂草”。'
                        result.context_reply_text.append(reply)
                elif context.step == 3:
                    if message == '种植杂草':
                        self.block_transmission = False
                        flower_dao.remove_context(qq, origin_list[index])
                        context.step += 1
                        flower_dao.insert_context(qq, context)
                        reply = user.username + '，很好！你的杂草已经种植在你的农场了\n' \
                                                '接下来试试“花店农场”查看你的农场。'
                        result.context_reply_text.append(reply)
                elif context.step == 4:
                    if message == '花店农场':
                        self.block_transmission = False
                        flower_dao.remove_context(qq, origin_list[index])
                        context.step += 1
                        flower_dao.insert_context(qq, context)
                        reply = user.username + '，在这里你可以看见你的花花的生长情况。\n' \
                                                '是不是很疑惑，为什么温度这些维度都没有具体的数值？\n' \
                                                '不急，接下来试试“花店农场设备”。'
                        result.context_reply_text.append(reply)
                elif context.step == 5:
                    if message == '花店农场设备':
                        self.block_transmission = False
                        flower_dao.remove_context(qq, origin_list[index])
                        context.step += 1
                        flower_dao.insert_context(qq, context)
                        reply = user.username + '，看见这里的水壶等东西了吗？这些道具将会影响你对“花店农场”的监控，' \
                                                '道具越高级数值越准确。\n' \
                                                '接下来试试“浇水”'
                        result.context_reply_text.append(reply)
                elif context.step == 6:
                    if message == '浇水':
                        self.block_transmission = False
                        user: User = util.get_user(qq, username)
                        if user.farm.watering_pot.item_name != '':
                            flower_dao.remove_context(qq, origin_list[index])
                            context.step = 9
                            flower_dao.insert_context(qq, context)
                            reply = user.username + '，浇水成功！\n' \
                                                    '等待可真是难熬，接下来试试“花店使用加速卡”，来加速你的农场'
                            result.context_reply_text.append(reply)
                        else:
                            flower_dao.remove_context(qq, origin_list[index])
                            context.step += 1
                            flower_dao.insert_context(qq, context)
                            reply = user.username + '，真可惜没有水壶\n' \
                                                    '接下来试试“花店使用新手水壶”把刚才的水壶装上去吧'
                            result.context_reply_text.append(reply)
                elif context.step == 7:
                    if message == '花店使用新手水壶' or message == '花店使用 新手水壶':
                        self.block_transmission = False
                        flower_dao.remove_context(qq, origin_list[index])
                        context.step += 1
                        flower_dao.insert_context(qq, context)
                        reply = user.username + '，很好！\n' \
                                                '接下来再次试试“浇水”'
                        result.context_reply_text.append(reply)
                elif context.step == 8:
                    if message == '浇水':
                        self.block_transmission = False
                        flower_dao.remove_context(qq, origin_list[index])
                        context.step += 1
                        flower_dao.insert_context(qq, context)
                        reply = user.username + '，浇水成功！\n' \
                                                '等待可真是难熬，接下来试试“花店使用加速卡”，来加速你的农场'
                        result.context_reply_text.append(reply)
                elif context.step == 9:
                    if message == '花店使用加速卡' or message == '花店使用 新手水壶':
                        self.block_transmission = False
                        flower_dao.remove_context(qq, origin_list[index])
                        context.step += 1
                        flower_dao.insert_context(qq, context)
                        reply = user.username + '，你的农场已经被加速了！\n' \
                                                '现在快使用命令“花店农场”去你的农场看看'
                        result.context_reply_text.append(reply)
                elif context.step == 10:
                    if message == '花店农场':
                        self.block_transmission = False
                        flower_dao.remove_context(qq, origin_list[index])
                        context.step += 1
                        flower_dao.insert_context(qq, context)
                        reply = user.username + '，看！你的种子不出意外的话应该已经成熟了，或者快要成熟。\n' \
                                                '接下来使用命令“花店收获”来收获成熟的花'
                        result.context_reply_text.append(reply)
                elif context.step == 11:
                    if message == '花店收获':
                        self.block_transmission = False
                        flower_dao.remove_context(qq, origin_list[index])
                        context.step += 1
                        flower_dao.insert_context(qq, context)
                        reply = user.username + '，你的花已经到你的仓库里去了！\n' \
                                                '注意花是有不同等级的，只有在成熟阶段才可以收获完美的花！\n' \
                                                '完美的花在完成任务的时候或许有特殊的作用！\n' \
                                                '接下来我们去看看别的指令吧。“花店信箱”！这个指令很有用'
                        result.context_reply_text.append(reply)
                elif context.step == 12:
                    if message == '花店信箱':
                        self.block_transmission = False
                        flower_dao.remove_context(qq, origin_list[index])
                        context.step += 1
                        flower_dao.insert_context(qq, context)
                        reply = user.username + '，这在里你可以看见每天的信件，有些时候系统会发送补偿信件，' \
                                                '有些时候npc也会给你送信\n' \
                                                '一定要及时查看，不然信箱满了就收不到新的信件（系统直接送达可以无视上限）。\n' \
                                                '信箱的其它操作指令可以看“花店帮助”。我们接下来试试“花店人物”'
                        result.context_reply_text.append(reply)
                elif context.step == 13:
                    if message == '花店人物':
                        self.block_transmission = False
                        flower_dao.remove_context(qq, origin_list[index])

                        item: DecorateItem = DecorateItem()
                        item_list: List[DecorateItem] = []

                        # 初始获取初始种子
                        seed_list = ['野草种子', '野花种子', '小黄花种子', '小红花种子']
                        for seed in seed_list:
                            item.item_name = seed
                            item.number = 5
                            item_list.append(copy.deepcopy(item))
                        # 新手道具
                        item.item_name = '加速卡'
                        item.number = 5
                        item.hour = 1
                        item_list.append(copy.deepcopy(item))
                        item.item_name = '完美加速卡'
                        item.number = 5
                        item.hour = 1
                        item_list.append(copy.deepcopy(item))
                        item.hour = 0
                        item.item_name = '随机旅行卡'
                        item.number = 1
                        item_list.append(copy.deepcopy(item))
                        item.item_name = '标准肥料'
                        item.number = 5
                        item_list.append(copy.deepcopy(item))
                        item.item_name = '花语卡'
                        item.number = 10
                        item_list.append(copy.deepcopy(item))

                        try:
                            user: User = util.get_user(qq, username)
                            util.insert_items(user.warehouse, item_list)
                            flower_dao.update_user_by_qq(user)
                        except ItemNotFoundException:
                            reply = '内部错误！'
                            result.context_reply_text.append(reply)
                            continue
                        except ItemNegativeNumberException:
                            reply = '内部错误！'
                            result.context_reply_text.append(reply)
                            continue
                        except WareHouseSizeNotEnoughException:
                            reply = '仓库空间不足，老手还装什么新人（手动滑稽）'
                            result.context_reply_text.append(reply)
                            continue

                        reply = user.username + '，这里每天都会刷新三位人物，他们会给你带来不同的道具以及种子\n' \
                                                '每天晚上十二点刷新哦~\n' \
                                                '具体的操作指令可以查看“花店帮助”，新手教程就到这里了~我们为你准备了一些新手道具，' \
                                                '可以前往仓库查看！'
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
                if user.gold < system_data.remove_farm_flower_cost_gold:
                    reply = user.username + '，金币不足' + '%.2f' % (
                            system_data.remove_farm_flower_cost_gold / 100) + '枚'
                    result.context_reply_text.append(reply)
                    continue
                user.gold -= system_data.remove_farm_flower_cost_gold
                user.farm.flower_id = ''
                user.exp += 1
                user_statistics: UserStatistics = util.get_user_statistics(qq)
                user_statistics.remove_flower += 1
                flower_dao.update_user_statistics(user_statistics)
                flower_dao.update_user_by_qq(user)
                reply = user.username + '，成功花费' + '%.2f' % (
                        system_data.remove_farm_flower_cost_gold / 100) + '金币为您铲除花'
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
                        util.unlock_user(qq)
                        reply = context.choices[command].callback(**context.choices[command].args)
                        util.lock_user(qq)
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
            elif isinstance(context, TravelContext):
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
                    flower_dao.remove_context(qq, origin_list[index])
                    continue
                city: City = flower_dao.select_city_by_name(message)
                if city is None or city.city_name != message:
                    reply = FlowerService.query_city(message) + '\n请选择一座城市，输入“取消”来取消本次旅行。'
                    result.context_reply_text.append(reply)
                    continue
                flower_dao.remove_context(qq, origin_list[index])
                user.city_id = city.get_id()
                user.farm = Farm()
                util.init_user_farm(user, city)
                flower_dao.update_user_by_qq(user)
                reply = username + '，旅行到了%s，来这里开始新的冒险吧~' % city.city_name
                result.context_reply_text.append(reply)
            # 知己知彼
            elif isinstance(context, ViewRelationshipContext):
                flower_dao.remove_context(qq, origin_list[index])
                user: User = util.get_user(qq, username)
                if not ObjectId.is_valid(message):
                    item: DecorateItem = DecorateItem()
                    item.item_name = '知己知彼'
                    item.number = 1
                    item.item_type = ItemType.props
                    util.insert_items(user.warehouse, [item])
                    flower_dao.update_user_by_qq(user)
                    reply = '已为你取消探查'
                    result.context_reply_text.append(reply)
                    continue
                relationship: Relationship = flower_dao.select_relationship_by_pair(message, str(qq))
                if not relationship.valid():
                    reply = '不存在该npc或者他还没有遇见你'
                else:
                    reply = '他对你的好感度为：%d' % relationship.value
                result.context_reply_text.append(reply)
                continue
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
                            '3.“修改金币 数量”来修改附件附赠的金币\n' \
                            '4.“追加收件人 QQ号”来追加一个收件人\n' \
                            '5.“删除收件人 QQ号”来删除一个收件人\n' \
                            '6.“发送给所有人”来发送信件给所有人\n' \
                            '7.取消发送给所有人”来取消发送信件给所有人\n' \
                            '8.“预览信件”来预览整个信件\n' \
                            '9.“确认”发送信件，注意必须要有一个收件人！\n' \
                            '10.“取消”来取消发送'
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
                        mail.gold = context.gold
                        mail.arrived = True  # 已经抵达
                        mail.status = '由系统直接送达'
                        mail.create_time = datetime.now()
                        reply = ''
                        update_number: int = 0
                        if context.send_all_user:
                            total_user_number: int = flower_dao.select_all_user_number()
                            page_size: int = 20
                            page: int = -1
                            while total_user_number > 0:
                                total_user_number -= page_size
                                page += 1
                                user_list: List[User] = flower_dao.select_all_user(page=page, page_size=page_size)
                                for user in user_list:
                                    target_qq: int = user.qq
                                    try:
                                        if target_qq != qq:
                                            util.lock_user(target_qq)
                                        user: User = util.get_user(target_qq)
                                        mail.target_qq = target_qq
                                        mail_id: str = flower_dao.insert_mail(mail)
                                        user.mailbox.mail_list.append(mail_id)
                                        flower_dao.update_user_by_qq(user)
                                        update_number += 1
                                    except UserNotRegisteredException:
                                        reply += str(target_qq) + '，未注册\n'
                                    except ResBeLockedException:
                                        reply += str(target_qq) + '，无法发送信件\n'
                                    finally:
                                        if target_qq != qq:
                                            util.unlock_user(target_qq)
                        else:
                            for target_qq in context.addressee:
                                try:
                                    if target_qq != qq:
                                        util.lock_user(target_qq)
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
                                        util.unlock_user(target_qq)
                        reply += '成功把信件发送给%d个人' % update_number
                        result.context_reply_text.append(reply)
                        continue
                    elif message == '预览信件':
                        reply = context.title
                        reply += '\n------\n'
                        reply += context.text
                        reply += '\n------\n'
                        reply += '来自：%s' % context.username
                        if len(context.appendix) > 0 and context.gold > 0:
                            reply += '\n附件：' + util.show_items(context.appendix) + '、金币（%.2f）' % (
                                    context.gold / 100)
                        elif len(context.appendix) > 0:
                            reply += '\n附件：' + util.show_items(context.appendix)
                        elif context.gold > 0:
                            reply += '\n附件：金币（%.2f）' % (context.gold / 100)
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
                    elif message[:4] == '修改金币':
                        try:
                            gold: int = int(float(message[4:].strip()) * 100)
                            flower_dao.remove_context(qq, origin_list[index])
                            context.gold = gold
                            flower_dao.insert_context(qq, context)
                            reply = '修改金币为：%.2f' % (gold / 100)
                            result.context_reply_text.append(reply)
                        except ValueError:
                            reply = '格式错误！格式“修改金币 数量”'
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
            # 玩家发送信件
            elif isinstance(context, UserSendMailContext):
                if context.valid_date != date.today():
                    del_context_list.append(origin_list[index])
                    continue
                if message == '取消':
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
                            '3.“修改收件人 QQ号”来修改收件人\n' \
                            '4.“预览信件”来预览整个信件\n' \
                            '5.“预览账单”来预览发送信件的开销\n' \
                            '6.“确认”发送信件，注意必须要有一个收件人！\n' \
                            '7.“取消”来取消发送'
                    result.context_reply_text.append(reply)
                elif context.step == 3:
                    if message == '确认':
                        if context.target_qq == 0:
                            reply = '没有任何收件人！请修改收件人'
                            result.context_reply_text.append(reply)
                            continue
                        del_context_list.append(origin_list[index])
                        mail: Mail = Mail()
                        mail.from_qq = qq
                        mail.title = context.title
                        mail.text = context.text
                        mail.username = context.username
                        mail.appendix = context.appendix
                        mail.gold = 0
                        mail.arrived = True  # 已经抵达
                        mail.status = '由邮递员%s（%s）送达' % (context.postman_name, context.postman_id)
                        mail.create_time = datetime.now()
                        reply = ''
                        user: User = flower_dao.select_user_by_qq(qq)
                        try:
                            util.lock_user(context.target_qq)
                            target_user: User = util.get_user(context.target_qq)
                            user_person: UserPerson = flower_dao.select_user_person(context.user_person_id)
                            # 扣除用户自己的物品和金币
                            level_dis: int = abs(target_user.level - user.level)
                            cost_gold, _ = util.calculate_item_mail_price(level_dis, context.appendix)

                            util.remove_items(user.warehouse, copy.deepcopy(context.appendix))
                            total_gold: int = cost_gold + user_person.send_mail_price
                            if total_gold > user.gold:
                                raise GoldNotEnough('金币不足')
                            user.gold -= total_gold
                            flower_dao.update_user_by_qq(user)

                            # 这里目前送信是直接到达，后续要做成延迟到达
                            mail.target_qq = context.target_qq
                            mail_id: str = flower_dao.insert_mail(mail)
                            if len(target_user.mailbox.mail_list) < target_user.mailbox.max_size:
                                target_user.mailbox.mail_list.append(mail_id)
                            flower_dao.update_user_by_qq(target_user)
                            # 送信一次后就不允许送信第二次了
                            user_person.send_mail_price = -1
                            flower_dao.update_user_person(user_person)
                            reply = '送信给%d成功\n目前送信是马上到达，请注意后续版本会改为延迟到达，路上还会遇见事件' % context.target_qq
                        except UserNotRegisteredException:
                            reply = str(context.target_qq) + '，未注册'
                        except ResBeLockedException:
                            reply = str(context.target_qq) + '，无法发送信件'
                        except ItemNotEnoughException or ItemNotFoundException or GoldNotEnough:
                            reply = '物品不足或金币，无法发送信件'
                        finally:
                            if reply == '':
                                reply = '由于未知原因送信可能失败了！'
                            util.unlock_user(context.target_qq)
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
                        reply += '\n收件人：' + str(context.target_qq)
                        result.context_reply_text.append(reply)
                        continue
                    elif message == '预览账单':
                        user: User = flower_dao.select_user_by_qq(qq)
                        target_user: User = util.get_user(context.target_qq)
                        user_person: UserPerson = flower_dao.select_user_person(context.user_person_id)
                        level_dis: int = abs(target_user.level - user.level)
                        cost_gold, bill = util.calculate_item_mail_price(level_dis, context.appendix)
                        reply = bill + '\n基础运费：%.2f\n------\n合计：%.2f' % (
                            user_person.send_mail_price / 100,
                            (cost_gold + user_person.send_mail_price) / 100
                        )
                        result.context_reply_text.append(reply)
                        continue
                    elif message[:5] == '修改收件人':
                        try:
                            target_qq = int(message[5:].strip())
                            flower_dao.remove_context(qq, origin_list[index])
                            if target_qq == qq:
                                reply = '不可以送信给自己！'
                            elif target_qq != context.target_qq:
                                try:
                                    util.get_user(target_qq)
                                    reply = '成功修改收件人！'
                                    context.target_qq = target_qq
                                except UserNotRegisteredException:
                                    reply = '对方未注册！'
                            else:
                                reply = '修改失败！收件人本来就是此人'
                            flower_dao.insert_context(qq, context)
                            result.context_reply_text.append(reply)
                        except ValueError:
                            reply = '格式错误！格式“追加收件人 QQ号”'
                            result.context_reply_text.append(reply)
                    elif message[:4] == '追加附件':
                        try:
                            data = message[4:].strip()
                            item: DecorateItem = util.analysis_item(data)
                            origin_item: Item = flower_dao.select_item_by_name(item.item_name)
                            if not origin_item.valid():
                                reply = '物品不存在'
                                result.context_reply_text.append(reply)
                                continue
                            elif origin_item.rot_second > 0:
                                reply = '不可以邮寄会腐烂的东西'
                                result.context_reply_text.append(reply)
                                continue
                            elif item.number < 1:
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
            # 给予buff
            elif isinstance(context, GiveBuffContext):
                if message == '取消':
                    del_context_list.append(origin_list[index])
                    reply = '已为您取消发送公告'
                    result.context_reply_text.append(reply)
                    continue
                if context.step == 0:
                    name: str = message.strip()
                    buff: Buff = flower_dao.select_buff_by_name(name)
                    if not buff.valid():
                        reply = '不存在“%s”' % name
                        result.context_reply_text.append(reply)
                        continue
                    flower_dao.remove_context(qq, origin_list[index])
                    context.buff = DecorateBuff().generate(buff)
                    context.step += 1
                    flower_dao.insert_context(qq, context)
                    reply = '请问持续时长是多久？（x天x小时x分钟x秒，不用的单位可以省略）'
                    result.context_reply_text.append(reply)
                elif context.step == 1:
                    seconds: int = util.analysis_time(message)
                    if seconds <= 0:
                        reply = '时间格式不正确！格式“x天x小时x分钟x秒”。输入“取消”可以取消'
                        result.context_reply_text.append(reply)
                        continue
                    flower_dao.remove_context(qq, origin_list[index])
                    context.expire_seconds = seconds
                    context.step += 1
                    flower_dao.insert_context(qq, context)
                    reply = '当前Buff：%s\n' \
                            '持续秒数（从确认时开始算）：%d\n' \
                            '是否要修改基础效果？（“是”表示是，其余表示否，“取消”表示取消）\n' \
                            '注：部分buff可能本身具有特殊效果' % (str(context.buff), seconds)
                    result.context_reply_text.append(reply)
                elif context.step == 2:
                    if message == '是':
                        flower_dao.remove_context(qq, origin_list[index])
                        context.step = 3
                        flower_dao.insert_context(qq, context)
                        reply = '1.“锁定/解锁湿度”\n' \
                                '2.“锁定/解锁营养”\n' \
                                '3.“锁定/解锁温度”\n' \
                                '4.“锁定/解锁土壤”\n' \
                                '5.“修改湿度 【数值】”\n' \
                                '6.“修改营养 【数值】”\n' \
                                '7.“修改温度 【数值】”\n' \
                                '8.“修改完美时长增幅 【数值】”\n' \
                                '9.“修改生长时长增幅 【数值】”\n' \
                                '10.“修改糟糕时长增幅 【数值】”\n' \
                                '11.“确认”，将buff给予出去\n' \
                                '12.“预览”，预览当前buff\n' \
                                '13.“取消”，取消发送'
                        result.context_reply_text.append(reply)
                        continue
                    context.buff.expired_time = datetime.now() + timedelta(seconds=context.expire_seconds)
                    for target_qq in context.target_qq_list:
                        if target_qq != qq:
                            util.lock_user(target_qq)
                        target_user: User = util.get_user(target_qq)
                        target_user.buff.append(context.buff)
                        flower_dao.update_user_by_qq(target_user)
                        if target_qq != qq:
                            util.unlock_user(target_qq)
                    del_context_list.append(origin_list[index])
                    reply = '给予成功！'
                    result.context_reply_text.append(reply)
                elif context.step == 3:
                    if message == '确认':
                        context.buff.expired_time = datetime.now() + timedelta(seconds=context.expire_seconds)
                        for target_qq in context.target_qq_list:
                            if target_qq != qq:
                                util.lock_user(target_qq)
                            target_user: User = util.get_user(target_qq)
                            target_user.buff.append(context.buff)
                            flower_dao.update_user_by_qq(target_user)
                            if target_qq != qq:
                                util.unlock_user(target_qq)
                        del_context_list.append(origin_list[index])
                        reply = '给予成功！'
                        result.context_reply_text.append(reply)
                    elif message == '预览':
                        reply = '当前Buff：%s\n' \
                                '持续秒数（从确认时开始算）：%d' % (str(context.buff), context.expire_seconds)
                        result.context_reply_text.append(reply)
                    elif message == '锁定湿度':
                        flower_dao.remove_context(qq, origin_list[index])
                        context.buff.lock_humidity = True
                        flower_dao.insert_context(qq, context)
                        reply = '锁定成功'
                        result.context_reply_text.append(reply)
                    elif message == '解锁湿度':
                        flower_dao.remove_context(qq, origin_list[index])
                        context.buff.lock_humidity = False
                        flower_dao.insert_context(qq, context)
                        reply = '解锁成功'
                        result.context_reply_text.append(reply)
                    elif message == '锁定温度':
                        flower_dao.remove_context(qq, origin_list[index])
                        context.buff.lock_temperature = True
                        flower_dao.insert_context(qq, context)
                        reply = '锁定成功'
                        result.context_reply_text.append(reply)
                    elif message == '解锁温度':
                        flower_dao.remove_context(qq, origin_list[index])
                        context.buff.lock_temperature = False
                        flower_dao.insert_context(qq, context)
                        reply = '解锁成功'
                        result.context_reply_text.append(reply)
                    elif message == '锁定营养':
                        flower_dao.remove_context(qq, origin_list[index])
                        context.buff.lock_nutrition = True
                        flower_dao.insert_context(qq, context)
                        reply = '锁定成功'
                        result.context_reply_text.append(reply)
                    elif message == '解锁营养':
                        flower_dao.remove_context(qq, origin_list[index])
                        context.buff.lock_nutrition = False
                        flower_dao.insert_context(qq, context)
                        reply = '解锁成功'
                        result.context_reply_text.append(reply)
                    elif message == '锁定土壤':
                        flower_dao.remove_context(qq, origin_list[index])
                        context.buff.lock_soil = True
                        flower_dao.insert_context(qq, context)
                        reply = '锁定成功'
                        result.context_reply_text.append(reply)
                    elif message == '解锁土壤':
                        flower_dao.remove_context(qq, origin_list[index])
                        context.buff.lock_soil = False
                        flower_dao.insert_context(qq, context)
                        reply = '解锁成功'
                        result.context_reply_text.append(reply)
                    elif message[:4] == '修改湿度':
                        try:
                            value: float = float(message[4:].strip())
                            flower_dao.remove_context(qq, origin_list[index])
                            context.buff.change_humidity = value
                            flower_dao.insert_context(qq, context)
                            reply = '修改成功'
                            result.context_reply_text.append(reply)
                        except ValueError:
                            reply = '格式错误！格式“修改湿度 【数值】”'
                            result.context_reply_text.append(reply)
                    elif message[:4] == '修改温度':
                        try:
                            value: float = float(message[4:].strip())
                            flower_dao.remove_context(qq, origin_list[index])
                            context.buff.change_temperature = value
                            flower_dao.insert_context(qq, context)
                            reply = '修改成功'
                            result.context_reply_text.append(reply)
                        except ValueError:
                            reply = '格式错误！格式“修改温度 【数值】”'
                            result.context_reply_text.append(reply)
                    elif message[:4] == '修改营养':
                        try:
                            value: float = float(message[4:].strip())
                            flower_dao.remove_context(qq, origin_list[index])
                            context.buff.change_nutrition = value
                            flower_dao.insert_context(qq, context)
                            reply = '修改成功'
                            result.context_reply_text.append(reply)
                        except ValueError:
                            reply = '格式错误！格式“修改营养 【数值】”'
                            result.context_reply_text.append(reply)
                    elif message[:8] == '修改完美时长增幅':
                        try:
                            value: float = float(message[8:].strip())
                            flower_dao.remove_context(qq, origin_list[index])
                            context.buff.perfect_coefficient = value
                            flower_dao.insert_context(qq, context)
                            reply = '修改成功'
                            result.context_reply_text.append(reply)
                        except ValueError:
                            reply = '格式错误！格式“修改完美时长增幅 【数值】”'
                            result.context_reply_text.append(reply)
                    elif message[:8] == '修改生长时长增幅':
                        try:
                            value: float = float(message[8:].strip())
                            flower_dao.remove_context(qq, origin_list[index])
                            context.buff.hour_coefficient = value
                            flower_dao.insert_context(qq, context)
                            reply = '修改成功'
                            result.context_reply_text.append(reply)
                        except ValueError:
                            reply = '格式错误！格式“修改生长时长增幅 【数值】”'
                            result.context_reply_text.append(reply)
                    elif message[:8] == '修改糟糕时长增幅':
                        try:
                            value: float = float(message[8:].strip())
                            flower_dao.remove_context(qq, origin_list[index])
                            context.buff.bad_hour_coefficient = value
                            flower_dao.insert_context(qq, context)
                            reply = '修改成功'
                            result.context_reply_text.append(reply)
                        except ValueError:
                            reply = '格式错误！格式“修改糟糕时长增幅 【数值】”'
                            result.context_reply_text.append(reply)
            # 向npc出售商品议价
            elif isinstance(context, CommodityBargainingContext):
                if context.step == 0:
                    if context.can_bargain:
                        if message == '是':
                            flower_dao.remove_context(qq, origin_list[index])
                            context.step += 1
                            flower_dao.insert_context(qq, context)
                            reply = '你可以输入“成交”来完成交易，“取消”来取消交易，“议价 价格”来提出一个价格，但npc不一定会接受\n' \
                                    '注意：价格是单价，不是整个的价格'
                            result.context_reply_text.append(reply)
                            continue
                        elif message == '否':
                            del_context_list.append(origin_list[index])
                            # 出售物品
                            user: User = util.get_user(qq, username)
                            try:
                                gold: int = context.gold * context.item.number
                                util.remove_items(user.warehouse, [context.item])
                                user.get_gold(gold)
                                flower_dao.update_user_by_qq(user)
                                reply = user.username + '，出售成功，获得金币%s，余额：%s' % (
                                    util.show_gold(gold),
                                    util.show_gold(user.gold)
                                )
                                result.context_reply_text.append(reply)
                                continue
                            except ItemNotFoundException:
                                reply = user.username + '，该物品不可以出售'
                                result.context_reply_text.append(reply)
                                continue
                            except ItemNotEnoughException:
                                reply = user.username + '，物品不足'
                                result.context_reply_text.append(reply)
                                continue
                        del_context_list.append(origin_list[index])
                        reply = '已为您取消出售'
                        result.context_reply_text.append(reply)
                        if context.user_person_id is not None:
                            user_person: UserPerson = flower_dao.select_user_person(context.user_person_id)
                            if context.item.item_name in user_person.cancel_sell_times:
                                user_person.cancel_sell_times[context.item.item_name] += 1
                            else:
                                user_person.cancel_sell_times[context.item.item_name] = 1
                            flower_dao.update_user_person(user_person)
                            continue
                    else:
                        del_context_list.append(origin_list[index])
                        if message != '是':
                            reply = '已为您取消出售'
                            result.context_reply_text.append(reply)
                            if isinstance(context.user_person_id, str):
                                user_person: UserPerson = flower_dao.select_user_person(context.user_person_id)
                                if context.item.item_name in user_person.cancel_sell_times:
                                    user_person.cancel_sell_times[context.item.item_name] += 1
                                else:
                                    user_person.cancel_sell_times[context.item.item_name] = 1
                                flower_dao.update_user_person(user_person)
                            continue
                        # 出售物品
                        user: User = util.get_user(qq, username)
                        try:
                            gold: int = context.gold * context.item.number
                            util.remove_items(user.warehouse, [context.item])
                            user.get_gold(gold)
                            flower_dao.update_user_by_qq(user)
                            reply = user.username + '，出售成功，获得金币%s，余额：%s' % (
                                util.show_gold(gold),
                                util.show_gold(user.gold)
                            )
                            result.context_reply_text.append(reply)
                            continue
                        except ItemNotFoundException:
                            reply = user.username + '，该物品不可以出售'
                            result.context_reply_text.append(reply)
                            continue
                        except ItemNotEnoughException:
                            reply = user.username + '，物品不足'
                            result.context_reply_text.append(reply)
                            continue
                elif context.step == 1:
                    if message == '取消':
                        del_context_list.append(origin_list[index])
                        reply = '已为您取消出售'
                        result.context_reply_text.append(reply)
                        user_person: UserPerson = flower_dao.select_user_person(context.user_person_id)
                        user_person.ban_item.append(context.item.item_name)
                        flower_dao.update_user_person(user_person)
                        continue
                    elif message == '成交':
                        del_context_list.append(origin_list[index])
                        # 出售物品
                        user: User = util.get_user(qq, username)
                        try:
                            gold: int = context.gold * context.item.number
                            util.remove_items(user.warehouse, [context.item])
                            user.get_gold(gold)
                            flower_dao.update_user_by_qq(user)
                            reply = user.username + '，出售成功，获得金币%s，余额：%s' % (
                                util.show_gold(gold),
                                util.show_gold(user.gold)
                            )
                            result.context_reply_text.append(reply)
                            continue
                        except ItemNotFoundException:
                            reply = user.username + '，该物品不可以出售'
                            result.context_reply_text.append(reply)
                            continue
                        except ItemNotEnoughException:
                            reply = user.username + '，物品不足'
                            result.context_reply_text.append(reply)
                            continue
                    elif message[:2] == '议价':
                        data = message[2:].strip()
                        try:
                            gold: int = int(float(data) * 100)
                            if context.bargain_times >= 3:
                                reply = '你已经议价3次了，不能继续议价了，只能输入“成交”/“取消”\n' \
                                        '当前单价：' + util.show_gold(context.gold) + '\n' \
                                                                                     '请注意取消交易，避免无意输入成交时达成了交易。'
                                result.context_reply_text.append(reply)
                                continue
                            item_obj: Item = flower_dao.select_item_by_name(context.item.item_name)
                            relationship: Relationship = flower_dao.select_relationship_by_pair(context.person_id,
                                                                                                str(qq))
                            person: Person = flower_dao.select_person(context.person_id)
                            max_gold: int = util.calculate_item_gold(context.item, item_obj, relationship,
                                                                     random_ratio=0.2)
                            flower_dao.remove_context(qq, origin_list[index])
                            context.bargain_times += 1
                            if gold > max_gold:
                                flower_dao.insert_context(qq, context)
                                reply = '%s表示自己不能接受这个价格' % person.name
                                result.context_reply_text.append(reply)
                                continue
                            if gold < -max_gold:
                                flower_dao.insert_context(qq, context)
                                reply = '%s：这个价格会不会太低了' % person.name
                                result.context_reply_text.append(reply)
                                continue
                            context.gold = gold
                            flower_dao.insert_context(qq, context)
                            reply = '%s接受了这个价格\n当前单价：%s' % (person.name, util.show_gold(context.gold))
                            if context.bargain_times >= 3:
                                reply = '你已经议价3次了，不能继续议价了，只能输入“成交”/“取消”\n' \
                                        '请注意取消交易，避免无意输入成交时达成了交易。'
                            result.context_reply_text.append(reply)
                            continue
                        except ValueError:
                            reply = '格式错误！格式“议价 价格”，如“议价 1.2”\n' \
                                    '注意价格是单价'
                            result.context_reply_text.append(reply)
                            continue
            # 确认开户
            elif isinstance(context, CreateAccountConfirm):
                del_context_list.append(origin_list[index])
                user: User = util.get_user(qq, username)
                if message == '确认':
                    if user.gold >= 1000 * 100:
                        user.gold -= 1000 * 100
                        user_account: UserAccount = UserAccount()
                        user_account.qq = qq
                        user_account.account_gold = 0
                        user_account.create_time = datetime.now()
                        user_account.update_time = datetime.now()
                        flower_dao.insert_user_account(user_account)
                        flower_dao.update_user_by_qq(user)
                        reply = user.username + '，开户成功！'
                        attention: str = '注意事项：\n' \
                                         '1.花店股市（期货）交易与现实无关，请勿代入现实，投资有风险须谨慎操作\n' \
                                         '2.如果你在股市中资不抵债，可以申请破产，“花店申请破产”，你将会失去一切东西，包括农场' \
                                         '的道具、花、仓库中的道具、所有的金币'
                        result.context_reply_text.append(attention)
                    else:
                        reply = user.username + '，金币不足，无法开户'
                else:
                    reply = user.username + '，已取消开户'
                result.context_reply_text.append(reply)
            # 贷款
            elif isinstance(context, DebtContext):
                if context.step == 0:
                    if message != '确认':
                        del_context_list.append(origin_list[index])
                        reply = '已为您取消贷款'
                        result.context_reply_text.append(reply)
                        continue
                    flower_dao.remove_context(qq, origin_list[index])
                    context.step += 1
                    flower_dao.insert_context(qq, context)
                    pawn_gold: int = round(context.debt.gold * context.debt.mortgage_rates)
                    reply = "贷款详情：\n" \
                            "金币：%s\n" \
                            "还款天数：%d\n" \
                            "日利率：%.4f%%\n" \
                            "提前还款最低利率：%.4f%%\n" \
                            "抵押率：%.4f%%\n" \
                            "是否是利滚利：%s\n" \
                            "------\n" \
                            "至少需要抵押的物品金额：%s\n" \
                            "1.“抵押 物品 数量 【小时数/品质/耐久】”来抵押某件物品\n" \
                            "2.“预览抵押账单”来查看目前抵押了多少金币\n" \
                            "3.“删除抵押 序号”来删除某一个抵押物\n" \
                            "4.“确认”来确认贷款\n" \
                            "5.“取消”来取消贷款" % (
                                util.show_gold(context.debt.gold),
                                context.debt.repayment_day,
                                context.debt.daily_interest_rate * 100,
                                context.debt.minimum_interest * 100,
                                context.debt.mortgage_rates * 100,
                                '是' if context.debt.rolling_interest else '否',
                                util.show_gold(pawn_gold)
                            )
                    result.context_reply_text.append(reply)
                    continue
                elif context.step == 1:
                    if message == '取消':
                        del_context_list.append(origin_list[index])
                        reply = '已为您取消贷款'
                        result.context_reply_text.append(reply)
                        continue
                    elif message == '确认':
                        cost_gold, _ = util.calculate_item_pawn_price(context.pawn)
                        pawn_gold: int = round(context.debt.gold * context.debt.mortgage_rates)
                        if cost_gold < pawn_gold:
                            reply = '抵押物金额不足！'
                            result.context_reply_text.append(reply)
                            continue
                        # 移除仓库的抵押物
                        user: User = util.get_user(qq, username)
                        try:
                            util.remove_items(user.warehouse, copy.deepcopy(context.pawn))
                        except ItemNotFoundException or ItemNotEnoughException:
                            reply = '仓库内物品不足！'
                            result.context_reply_text.append(reply)
                            continue
                        flower_dao.update_user_by_qq(user)
                        # 更新账户的数据
                        user_account: UserAccount = util.get_user_account(qq)
                        debt: Debt = Debt()
                        debt.debt_id = context.debt.get_id()
                        debt.pawn = context.pawn
                        debt.create_time = datetime.now()
                        user_account.debt_list.append(debt)
                        user_account.debt_gold += context.debt.gold
                        user_account.account_gold += context.debt.gold
                        flower_dao.update_user_account(user_account)
                        # 更新贷款，标记为已借出
                        context.debt.borrowing = True
                        flower_dao.update_today_debt(context.debt)
                        del_context_list.append(origin_list[index])
                        reply = user.username + '，贷款成功！'
                        result.context_reply_text.append(reply)
                        continue
                    elif message == '预览抵押账单':
                        cost_gold, bill = util.calculate_item_pawn_price(context.pawn)
                        pawn_gold: int = round(context.debt.gold * context.debt.mortgage_rates)
                        if cost_gold >= pawn_gold:
                            state: str = '抵押物足够'
                        else:
                            state: str = '抵押物不足'
                        reply = '%s\n' \
                                '------\n' \
                                '%s' % (bill, state)
                        result.context_reply_text.append(reply)
                        continue
                    elif message[:2] == '抵押':
                        try:
                            data = message[2:].strip()
                            item: DecorateItem = util.analysis_item(data)
                            origin_item: Item = flower_dao.select_item_by_name(item.item_name)
                            if not origin_item.valid():
                                reply = '物品不存在'
                                result.context_reply_text.append(reply)
                                continue
                            elif origin_item.rot_second > 0:
                                reply = '不可以抵押会腐烂的东西'
                                result.context_reply_text.append(reply)
                                continue
                            elif item.number < 1:
                                reply = '格式错误！格式“抵押 物品 数量 【小时数/品质/耐久】”。加速卡要跟小时，如果物品有耐久度，请跟耐久，如果有品质请跟品质，如果都没有省略'
                                result.context_reply_text.append(reply)
                                continue
                            flower_dao.remove_context(qq, origin_list[index])
                            context.pawn.append(item)
                            flower_dao.insert_context(qq, context)
                            reply = '成功追加物品：%s' % str(item)
                            result.context_reply_text.append(reply)
                        except TypeException:
                            raise '格式错误！格式“抵押 物品 数量 【小时数/品质/耐久】”'
                        except ItemNotFoundException:
                            raise '格式错误！物品不存在'
                    elif message[:4] == '删除抵押':
                        data = message[4:].strip()
                        try:
                            item_index: int = int(data)
                            if item_index > 0:
                                item_index -= 1
                            if item_index < 0 or item_index >= len(context.pawn):
                                reply = '格式错误！格式“删除抵押 【附件序号】”，序号超出范围'
                                result.context_reply_text.append(reply)
                                continue
                            flower_dao.remove_context(qq, origin_list[index])
                            item = context.pawn[item_index]
                            del context.pawn[item_index]
                            flower_dao.insert_context(qq, context)
                            reply = '成功删除物品：%s' % str(item)
                            result.context_reply_text.append(reply)
                        except ValueError:
                            reply = '格式错误！格式“删除抵押 【附件序号】”'
                            result.context_reply_text.append(reply)
                            continue
            # 多重选择出售期货
            elif isinstance(context, SellFutureContext):
                del_context_list.append(origin_list[index])
                try:
                    choose_index: int = int(message)
                    if choose_index > 0:
                        choose_index -= 1
                except ValueError:
                    choose_index = -1
                if choose_index < 0 or choose_index >= len(context.index_list):
                    reply = '已为你取消出售期货'
                    result.context_reply_text.append(reply)
                    continue
                choose_stock = context.index_list[choose_index]
                user: User = util.get_user(qq, username)
                user_account: UserAccount = util.get_user_account(qq)
                flower: Flower = flower_dao.select_flower_by_id(context.flower_id)
                record: TradeRecords = TradeRecords()
                record.flower_id = flower.get_id()
                record.user_id = qq
                record.nickname = user.username
                record.trade_type = TradeType.sell
                record.price = context.price
                record.number = context.number
                record.stock_hold_time = user_account.hold_stock[choose_stock].create_time
                record.create_time = datetime.now()
                # 对应的也要减少数量
                user_account.hold_stock[choose_stock].number -= context.number
                if user_account.hold_stock[choose_stock].number <= 0:
                    user_account.hold_stock.remove(user_account.hold_stock[choose_stock])
                flower_dao.update_user_account(user_account)
                flower_dao.insert_trade_record(record)
                reply = user.username + '，你的交易请求已发送到市场\n' \
                                        '注意！你的交易单最多只会挂24小时，超过24小时将会按照实际交易数量结算你的交易，' \
                                        '可能不能100%完成你的交易请求。'
                result.context_reply_text.append(reply)
            # 选择幸运数字
            elif isinstance(context, ChooseLuckyNumber):
                if message == '取消':
                    del_context_list.append(origin_list[index])
                    reply = '已为你取消购买彩票'
                    result.context_reply_text.append(reply)
                    continue
                try:
                    lucky_number: int = int(message)
                except ValueError:
                    lucky_number: int = -1
                if lucky_number <= 0 or lucky_number > 10:
                    reply = '数字只能在1~10之间选择，输入“取消”可以取消购买'
                    result.context_reply_text.append(reply)
                    continue
                user: User = util.get_user(qq, username)
                if user.gold < 1000:
                    del_context_list.append(origin_list[index])
                    reply = '你的金币不足10，购买失败！'
                    result.context_reply_text.append(reply)
                    continue
                del_context_list.append(origin_list[index])
                user.gold -= 1000
                flower_dao.update_user_by_qq(user)
                lottery: Lottery = Lottery()
                lottery.qq = qq
                lottery.lucky_number = lucky_number
                lottery.create_time = datetime.now()
                flower_dao.insert_lottery(lottery)
                system_data: SystemData = util.get_system_data()
                system_data.lottery_prize_pool += 1000
                flower_dao.update_system_data(system_data)
                user_statistics = util.get_user_statistics(qq)
                user_statistics.lottery_times += 1
                flower_dao.update_user_statistics(user_statistics)
                reply = '彩票购买成功！当前奖金池：%s\n' \
                        '每天晚上十二点整将会结算彩票，猜中数字的人会平分奖金池' % util.show_gold(system_data.lottery_prize_pool)
                result.context_reply_text.append(reply)
        for context in del_context_list:
            flower_dao.remove_context(qq, context)
        return result


class FlowerService:

    @classmethod
    def view_all_trading_flower(cls, page, page_size: int = 20) -> str:
        system_data: SystemData = util.get_system_data()
        res: str = ''
        index: int = 0
        total: int = len(system_data.allow_trading_flower_list)
        if page * page_size >= total or page < 0:
            return '页码超限'
        for flower_id in system_data.allow_trading_flower_list:
            if index >= (page + 1) * page_size:
                break
            if index >= page * page_size:
                index += 1
                flower: Flower = flower_dao.select_flower_by_id(flower_id)
                flower_price: FlowerPrice = util.get_now_price(flower.name)
                res += '%d.%s：%s\n' % (index, flower.name, util.show_gold(flower_price.latest_price))
            else:
                index += 1
        res += '-' * 6 + '\n'
        total_page = total // page_size
        if total % page_size > 0:
            total_page += 1
        res += '页码：%d/%d' % (page + 1, total_page)
        return res

    @classmethod
    def query_city(cls, name: str) -> str:
        """
        查询城市
        :param name: 城市名
        :return:
        """
        if len(name) > 30:
            return '城市名过长'
        if len(name) == 0:
            return '城市名为空'
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
    def query_flower(cls, qq: int, username: str, name: str) -> str:
        """
        查询花
        :param qq: qq
        :param username: 用户名
        :param name: 花名
        :return: 结果
        """
        user: User = util.get_user(qq, username)
        if len(name) > 30:
            return '花名过长'
        flower = flower_dao.select_flower_by_name(name)
        if flower is None or flower.name != name:
            return '没有找到花名' + name
        if name in user.knowledge:
            level: int = user.knowledge[name]
        else:
            level: int = 0
        res = '名字：' + flower.name
        res += '\n等级：' + FlowerLevel.view_level(flower.level)
        if flower.first_user_qq != 0:
            try:
                user: User = util.get_user(flower.first_user_qq)
                if user.auto_get_name:
                    user.username = '匿名'
                res += '\n第一个种出完美的人：' + user.username
                if flower.first_user_time != datetime.now():
                    res += '（%s）' % flower.first_user_time.strftime('%Y-%m-%d %H:%M:%S')
                    if qq == flower.first_user_qq:
                        res += '【你自己】'
            except UserNotRegisteredException:
                logger.error('第一个种花的人未注册@%d' % flower.first_user_qq)
        temp_group_text = ''
        for group in flower.groups:
            flower_group = flower_dao.select_flower_group(group)
            if flower_group.valid():
                temp_group_text += '、' + flower_group.name
        if len(temp_group_text) > 0:
            res += '\n专辑：' + temp_group_text[1:]

        system_data: SystemData = util.get_system_data()
        if flower.get_id() in system_data.allow_trading_flower_list:
            res += '\n该花可以参与期货交易'

        if level >= 1:
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
        if level >= 2:
            res += '\n吸收水分：' + str(flower.water_absorption) + '/小时'
            res += '\n吸收营养：' + str(flower.nutrition_absorption) + '/小时'
        if level >= 4:
            res += '\n需累计完美时长：' + str(flower.prefect_time)
            res += '\n能忍受恶劣条件：' + str(flower.withered_time) + '小时'
        if level >= 3:
            res += '\n种子：'
            if level >= 4:
                res += '\n\t周期：' + str(flower.seed_time) + '小时'
            res += util.show_conditions(flower.seed_condition)
            res += '\n幼苗：'
            if level >= 4:
                res += '\n\t周期：' + str(flower.grow_time) + '小时'
            res += util.show_conditions(flower.grow_condition)
            res += '\n成熟：'
            if level >= 4:
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
        util.lock_user(qq)
        user: User = util.get_user(qq, username)
        born_city: City = flower_dao.select_city_by_id(user.born_city_id)
        city: City = flower_dao.select_city_by_id(user.city_id)
        res = '用户名：' + user.username
        if user.auto_get_name:
            res += '（自动获取）'
        res += '\n等级：'
        util.calculate_user_level(user)
        level = user.level
        system_data = util.get_system_data()
        res += str(level) + '（%d/%d）' % (user.exp, system_data.exp_level[level])
        res += '\n角色性别：' + user.gender.show()
        res += '\n出生地：' + born_city.city_name
        res += '\n所在城市：' + city.city_name
        res += '\n金币：' + util.show_gold(user.gold)
        gold_rank: int = flower_dao.get_gold_rank(qq) + 1
        res += '（第%d名）' % gold_rank
        res += '\n仓库：' + str(len(user.warehouse.items)) + '/' + str(user.warehouse.max_size)
        res += '\n今日还能抽到物品：' + str(user.draw_card_number)
        res += '\n已在花店%d天' % ((datetime.now() - user.create_time).total_seconds() // global_config.day_second + 1)
        util.unlock_user(qq)
        return res

    @classmethod
    def view_user_farm_equipment(cls, qq: int, username: str) -> str:
        """
        根据用户查询其农场设备
        :param qq: qq号
        :param username: 用户名
        :return: 农场信息
        """
        util.lock_user(qq)
        user, city, soil, climate, _, _ = util.get_farm_information(qq, username)
        flower_dao.update_user_by_qq(user)
        util.unlock_user(qq)

        reply = user.username + '的农场设备：'
        reply += '\n所在地：' + city.city_name
        reply += '\n气候：' + climate.name
        reply += '\n土壤：' + soil.name

        reply += '\n温度计：' + str(user.farm.thermometer)
        reply += '\n空调：' + str(user.farm.air_condition)
        reply += '\n土壤监控站：' + str(user.farm.soil_monitoring_station)
        reply += '\n浇水壶：' + str(user.farm.watering_pot)
        reply += '\n信箱：' + str(user.farm.mailbox)
        reply += '\n温室：' + str(user.farm.greenhouse)
        reply += '\n仓库：' + str(user.farm.warehouse)
        return reply

    @classmethod
    def view_user_farm(cls, qq: int, username: str) -> str:
        """
        查看用户农场
        :param qq: QQ
        :param username: 用户名
        :return:
        """
        util.lock_user(qq)
        user, city, soil, climate, weather, flower = util.get_farm_information(qq, username)
        now_temperature = util.get_now_temperature(weather)
        util.update_farm(user, city, soil, weather, flower)
        flower_dao.update_user_by_qq(user)
        util.unlock_user(qq)

        reply = user.username + '的农场：'
        reply += '\n种植的花：'
        if user.farm.flower_id != '':
            reply += flower.name
            reply += '\n花的状态：' + FlowerState.view_name(user.farm.flower_state)

            seed_time: int = flower.seed_time
            grow_time: int = seed_time + flower.grow_time
            mature_time: int = grow_time + flower.mature_time
            overripe_time: int = mature_time + flower.overripe_time
            if user.farm.hour < seed_time:
                reply += '\n阶段：种子'
            elif user.farm.hour < grow_time:
                reply += '\n阶段：幼苗'
            elif user.farm.hour < mature_time:
                reply += '\n阶段：成熟'
            elif user.farm.hour < overripe_time:
                reply += '\n阶段：过熟'
            else:
                reply += '\n阶段：枯萎'
            if user.farm.hour < grow_time:
                reply += '\n成长度：' + '%.1f%%' % (user.farm.hour * 100.0 / grow_time)
            elif user.farm.hour < mature_time:
                reply += '\n成长度：100%'
                reply += '\n成熟度：' + '%.1f%%' % ((user.farm.hour - grow_time) * 100.0 / flower.mature_time)
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

        reply += '\n马：'
        if user.farm.horse.name != '':
            reply += user.farm.horse.name
            reply += '（%d/%d岁）' % (
                (datetime.now() - user.farm.horse.born_time).total_seconds() * 2 // global_config.day_second,
                user.farm.horse.max_age
            )
        else:
            reply += '暂无'
        reply += '\n狗：'
        if user.farm.dog.name != '':
            reply += user.farm.dog.name
            reply += '（%d/%d岁）' % (
                (datetime.now() - user.farm.dog.born_time).total_seconds() * 2 // global_config.day_second,
                user.farm.dog.max_age
            )
        else:
            reply += '暂无'
        reply += '\n猫：'
        if user.farm.cat.name != '':
            reply += user.farm.cat.name
            reply += '（%d/%d岁）' % (
                (datetime.now() - user.farm.cat.born_time).total_seconds() * 2 // global_config.day_second,
                user.farm.cat.max_age
            )
        else:
            reply += '暂无'

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
        if len(mail.appendix) > 0 and mail.gold > 0:
            reply += '\n附件：' + util.show_items(mail.appendix) + '、金币（%.2f）' % (mail.gold / 100)
        elif len(mail.appendix) > 0:
            reply += '\n附件：' + util.show_items(mail.appendix)
        elif mail.gold > 0:
            reply += '\n附件：金币（%.2f）' % (mail.gold / 100)
        if mail.received:
            reply += '（已领取附件）'
        return reply

    @classmethod
    def view_flower_group(cls, name: str) -> str:
        flower_group: FlowerGroup = flower_dao.select_flower_group_by_name(name)
        if flower_group.valid():
            return str(flower_group)
        return '未找到专辑：' + name

    @classmethod
    def view_achievement(cls, achievement_name: str) -> str:
        """
        查询成就
        :param achievement_name: 成就名
        :return:
        """
        achievement: Achievement = flower_dao.select_achievement_by_name(achievement_name)
        if not achievement.valid():
            return '成就“%s”不存在' % achievement_name
        return str(achievement)

    @classmethod
    def view_buff(cls, buff_name: str) -> str:
        """
        查询成就
        :param buff_name: buff名
        :return:
        """
        buff: Buff = flower_dao.select_buff_by_name(buff_name)
        if not buff.valid():
            return 'BUFF“%s”不存在' % buff_name
        return str(buff)

    @classmethod
    def view_user_clothing(cls, qq: int, username: str) -> str:
        """
        展示时装
        """
        user: User = util.get_user(qq, username)
        reply: str = user.username + '，你的时装如下：'
        reply += '\n帽子：' + str(user.clothing.hat)
        reply += '\n衣服：' + str(user.clothing.clothes)
        reply += '\n裤子：' + str(user.clothing.trousers)
        reply += '\n鞋子：' + str(user.clothing.shoes)
        reply += '\n手套：' + str(user.clothing.glove)
        reply += '\n项链：' + str(user.clothing.necklace)
        reply += '\n手链：' + str(user.clothing.bracelet)
        reply += '\n脚链：' + str(user.clothing.foot_ring)
        reply += '\n披风：' + str(user.clothing.cape)
        reply += '\n外套：' + str(user.clothing.coat)
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
            util.unlock_user(qq)
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
        util.lock_user(qq)
        user: User = util.get_user(qq, username)
        try:
            if mail_index > 0:
                mail_index -= 1
            if mail_index < 0 or mail_index >= len(user.mailbox.mail_list):
                return user.username + '，超出范围'
            mail_id = user.mailbox.mail_list[mail_index]
            mail: Mail = flower_dao.select_mail_by_id(mail_id)
            if len(mail.appendix) == 0 and mail.gold == 0:
                return user.username + '，该信件没有附件可以领取。'
            if mail.received:
                return user.username + '，你已经领取过该附件了。'
            util.insert_items(user.warehouse, copy.deepcopy(mail.appendix))
            user.get_gold(mail.gold)
            mail.received = True
            flower_dao.update_mail(mail)
            flower_dao.update_user_by_qq(user)
            return user.username + '，领取成功，信件“%s”的附件%s，附赠金币%.2f' % (
                mail.title, util.show_items(mail.appendix), mail.gold / 100)
        except WareHouseSizeNotEnoughException:
            return user.username + '，领取失败，仓库空间不足！'
        except ItemNegativeNumberException:
            return user.username + '，领取失败！该附件可能在送信的路上已损坏。人生命途总是充满了变数。'
        except ItemNotFoundException:
            return user.username + '，领取失败！该附件可能在送信的路上已损坏。人生命途总是充满了变数。'
        finally:
            util.unlock_user(qq)

    @classmethod
    def view_user_buff(cls, qq: int, username: str, page: int = 0, page_size: int = 20):
        """
        查看成就
        :param qq:
        :param username:
        :param page:
        :param page_size:
        :return:
        """
        user: User = util.get_user(qq, username)
        reply: str = '%s，你的BUFF如下：' % user.username
        buff_list: List[DecorateBuff] = [buff for buff in user.buff if not buff.expired()]
        if len(buff_list) == 0:
            reply += '\n没有任何buff呢~'
            return reply
        index = -1
        for buff in buff_list:
            index += 1
            if index < page * page_size:
                continue
            elif index > (page + 1) * page_size:
                break
            reply += '\n' + str(buff)
        total = len(buff_list)
        if total > page_size:
            total_page = total // page_size
            if total % page_size > 0:
                total_page += 1
            reply += '\n------\n当前页码：%d/%d，输入“花店buff %d”查看下一页' % (page + 1, total_page, page + 2)
        return reply

    @classmethod
    def view_user_achievement(cls, qq: int, username: str, page: int = 0, page_size: int = 20) -> str:
        """
        查看成就
        :param qq:
        :param username:
        :param page:
        :param page_size:
        :return:
        """
        user: User = util.get_user(qq, username)
        reply: str = '%s，你的成就如下：' % user.username
        achievement_list = [user.achievement[achievement_name] for achievement_name in user.achievement if
                            user.achievement[achievement_name].level > 0]
        if len(achievement_list) == 0:
            reply += '\n你的成就栏看起来还空空如也'
            return reply
        index = -1
        for achievement in achievement_list:
            index += 1
            if index < page * page_size:
                continue
            elif index > (page + 1) * page_size:
                break
            reply += '\n' + str(achievement)
        total = len(achievement_list)
        if total > page_size:
            total_page = total // page_size
            if total % page_size > 0:
                total_page += 1
            reply += '\n------\n当前页码：%d/%d，输入“花店成就 %d”查看下一页' % (page + 1, total_page, page + 2)
        return reply

    @classmethod
    def view_user_simple_achievement(cls, qq: int, username: str, page: int = 0, page_size: int = 20) -> str:
        """
        查看成就
        :param qq:
        :param username:
        :param page:
        :param page_size:
        :return:
        """
        user: User = util.get_user(qq, username)
        reply: str = '%s，你的精简成就如下（不包含种植植物的）：' % user.username
        achievement_list = [user.achievement[achievement_name] for achievement_name in user.achievement if
                            user.achievement[achievement_name].level > 0]
        achievement_list = [achievement for achievement in achievement_list if
                            not achievement.name.startswith('擅长') and not achievement.name.endswith('大师')]
        if len(achievement_list) == 0:
            reply += '\n你的精简成就栏看起来还空空如也'
            return reply
        index = -1
        for achievement in achievement_list:
            index += 1
            if index < page * page_size:
                continue
            elif index > (page + 1) * page_size:
                break
            reply += '\n' + str(achievement)
        total = len(achievement_list)
        if total > page_size:
            total_page = total // page_size
            if total % page_size > 0:
                total_page += 1
            reply += '\n------\n当前页码：%d/%d，输入“花店成就 %d”查看下一页' % (page + 1, total_page, page + 2)
        return reply

    @classmethod
    def view_knowledge(cls, qq: int, username: str, page: int = 0, page_size: int = 20) -> str:
        """
        查看成就
        :param qq:
        :param username:
        :param page:
        :param page_size:
        :return:
        """
        user: User = util.get_user(qq, username)
        reply: str = '%s，你的知识如下：' % user.username
        if len(user.knowledge) == 0:
            reply += '\n你的知识看起来还空空如也'
            return reply
        index = -1
        for flower_name in user.knowledge:
            index += 1
            if index < page * page_size:
                continue
            elif index > (page + 1) * page_size:
                break
            reply += '\n' + str(flower_name) + '-' + util.show_knowledge_level(user.knowledge[flower_name])
        total = len(user.knowledge)
        if total > page_size:
            total_page = total // page_size
            if total % page_size > 0:
                total_page += 1
            reply += '\n------\n当前页码：%d/%d，输入“花店知识 %d”查看下一页' % (page + 1, total_page, page + 2)
        return reply

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
        system_data: SystemData = util.get_system_data()
        util.lock_user(qq)
        user: User = util.get_user(qq, username)
        now: datetime = datetime.now()
        if user.last_sign_date.date() == now.date():
            util.unlock_user(qq)
            return user.username + '，今天已经签到过了'
        if user.last_sign_date.date() + timedelta(days=1) == now.date():
            user.sign_continuous += 1
        else:
            user.sign_continuous = 1
        user.sign_count += 1
        user.last_sign_date = now
        # 如果连续签到的第七天会额外获得东西
        item: DecorateItem or None = None
        if user.sign_continuous % 7 == 0:
            item = DecorateItem()
            item.item_name = '加速卡'
            item.item_type = ItemType.accelerate
            item.number = 1
            item.hour = 12
            try:
                util.insert_items(user.warehouse, [copy.deepcopy(item)])
            except MyException:
                item = None
        # 查看连续签到的成就奖励
        util.give_achievement(user, '连续签到', value=user.sign_continuous, cover_old_value=True)
        # 签到1点经验
        user.exp += 1
        gold = random.randint(100, 500)
        user.get_gold(gold)
        # 只对于不足次数的补足，有可能有活动之类的额外增加了每日的抽卡次数
        if user.draw_card_number < system_data.draw_card_max_number:
            user.draw_card_number = system_data.draw_card_max_number
        user.update(user.qq)
        res = user.username + '，签到成功！'
        res += '\n获得金币：' + '%.2f' % (gold / 100)
        res += '\n剩余金币：' + '%.2f' % (user.gold / 100)
        res += '\n连续签到：' + str(user.sign_continuous) + '天'
        res += '\n累计签到：' + str(user.sign_count) + '天'
        if item is not None:
            res += '\n额外获得物品：' + str(item)
        flower_dao.update_user_by_qq(user)
        sign_record: SignRecord = SignRecord()
        sign_record.qq = user.qq
        sign_record.update(user.qq)
        flower_dao.insert_sign_record(sign_record)
        util.unlock_user(qq)
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
        util.lock_user(qq)
        user: User = util.get_user(qq, username)
        reply = '转账结果如下：'
        for target_qq in at_list:
            try:
                util.lock_user(target_qq)
                target_user: User = util.get_user(target_qq, '')
                if user.gold < gold:
                    reply += '\n对' + target_user.username + '转账失败，余额不足'
                else:
                    user.gold -= gold
                    # 转账1个人加一次经验
                    user.exp += 1
                    level = abs(user.level - target_user.level)
                    if level <= 3:
                        ration = 0.83 * (1.0 + 0.2 * (random.random() - 0.5) - 0.05 * level)
                    elif level <= 6:
                        ration = 0.4 * (1.0 + 0.2 * (random.random() - 0.5) - 0.05 * level)
                    elif level <= 9:
                        ration = 0.1 * (1.0 + 0.2 * (random.random() - 0.5) - 0.05 * level)
                    else:
                        reply += '\n对' + target_user.username + '转账失败，等级相差过大'
                        continue

                    result_gold: int = int(gold * ration)
                    target_user.get_gold(result_gold)
                    target_user.update(qq)
                    flower_dao.update_user_by_qq(target_user)
                    reply += '\n对' + target_user.username + '转账成功，余额：%s，税率%.2f%%，实际到账：%s' % (
                        util.show_gold(user.gold), (1 - ration) * 100, util.show_gold(result_gold))
            except ResBeLockedException:
                reply += '\n对' + str(target_qq) + '转账失败，无法转账或网络波动'
            except UserNotRegisteredException:
                reply += '\n对' + str(target_qq) + '转账失败，还未注册'
            finally:
                util.unlock_user(target_qq)
        flower_dao.update_user_by_qq(user)
        util.unlock_user(qq)
        return reply

    @classmethod
    def view_warehouse(cls, qq: int, username: str, page: int, page_size: int = 20,
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
        if page > 0:
            page -= 1
        user: User = util.get_user(qq, username)
        total_number = len(user.warehouse.items)
        reply = user.username + '，你的花店仓库如下：' + str(total_number) + '/' + str(user.warehouse.max_size)
        if total_number == 0:
            reply += '\n暂无'
        else:
            total_page = int(total_number / page_size)
            if total_number % page_size != 0:
                total_page += 1
            if page < 0 or page >= total_page:
                raise PageOutOfRangeException('背包页码超限，总计：' + str(total_page))
            index = -1
            for item in user.warehouse.items:
                index += 1
                if index < page * page_size:
                    continue
                if index > (page + 1) * page_size:
                    break
                reply += '\n' + str(item)
            reply += '\n------'
            reply += '\n总计页码：' + str(total_page)
        description = ''
        if user.warehouse.description != '' and remove_description:
            util.lock_user(qq)
            description = user.warehouse.description[:-1]
            user.warehouse.description = ''
            flower_dao.update_user_by_qq(user)
            util.unlock_user(qq)
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
        util.lock_user(qq)
        user: User = util.get_user(qq, username)
        if user.beginner_pack:
            return user.username + '，你已经领取过初始礼包了'
        user.beginner_pack = True
        item: DecorateItem = DecorateItem()
        item_list: List[DecorateItem] = []

        # 初始获取初始种子
        seed_list = ['杂草种子']
        for seed in seed_list:
            item.item_name = seed
            item.number = 5
            item_list.append(copy.deepcopy(item))
        # 新手道具
        item.item_name = '新手水壶'
        item.number = 1
        item.durability = -1
        item_list.append(copy.deepcopy(item))
        item.item_name = '加速卡'
        item.number = 1
        item.hour = 7
        item_list.append(copy.deepcopy(item))

        try:
            util.insert_items(user.warehouse, item_list)
            flower_dao.update_user_by_qq(user)
        except ItemNotFoundException:
            return '内部错误！'
        except ItemNegativeNumberException:
            return '内部错误！'
        except WareHouseSizeNotEnoughException:
            return '仓库空间不足'
        finally:
            util.unlock_user(qq)

        context: BeginnerGuideContext = BeginnerGuideContext()
        flower_dao.insert_context(qq, context)
        return '领取成功！接下来输入“花店签到”试试。\n' \
               '输入“关闭新手指引”可以关闭。不过你只有完成新手指引才可以领取完整的礼包哦~'

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
        return str(weather)

    @classmethod
    def throw_item(cls, qq: int, username: str, item: DecorateItem) -> str:
        """
        丢弃一件物品
        :param qq: qq
        :param username: 用户名
        :param item: 物品
        :return: 结果
        """
        util.lock_user(qq)
        user: User = util.get_user(qq, username)
        try:
            if item.number <= 0:
                return user.username + '，物品数量不能小于等于0'
            util.remove_items(user.warehouse, [item])
            flower_dao.update_user_by_qq(user)
            return user.username + '，丢弃成功'
        except ItemNotFoundException:
            return user.username + '，没有该物品'
        except ItemNotEnoughException:
            return user.username + '，物品不足'
        finally:
            util.unlock_user(qq)

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
        util.lock_user(qq)
        user: User = util.get_user(qq, username)
        try:
            if user.farm.flower_id != '':
                return user.username + '，您的农场已经有花了'
            flower: Flower = flower_dao.select_flower_by_name(flower_name)
            if flower.name != flower_name:
                return user.username + '，不存在这种花或该花不可以种植'
            item: DecorateItem = DecorateItem()
            item.item_name = flower_name + '种子'
            item.number = 1
            util.remove_items(user.warehouse, [item])
            user.farm.flower_id = flower.get_id()
            user.farm.flower_state = FlowerState.normal
            user.farm.last_check_time = datetime.now()
            user.farm.reality_hour = 0
            user.farm.hour = 0.0
            user.farm.bad_hour = 0.0
            user.farm.perfect_hour = 0.0
            user.farm.stop_prefect = 0
            user.farm.non_perfect_hour = 0
            user_statistics: UserStatistics = util.get_user_statistics(qq)
            if flower_name in user_statistics.plant_flower:
                user_statistics.plant_flower[flower_name] += 1
            else:
                user_statistics.plant_flower[flower_name] = 1
            flower_dao.update_user_statistics(user_statistics)
            flower_dao.update_user_by_qq(user)
            return user.username + '，种植' + flower_name + '成功！'
        except ItemNotFoundException:
            return user.username + '，没有' + flower_name + '种子'
        except ItemNotEnoughException:
            return user.username + '，没有足够的' + flower_name + '种子'
        finally:
            util.unlock_user(qq)

    @classmethod
    def watering(cls, qq: int, username: str, multiple: int) -> str:
        system_data: SystemData = util.get_system_data()
        util.lock_user(qq)
        user: User = util.get_user(qq, username)

        watering_pot: DecorateItem = user.farm.watering_pot
        if user.farm.watering_pot.max_durability > 0 and user.farm.watering_pot.durability > 0:
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
            else:
                return user.username + '，浇水失败！当前没有浇水壶或已没有耐久！'
        else:
            return user.username + '，浇水失败！当前没有浇水壶或已没有耐久！'
        if multiple <= 0:
            return user.username + '，浇水次数不可以是负数！'
        # 设置湿度的上限
        soil: Soil = flower_dao.select_soil_by_id(user.farm.soil_id)
        if soil.valid() and user.farm.humidity > soil.max_humidity:
            humidity_change -= user.farm.humidity - soil.max_humidity
            user.farm.humidity = soil.max_humidity
        if user.farm.humidity > system_data.soil_max_humidity:
            humidity_change -= user.farm.humidity - system_data.soil_max_humidity
            user.farm.humidity = system_data.soil_max_humidity
        cost_gold: int = int(system_data.watering_cost_gold / 5.0 * humidity_change)
        # 金币消耗
        if user.gold < cost_gold:
            return user.username + '，浇水失败！金币不足！\n每浇水一次，需要金币%.2f' % (
                    system_data.watering_cost_gold / 100)
        user.gold -= cost_gold
        # 浇水多少次加多少经验值
        user.exp += 1
        user_statistics: UserStatistics = util.get_user_statistics(qq)
        user_statistics.watering += 1
        flower_dao.update_user_statistics(user_statistics)
        flower_dao.update_user_by_qq(user)
        util.unlock_user(qq)
        if humidity_change == 0.0:
            return user.username + '，浇水失败！湿度已达到土壤的上限！'
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
        try:
            util.lock_user(qq)
            # 把名字一起锁定了
            util.lock_username(new_username)
            user: User = util.get_user(qq, username)
            old_user: User = flower_dao.select_user_by_username(new_username)
            if old_user.valid():
                return '该名字已被别人使用！'
            user.username = new_username
            user.auto_get_name = False
            flower_dao.update_user_by_qq(user)
            return '已成功更改你的游戏名'
        finally:
            util.unlock_username(new_username)

    @classmethod
    def clear_username(cls, qq: int, username: str) -> str:
        """
        清除用户名
        :param qq: qq
        :param username: 自动获取的用户名
        :return: 结果
        """
        util.lock_user(qq)
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
        util.lock_user(qq)
        user: User = util.get_user(qq, username)
        try:
            if item.number <= 0:
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
                    user.accelerate_buff(seconds=global_config.hour_second * hour)
                    city: City = flower_dao.select_city_by_id(user.city_id)
                    flower: Flower = flower_dao.select_flower_by_id(user.farm.flower_id)
                    soil: Soil = flower_dao.select_soil_by_id(user.farm.soil_id)
                    weather: Weather = util.get_weather(city)
                    util.update_farm(user, city, soil, weather, flower)
                    return user.username + '，成功加速农场%d小时' % hour
                elif item.item_name == '完美加速卡':
                    hour: int = item.hour * item.number
                    user.farm.hour += hour
                    return user.username + '，成功完美加速农场%d小时' % hour
            # 化肥
            elif item.item_type == ItemType.fertilizer:
                nutrition: float = item.nutrition * item.number
                nutrition = util.add_nutrition(user.farm, nutrition)
                humidity: float = item.humidity * item.number
                humidity = util.add_humidity(user.farm, humidity)
                return user.username + '，成功增加营养%.2f，湿度%.2f' % (nutrition, humidity)
            # 温度计
            elif item.item_type == ItemType.thermometer:
                if item.number == 1:
                    if user.farm.thermometer.item_name != '':
                        util.insert_items(user.warehouse, [user.farm.thermometer])
                    item.update = datetime.now()
                    item.durability -= 1
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
                    item.durability -= 1
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
                    item.durability -= 1
                    user.farm.watering_pot = item
                    return user.username + '，成功使用%s' % str(item)
                else:
                    raise UseFailException(user.username + '，该类型物品只能使用一个')
            # 空调
            elif item.item_type == ItemType.air_condition:
                if item.number == 1:
                    if user.farm.air_condition.item_name != '':
                        util.insert_items(user.warehouse, [user.farm.air_condition])
                    item.update = datetime.now()
                    item.durability -= 1
                    user.farm.air_condition = item
                    return user.username + '，成功使用%s' % str(item)
                else:
                    raise UseFailException(user.username + '，该类型物品只能使用一个')
            # 信箱
            elif item.item_type == ItemType.mailbox:
                if item.number == 1:
                    if user.farm.mailbox.item_name != '':
                        util.insert_items(user.warehouse, [user.farm.mailbox])
                    item.update = datetime.now()
                    item.durability -= 1
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
                    item.durability -= 1
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
                    item.durability -= 1
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
                elif item.item_name == '小金卡':
                    gold = random.randint(50 * item.number, 501 * item.number)
                    user.get_gold(gold)
                    return user.username + '，获得%.2f金币' % (gold / 100)
                elif item.item_name == '大金卡':
                    gold = random.randint(50 * item.number, 50001 * item.number)
                    user.get_gold(gold)
                    return user.username + '，获得%.2f金币' % (gold / 100)
                elif item.item_name == '金砖卡':
                    gold = random.randint(50 * item.number, 500001 * item.number)
                    user.get_gold(gold)
                    return user.username + '，获得%.2f金币' % (gold / 100)
                elif item.item_name == '铲铲卡':
                    if user.farm.flower_id == '':
                        raise UseFailException(user.username + '，你的农场没有花')
                    user.farm.flower_id = ''
                    user_statistics: UserStatistics = util.get_user_statistics(qq)
                    user_statistics.remove_flower += 1
                    flower_dao.update_user_statistics(user_statistics)
                    return user.username + '，成功铲除花'
                elif item.item_name == '暖风卡':
                    temperature = item.temperature * item.number
                    user.farm.temperature += temperature
                    return user.username + '，温度+%.2f℃' % temperature
                elif item.item_name == '寒风卡':
                    temperature = item.temperature * item.number
                    user.farm.temperature += temperature
                    return user.username + '，温度%.2f℃' % temperature
                elif item.item_name == '小肥料卡' or item.item_name == '大肥料卡':
                    nutrition: float = item.nutrition * item.number
                    nutrition = util.add_nutrition(user.farm, nutrition)
                    return user.username + '，营养+%.2f' % nutrition
                elif item.item_name == '涓流卡' or item.item_name == '湍流卡':
                    humidity: float = item.humidity * item.number
                    humidity = util.add_humidity(user.farm, humidity)
                    return user.username + '，湿度+%.2f' % humidity
                elif item.item_name == '经验卡':
                    exp: int = random.randint(item.number, 5 * item.number)
                    user.exp += exp
                    return user.username + '，经验值+%d' % exp
                elif item.item_name == '缓控释肥' or item.item_name == '烈度缓释肥' or item.item_name == '微量缓释肥':
                    buff: Buff = flower_dao.select_buff_by_name('文鳐')
                    if buff.valid():
                        decorate_buff: DecorateBuff = DecorateBuff().generate(buff)
                        decorate_buff.change_nutrition = item.nutrition * item.number
                        decorate_buff.expired_time = datetime.now() + timedelta(seconds=global_config.hour_second * 6)
                        user.buff.append(decorate_buff)
                        return user.username + '，获得buff：%s' % str(decorate_buff)
                elif item.item_name == '涓涓细流' or item.item_name == '湍湍江润' or item.item_name == '薄薄雾拥':
                    buff: Buff = flower_dao.select_buff_by_name('天吴')
                    if buff.valid():
                        decorate_buff: DecorateBuff = DecorateBuff().generate(buff)
                        decorate_buff.change_humidity = item.humidity * item.number
                        decorate_buff.expired_time = datetime.now() + timedelta(seconds=global_config.hour_second * 6)
                        user.buff.append(decorate_buff)
                        return user.username + '，获得buff：%s' % str(decorate_buff)
                elif item.item_name == '炭火卡':
                    buff: Buff = flower_dao.select_buff_by_name('祝融')
                    if buff.valid():
                        decorate_buff: DecorateBuff = DecorateBuff().generate(buff)
                        decorate_buff.change_temperature = item.temperature * item.number
                        decorate_buff.expired_time = datetime.now() + timedelta(seconds=global_config.hour_second * 6)
                        user.buff.append(decorate_buff)
                        return user.username + '，获得buff：%s' % str(decorate_buff)
                elif item.item_name == '冰块卡':
                    buff: Buff = flower_dao.select_buff_by_name('玄武')
                    if buff.valid():
                        decorate_buff: DecorateBuff = DecorateBuff().generate(buff)
                        decorate_buff.change_temperature = item.temperature * item.number
                        decorate_buff.expired_time = datetime.now() + timedelta(seconds=global_config.hour_second * 6)
                        user.buff.append(decorate_buff)
                        return user.username + '，获得buff：%s' % str(decorate_buff)
                elif item.item_name == '花语卡' or item.item_name == '2022中秋花语卡':
                    if item.number != 1:
                        raise UseFailException(user.username + '，该类型物品只能使用一个')
                    if user.farm.flower_id == '':
                        return user.username + '，好像什么也没有听见'
                    flower: Flower = flower_dao.select_flower_by_id(user.farm.flower_id)
                    if not flower.valid() and random.randint(0, 100) >= 70:
                        return user.username + '，好像什么也没有听见'
                    # 计算条件
                    if user.farm.hour < flower.seed_time:
                        condition_level: ConditionLevel = flower.seed_condition.get_condition_level(
                            user.farm.temperature,
                            user.farm.humidity,
                            user.farm.nutrition)
                    elif user.farm.hour < flower.grow_time:
                        condition_level: ConditionLevel = flower.grow_condition.get_condition_level(
                            user.farm.temperature,
                            user.farm.humidity,
                            user.farm.nutrition)
                    elif user.farm.hour < flower.mature_time:
                        condition_level: ConditionLevel = flower.mature_condition.get_condition_level(
                            user.farm.temperature,
                            user.farm.humidity,
                            user.farm.nutrition)
                    else:
                        condition_level: ConditionLevel = flower.mature_condition.get_condition_level(
                            user.farm.temperature,
                            user.farm.humidity,
                            user.farm.nutrition)
                    if condition_level == ConditionLevel.PERFECT:
                        if user.farm.perfect_hour / flower.prefect_time > 0.5:
                            return user.username + '，你的花花看起来开心极了，它很喜欢你'
                        else:
                            return user.username + '，你的花花看起来非常开心'
                    elif condition_level == ConditionLevel.SUITABLE:
                        return user.username + '，你的花花有点开心'
                    elif condition_level == ConditionLevel.NORMAL:
                        return user.username + '，你的花花心情平平无奇'
                    elif condition_level == ConditionLevel.BAD:
                        if user.farm.bad_hour / flower.withered_time > 0.5:
                            return user.username + '，你的花花看起来有点讨厌你'
                        else:
                            return user.username + '，你的花花有点沮丧'
                    return user.username + '，好像什么也没有听见'
                elif item.item_name == '知己知彼' or item.item_name == '2022中秋知己知彼':
                    if item.number != 1:
                        raise UseFailException(user.username + '，该类型物品只能使用一个')
                    context: ViewRelationshipContext = ViewRelationshipContext()
                    flower_dao.insert_context(qq, context)
                    return user.username + '，请输入npc的id，你可以输入“花店人物 序号”，npc名字后的括号内一串字母数字就是npc的id。' \
                                           '其余任何输入表示取消探查。'
                elif item.item_name == '贫瘠卡':
                    nutrition: float = item.nutrition * item.number
                    nutrition = util.add_nutrition(user.farm, nutrition)
                    return user.username + '，营养%.2f' % nutrition
                elif item.item_name == '干燥卡':
                    humidity: float = item.humidity * item.number
                    humidity = util.add_humidity(user.farm, humidity)
                    return user.username + '，湿度%.2f' % humidity
                elif item.item_name == '随机加速卡':
                    hour: int = random.randint(item.number, 12 * item.number)
                    user.farm.last_check_time -= timedelta(hours=hour)
                    user.accelerate_buff(seconds=global_config.hour_second * hour)
                    city: City = flower_dao.select_city_by_id(user.city_id)
                    flower: Flower = flower_dao.select_flower_by_id(user.farm.flower_id)
                    soil: Soil = flower_dao.select_soil_by_id(user.farm.soil_id)
                    weather: Weather = util.get_weather(city)
                    util.update_farm(user, city, soil, weather, flower)
                    return user.username + '，成功加速农场%d小时' % hour
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
            user_statistics: UserStatistics = util.get_user_statistics(qq)
            if item.item_name in user_statistics.use_item:
                user_statistics.use_item[item.item_name] += item.number
            else:
                user_statistics.use_item[item.item_name] = item.number
            flower_dao.update_user_statistics(user_statistics)
            flower_dao.update_user_by_qq(user)
            util.unlock_user(qq)

    @classmethod
    def reward_flower(cls, qq: int, username: str) -> str:
        """
        收获
        :param qq: qq
        :param username: 用户名
        :return: 收获
        """
        util.lock_user(qq)
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
            if user.farm.hour < grow_time:
                return user.username + '，你的花还未成熟。'
            elif user.farm.hour < overripe_time:
                item: DecorateItem = DecorateItem()
                item_obj: Item = flower_dao.select_item_by_name(flower.name)
                if item_obj.name == '':
                    raise ItemNotFoundException('物品' + flower.name + '不存在')
                item.item_name = flower.name
                # 产量需要根据bad hour进行计算（最坏的情况产量只有50%）
                item.number = flower.flower_yield
                if flower.withered_time > 0:
                    ratio: float = user.farm.bad_hour / flower.withered_time
                    item.number = int(flower.flower_yield * (1.0 - ratio))
                    if item.number == 0:
                        item.number = 1
                item.item_type = item_obj.item_type
                item.flower_quality = FlowerQuality.normal
                # 过熟阶段没法拿到完美的花
                if user.farm.flower_state == FlowerState.perfect and user.farm.hour <= mature_time:
                    item.flower_quality = FlowerQuality.perfect
                item.create = datetime.now()
                item.update = datetime.now()
                try:
                    # 将花插入背包
                    number = item.number
                    util.insert_items(user.warehouse, [item])
                    user.farm.flower_id = ''
                    # 成就管理
                    good_at_flower: str = '擅长' + flower.name
                    flower_master: str = flower.name + '大师'
                    util.give_achievement(user, good_at_flower, number)
                    if user.farm.flower_state == FlowerState.perfect:
                        util.give_achievement(user, flower_master, number)
                    # 增加经验值
                    if flower.level == FlowerLevel.S:
                        exp = 1000
                    elif flower.level == FlowerLevel.A:
                        exp = 500
                    elif flower.level == FlowerLevel.B:
                        exp = 100
                    elif flower.level == FlowerLevel.C:
                        exp = 50
                    else:
                        exp = 5
                    if user.farm.flower_state == FlowerState.perfect:
                        exp *= 2
                    user.exp += exp
                    # 更新统计数据
                    user_statistics: UserStatistics = util.get_user_statistics(qq)
                    if flower.name in user_statistics.plant_perfect_flower:
                        user_statistics.plant_perfect_flower[flower.name] += 1
                    else:
                        user_statistics.plant_perfect_flower[flower.name] = 1
                    flower_dao.update_user_statistics(user_statistics)
                    # 心跳时刻（是否是在成熟的那一个小时完美的）
                    if int(user.farm.perfect_hour) - (int(user.farm.hour) - mature_time) == flower.prefect_time:
                        util.give_achievement(user, '心跳时刻')
                    # 虚惊一场（是否bad hour刚好差一个小时）
                    if int(user.farm.bad_hour) == flower.withered_time - 1:
                        util.give_achievement(user, '虚惊一场')
                    # 植物学专家（从头完美到结束）
                    if user.farm.non_perfect_hour == 0 and flower.level != FlowerLevel.D:
                        util.give_achievement(user, '植物学专家')
                    # 完美主义者（种植一朵C级及以上完美的花）
                    if user.farm.flower_state == FlowerState.perfect and flower.level != FlowerLevel.D:
                        util.give_achievement(user, '完美主义')
                    # 更新花店第一人
                    if flower.first_user_qq == 0 and user.farm.flower_state == FlowerState.perfect:
                        flower.first_user_qq = qq
                        flower.first_user_time = datetime.now()
                        flower_dao.update_flower(flower)
                    # 更新user
                    flower_dao.update_user_by_qq(user)
                    return user.username + '，收获成功，获得%s-%sx%d' % (
                        flower.name,
                        FlowerQuality.view_name(item.flower_quality),
                        number
                    )
                except WareHouseSizeNotEnoughException:
                    return user.username + '，收获失败，仓库空间不足。'
            else:
                return user.username + '，你的花已枯萎。'
        finally:
            util.unlock_user(qq)

    @classmethod
    def view_today_person(cls, qq: int, username: str) -> str:
        """
        查看今天的人物
        :param qq: qq
        :param username: 用户名
        :return:
        """
        util.lock_user(qq)
        user: User = util.get_user(qq, username)
        user_person_list: List[UserPerson] = util.get_today_person(qq)
        reply: str = user.username + '，你今天的人物如下：'
        index: int = 0
        for user_person in user_person_list:
            index += 1
            person: Person = flower_dao.select_person(user_person.person_id)
            profession: Profession = flower_dao.select_profession(person.profession_id)
            reply += '\n%d.%s（%s）' % (index, person.name, profession.name)
        util.unlock_user(qq)
        return reply

    @classmethod
    def view_today_person_index(cls, qq: int, username: str, index: int) -> str:
        """
        查看今天的人物
        :param qq: qq
        :param username: 用户名
        :param index: 序号
        :return:
        """
        util.lock_user(qq)
        user: User = util.get_user(qq, username)
        user_person_list: List[UserPerson] = util.get_today_person(qq)
        if index > 0:
            index -= 1
        if index < 0 or index >= len(user_person_list):
            util.unlock_user(qq)
            return user.username + '，序号超限'
        user_person: UserPerson = user_person_list[index]
        person: Person = flower_dao.select_person(user_person.person_id)
        reply: str = person.name + '（%s）' % person.get_id()
        if person.gender == Gender.male:
            reply += '\n性别：男'
        elif person.gender == Gender.female:
            reply += '\n性别：女'
        age: int = int((datetime.now() - person.born_time).total_seconds() // global_config.day_second)
        reply += '\n年龄：%d' % age
        race: Race = flower_dao.select_world_race(person.race_id)
        if race.valid():
            reply += '\n种族：' + race.name

        reply += '\n' + '-' * 6
        if len(user_person.news) > 0:
            reply += '\n可以打听小道消息'
            reply += '\n' + '-' * 6
        if len(user_person.commodities) > 0:
            reply += '\n可以购买如下商品：'
            index = 0
            for commodity in user_person.commodities:
                index += 1
                item: Item = flower_dao.select_item_by_id(commodity.item_id)
                reply += '\n%d.%s，金币：%.2f，库存：%d' % (index, item.name, commodity.gold / 100, commodity.stock)
            reply += '\n' + '-' * 6
        if len(user_person.knowledge) > 0:
            reply += '\n可以购买如下知识：'
            index = 0
            for knowledge in user_person.knowledge:
                index += 1
                level = user_person.knowledge[knowledge][0]
                level_str = util.show_knowledge_level(level)
                price = user_person.knowledge[knowledge][1]
                reply += '\n%d.%s-%s：%.2f金币' % (index, knowledge, level_str, price / 100)
            reply += '\n' + '-' * 6
        if user_person.send_mail_price > 0:
            reply += '\n可以送信，基本费用：%.2f' % (user_person.send_mail_price / 100)
            reply += '\n' + '-' * 6
        if user_person.can_create_market_account:
            reply += '\n可以给期货市场开户'
            reply += '\n' + '-' * 6
        util.unlock_user(qq)
        return reply

    @classmethod
    def buy_commodity(cls, qq: int, username: str, person_index: int, commodity_index: int, number: int) -> str:
        """
        购买商品
        :param qq:
        :param username:
        :param person_index:
        :param commodity_index:
        :param number:
        :return:
        """
        util.lock_user(qq)
        user: User = util.get_user(qq, username)
        user_person_list: List[UserPerson] = util.get_today_person(qq)
        if person_index > 0:
            person_index -= 1
        if person_index < 0 or person_index >= len(user_person_list):
            util.unlock_user(qq)
            return user.username + '，人物序号超限'
        if number <= 0:
            return user.username + '，不允许购买负数商品'
        user_person: UserPerson = user_person_list[person_index]
        relationship: Relationship = flower_dao.select_relationship_by_pair(user_person.person_id, str(qq))
        person: Person = flower_dao.select_person(user_person.person_id)
        profession: Profession = flower_dao.select_profession(person.profession_id)
        if not relationship.valid():
            relationship.src_person = user_person.person_id
            relationship.dst_person = str(qq)
            relationship.value = person.affinity
            flower_dao.insert_relationship(relationship)
            relationship: Relationship = flower_dao.select_relationship_by_pair(user_person.person_id, str(qq))
        if commodity_index > 0:
            commodity_index -= 1
        if commodity_index < 0 or commodity_index >= len(user_person.commodities):
            util.unlock_user(qq)
            return user.username + '，商品序号超限'
        commodity: Commodity = user_person.commodities[commodity_index]
        if commodity.stock < number:
            util.unlock_user(qq)
            return user.username + '，商品库存不足'
        if user.gold < commodity.gold * number:
            util.unlock_user(qq)
            return user.username + '，金币不足'
        try:
            item_obj: Item = flower_dao.select_item_by_id(commodity.item_id)
            item: DecorateItem = DecorateItem()
            item.item_name = item_obj.name
            item.item_type = item_obj.item_type
            item.rot_second = item_obj.rot_second  # 腐烂的秒数
            item.create = datetime.now()  # 记录当前的创建时间
            item.humidity = item_obj.humidity  # 湿度
            item.nutrition = item_obj.nutrition  # 营养
            item.temperature = item_obj.temperature  # 温度
            item.level = item_obj.level
            item.item_id = commodity.item_id
            item.number = number
            if item_obj.max_durability > 0:
                item.durability = item_obj.max_durability
            if item_obj.item_type == ItemType.accelerate:
                item.hour = random.randint(1, 4)
            elif item_obj.item_type == ItemType.flower:
                item.flower_quality = FlowerQuality.normal
            util.insert_items(user.warehouse, [copy.deepcopy(item)])
            user.gold -= commodity.gold * number
            # 经验
            exp: int = int(commodity.gold * number / 500)
            if exp <= 0:
                exp = 1
            user.exp += exp
            if profession.name == '商人':
                rand: int = random.randint(0, 100)
                if rand < person.affinity and relationship.value < 95:
                    relationship.value += 1
                    flower_dao.update_relationship(relationship)
                elif rand < person.affinity and relationship.value >= 95:
                    relationship.value -= 1
                    flower_dao.update_relationship(relationship)
            flower_dao.update_user_by_qq(user)
            user_person.commodities[commodity_index].stock -= number
            flower_dao.update_user_person(user_person)
            return user.username + '，花费金币%.2f，购买%s' % (commodity.gold * number / 100, str(item))
        except ItemNotFoundException:
            return user.username + '，该商品不可以购买'
        except ItemNegativeNumberException:
            return user.username + '，不可以购买0份或者负数份'
        except WareHouseSizeNotEnoughException:
            return user.username + '，背包容量不够'
        finally:
            util.unlock_user(qq)

    @classmethod
    def buy_knowledge(cls, qq: int, username: str, person_index: int, flower_name: str) -> str:
        """
        购买知识
        :param qq:
        :param username:
        :param person_index:
        :param flower_name:
        :return:
        """
        util.lock_user(qq)
        user: User = util.get_user(qq, username)
        user_person_list: List[UserPerson] = util.get_today_person(qq)
        if person_index > 0:
            person_index -= 1
        if person_index < 0 or person_index >= len(user_person_list):
            util.unlock_user(qq)
            return user.username + '，人物序号超限'
        user_person: UserPerson = user_person_list[person_index]
        if flower_name not in user_person.knowledge:
            util.unlock_user(qq)
            return user.username + '，该人物不出售该花的知识'
        (level, gold) = user_person.knowledge[flower_name]
        if user.gold < gold:
            util.unlock_user(qq)
            return user.username + '，金币不足'
        if flower_name in user.knowledge and user.knowledge[flower_name] >= level:
            util.unlock_user(qq)
            return user.username + '，你已经有了更高级别的该知识'
        user.gold -= gold
        # 经验
        exp: int = int(gold / 500)
        if exp <= 0:
            exp = 1
        user.exp += exp
        user.knowledge[flower_name] = level
        flower_dao.update_user_by_qq(user)
        util.unlock_user(qq)
        return user.username + '，购买成功！'

    @classmethod
    def sell_commodity(cls, qq: int, username: str, person_index: int, item: DecorateItem) -> str:
        """
        出售商品
        :param qq:
        :param username:
        :param person_index:
        :param item:
        :return:
        """
        util.lock_user(qq)
        user: User = util.get_user(qq, username)
        try:
            user_person_list: List[UserPerson] = util.get_today_person(qq)
            if person_index > 0:
                person_index -= 1
            if person_index < 0 or person_index >= len(user_person_list):
                return user.username + '，人物序号超限'
            if item.number <= 0:
                return user.username + '，出售商品不可以为负数'
            user_person: UserPerson = user_person_list[person_index]
            relationship: Relationship = flower_dao.select_relationship_by_pair(user_person.person_id, str(qq))
            person: Person = flower_dao.select_person(user_person.person_id)
            profession: Profession = flower_dao.select_profession(person.profession_id)
            if not relationship.valid():
                relationship.src_person = user_person.person_id
                relationship.dst_person = str(qq)
                relationship.value = person.affinity
            if profession.name != '商人' and profession.name != '探险家':
                return user.username + '，对方不接受出售该商品'
            if item.item_name in user_person.ban_item:
                return user.username + '，对方不接受出售该商品'
            if user_person.cancel_sell_times is None:
                user_person.cancel_sell_times = {}
                flower_dao.update_user_person(user_person)
            if item.item_name in user_person.cancel_sell_times and user_person.cancel_sell_times[item.item_name] > 5:
                relationship: Relationship = flower_dao.select_relationship_by_pair(user_person.person_id, str(qq))
                if relationship.valid():
                    relationship.value -= 1
                    flower_dao.update_relationship(relationship)
                return user.username + '，对方不接受出售该商品'
            item_obj: Item = flower_dao.select_item_by_name(item.item_name)
            gold: int = util.calculate_item_gold(item, item_obj, relationship)
            can_bargain: bool = relationship.value > 70
            context: CommodityBargainingContext = CommodityBargainingContext(
                user_person_id=user_person.get_id(),
                person_id=person.get_id(),
                item=item,
                gold=gold,
                can_bargain=can_bargain
            )
            flower_dao.insert_context(qq, context)
            if can_bargain:
                return user.username + '，%s出价单个%.2f，是否要议价，' \
                                       '“是”表示需要议价，“否”表示不需要直接出售，其余输入表示取消' % (
                           person.name, gold / 100)
            else:
                return user.username + '，%s出价单个%.2f，' \
                                       '“是”表示确认出售，其余输入表示取消' % (person.name, gold / 100)
        finally:
            util.unlock_user(qq)

    @classmethod
    def send_mail(cls, qq: int, username: str, person_index: int):
        """
        送信
        """
        util.lock_user(qq)
        user: User = util.get_user(qq, username)
        try:
            user_person_list: List[UserPerson] = util.get_today_person(qq)
            if person_index > 0:
                person_index -= 1
            if person_index < 0 or person_index >= len(user_person_list):
                return user.username + '，人物序号超限'
            user_person: UserPerson = user_person_list[person_index]
            if user_person.send_mail_price <= 0:
                return user.username + '，对方不接受帮你送信 或者 正在帮你送信'
            person: Person = flower_dao.select_person(user_person.person_id)
            context: UserSendMailContext = UserSendMailContext()
            context.user_person_id = user_person.get_id()
            context.postman_name = person.name
            context.postman_id = person.get_id()
            context.valid_date = date.today()
            flower_dao.insert_context(qq, context)
            return '请问信件的标题是什么？只可以包含文字。'
        finally:
            util.unlock_user(qq)

    @classmethod
    def create_account(cls, qq: int, username: str, person_index: int) -> str:
        """
        花店开户
        """
        util.lock_user(qq)
        user: User = util.get_user(qq, username)
        try:
            user_person_list: List[UserPerson] = util.get_today_person(qq)
            if person_index > 0:
                person_index -= 1
            if person_index < 0 or person_index >= len(user_person_list):
                return user.username + '，人物序号超限'
            user_person: UserPerson = user_person_list[person_index]
            if not user_person.can_create_market_account:
                return user.username + '，对方不能帮你开户'
            try:
                util.get_user_account(qq)
                return user.username + '，你已经开过户了'
            except NoAccount:
                context: CreateAccountConfirm = CreateAccountConfirm()
                flower_dao.insert_context(qq, context)
                return user.username + '，开户将会花费1000金币，确定要开户吗？\n输入“确认”表示确认，其余任何输入表示取消'
        finally:
            util.unlock_user(qq)

    @classmethod
    def view_user_account(cls, qq: int, username: str) -> str:
        user: User = util.get_user(qq, username)
        user_account: UserAccount = util.get_user_account(qq)
        reply = user.username + '，你的花店账户如下：'
        reply += '\n账户金币：%s' % util.show_gold(user_account.account_gold)
        reply += '\n贷款金币：%s' % util.show_gold(user_account.debt_gold)
        reply += '\n持有的期货数：%d' % len(user_account.hold_stock)
        reply += '\n未还贷款数：%d' % len(user_account.debt_list)
        return reply

    @classmethod
    def view_gold_rank(cls, debug: bool = False) -> str:
        gold_rank: List[Tuple[str, float]] = flower_dao.get_gold_rank_list()
        reply = '金币排行榜'
        reply += '\n' + '-' * 6
        index: int = 0
        for target in gold_rank:
            index += 1
            target_user: User = util.get_user(int(target[0]))
            if target_user.auto_get_name:
                target_user.username = '匿名'
            reply += '\n%d.%s：%s' % (index, target_user.username, util.show_gold(int(target[1])))
            if debug:
                reply += '@%d' % target_user.qq
        reply += '\n' + '-' * 6
        reply += '\n排行榜为动态生成，更新将会导致排行榜重置，只需要使用任一指令即可参与排行榜计算'
        return reply

    @classmethod
    def view_total_gold_rank(cls, debug: bool = False) -> str:
        exp_rank: List[Tuple[str, float]] = flower_dao.get_total_gold_rank_list()
        reply = '赚取金币排行榜'
        reply += '\n' + '-' * 6
        index: int = 0
        for target in exp_rank:
            index += 1
            util.lock_user(int(target[0]))
            target_user: User = util.get_user(int(target[0]))
            util.calculate_user_level(target_user)
            util.unlock_user(int(target[0]))
            if target_user.auto_get_name:
                target_user.username = '匿名'
            reply += '\n%d.%s：%s' % (index, target_user.username, util.show_gold(int(target[1])))
            if debug:
                reply += '@%d' % target_user.qq
        reply += '\n' + '-' * 6
        reply += '\n排行榜为动态生成，更新将会导致排行榜重置，只需要使用任一指令即可参与排行榜计算'
        return reply

    @classmethod
    def view_exp_rank(cls, debug: bool = False) -> str:
        exp_rank: List[Tuple[str, float]] = flower_dao.get_exp_rank_list()
        reply = '等级排行榜'
        reply += '\n' + '-' * 6
        index: int = 0
        for target in exp_rank:
            index += 1
            util.lock_user(int(target[0]))
            target_user: User = util.get_user(int(target[0]))
            util.calculate_user_level(target_user)
            util.unlock_user(int(target[0]))
            if target_user.auto_get_name:
                target_user.username = '匿名'
            reply += '\n%d.%s：%d级' % (index, target_user.username, target_user.level)
            if debug:
                reply += '@%d' % target_user.qq
        reply += '\n' + '-' * 6
        reply += '\n排行榜为动态生成，更新将会导致排行榜重置，只需要使用任一指令即可参与排行榜计算'
        return reply

    @classmethod
    def view_draw_card_rank(cls, debug: bool = False) -> str:
        draw_card_rank: List[Tuple[str, float]] = flower_dao.get_draw_card_rank_list()
        reply = '抽卡排行榜'
        reply += '\n' + '-' * 6
        index: int = 0
        for target in draw_card_rank:
            index += 1
            target_user: User = util.get_user(int(target[0]))
            if target_user.auto_get_name:
                target_user.username = '匿名'
            reply += '\n%d.%s：%d次' % (index, target_user.username, int(target[1]))
            if debug:
                reply += '@%d' % target_user.qq
        reply += '\n' + '-' * 6
        reply += '\n排行榜为动态生成，更新将会导致排行榜重置，只需要使用任一指令即可参与排行榜计算'
        return reply

    @classmethod
    def view_sign_rank(cls, debug: bool = False) -> str:
        sign_rank: List[Tuple[str, float]] = flower_dao.get_sign_rank_list()
        reply = '连续签到排行榜'
        reply += '\n' + '-' * 6
        index: int = 0
        for target in sign_rank:
            index += 1
            target_user: User = util.get_user(int(target[0]))
            if target_user.auto_get_name:
                target_user.username = '匿名'
            reply += '\n%d.%s：连续签到%d天' % (index, target_user.username, int(target[1]))
            if debug:
                reply += '@%d' % target_user.qq
        reply += '\n' + '-' * 6
        reply += '\n排行榜为动态生成，更新将会导致排行榜重置，只需要使用任一指令即可参与排行榜计算'
        return reply

    @classmethod
    def view_user_statistics(cls, qq: int, username: str) -> str:
        """
        查看统计数据
        """
        user: User = util.get_user(qq, username)
        user_statistics: UserStatistics = util.get_user_statistics(qq)
        reply: str = '%s，你的花店统计数据如下：' % user.username
        sign_rank: int = flower_dao.get_sign_rank(qq)
        reply += '\n连续签到：%d天（第%d名）' % (user.sign_continuous, sign_rank + 1)
        reply += '\n总计签到：%d天' % user.sign_count
        reply += '\n赚取的总金币：' + util.show_gold(user.total_gold)
        reply += '\n浇水：%d次' % user_statistics.watering
        reply += '\n铲除：%d次' % user_statistics.remove_flower
        total_item: int = 0
        for item in user_statistics.use_item:
            total_item += user_statistics.use_item[item]
        reply += '\n使用过道具：%d个' % total_item
        plant_times: int = 0
        for plant in user_statistics.plant_flower:
            plant_times += user_statistics.plant_flower[plant]
        reply += '\n种植植物：%d次' % plant_times
        plant_perfect_times: int = 0
        for plant in user_statistics.plant_perfect_flower:
            plant_perfect_times += user_statistics.plant_perfect_flower[plant]
        reply += '\n收获完美植物：%d次' % plant_times
        reply += '\n抽卡次数：%d次' % user_statistics.draw_times
        draw_card_rank: int = flower_dao.get_draw_card_rank(qq)
        reply += '（第%d名）' % (draw_card_rank + 1)
        reply += '\n抽到物品次数：%d次' % user_statistics.success_draw_times
        reply += '\n抽完所有物品：%d次' % user_statistics.all_draw_times
        reply += '\n破产次数：%d次' % user_statistics.bankruptcy
        reply += '\n购买彩票次数：%d次' % user_statistics.lottery_times
        reply += '\n彩票中奖次数：%d次' % user_statistics.winning_lottery_times
        return reply

    @classmethod
    def transfer_in(cls, qq: int, username: str, gold: int) -> str:
        """
        转入
        """
        util.lock_user(qq)
        user: User = util.get_user(qq, username)
        user_account: UserAccount = util.get_user_account(qq)
        try:
            if user.gold < gold:
                return user.username + '，金币不足！'
            if gold <= 0:
                return user.username + '，不允许负数金币'
            user.gold -= gold
            user_account.account_gold += gold
            flower_dao.update_user_account(user_account)
            flower_dao.update_user_by_qq(user)
            return user.username + '，转入交易账户成功！'
        finally:
            util.unlock_user(qq)

    @classmethod
    def transfer_out(cls, qq: int, username: str, gold: int) -> str:
        """
        转出
        """
        util.lock_user(qq)
        user: User = util.get_user(qq, username)
        user_account: UserAccount = util.get_user_account(qq)
        try:
            if user_account.account_gold < gold:
                return user.username + '，交易账户金币不足！'
            if user_account.account_gold - gold < user_account.debt_gold:
                return user.username + '，交易账户金币数不能小于借款金币数。即，借款的钱无法转出交易账户。'
            if gold <= 0:
                return user.username + '，不允许负数金币'
            user.gold += gold
            user_account.account_gold -= gold
            flower_dao.update_user_account(user_account)
            flower_dao.update_user_by_qq(user)
            return user.username + '，转出交易账户成功！'
        finally:
            util.unlock_user(qq)

    @classmethod
    def view_today_debt_choice(cls, qq: int, index: int) -> str:
        """浏览今日的贷款"""
        util.get_user_account(qq)
        debt_list: List[TodayDebt] = flower_dao.select_today_debt_by_qq(qq, datetime.now())
        if len(debt_list) == 0:
            util.generate_today_debt(qq)
            debt_list: List[TodayDebt] = flower_dao.select_today_debt_by_qq(qq, datetime.now())
        if index >= len(debt_list):
            return '页码超限！总计页码：%d' % len(debt_list)
        debt: TodayDebt = debt_list[index]
        return "金币：%s\n" \
               "还款天数：%d\n" \
               "日利率：%.4f%%\n" \
               "提前还款最低利率：%.4f%%\n" \
               "抵押率：%.4f%%\n" \
               "是否是利滚利：%s\n" \
               "是否已借出：%s\n" \
               "------\n" \
               "总计页码：%d" % (
                   util.show_gold(debt.gold),
                   debt.repayment_day,
                   debt.daily_interest_rate * 100,
                   debt.minimum_interest * 100,
                   debt.mortgage_rates * 100,
                   '是' if debt.rolling_interest else '否',
                   '是' if debt.borrowing else '否',
                   len(debt_list)
               )

    @classmethod
    def view_all_today_debt_choice(cls, qq: int) -> str:
        """浏览今日的全部贷款"""
        util.get_user_account(qq)
        debt_list: List[TodayDebt] = flower_dao.select_today_debt_by_qq(qq, datetime.now())
        if len(debt_list) == 0:
            util.generate_today_debt(qq)
            debt_list: List[TodayDebt] = flower_dao.select_today_debt_by_qq(qq, datetime.now())
        reply: str = ''
        index: int = 0
        for debt in debt_list:
            index += 1
            reply += '%d.%s（利息%.4f%%）\n' % (index, util.show_gold(debt.gold), debt.daily_interest_rate * 100)
        return reply[:-1]

    @classmethod
    def get_debt(cls, qq: int, index: int) -> str:
        """获取今日的某个贷款"""
        user_account: UserAccount = util.get_user_account(qq)
        debt_list: List[TodayDebt] = flower_dao.select_today_debt_by_qq(qq, datetime.now())
        if len(debt_list) == 0:
            util.generate_today_debt(qq)
            debt_list: List[TodayDebt] = flower_dao.select_today_debt_by_qq(qq, datetime.now())
        if index >= len(debt_list):
            return '页码超限！总计页码：%d' % len(debt_list)
        debt: TodayDebt = debt_list[index]
        if debt.borrowing:
            return '该贷款已借出，不可以重复借'
        if len(user_account.debt_list) >= 10:
            return '贷款数目不能超过10个！'
        context: DebtContext = DebtContext(debt)
        flower_dao.insert_context(qq, context)
        return '借款协议：\n' \
               '1.本游戏与现实无关，不鼓励现实非必要贷款。\n' \
               '2.还款日第二天3:00分必须还款，如果交易账户资金足够还款将会扣除还款与抵押物，否则将会破产清算失去所有东西\n' \
               '3.利滚利即上一日的利息会加入下一天的利息计算，反之则不加入。最低还款利息即提前还款也需要至少交这么多利息\n' \
               '------\n' \
               '输入“确认”同意上述协议，其余任何输入表示取消。'

    @classmethod
    def view_debt(cls, qq: int) -> str:
        """查看欠款"""
        user_account: UserAccount = util.get_user_account(qq)
        index: int = 0
        reply: str = ''
        for debt in user_account.debt_list:
            index += 1
            origin_debt: TodayDebt = flower_dao.select_debt_by_id(debt.debt_id)
            interest = util.calculate_interest(debt)
            reply += '%d.欠款%s，今日应还%s（还款期限%s）\n' % (
                index,
                util.show_gold(origin_debt.gold),
                util.show_gold(interest),
                (debt.create_time + timedelta(days=origin_debt.repayment_day)).strftime('%Y-%m-%d %H:%M:%S')
            )
        return reply[:-1]

    @classmethod
    def repayment_debt(cls, qq: int, username: str, index: int) -> str:
        """还款"""
        util.lock_user(qq)
        user: User = util.get_user(qq, username)
        user_account: UserAccount = util.get_user_account(qq)
        try:
            if index >= len(user_account.debt_list) or index < 0:
                return user.username + '，序号超限！不存在对应的欠款'
            debt: Debt = user_account.debt_list[index]
            origin_debt: TodayDebt = flower_dao.select_debt_by_id(debt.debt_id)
            interest = util.calculate_interest(debt)
            if user_account.account_gold < interest:
                return user.username + '，账户中金币不足！'
            # 还回抵押物与扣除金币
            util.insert_items(user.warehouse, copy.deepcopy(debt.pawn))
            flower_dao.update_user_by_qq(user)
            user_account.account_gold -= interest
            user_account.debt_gold -= origin_debt.gold
            # 在欠款列表中删除该欠款
            user_account.debt_list.remove(debt)
            flower_dao.update_user_account(user_account)
            return user.username + '，还款成功！当前余额：' + util.show_gold(user_account.account_gold)
        except ItemNotFoundException or ItemNegativeNumberException or WareHouseSizeNotEnoughException:
            return user.username + '，仓库空间不足！请尽快腾出部分空间然后再还款，避免耽误时间。'
        finally:
            util.unlock_user(qq)

    @classmethod
    def buy_futures(cls, qq: int, username: str, name: str, price: int, number: int) -> str:
        """买入期货"""
        user: User = util.get_user(qq, username)
        util.get_user_account(qq)
        system_data: SystemData = util.get_system_data()
        flower: Flower = flower_dao.select_flower_by_name(name)
        flower_price: FlowerPrice = util.get_now_price(flower.name)
        if not flower.valid() or flower.get_id() not in system_data.allow_trading_flower_list or flower_price is None:
            return user.username + '，%s不能参与期货交易' % name
        if number <= 0:
            return user.username + '，%s期货数量不可以为负数'
        if flower_price.latest_price * 0.8 > price or flower_price.latest_price * 1.2 < price:
            return user.username + '，%s的当前价格为%s，不可以超出这个价格的正负20%%' % (
                flower.name, util.show_gold(flower_price.latest_price)
            )
        record: TradeRecords = TradeRecords()
        record.flower_id = flower.get_id()
        record.user_id = qq
        record.nickname = user.username
        record.trade_type = TradeType.buy
        record.price = price
        record.number = number
        record.create_time = datetime.now()
        flower_dao.insert_trade_record(record)
        return user.username + '，你的交易请求已发送到市场\n' \
                               '注意！你的交易单最多只会挂24小时，超过24小时将会按照实际交易数量结算你的交易，可能不能100%完成你的交易请求。'

    @classmethod
    def sell_futures(cls, qq: int, username: str, name: str, price: int, number: int) -> str:
        """卖出期货"""
        user: User = util.get_user(qq, username)
        user_account: UserAccount = util.get_user_account(qq)
        system_data: SystemData = util.get_system_data()
        flower: Flower = flower_dao.select_flower_by_name(name)
        flower_price: FlowerPrice = util.get_now_price(flower.name)
        if not flower.valid() or flower.get_id() not in system_data.allow_trading_flower_list or flower_price is None:
            return user.username + '，%s不能参与期货交易' % name
        if number <= 0:
            return user.username + '，%s期货数量不可以为负数'
        if flower_price.latest_price * 0.8 > price or flower_price.latest_price * 1.2 < price:
            return user.username + '，%s的当前价格为%s，不可以超出这个价格的正负20%%' % (
                flower.name, util.show_gold(flower_price.latest_price)
            )
        choose_stock = -1
        multiple_choice = []
        index: int = 0
        for stock in user_account.hold_stock:
            if stock.flower_id == flower.get_id() and stock.number >= number:
                multiple_choice.append(index)
                if choose_stock == -1:
                    choose_stock = index
                elif choose_stock >= 0:
                    choose_stock = -2
            index += 1
        if choose_stock >= 0:
            record: TradeRecords = TradeRecords()
            record.flower_id = flower.get_id()
            record.user_id = qq
            record.nickname = user.username
            record.trade_type = TradeType.sell
            record.price = price
            record.number = number
            record.stock_hold_time = user_account.hold_stock[choose_stock].create_time
            record.create_time = datetime.now()
            # 对应的也要减少数量
            user_account.hold_stock[choose_stock].number -= number
            if user_account.hold_stock[choose_stock].number <= 0:
                user_account.hold_stock.remove(user_account.hold_stock[choose_stock])
            flower_dao.update_user_account(user_account)
            flower_dao.insert_trade_record(record)
        elif choose_stock == -1:
            return user.username + '，你没有足够数量的该期货。'
        else:
            reply = user.username + '，你的持仓内有多重选择：\n'
            index: int = 0
            for choose_index in multiple_choice:
                index += 1
                hold_stock = user_account.hold_stock[choose_index]
                flower: Flower = flower_dao.select_flower_by_id(hold_stock.flower_id)
                days = (datetime.now() - hold_stock.create_time).total_seconds() // global_config.day_second
                reply += '%d.%sx%d（持仓价格：%s，持仓天数：%d）\n' % (
                    index, flower.name, hold_stock.number, util.show_gold(hold_stock.gold), days
                )
            reply += '-' * 6 + '\n'
            reply += '输入对应的序号选择期货，其他输入视为取消出售'
            context: SellFutureContext = SellFutureContext()
            context.index_list = multiple_choice
            context.flower_id = flower.get_id()
            context.number = number
            context.price = price
            flower_dao.insert_context(qq, context)
            return reply
        return user.username + '，你的交易请求已发送到市场\n' \
                               '注意！你的交易单最多只会挂24小时，超过24小时将会按照实际交易数量结算你的交易，可能不能100%完成你的交易请求。'

    @classmethod
    def view_trade_states(cls, qq: int, username: str, page: int, page_size: int = 20) -> str:
        """查看所有的交易状态"""
        user: User = util.get_user(qq, username)
        util.get_user_account(qq)
        trade_number: int = flower_dao.select_trade_record_by_qq_number(qq)
        if trade_number == 0:
            return user.username + '，你目前没有未完成的交易。'
        if page * page_size >= trade_number or page < 0:
            return user.username + '，页码超限！'
        trade_list: List[TradeRecords] = flower_dao.select_trade_record_by_qq(qq, page, page_size)
        reply = ''
        index: int = 0
        for trade_record in trade_list:
            index += 1
            flower: Flower = flower_dao.select_flower_by_id(trade_record.flower_id)
            reply += '%d.%s%sx%d（已完成数目：%d，锚定价格：%s）\n' % (
                index,
                '买入' if trade_record.trade_type == TradeType.buy else '卖出',
                flower.name,
                trade_record.number,
                trade_record.transaction_volume,
                util.show_gold(trade_record.price)
            )
        reply += '-' * 6 + '\n'
        total_page: int = trade_number // page_size
        if trade_number % page_size > 0:
            total_page += 1
        reply += '当前页码：%d/%d' % (page + 1, total_page)
        return reply

    @classmethod
    def view_hold_stock(cls, qq: int, username: str, page: int, page_size: int = 20) -> str:
        """查看自己持仓的期货"""
        user: User = util.get_user(qq, username)
        user_account: UserAccount = util.get_user_account(qq)
        if len(user_account.hold_stock) == 0:
            return user.username + '，你目前还没有持有期货'
        reply = ''
        index: int = 0
        for hold_stock in user_account.hold_stock:
            if index >= page * page_size:
                index += 1
                flower: Flower = flower_dao.select_flower_by_id(hold_stock.flower_id)
                days = (datetime.now() - hold_stock.create_time).total_seconds() // global_config.day_second
                reply += '%d.%sx%d（持仓价格：%s，持仓天数：%d）\n' % (
                    index, flower.name, hold_stock.number, util.show_gold(hold_stock.gold), days
                )
            elif index >= (page + 1) * page_size:
                break
            else:
                index += 1
        total_page = len(user_account.hold_stock) // page_size
        if len(user_account.hold_stock) % page_size > 0:
            total_page += 1
        reply += '-' * 6 + '\n'
        reply += '当前页码：%d/%d' % (page + 1, total_page)
        return reply

    @classmethod
    def generate_price_map(cls, qq: int, username: str, flower_name: str) -> str:
        """生成价格曲线"""
        user: User = util.get_user(qq, username)
        util.get_user_account(qq)
        flower: Flower = flower_dao.select_flower_by_name(flower_name)
        system_data: SystemData = util.get_system_data()
        if flower.get_id() not in system_data.allow_trading_flower_list:
            return user.username + '，该花不是期货，不能参与期货交易'
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        today_price: FlowerPrice = flower_dao.select_today_flower_price(flower.get_id(), today)
        yesterday_price: FlowerPrice = flower_dao.select_today_flower_price(flower.get_id(), yesterday)
        hour = today.hour
        price = yesterday_price.price[hour + 1:] + today_price.price[:hour + 1]
        price = [gold / 100 for gold in price]
        my_font = font_manager.FontProperties(family='SimHei', size=16)
        plt.plot(range(len(price)), price, color='skyblue')
        plt.plot([len(price) - 1], price[-1], 'o', color='orange')
        plt.text(len(price) - 1, price[-1], util.show_gold(price[-1] * 100), fontproperties=my_font, color="black")
        plt.xlabel('hour', fontproperties=my_font)
        plt.ylabel('price', fontproperties=my_font)
        plt.title('price in 24 hour', fontproperties=my_font)
        file_name = '%s.png' % flower_name
        plt.savefig('cache/' + file_name)
        plt.clf()  # 清图
        return file_name

    @classmethod
    def buy_lottery(cls, qq: int, username: str) -> str:
        user: User = util.get_user(qq, username)
        lottery: Lottery = flower_dao.select_today_lottery_by_qq(qq, datetime.now())
        if lottery.valid():
            return user.username + '，你今天已经购买彩票了，选择的幸运数字为：%d' % lottery.lucky_number
        context: ChooseLuckyNumber = ChooseLuckyNumber()
        flower_dao.insert_context(qq, context)
        return user.username + '，请选择一个幸运数字，需要在1~10之间，输入“取消”可以取消购买彩票'


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
        util.lock_user(qq)
        system_data: SystemData = util.get_system_data()
        try:
            user: User = util.get_user(qq, username)
        except UserNotRegisteredException:
            util.unlock_user(qq)
            return ''
        user_statistics: UserStatistics = util.get_user_statistics(qq)
        try:
            user_statistics.draw_times += 1
            if user.draw_card_number <= 0:
                return ''
            rand: int = random.randint(0, system_data.draw_card_probability_unit)
            # 对于当天次数大于5次的，多余的部分按照第1个物品的概率去抽取，剩余的按照0、1、2、3、4依次类推
            draw_probability_index: int = system_data.draw_card_max_number - user.draw_card_number
            if draw_probability_index < 0:
                draw_probability_index = 0
            if rand < system_data.draw_card_probability[draw_probability_index]:
                if user.draw_card_number != 1:
                    if random.random() < 0.8:
                        pool: Dict[str, int] = system_data.draw_item_pool
                    else:
                        pool: Dict[str, int] = system_data.draw_seed_pool
                else:
                    pool: Dict[str, int] = system_data.draw_seed_pool
                commodity: Commodity = util.random_choice_pool(pool, Relationship())
                item_obj: Item = flower_dao.select_item_by_id(commodity.item_id)
                item: DecorateItem = DecorateItem()
                item.number = 1
                item.item_id = item_obj.get_id()
                item.item_name = item_obj.name
                item.item_type = item_obj.item_type
                item.max_durability = item_obj.max_durability  # 最大耐久度
                item.durability = item_obj.max_durability
                item.rot_second = item_obj.rot_second  # 腐烂的秒数
                item.create = datetime.now()  # 记录当前的创建时间
                item.humidity = item_obj.humidity  # 湿度
                item.nutrition = item_obj.nutrition  # 营养
                item.temperature = item_obj.temperature  # 温度
                item.level = item_obj.level
                if item_obj.item_type == ItemType.flower and item.flower_quality == FlowerQuality.not_flower:
                    item.flower_quality = FlowerQuality.normal
                if item_obj.item_type == ItemType.accelerate and item.hour < 1:
                    item.hour = random.randint(1, 4)
                try:
                    util.insert_items(user.warehouse, [copy.deepcopy(item)])
                    user.draw_card_number -= 1
                    # 如果今天抽完了所有的卡片，就将抽卡记录到统计数据
                    if user.draw_card_number == 0:
                        user_statistics.all_draw_times += 1
                        # 如果抽卡抽完了，还要录入成就
                        util.give_achievement(user, '欧皇', 1)
                    user_statistics.success_draw_times += 1
                    flower_dao.update_user_by_qq(user)
                    return user.username + '，抽到物品%s' % str(item)
                except ItemNotFoundException:
                    return user.username + '，抽到物品%s，但是背包容量不足或该物品已经绝版' % str(item)
                except ItemNegativeNumberException:
                    return user.username + '，抽到物品%s，但是背包容量不足或该物品已经绝版' % str(item)
                except WareHouseSizeNotEnoughException:
                    return user.username + '，抽到物品%s，但是背包容量不足或该物品已经绝版' % str(item)
            return ''
        except UserNotRegisteredException:
            return ''
        finally:
            flower_dao.update_user_statistics(user_statistics)
            util.unlock_user(qq)


if __name__ == '__main__':
    pass
