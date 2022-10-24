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
    "TradeType", "TradeRecords", "FlowerPrice", "Stock", "Debt", "TodayDebt", "UserAccount", "Lottery"
]


class TradeType(Enum):
    """
    贸易类型
    """
    none = 'none'
    buy = 'buy'
    sell = 'sell'

    @classmethod
    def view_type(cls, trade_type) -> str:
        if trade_type == cls.buy:
            return '买入'
        elif trade_type == cls.sell:
            return '卖出'
        return '未知'

    @classmethod
    def get_type(cls, trade_type: str):
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

    def __init__(self, user_id: int = 0, role_id: str = '', nickname: str = '', trade_type: TradeType = TradeType.none,
                 flower_id: str = '', transaction_complete: bool = False,
                 number: int = 0, price: int = 0, transaction_volume: int = 0,
                 stock_hold_time: datetime = datetime.now(),
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
        self.stock_hold_time = stock_hold_time  # 对于卖出的，要记录一下持仓的日期方便退回


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
        self.latest_price = -1
        self.init = False

    def insert_price(self, price: int, hour: int):
        if price < 0:
            return
        self.latest_price = price
        if not self.init:
            self.max_price = price
            self.min_price = price
            self.price = [-1 for _ in range(24)]
            self.price[hour] = price
            self.init = True
        else:
            self.max_price = max(self.max_price, price)
            self.min_price = min(self.min_price, price)
            self.price[hour] = price

    def get_latest_price(self):
        """获取最新的价格"""
        return self.latest_price


class Stock(InnerClass):
    """
    股票、期货
    """

    def __init__(self, flower_id: str = '', number: int = 0, gold: int = 0, create_time: datetime = datetime.now()):
        super().__init__('Stock')

        self.flower_id = flower_id  # 花的id
        self.number = number  # 数量
        self.gold = gold  # 持仓价格
        self.create_time = create_time  # 持仓开始日期


class TodayDebt(EntityClass):
    """
    今日的可选债务
    """

    def __init__(self, qq: int = 0, gold: int = 0, flower_id: str = '', number: int = 0,
                 repayment_day: int = 1, daily_interest_rate: float = 0.0,
                 rolling_interest: bool = False, minimum_interest: float = 0.0, mortgage_rates: float = 0.0,
                 borrowing: bool = False,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)

        self.qq = qq  # qq
        self.gold = gold  # 借款金币
        self.flower_id = flower_id  # 花的id
        self.number = number  # 花的数量
        self.repayment_day = repayment_day  # 还款的天数

        self.daily_interest_rate = daily_interest_rate  # 日利率
        self.rolling_interest = rolling_interest  # 是否是利滚利（即是否以前一天加上利率的价格算今天的利率）
        self.minimum_interest = minimum_interest  # 最低利率
        self.mortgage_rates = mortgage_rates  # 抵押率

        self.borrowing = borrowing  # 是否有被借走


class Debt(InnerClass):
    """
    债务
    """

    def __init__(self, debt_id: str = '', pawn: List[DecorateItem] = None, create_time: datetime = datetime.now()):
        super().__init__('Debt')

        self.debt_id = debt_id  # 贷款的id

        if pawn is None:
            pawn = []
        self.pawn = pawn  # 抵押物

        self.create_time = create_time  # 创建时间


class UserAccount(EntityClass):
    """
    用户账户
    """

    def __init__(self, qq: int = 0, account_gold: int = 0, debt_gold: int = 0, hold_stock: List[Stock] = None,
                 debt_list: List[Debt] = None, not_enough_bond_days: int = 0, earn_gold: float = 0,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)

        self.qq = qq  # qq
        self.account_gold = account_gold  # 账户中的金币
        self.debt_gold = debt_gold  # 账户中欠款的金币
        self.earn_gold = earn_gold  # 赚取的金币
        self.not_enough_bond_days = not_enough_bond_days  # 保证金不足的天数
        if hold_stock is None:
            hold_stock = []
        self.hold_stock = hold_stock  # 持有股票、期货
        if debt_list is None:
            debt_list = []
        self.debt_list = debt_list  # 债务


class Lottery(EntityClass):
    """彩票"""

    def __init__(self, qq: int = 0, lucky_number: int = 0, winning: bool = False,
                 create_time: datetime = datetime.now(), create_id: str = '0', update_time: datetime = datetime.now(),
                 update_id: str = '0', is_delete: int = 0, _id: str or None = None):
        super().__init__(create_time, create_id, update_time, update_id, is_delete, _id)

        self.qq = qq  # QQ号
        self.lucky_number = lucky_number  # 幸运数字
        self.winning = winning  # 是否获奖
