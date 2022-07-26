# coding=utf-8
class MyException(Exception):
    def __init__(self, message):
        self.message = message


class UserNotRegisteredException(MyException):
    """
    用户未注册
    """
    
    def __init__(self, message):
        self.message = message


class ItemNegativeNumberException(MyException):
    """
    商品数量不能为负数
    """
    
    def __init__(self, message):
        self.message = message


class ItemNotFoundException(MyException):
    """
    商品不存在
    """
    
    def __init__(self, message):
        self.message = message


class ItemNotEnoughException(MyException):
    """
    商品不足
    """
    
    def __init__(self, message):
        self.message = message


class WareHouseSizeNotEnoughException(MyException):
    """
    仓库容量不足
    """
    
    def __init__(self, message):
        self.message = message


class UserBeLockedException(MyException):
    """
    用户被锁定
    """
    
    def __init__(self, message):
        self.message = message


class AtListNullException(MyException):
    """
    艾特列表没有用户
    """
    
    def __init__(self, message):
        self.message = message


class TypeException(MyException):
    """
    指令格式错误（一般是带参数的指令）
    """
    
    def __init__(self, message):
        self.message = message


class PageOutOfRangeException(MyException):
    """
    页码超限
    """
    
    def __init__(self, message):
        self.message = message
