import datetime

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import uvicorn

import flower
from model import *

app = FastAPI()


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
    return Response(code=0, message='success', data=Result.init(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))


@app.post("/draw")
def draw_card():
    """
    抽卡
    :return: 抽卡结果
    """
    # todo: 抽卡（第一个道具是50%，第二个道具20%，第三个道具10%，第四个道具1%，第五个道具0.1%，之后不能抽到道具）
    return ''


@app.post("/flower")
async def add_flower(message: Message):
    """
    花店处理类
    :param message: 消息
    :return: 结果
    """
    result: Result = flower.handle(message.message, message.qq, message.username, message.bot_qq, message.bot_name,
                                   message.at_list)
    # 上下文的处理消息要放到最后一条去
    if len(result.reply_text) > 0:
        context_reply: str = result.reply_text[0]
        del result.reply_text[0]
        result.reply_text.append(context_reply)
    return Response(code=0, message="success", data=result)


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
