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
