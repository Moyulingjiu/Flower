# coding=utf-8
"""
存储与世界PCG演化相关的模型
"""
from enum import Enum

from model.base_model import *


class Disease(Enum):
    """
    疾病枚举类
    """

    @classmethod
    def view_level(cls, disease) -> str:
        pass

    @classmethod
    def get_level(cls, disease: str):
        pass


class Profession(Enum):
    """
    职业类
    """

    @classmethod
    def view_level(cls, profession) -> str:
        pass

    @classmethod
    def get_level(cls, profession: str):
        pass


class Race(Enum):
    """
    种族类
    """

    @classmethod
    def view_level(cls, race) -> str:
        pass

    @classmethod
    def get_level(cls, race: str):
        pass


class WorldArea(EntityClass):
    """
    世界地区
    """

    def __init__(self,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)


class Kingdom(EntityClass):
    """
    王国
    """

    def __init__(self,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)


class Person(EntityClass):
    """
    人物模型
    """

    def __init__(self,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)
