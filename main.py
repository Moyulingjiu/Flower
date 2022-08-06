# coding=utf-8
import datetime
from typing import List

import uvicorn
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from pydantic import BaseModel

import global_config  # global_config必须放到第一位来，进行配置的初始化
# 导入花店需要的辅助类
import flower
import flower_dao
import util
from global_config import logger
from model import *
from world_handler import update_world

redis_db = {
    "db": global_config.redis_background_db,
    "host": global_config.redis_host,
    "port": global_config.redis_port,
    "password": global_config.redis_password
}
task_config = {
    # 配置存储器
    "jobstores": {
        # 使用Redis进行存储
        'default': RedisJobStore(**redis_db)
    },
    # 配置执行器
    "executors": {
        # 使用进程池进行调度，最大进程数是10个
        'default': ThreadPoolExecutor(10)
    },
    # 创建job时的默认参数
    "job_defaults": {
        'coalesce': False,  # 是否合并执行
        'max_instances': 3,  # 最大实例数
    }
}
scheduler = AsyncIOScheduler(**task_config)

app = FastAPI()


@app.on_event("startup")
async def start_event():
    # 每天凌晨3、4点更新天气
    scheduler.add_job(util.get_all_weather, 'cron', day_of_week='0-6', hour=3, minute=0,
                      second=0, timezone='Asia/Shanghai', args=[], id="get_all_weather_regularly",
                      replace_existing=True)
    scheduler.add_job(util.get_all_weather, 'cron', day_of_week='0-6', hour=4, minute=0,
                      second=0, timezone='Asia/Shanghai', args=[], id="get_all_weather_regularly2",
                      replace_existing=True)
    # 每天凌晨3天更新世界
    scheduler.add_job(update_world, 'cron', day_of_week='0-6', hour=3, minute=0,
                      second=0, timezone='Asia/Shanghai', args=[], id="update_world",
                      replace_existing=True)
    scheduler.start()
    logger.info('背景任务已启动')
    logger.info('FastApi已启动')


class Message(BaseModel):
    message: str
    qq: int
    username: str
    bot_qq: int
    bot_name: str
    at_list: List[int]


class Response(BaseModel):
    code: int
    message: str
    data: Result


@app.get("/calibration")
def calibration():
    """
    校准
    :return: 时间校准
    """
    return Response(code=0, message='success',
                    data=Result.init(reply_text=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))


@app.post("/draw")
async def draw_card(message: Message):
    """
    抽卡
    :return: 抽卡结果
    """
    # 全局加锁不进行响应
    if global_config.global_lock:
        return Response(code=0, message="success", data=Result.init())
    reply: str = flower.DrawCard.draw_card(message.qq, message.username)
    if reply == '':
        return Result.init()
    logger.info(
        '玩家<%s>(%d)@机器人<%s>(%d)：抽卡，%s' % (message.username, message.qq, message.bot_name, message.bot_qq, reply))
    return Result.init(reply_text=reply)


@app.post("/flower")
async def add_flower(message: Message):
    """
    花店处理类
    :param message: 消息
    :return: 结果
    """
    # 全局加锁不进行响应
    if global_config.global_lock:
        return Response(code=0, message="success", data=Result.init())
    # 进行花店的操作逻辑
    result: Result = flower.handle(message.message, message.qq, message.username, message.bot_qq, message.bot_name,
                                   message.at_list)
    if len(result.reply_text) > 0 or len(result.context_reply_text) > 0 or len(result.reply_image) or len(
            result.context_reply_image) > 0:
        # 对此不必要加锁，公告只是通知而已，通知几次无所谓（线程冲突的后果也不过多通知一次）
        announcement_list: List[Announcement] = flower_dao.select_valid_announcement()
        for announcement in announcement_list:
            qq_str: str = str(message.qq)
            if qq_str not in announcement.read_list or announcement.read_list[qq_str] < 3:
                if qq_str not in announcement.read_list:
                    announcement.read_list[qq_str] = 1
                else:
                    announcement.read_list[qq_str] += 1
                flower_dao.update_announcement(announcement)
                reply = '花店公告（由%s编辑）\n------\n%s\n------\n发布日期：%s\n*公告仅会展示三次' % (
                    announcement.username,
                    announcement.text,
                    announcement.expire_time.strftime('%Y-%m-%d %H:%M:%S')
                )
                result.reply_text.append(reply)
        
        logger.info('来自玩家<%s>(%d)[%s，at_list:%s]@机器人<%s>(%d)：%s' % (
            message.username, message.qq, message.message, str(message.at_list), message.bot_name, message.bot_qq,
            str(result)))
    return Response(code=0, message="success", data=result)


if __name__ == '__main__':
    uvicorn.run(app, host=global_config.host, port=global_config.port)
