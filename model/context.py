# coding=utf-8
import datetime
from typing import Dict

from flower_exceptions import FunctionArgsException


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

    def __init__(self, qq: int, username: str):
        super().__init__(1, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))
        self.qq = qq
        self.username = username


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
