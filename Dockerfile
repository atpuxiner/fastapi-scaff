FROM python:3.12-bullseye

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/backend \
    TZ=Asia/Shanghai \
    APP_ENV=prod

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /backend

COPY requirements.txt .
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -f requirements.txt

COPY config ./config
COPY app ./app
