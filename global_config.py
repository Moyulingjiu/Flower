# coding=utf-8
"""
这里存储一些全局的常量
"""
# 需要的库
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import List, Dict

import yaml

from flower_exceptions import ConfigException

host: str = '0.0.0.0'
port: int = 8000
center: str = '127.0.0.1:9000'  # 中心服务器地址

# MongoDB服务器地址
mongo_connection: str = 'mongodb://root:123456@localhost:27017/'

# Redis服务器地址
redis_host = 'localhost'
redis_port = '6379'
redis_background_db = 2
redis_db = 1
redis_password = ''

# 百度登陆的cookie（用于爬取百度的天气，不然不可用）
baidu_login_cookie = ''

# 全局锁
get_right_update_data: bool = False
get_all_weather: bool = False

object_id_length: int = 24  # mongodb的object id的长度

# 时间
minute_second: int = 60
ten_minute_second: int = 10 * 60
hour_second: int = 3600
day_second: int = hour_second * 24
half_day_second: int = hour_second * 12
week_second: int = day_second * 7
month_second: int = day_second * 30
year_second: int = day_second * 365

# 延迟任务的留言板
message_board: Dict[int, List[str]] = {}


class FlowerLog:
    """
    花店日志（每天一个日志文件，需要手动删除日志）
    """
    log_name = 'flower'  # 日志名称
    log_dir = 'logs'  # 日志目录
    formatter = logging.Formatter(
        '%(asctime)s - %(name)-s [%(levelname)-9s] - %(message)s',
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


def load_config(config_path: str = 'config.yaml'):
    """
    加载配置文件
    """
    global host, port, center
    global mongo_connection, redis_host, redis_port, redis_background_db, redis_db, redis_password
    global baidu_login_cookie
    
    with open(config_path, 'r', encoding='utf8') as f:
        config_yaml = yaml.safe_load(f.read())
        if 'host' in config_yaml:
            host = config_yaml['host']
        if 'port' in config_yaml:
            port = config_yaml['port']
        if 'center' in config_yaml:
            center = config_yaml['center']
        
        if 'mongo_connection' in config_yaml:
            mongo_connection = config_yaml['mongo_connection']
        if 'redis_host' in config_yaml:
            redis_host = config_yaml['redis_host']
        if 'redis_port' in config_yaml:
            redis_port = config_yaml['redis_port']
        if 'redis_background_db' in config_yaml:
            redis_background_db = config_yaml['redis_background_db']
        if 'redis_db' in config_yaml:
            redis_db = config_yaml['redis_db']
        if 'redis_password' in config_yaml:
            redis_password = config_yaml['redis_password']

        if 'baidu_login_cookie' in config_yaml:
            baidu_login_cookie = config_yaml['baidu_login_cookie']


def check_config():
    """
    检查配置信息是否正确
    """
    global host, port, center
    global mongo_connection, redis_host, redis_port, redis_background_db, redis_db, redis_password
    
    if not isinstance(host, str):
        raise ConfigException('host 配置错误')
    if not isinstance(port, int) or port < 0 or port > 65535:
        raise ConfigException('port 配置错误')
    if not isinstance(center, str):
        raise ConfigException('center 配置错误')
    
    if not isinstance(mongo_connection, str):
        raise ConfigException('mongo_connection 配置错误')
    if not isinstance(redis_host, str):
        raise ConfigException('redis_host 配置错误')
    if not isinstance(redis_port, str):
        raise ConfigException('redis_port 配置错误')
    if not isinstance(redis_background_db, int):
        raise ConfigException('redis_background_db 配置错误')
    if not isinstance(redis_db, int):
        raise ConfigException('redis_background_db 配置错误')
    if not isinstance(redis_password, str):
        raise ConfigException('redis_password 配置错误')


# 加载配置
argv = sys.argv[1:]
if len(argv) == 1:
    load_config(argv[0])
else:
    load_config()
check_config()
