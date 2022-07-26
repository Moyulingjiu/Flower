# coding=utf-8
import random
from datetime import datetime, timedelta

import flower_dao
from util import *


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
            reply = FlowerService.view_warehouse(qq, username, page)
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
        elif message == '花店农场信息':
            reply = FlowerService.view_user_farm(qq, username)
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
        elif message[:2] == '丢弃':
            data = message[2:]
            try:
                item: DecorateItem = analysis_item(data)
                reply = FlowerService.throw_item(qq, username, item)
                result.reply_text.append(reply)
                return result
            except TypeException:
                raise TypeException('格式错误，格式“丢弃 【物品名字】 【数量】”')
        elif message == '清空花店仓库':
            reply = FlowerService.throw_all_items(qq, username)
            result.reply_text.append(reply)
            return result
        elif message[:2] == '种植':
            data = message[2:].strip()
            reply = FlowerService.plant_flower(qq, username, data)
            result.reply_text.append(reply)
            return result
        
        # 管理员操作
        if get_user_right(qq) == UserRight.ADMIN:
            return AdminHandler.handle(message, qq, username, bot_qq, bot_name, at_list)
    except UserNotRegisteredException:
        return Result.init(reply_text='您还未初始化花店账号，请输入“初始化花店”进行初始化')
    except UserBeLockedException:
        return Result.init(reply_text='操作超时，请稍后再试\n出现的原因可能有：\n1.您的操作过于频繁，请稍后再试\n2.账号风险行为，耐心等待两小时重置\n3.网络波动')
    except AtListNullException as e:
        return Result.init(e.message)
    except TypeException as e:
        return Result.init(e.message)
    except PageOutOfRangeException as e:
        return Result.init(e.message)
    finally:
        flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
    return Result.init()


