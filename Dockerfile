# 使用python镜像自定义我们的镜像
FROM python:3.9

# 添加时区环境变量，亚洲，上海
ENV TimeZone=Asia/Shanghai
# 使用软连接，并且将时区配置覆盖/etc/timezone
RUN ln -snf /usr/share/zoneinfo/$TimeZone /etc/localtime && echo $TimeZone > /etc/timezone

#创建/app目录
RUN mkdir /app

#将项目文件内的所有目录拷贝到/app
COPY ./ /app

#切换到/app目录
WORKDIR /app
#使用豆瓣源https://pypi.douban.com/simple安装项目的python依赖
RUN pip install -r requirements.txt -i https://pypi.douban.com/simple
EXPOSE 8000
ENTRYPOINT ["uvicorn","main:app","--host","0.0.0.0","--port","8000","--reload"]
