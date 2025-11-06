FROM python:3.12-bullseye

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/backend \
    TZ=Asia/Shanghai \
    app_env=prod

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /backend

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/ && \
    rm requirements.txt

COPY config ./config
COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "5", "--log-level", "info"]
