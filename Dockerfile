FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 系统依赖（libpq for psycopg2, gcc for cffi）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# 应用代码
COPY . .

# 日志目录
RUN mkdir -p logs

EXPOSE 8000

CMD ["fastapi", "run", "--workers", "4", "app/main.py"]
