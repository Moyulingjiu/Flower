#!/bin/bash
docker build -t xiaoqi_flower
docker run -d -p 8000:8000 -v ./ /app xiaoqi_flower
