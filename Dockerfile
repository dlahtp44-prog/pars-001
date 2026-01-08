FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y libjpeg-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 프로젝트 루트(/app)에 app/ 패키지가 있으므로 import가 되도록 설정
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ✅ Railway/Render 등 PaaS는 PORT 환경변수를 줍니다.
# Start Command에서 $PORT가 그대로 보이는 문제를 피하려고, shell로 실행해 변수 확장을 보장합니다.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