class AdminHandler:
    """
    管理员指令处理器
    """
    
    @classmethod
    def handle(cls, message: str, qq: int, username: str, bot_qq: int, bot_name: str, at_list: List[int]) -> Result:
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
                return Result.init(reply_text=['成功给予金币给' + str(update_number) + '人'])
            else:
                return Result.init(reply_text=['未能给予任何人金币'])
        elif message[:4] == '给予物品':
            data: str = message[4:].strip()
            try:
                item: DecorateItem = analysis_item(data)
            except TypeException:
                raise TypeException('格式错误，格式“@xxx 给予物品 【物品名字】 【数量】”')
            
            update_number: int = 0
            if len(at_list) == 0:
                if cls.give_item(qq, qq, item):
                    update_number += 1
            else:
                for target_qq in at_list:
                    if cls.give_item(target_qq, qq, item):
                        update_number += 1
            if update_number > 0:
                return Result.init(reply_text=['成功给予' + item.item_name + '给' + str(update_number) + '人'])
            else:
                return Result.init(reply_text=['未能给予任何人' + item.item_name])
        
        return Result.init()
    
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
            user: User = get_user(qq, '')
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
            user: User = get_user(qq, '')
            insert_items(user.warehouse, [item])
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
        context_list: List = flower_dao.get_context(qq)
        del_context_list: List = [context for context in context_list if context.is_expired()]
        result: Result = Result.init()
        if len(context_list) == 0:
            return result
        for context in context_list:
            if context in del_context_list:
                continue
            # 账号注册
            if isinstance(context, RegisterContext):
                if message == '取消':
                    del_context_list.append(context)
                    reply = '已为您取消注册'
                    result.context_reply_text.append(reply)
                    continue
                if context.step == 0:
                    city: City = flower_dao.select_city_by_name(message)
                    if city is None or city.city_name != message:
                        reply = FlowerService.query_city(message) + '\n请选择一座城市，只支持地级市（你可以输入“取消”来取消初始化账户）。'
                        result.context_reply_text.append(reply)
                        continue
                    user: User = User()
                    user.qq = qq
                    user.username = username
                    user.create_id = str(bot_qq)
                    user.update(bot_qq)
                    
                    user.city_id = city.get_id()
                    user.born_city_id = city.get_id()
                    
                    # 农场的处理
                    user.farm.soil_id = city.soil_id
                    soil: Soil = flower_dao.select_soil_by_id(city.soil_id)
                    user.farm.humidity = (soil.max_humidity + soil.min_humidity) / 2
                    user.farm.nutrition = (soil.max_nutrition + soil.min_nutrition) / 2
                    weather: Weather = get_weather(city)
                    user.farm.temperature = (weather.max_temperature - weather.min_temperature) * 3 / 4 + weather.min_temperature
                    
                    flower_dao.insert_user(user)
                    del_context_list.append(context)
                    reply = bot_name + '已为您初始化花店\n' + '免责声明：本游戏一切内容与现实无关，城市只是为了增强代入感！\n' + '现在输入“领取花店初始礼包”试试吧'
                    result.context_reply_text.append(reply)
            # 新手指引
            elif isinstance(context, BeginnerGuideContext):
                if message == '关闭新手指引':
                    del_context_list.append(context)
                    reply = '已为您关闭新手指引'
                    result.context_reply_text.append(reply)
                if context.step == 0:
                    if message == '花店签到':
                        self.block_transmission = False
                        context.step += 1
                        reply = '很好你已经完成了签到！每日签到可以获取金币。接下来试试“花店数据”。\n您可以输入“关闭新手指引”来取消指引。'
                        result.context_reply_text.append(reply)
                elif context.step == 1:
                    if message == '花店数据':
                        self.block_transmission = False
                        context.step += 1
                        reply = '在这里你可以看见一些玩家的基本数据，接下来试试“花店仓库”。\n您可以输入“关闭新手指引”来取消指引。'
                        result.context_reply_text.append(reply)
                elif context.step == 2:
                    if message == '花店仓库':
                        self.block_transmission = False
                        del_context_list.append(context)
                        reply = '在这里你可以看见你的新手物资。新手指引结束了（这句话后面再改）。'
                        result.context_reply_text.append(reply)
            # 丢弃所有物品
            elif isinstance(context, ThrowAllItemContext):
                del_context_list.append(context)
                # context 会自动lock无需手动加锁
                user: User = get_user(qq, username)
                if message != '确认':
                    reply = user.username + '，已取消清空花店仓库'
                    result.context_reply_text.append(reply)
                    continue
                user.warehouse.items = []
                flower_dao.update_user_by_qq(user)
                reply = user.username + '，已为您清空花店仓库'
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
                ans += show_cities_name(cities)
            else:
                length: int = len(name) - 1
                init: bool = False
                while length > 0:
                    for i in range(len(name) - length):
                        cities = flower_dao.select_city_by_name_like(name[i:i + length])
                        cities_name = show_cities_name(cities)
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
            res += '\n最低湿度变化土壤：' + get_soil_list(soil.min_change_humidity_soil_id)
        if len(soil.max_change_humidity_soil_id) != 0:
            res += '\n最高湿度变化土壤：' + get_soil_list(soil.max_change_humidity_soil_id)
        if len(soil.min_change_nutrition_soil_id) != 0:
            res += '\n最低营养变化土壤：' + get_soil_list(soil.min_change_nutrition_soil_id)
        if len(soil.max_change_nutrition_soil_id) != 0:
            res += '\n最高营养变化土壤：' + get_soil_list(soil.max_change_nutrition_soil_id)
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
            res += '\n适宜气候：' + get_climate_list(flower.climate_id)
        elif len(flower.op_climate_id) > 0:
            res += '\n不适宜气候：' + get_climate_list(flower.op_climate_id)
        elif len(flower.climate_id) == 0 and len(flower.op_climate_id) == 0:
            res += '\n适宜气候：所有气候'
        if len(flower.soil_id) > 0:
            res += '\n适宜土壤：' + get_soil_list(flower.soil_id)
        elif len(flower.op_soil_id) > 0:
            res += '\n不适宜土壤：' + get_soil_list(flower.op_soil_id)
        elif len(flower.soil_id) == 0 and len(flower.op_soil_id) == 0:
            res += '\n适宜土壤：所有土壤'
        
        res += '\n吸收水分：' + str(flower.water_absorption) + '/小时'
        res += '\n吸收营养：' + str(flower.nutrition_absorption) + '/小时'
        res += '\n能忍受恶劣条件：' + str(flower.withered_time) + '小时'
        
        res += '\n种子：'
        res += '\n\t周期：' + str(flower.seed_time) + '小时'
        res += show_conditions(flower.seed_condition)
        res += '\n幼苗：'
        res += '\n\t周期：' + str(flower.grow_time) + '小时'
        res += show_conditions(flower.grow_condition)
        res += '\n成熟：'
        res += '\n\t成熟周期：' + str(flower.mature_time) + '小时'
        res += '\n\t过熟周期：' + str(flower.overripe_time) + '小时'
        res += show_conditions(flower.mature_condition)
        
        return res
    
    @classmethod
    def view_user_data(cls, qq: int, username: str) -> str:
        """
        查询用户数据
        :param qq: qq
        :param username: 用户名
        :return: 结果
        """
        user: User = get_user(qq, username)
        born_city: City = flower_dao.select_city_by_id(user.born_city_id)
        city: City = flower_dao.select_city_by_id(user.city_id)
        res = '用户名：' + user.username
        res += '\n等级：'
        level = 0
        system_data = flower_dao.select_system_data()
        for i in range(len(system_data.exp_level)):
            if user.exp >= system_data.exp_level[i]:
                level = i
        res += str(level + 1)
        res += '\n出生地：' + born_city.city_name
        res += '\n所在城市：' + city.city_name
        res += '\n金币：' + '%.2f' % (user.gold / 100)
        res += '\n仓库：' + str(len(user.warehouse.items)) + '/' + str(user.warehouse.max_size)
        return res
    
    @classmethod
    def view_user_farm(cls, qq: int, username: str) -> str:
        """
        根据用户查询其农场
        :param qq: qq号
        :param username: 用户名
        :return: 农场信息
        """
        user: User = get_user(qq, username)
        city: City = flower_dao.select_city_by_id(user.city_id)
        soil: Soil = flower_dao.select_soil_by_id(user.farm.soil_id)
        climate: Climate = flower_dao.select_climate_by_id(city.climate_id)
        weather: Weather = get_weather(city)
        flower: Flower = Flower()
        if user.farm.flower_id != '':
            flower: Flower = flower_dao.select_flower_by_id(user.farm.flower_id)
        now: datetime = datetime.now()
        now_temperature = abs(now.hour - 12) * (weather.max_temperature - weather.min_temperature)
        
        reply = user.username + '的农场：'
        reply += '\n所在地：' + city.city_name
        reply += '\n气候：' + climate.name
        reply += '\n土壤：' + soil.name
        
        reply += '\n气温：' + str(user.farm.temperature)
        if user.farm.temperature > now_temperature:
            reply += '（↓）'
        elif user.farm.temperature < now_temperature:
            reply += '（↑）'
        else:
            reply += '（=）'
        reply += '\n土壤湿度：' + str(user.farm.humidity)
        reply += '\n土壤营养：' + str(user.farm.nutrition)
        
        reply += '\n温度计：' + str(user.farm.thermometer)
        reply += '\n土壤监控站：' + str(user.farm.soil_monitoring_station)
        reply += '\n浇水壶：' + str(user.farm.watering_pot)
        
        if flower.get_id() != '':
            reply += '\n种植的花：' + flower.name
        
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
            user: User = get_user(qq, username)
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
        user: User = get_user(qq, username)
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
        user: User = get_user(qq, username)
        reply = '转账结果如下：'
        for target_qq in at_list:
            try:
                flower_dao.lock(flower_dao.redis_user_lock_prefix + str(target_qq))
                target_user: User = get_user(target_qq, '')
                if user.gold < gold:
                    reply += '\n对' + str(target_qq) + '转账失败，余额不足'
                else:
                    user.gold -= gold
                    target_user.gold += int(gold * 0.8)
                    target_user.update(qq)
                    flower_dao.update_user_by_qq(target_user)
                    reply += '\n对' + str(target_qq) + '转账成功，余额：' + '%.2f' % (user.gold / 100)
            except UserBeLockedException:
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
    def view_warehouse(cls, qq: int, username: str, page: int, page_size: int = 30):
        """
        查看仓库
        无需加锁，只读！
        :param qq: qq
        :param username: 用户名
        :param page: 页码
        :param page_size: 页面大小
        :return: 结果
        """
        user: User = get_user(qq, username)
        total_number = len(user.warehouse.items)
        reply = user.username + '你的花店仓库如下：' + str(total_number) + '/' + str(user.warehouse.max_size)
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
        return reply
    
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
            ans += show_items_name(item_list)
        else:
            length: int = len(item_name) - 1
            init: bool = False
            while length > 0:
                for i in range(len(item_name) - length):
                    item_list: List[Item] = flower_dao.select_item_like_name(item_name[i:i + length])
                    items_name: str = show_items_name(item_list)
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
        user: User = get_user(qq, username)
        if user.beginner_pack:
            return user.username + '，你已经领取过初始礼包了'
        user.beginner_pack = True
        flower_dao.update_user_by_qq(user)
        flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
        item: DecorateItem = DecorateItem()
        
        # 初始获取两种种子
        seed_list = ['野草种子', '野花种子', '小黄花种子', '小红花种子']
        for i in range(2):
            seed = random.choice(seed_list)
            item.item_name = seed
            item.number = 5
            AdminHandler.give_item(qq, qq, copy.deepcopy(item))
        
        # 领取化肥
        item.item_name = '初级化肥'
        item.number = 5
        AdminHandler.give_item(qq, qq, copy.deepcopy(item))
        
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
            weather: Weather = get_weather(city)
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
        user: User = get_user(qq, username)
        try:
            remove_items(user.warehouse, [item])
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
        user: User = get_user(qq, username)
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
        user: User = get_user(qq, username)
        try:
            if user.farm.flower_id != '':
                return user.username + '，您的农场已经有花了'
            flower: Flower = flower_dao.select_flower_by_name(flower_name)
            if flower.name != flower_name:
                return user.username + '，不存在这种花'
            item: DecorateItem = DecorateItem()
            item.item_name = flower_name + '种子'
            item.number = 1
            remove_items(user.warehouse, [item])
            user.farm.flower_id = flower.get_id()
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


if __name__ == '__main__':
    pass
