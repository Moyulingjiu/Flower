# coding=utf-8
import datetime
from typing import Dict, List

from flower_exceptions import FunctionArgsException
from model import City, DecorateItem, DecorateBuff
from model.stock_market_model import TodayDebt

__all__ = [
    "BaseContext", "RegisterContext", "BeginnerGuideContext", "ThrowAllItemContext", "RemoveFlowerContext",
    "Choice", "ChooseContext", "RandomTravelContext", "TravelContext", "AnnouncementContext",
    "AdminSendMailContext", "ClearMailBoxContext", "DeleteMailContext", "GiveBuffContext", "CommodityBargainingContext",
    "ViewRelationshipContext", "UserSendMailContext", "CreateAccountConfirm", "DebtContext", "SellFutureContext",
    "ChooseLuckyNumber"
]


class BaseContext:
    """
    基础上下文
    """
    
    def __init__(self, max_step: int, expire_time: datetime.datetime):
        self.step = 0
        self.max_step = max_step
        self.expire_time = expire_time
    
    def is_expired(self):
        return self.expire_time < datetime.datetime.now()


class RegisterContext(BaseContext):
    """
    用户注册的上下文
    """
    
    def __init__(self, qq: int, username: str, city: City = City()):
        super().__init__(2, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))
        self.qq = qq
        self.username = username
        self.city = city


class BeginnerGuideContext(BaseContext):
    """
    新手指引的上下文
    """
    
    def __init__(self):
        super().__init__(2, expire_time=datetime.datetime.now() + datetime.timedelta(days=7))


class ThrowAllItemContext(BaseContext):
    """
    丢弃所有物品的上下文
    """
    
    def __init__(self):
        super().__init__(1, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))


class RemoveFlowerContext(BaseContext):
    """
    铲除农场的花
    """
    
    def __init__(self):
        super().__init__(1, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))


class Choice:
    """
    抉择
    """
    
    def __init__(self, args: dict, callback):
        self.__args = args
        if not callable(callback):
            raise FunctionArgsException('不是可以回调的类型')
        self.__callback = callback
    
    @property
    def args(self):
        return self.__args
    
    @property
    def callback(self):
        return self.__callback


class ChooseContext(BaseContext):
    """
    抉择的上下文
    """
    
    def __init__(self, choices: Dict[str, Choice], auto_cancel: bool = True, cancel_command: str = '取消'):
        super().__init__(1, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))
        self.choices = choices  # 第二个参数必须为回调函数！
        self.auto_cancel = auto_cancel
        self.cancel_command = cancel_command


class RandomTravelContext(BaseContext):
    """
    随机旅行
    """
    
    def __init__(self):
        super().__init__(1, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))


class TravelContext(BaseContext):
    """
    定向旅行
    """
    
    def __init__(self):
        super().__init__(2, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))


class AnnouncementContext(BaseContext):
    """
    发送公告的上下文
    """
    
    def __init__(self, text: str = '', valid_second: int = 0, username: str = ''):
        super().__init__(3, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))
        self.text = text  # 正文
        self.valid_second = valid_second  # 有效时间
        self.username = username  # 发件人


class AdminSendMailContext(BaseContext):
    """
    发送公告的上下文
    """
    
    def __init__(self, title: str = '', text: str = '', appendix: List[DecorateItem] = None, username: str = '',
                 addressee: List[int] = None, send_all_user: bool = False, gold: int = 0):
        super().__init__(3, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))
        self.title = title  # 标题
        self.text = text  # 正文
        if not isinstance(appendix, list):
            appendix = []
        self.appendix = appendix  # 附件
        self.username = username  # 发件人
        if not isinstance(addressee, list):
            addressee = []
        self.addressee = addressee  # 收件人QQ号
        self.send_all_user = send_all_user  # 是否发送给所有人
        self.gold = gold  # 附赠的金币


class UserSendMailContext(BaseContext):
    """
    发送公告的上下文
    """

    def __init__(self, title: str = '', text: str = '', appendix: List[DecorateItem] = None, username: str = '',
                 target_qq: int = 0, postman_name: str = '', postman_id: str = '', user_person_id: str = '',
                 valid_date: datetime.date = datetime.date.today()):
        super().__init__(3, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))
        self.title = title  # 标题
        self.text = text  # 正文
        if not isinstance(appendix, list):
            appendix = []
        self.appendix = appendix  # 附件
        self.username = username  # 发件人
        self.target_qq = target_qq  # 收件人QQ号
        self.postman_name = postman_name  # 邮递员姓名
        self.postman_id = postman_id  # 邮递员id
        self.user_person_id = user_person_id  # 用户，person关联的id
        self.valid_date = valid_date  # 有效日期


class ClearMailBoxContext(BaseContext):
    """
    清空信箱的上下文
    """
    
    def __init__(self):
        super().__init__(1, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))


class DeleteMailContext(BaseContext):
    """
    删除信件的上下文
    """
    
    def __init__(self, index: int):
        super().__init__(1, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))
        self.index = index


class GiveBuffContext(BaseContext):
    """
    给予buff
    """
    
    def __init__(self, target_qq_list: List[int] = None, buff: DecorateBuff = DecorateBuff(), expire_seconds: int = 0):
        super().__init__(1, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))
        if target_qq_list is None:
            target_qq_list = []
        self.target_qq_list = target_qq_list
        self.buff = buff
        self.expire_seconds = expire_seconds


class CommodityBargainingContext(BaseContext):
    """
    议价
    """
    
    def __init__(self, user_person_id: str, person_id: str, item: DecorateItem, gold: int,
                 can_bargain: bool = False, bargain_times: int = 0):
        super().__init__(1, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))
        self.user_person_id = user_person_id  # 今日任务
        self.person_id = person_id  # npc id
        self.item = item  # 商品
        self.gold = gold  # 价格
        self.can_bargain = can_bargain  # 能否议价
        self.bargain_times = bargain_times  # 议价次数


class ViewRelationshipContext(BaseContext):
    """
    探查npc好感度
    """

    def __init__(self):
        super().__init__(1, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))


class CreateAccountConfirm(BaseContext):
    """
    确认开通账户
    """

    def __init__(self):
        super().__init__(1, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))


class DebtContext(BaseContext):
    """
    借款
    """

    def __init__(self, debt: TodayDebt, pawn: List[DecorateItem] = None):
        super().__init__(1, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))
        self.debt = debt  # 贷款
        if pawn is None:
            pawn = []
        self.pawn = pawn  # 抵押物


class SellFutureContext(BaseContext):
    """
    期货选择
    """

    def __init__(self, index_list: List[int] = None):
        super().__init__(1, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))
        if index_list is None:
            index_list = []
        self.index_list = index_list
        self.flower_id: str = ''
        self.number: int = 0
        self.price: int = 0


class ChooseLuckyNumber(BaseContext):
    """
    选择幸运数字
    """

    def __init__(self):
        super().__init__(1, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))