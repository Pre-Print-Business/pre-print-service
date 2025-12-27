FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y default-libmysqlclient-dev pkg-config gcc
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# 로그 폴더 생성 보장
RUN mkdir -p /app/log/locker_reset /app/log/send_email
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]