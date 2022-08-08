# coding=utf-8
"""
股市的模型
"""
from datetime import datetime
from enum import Enum
from typing import List

from model.base_model import *

__all__ = [
    "TradeType", "TradeRecords", "FlowerPrice"
]


class TradeType(Enum):
    """
    贸易类型
    """
    none = 'none'
    buy = 'buy'
    sell = 'sell'

    @classmethod
    def view_level(cls, trade_type) -> str:
        if trade_type == cls.buy:
            return '买入'
        elif trade_type == cls.sell:
            return '卖出'
        return '未知'

    @classmethod
    def get_level(cls, trade_type: str):
        if not trade_type.startswith('TradeType.'):
            level = 'TradeType.' + trade_type
        if trade_type == str(cls.buy):
            return cls.buy
        if trade_type == str(cls.sell):
            return cls.sell
        return cls.none


class TradeRecords(EntityClass):
    """
    贸易记录
    """

    def __init__(self, user_id: str, role_id: str, nickname: str, trade_type: TradeType = TradeType.none,
                 flower_id: str = '', transaction_complete: bool = False,
                 number: int = 0, price: int = 0, transaction_volume: int = 0,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)

        # 可能是用户交易的也可能是角色（npc）交易的
        self.user_id = user_id  # 用户id
        self.role_id = role_id  # 角色id
        self.nickname = nickname  # 用户名（交易时的用户名）
        self.trade_type = trade_type  # 贸易类型
        self.flower_id = flower_id  # 花的id
        self.transaction_complete = transaction_complete  # 是否交易完成
        self.number = number  # 交易的数量
        self.price = price  # 交易时的价格
        self.transaction_volume = transaction_volume  # 实际交易数量


class FlowerPrice(EntityClass):
    """
    实时花的价格（每天）
    一天的所有花的价格将会记录在这个类中，不同天需要生成不同的类
    """

    def __init__(self, flower_id: str, price: List[int] = None,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)

        self.flower_id = flower_id  # 花的id
        if price is None:
            price = []
        # 价格从每天早上十点开市，到晚上十点关市
        self.price = price  # 价格记录
