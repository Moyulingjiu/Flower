# coding=utf-8


__all__ = [
    "FixPointNumber"
]


class FixPointNumber:
    """
    定点数
    运算中会舍弃多余的小数部分，不会四舍五入
    """

    def __init__(self, number: int = 0, place: int = 2):
        self.number: int = number
        if place < 0:
            raise ValueError('小数位数不能小于0')
        self.place = place

    def __str__(self):
        if self.place == 0:
            return str(self.number)
        res: str = ''
        number = self.number
        if self.number < 0:
            res += '-'
            number = -self.number
        base: int = 10 ** self.place
        res += str(number // base) + '.'
        decimal: str = str(number % base)
        length: int = len(decimal)
        for index in range(self.place - length):
            res += '0'
        res += str(decimal)
        return res

    def __repr__(self):
        return self.__str__()

    def __add__(self, other):
        if isinstance(other, FixPointNumber):
            if self.place >= other.place:
                return FixPointNumber(self.number + other.number * 10 ** (self.place - other.place), self.place)
            else:
                return FixPointNumber(self.number * 10 ** (other.place - self.place) + other.number, other.place)
        elif isinstance(other, int):
            return FixPointNumber(self.number + other * 10 ** self.place, self.place)
        elif isinstance(other, float):
            return FixPointNumber(self.number + int(other * 10 ** self.place), self.place)
        else:
            raise TypeError('不支持这两种类型相加 +: \'FixPointNumber\' 和 \'{}\''.format(type(other)))

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, FixPointNumber):
            if self.place >= other.place:
                return FixPointNumber(self.number - other.number * 10 ** (self.place - other.place), self.place)
            else:
                return FixPointNumber(self.number * 10 ** (other.place - self.place) - other.number, other.place)
        elif isinstance(other, int):
            return FixPointNumber(self.number - other * 10 ** self.place, self.place)
        elif isinstance(other, float):
            return FixPointNumber(self.number - int(other * 10 ** self.place), self.place)
        else:
            raise TypeError('不支持这两种类型相减 -: \'FixPointNumber\' 和 \'{}\''.format(type(other)))

    def __rsub__(self, other):
        if isinstance(other, FixPointNumber):
            return other - self
        elif isinstance(other, int):
            return FixPointNumber(other * 10 ** self.place - self.number, self.place)
        elif isinstance(other, float):
            return FixPointNumber(int(other * 10 ** self.place) - self.number, self.place)
        else:
            raise TypeError('不支持这两种类型相减 -: \'FixPointNumber\' 和 \'{}\''.format(type(other)))

    def __mul__(self, other):
        if isinstance(other, FixPointNumber):
            return FixPointNumber(self.number * other.number, self.place + other.place)
        elif isinstance(other, int):
            return FixPointNumber(self.number * other, self.place)
        elif isinstance(other, float):
            return FixPointNumber(int(self.number * other), self.place)
        else:
            raise TypeError('不支持这两种类型相乘 *: \'FixPointNumber\' 和 \'{}\''.format(type(other)))

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, FixPointNumber):
            if self.place >= other.place:
                return FixPointNumber(
                    int(self.number / (other.number * 10 ** (self.place - other.place)) * 10 ** self.place), self.place
                )
            else:
                return FixPointNumber(
                    int(self.number * 10 ** (other.place - self.place) / other.number * 10 ** other.place), other.place
                )
        elif isinstance(other, int):
            return FixPointNumber(self.number // other, self.place)
        elif isinstance(other, float):
            return FixPointNumber(int(self.number // other), self.place)
        else:
            raise TypeError('不支持这两种类型相除 /: \'FixPointNumber\' 和 \'{}\''.format(type(other)))

    def __rtruediv__(self, other):
        if isinstance(other, FixPointNumber):
            return other / self
        elif isinstance(other, int):
            return FixPointNumber(other * 10 ** (self.place * 2) // self.number, self.place)
        elif isinstance(other, float):
            return FixPointNumber(int(other * 10 ** (self.place * 2)) // self.number, self.place)
        else:
            raise TypeError('不支持这两种类型相除 /: \'FixPointNumber\' 和 \'{}\''.format(type(other)))

    def __floordiv__(self, other):
        return self.__truediv__(other)

    def __rfloordiv__(self, other):
        return self.__rtruediv__(other)

    def __int__(self):
        base: int = 10 ** self.place
        return self.number // base

    def to_dict(self) -> dict[str, int]:
        number_dict = {
            'number': self.number,
            'place': self.place
        }
        return number_dict

    @classmethod
    def dict_to_fix_number(cls, number_dict: dict[str, int]) -> 'FixPointNumber':
        if not isinstance(number_dict, dict):
            raise TypeError('只能从dict转为FixPointNumber')
        if 'place' not in number_dict or 'number' not in number_dict:
            raise TypeError('dict字段错误')
        return FixPointNumber(number_dict['number'], number_dict['place'])

    def to_int(self) -> int:
        return self.__int__()

    def to_float(self) -> float:
        return self.number / 10 ** self.place
