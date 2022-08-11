# Flower（花店）

花店是一款养成类游戏，其主要是通过mirai框架，来连接QQ，然后识别QQ消息并进行回复。

当然你也可以选择在此基础上魔改，将消息处理变成http请求以兼容其它游戏模式。

## 技术栈

- FastApi
- MongoDB
- Redis

推荐的Python版本为`3.10`，最低兼容为`3.7`。

## 启动

首先安装`Python3`。然后运行`build-dev`，如果是Linux系统运行sh文件，windows系统运行cmd文件。

等待环境安装完成后，就可以直接运行了。

最直接的运行方式就是

```bash
# for windows
python main.py
# for linux
python3 main.py
```

> 注： 该方法需要在main.py加入以下代码
> ```python
> if __name__ == '__main__':
>     uvicorn.run(app, host=global_config.host, port=global_config.port)
> ```

其次可以通过`uvicorn`运行

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

host可以指定运行的ip。127.0.0.1为只允许本机访问。port指定了端口。readload指定了如果代码发生改变，会自动重新加载运行。

出现：

```
INFO:     Started server process [18876]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

即启动成功。访问`http://127.0.0.1:8000/docs`即可看见api文档

> 不建议在生产环境外漏api细节，要么关闭docs，要么配置白名单访问
> - `app = FastAPI(docs_url=None)`关掉文档
> - 配置白名单
> ```python
> app.add_middleware(
>    TrustedHostMiddleware, allowed_hosts=["example.com","*.example.com"] 
> )
> ```

## 版权申明

仅能用于研究学习，不可挪作它用。

## 常见问题

### 1. 目标服务器积极拒绝连接

该情况一般是数据库、redis没有打开。或者数据库访问权限不对。

### 2. 天气爬取出现错误

建议重写爬虫，没有爬虫能够保证永远有效，应该是爬虫过期了，或者网络波动造成无法爬取数据。

### 3. HTTPSConnection 发生错误ssl.SSLEOFError: EOF occurred in violation of protocol

不要开代理！！！请使用国内的网络，或者重写天气爬虫。
