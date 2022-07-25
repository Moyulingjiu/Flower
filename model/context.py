import datetime
from typing import Dict


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


class BeginnerGuide(BaseContext):
    """
    新手指引的上下文
    """
    def __init__(self):
        super().__init__(2, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))


class ThrowAllItem(BaseContext):
    """
    丢弃所有物品的上下文
    """
    def __init__(self):
        super().__init__(1, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))


# 上下文缓冲器
# todo: 上下文应该放到全局redis里去，同时上下文应该不止一种，一个用户可以同时具有多种上下文
_context: Dict[int, BaseContext] = {}


def clear_expired_context():
    """
    清除过期的上下文
    """
    for key in _context:
        if not isinstance(_context[key], BaseContext):
            del _context[key]
        if _context[key].is_expired():
            del _context[key]


def get_context(key: int) -> BaseContext or None:
    """
    获取上下文
    """
    clear_expired_context()
    if key in _context:
        return _context[key]
    return None


def insert_context(key: int, context: BaseContext):
    """
    插入上下文
    """
    clear_expired_context()
    _context[key] = context


def delete_context(key: int):
    """
    删除上下文
    """
    if key in _context:
        del _context[key]
