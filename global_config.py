# coding=utf-8
"""
这里存储一些全局的常量
"""
import logging
import logging.handlers
import os
from datetime import datetime

# MongoDB服务器地址
mongo_connection: str = 'mongodb://root:123456@localhost:27017/'

# Redis服务器地址
redis_host = 'localhost'
redis_port = '6379'
redis_db = 1
redis_password = '123456'

# 全局锁
global_lock = False

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


class FlowerLog:
    """
    花店日志（每天一个日志文件，需要手动删除日志）
    """
    log_name = 'flower'  # 日志名称
    log_dir = 'logs'  # 日志目录
    formatter = logging.Formatter(
        '%(asctime)s - %(name)-s [%(levelname)-9s] - @%(filename)-8s:%(lineno)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )  # 日志输出格式
    
    def __init__(self):
        # 创建logs文件夹
        cur_path = os.path.dirname(os.path.realpath(__file__))
        log_path = os.path.join(cur_path, self.log_dir)
        # 如果不存在这个logs文件夹，就自动创建一个
        if not os.path.exists(log_path):
            os.mkdir(log_path)
        
        logging.basicConfig()
        self.logger = logging.getLogger(self.log_name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
    
    def __console(self, level, message):
        # 文件的命名
        log_name = os.path.join(FlowerLog.log_dir, '%s.log' % datetime.now().strftime('%Y-%m-%d'))
        # 创建一个FileHandler，用于写到本地
        fh = logging.FileHandler(log_name, 'a', encoding='utf-8')
        fh.setLevel(logging.INFO)
        fh.setFormatter(self.formatter)
        self.logger.addHandler(fh)
        
        # 创建一个StreamHandler,用于输出到控制台
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)
        ch.setFormatter(self.formatter)
        self.logger.addHandler(ch)
        
        if level == 'info':
            self.logger.info(message)
        elif level == 'debug':
            self.logger.debug(message)
        elif level == 'warning':
            self.logger.warning(message)
        elif level == 'error':
            self.logger.error(message)
        self.logger.removeHandler(ch)
        self.logger.removeHandler(fh)
        # 关闭打开的文件
        fh.close()
    
    def debug(self, message):
        self.__console('debug', message)
    
    def info(self, message):
        self.__console('info', message)
    
    def warning(self, message):
        self.__console('warning', message)
    
    def error(self, message):
        self.__console('error', message)


logger: FlowerLog = FlowerLog()
