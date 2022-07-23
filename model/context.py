import datetime
from typing import Dict


class BaseContext:
    def __init__(self, max_step: int, expire_time: datetime.datetime):
        self.step = 0
        self.max_step = max_step
        self.expire_time = expire_time
    
    def is_expired(self):
        return self.expire_time < datetime.datetime.now()


class RegisterContext(BaseContext):
    def __init__(self, qq: int, username: str):
        super().__init__(1, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))
        self.qq = qq
        self.username = username


class BeginnerGuide(BaseContext):
    def __init__(self):
        super().__init__(2, expire_time=datetime.datetime.now() + datetime.timedelta(hours=1))


_context: Dict[int, BaseContext] = {}


def clear_expired_context():
    for key in _context:
        if not isinstance(_context[key], BaseContext):
            del _context[key]
        if _context[key].is_expired():
            del _context[key]


def get_context(key: int) -> BaseContext or None:
    clear_expired_context()
    if key in _context:
        return _context[key]
    return None


def insert_context(key: int, context: BaseContext):
    clear_expired_context()
    _context[key] = context


def delete_context(key: int):
    if key in _context:
        del _context[key]
