# coding=utf-8
"""
这里存储一些全局的常量
"""

# MongoDB服务器地址
mongo_connection: str = 'mongodb://root:123456@localhost:27017/'

# Redis服务器地址
redis_host = 'localhost'
redis_port = '6379'
redis_db = 1
redis_password = '123456'

# 时间
minute_second: int = 60
ten_minute_second: int = 10 * 60
hour_second: int = 3600
day_second: int = hour_second * 24
half_day_second: int = hour_second * 12
week_second: int = day_second * 7
month_second: int = day_second * 30
year_second: int = day_second * 365

# 土壤改变的小时数
soil_change_hour = 8

# 铲除花所需要花费的金币数
remove_farm_flower_cost_gold = 500
