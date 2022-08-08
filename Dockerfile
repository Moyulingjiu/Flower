# 使用python镜像自定义我们的镜像
FROM python:latest
#创建/app目录
RUN mkdir /app

#将项目文件内的requirements.txt拷贝到/app
COPY ./requirements.txt /app

#切换到/app目录
WORKDIR /app
#使用豆瓣源https://pypi.douban.com/simple安装项目的python依赖
RUN pip install -r requirements.txt -i https://pypi.douban.com/simple
EXPOSE 8000
ENTRYPOINT ["uvicorn","main:app","--host","0.0.0.0","--port","8000","--reload"]
