# coding=utf-8
"""
模型基类
"""
from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel

__all__ = [
    "Gender", "InnerClass", "EntityClass", "Result"
]


class Gender(Enum):
    """
    性别
    """

    male = 0  # 男
    female = 1  # 女
    intersex = 2  # 双性
    unknown = 3  # 未知

    @classmethod
    def get(cls, gender):
        if gender == 0:
            return cls.male
        elif gender == 1:
            return cls.female
        elif gender == 2:
            return cls.intersex
        return cls.unknown

    def show(self) -> str:
        if self == Gender.male:
            return '男'
        elif self == Gender.female:
            return '女'
        elif self == Gender.intersex:
            return '双性'
        return '未知'

    def __str__(self):
        return self.show()

    def __repr__(self):
        return self.show()


class InnerClass:
    """
    可以转化为字典的类
    """

    def __init__(self, class_type: str = ''):
        self.class_type = class_type


class EntityClass:
    """
    实体类
    """

    def __init__(self, create_time: datetime = datetime.now(), create_id: str = '0',
                 update_time: datetime = datetime.now(), update_id: str = '0', is_delete: int = 0,
                 _id: str or None = None):
        self._id = _id
        # 管理字段
        self.create_time = create_time
        self.create_id = create_id
        self.update_time = update_time
        self.update_id = update_id
        self.is_delete = is_delete

    def get_id(self) -> str:
        return self._id

    def valid(self) -> bool:
        return self._id is not None and self._id != ''

    def update(self, update_id: int or str) -> None:
        self.update_time = datetime.now()
        self.update_id = str(update_id)


class Result(BaseModel):
    """
    返回类
    """

    context_reply_text: List[str] = []
    context_reply_image: List[str] = []
    reply_text: List[str] = []
    reply_image: List[str] = []
    at_list: List[int] = None

    @classmethod
    def init(cls, context_reply_text: List[str] = None, context_reply_image: List[str] = None,
             reply_text: List[str] or str = None, reply_image: List[str] or str = None,
             at_list: List[int] = None) -> 'Result':
        if context_reply_text is None:
            context_reply_text = []
        if context_reply_image is None:
            context_reply_image = []

        if reply_text is None:
            reply_text = []
        elif isinstance(reply_text, str):
            reply_text = [reply_text]

        if reply_image is None:
            reply_image = []
        elif isinstance(reply_image, str):
            reply_image = [reply_image]

        if at_list is None:
            at_list = []

        return Result(context_reply_text=context_reply_text, context_reply_image=context_reply_image,
                      reply_text=reply_text, reply_image=reply_image, at_list=at_list)
