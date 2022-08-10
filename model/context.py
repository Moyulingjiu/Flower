# coding=utf-8
import datetime
from typing import Dict, List

from flower_exceptions import FunctionArgsException
from model import City, DecorateItem, DecorateBuff

__all__ = [
    "BaseContext", "RegisterContext", "BeginnerGuideContext", "ThrowAllItemContext", "RemoveFlowerContext",
    "Choice", "ChooseContext", "RandomTravelContext", "TravelContext", "AnnouncementContext",
    "AdminSendMailContext", "ClearMailBoxContext", "DeleteMailContext", "GiveBuff"
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


class GiveBuff(BaseContext):
    """
    给予buff
    """

    def __init__(self, target_qq: List[int] = None, buff: DecorateBuff = DecorateBuff(), expire_seconds: int = 0):
        super().__init__(1, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))
        if target_qq is None:
            target_qq = []
        self.target_qq = target_qq
        self.buff = buff
        self.expire_seconds = expire_seconds
