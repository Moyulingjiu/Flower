import random

from util import *
import flower_dao
from datetime import datetime, timedelta


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
        reply = ContextHandler.handle(message, qq, username, bot_qq, bot_name, at_list)
        if reply != '':
            return Result.init(reply)
        
        # 数据查询部分
        if message[:4] == '查询城市' and message[4:].strip() != '':
            reply = FlowerService.query_city(message[4:].strip())
            return Result.init(reply)
        elif message[:4] == '查询土壤' and message[4:].strip() != '':
            reply = FlowerService.query_soil(message[4:].strip())
            return Result.init(reply)
        elif message[:3] == '查询花' and message[3:].strip() != '':
            reply = FlowerService.query_flower(message[3:].strip())
            return Result.init(reply)
        elif message[:4] == '花店数据':
            reply = FlowerService.query_user_data(qq, username)
            return Result.init(reply)
        elif message == '初始化花店':
            reply = FlowerService.init_user(qq, username)
            return Result.init(reply)
        elif message[:4] == '花店仓库':
            data = message[4:].strip()
            page = 0
            if data != '':
                try:
                    page = int(data)
                except ValueError:
                    raise TypeException('格式错误，格式“花店仓库【页码】”')
            reply = FlowerService.view_warehouse(qq, username, page)
            return Result.init(reply)
        
        # 操作部分
        elif message == '花店签到':
            reply = FlowerService.user_sign_in(qq, username)
            return Result.init(reply)
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
            return Result.init(reply)
        
        # 管理员操作
        if get_user_right(qq) == UserRight.ADMIN:
            return AdminHandler.handle(message, qq, username, bot_qq, bot_name, at_list)
    except UserNotRegisteredException:
        return Result.init('您还未初始化花店账号，请输入“初始化花店”进行初始化')
    except UserBeLockedException:
        return Result.init('操作超时，请稍后再试\n出现的原因可能有：\n1.您的操作过于频繁，请稍后再试\n2.账号风险行为，耐心等待两小时重置')
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
            data: str = message[4:]
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
                return Result.init('成功给予金币给' + str(update_number) + '人')
            else:
                return Result.init('未能给予任何人金币')
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
            flower_dao.unlock(flower_dao.redis_user_lock_prefix + str(qq))
            return True
        except UserNotRegisteredException:
            return False


class ContextHandler:
    """
    上下文处理器
    """
    
    @classmethod
    def handle(cls, message: str, qq: int, username: str, bot_qq: int, bot_name: str, at_list: List[int]) -> str:
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
        context = get_context(qq)
        if context is None:
            return ''
        # 账号注册
        if isinstance(context, RegisterContext):
            if message == '取消':
                delete_context(qq)
                return '已为您取消注册'
            if context.step == 0:
                city: City = flower_dao.select_city_by_name(message)
                if city is None or city.city_name != message:
                    return FlowerService.query_city(message) + '\n请选择一座城市，只支持地级市（你可以输入“取消”来取消初始化账户）。'
                user: User = User()
                user.qq = qq
                user.username = username
                user.create_id = str(bot_qq)
                user.update(bot_qq)
                
                user.city_id = city.get_id()
                user.born_city_id = city.get_id()
                
                flower_dao.insert_user(user)
                delete_context(qq)
                return bot_name + '已为您初始化花店\n' + '免责声明：本游戏一切内容与现实无关，城市只是为了增强代入感！'


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
        res += '\n等级：' + str(flower.level)
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
    def query_user_data(cls, qq, username: str) -> str:
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
            context = get_context(qq)
            if context is None:
                context = RegisterContext(qq, username)
                insert_context(qq, context)
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
                reply += '\n' + item.item_name
                if item.number > 1:
                    reply += 'x' + str(item.number)
                index += 1
            reply += '\n------'
            reply += '总计页码：' + str(total_page)
        return reply


if __name__ == '__main__':
    pass
