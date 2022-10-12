# coding=utf-8
"""
股市的模型
"""
from datetime import datetime
from enum import Enum
from typing import List

from model.base_model import *
from model.model import DecorateItem

__all__ = [
    "TradeType", "TradeRecords", "FlowerPrice", "Stock", "Debt", "TodayDebt", "UserAccount"
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
            trade_type = 'TradeType.' + trade_type
        if trade_type == str(cls.buy):
            return cls.buy
        if trade_type == str(cls.sell):
            return cls.sell
        return cls.none


class TradeRecords(EntityClass):
    """
    贸易记录
    """

    def __init__(self, user_id: str = '', role_id: str = '', nickname: str = '', trade_type: TradeType = TradeType.none,
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

    def __init__(self, flower_id: str = '', price: List[int] = None, max_price: int = 0, min_price: int = 0,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)

        self.flower_id = flower_id  # 花的id
        if price is None:
            price = []
        # 价格从每天早上十点开市，到晚上十点关市
        self.price = price  # 价格记录
        self.max_price = max_price
        self.min_price = min_price

    def insert_price(self, price: int):
        self.max_price = max(self.max_price, price)
        self.min_price = min(self.min_price, price)
        self.price.append(price)


class Stock(InnerClass):
    """
    股票、期货
    """

    def __init__(self, flower_id: str = '', number: int = 0):
        super().__init__('Stock')

        self.flower_id = flower_id  # 花的id
        self.number = number  # 数量


class Debt(InnerClass):
    """
    债务
    """

    def __init__(self, gold: int = 0, borrowing_time: datetime = datetime.now(),
                 repayment_date: datetime = datetime.now(), daily_interest_rate: float = 0.0,
                 rolling_interest: bool = False, minimum_interest: int = 0,
                 pawn: List[DecorateItem] = None):
        super().__init__('Debt')

        self.gold = gold  # 借款金币
        self.borrowing_time = borrowing_time  # 借款时间
        self.repayment_date = repayment_date  # 还款时间

        self.daily_interest_rate = daily_interest_rate  # 日利率
        self.rolling_interest = rolling_interest  # 是否是利滚利（即是否以前一天加上利率的价格算今天的利率）
        self.minimum_interest = minimum_interest  # 最低利率

        if pawn is None:
            pawn = []
        self.pawn = pawn  # 抵押物


class TodayDebt(EntityClass):
    """
    今日的可选债务
    """

    def __init__(self, qq: int = 0, gold: int = 0, repayment_day: int = 1, daily_interest_rate: float = 0.0,
                 rolling_interest: bool = False, minimum_interest: int = 0, borrowing: bool = False,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)

        self.qq = qq  # qq
        self.gold = gold  # 借款金币
        self.repayment_day = repayment_day  # 还款的天数

        self.daily_interest_rate = daily_interest_rate  # 日利率
        self.rolling_interest = rolling_interest  # 是否是利滚利（即是否以前一天加上利率的价格算今天的利率）
        self.minimum_interest = minimum_interest  # 最低利率

        self.borrowing = borrowing  # 是否有被借走


class UserAccount(EntityClass):
    """
    用户账户
    """

    def __init__(self, qq: int = 0, account_gold: int = 0, hold_stock: List[Stock] = None, debt_list: List[Debt] = None,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)

        self.qq = qq  # qq
        self.account_gold = account_gold  # 账户中的金币
        if hold_stock is None:
            hold_stock = []
        self.hold_stock = hold_stock  # 持有股票、期货
        if debt_list is None:
            debt_list = []
        self.debt_list = debt_list  # 债务
