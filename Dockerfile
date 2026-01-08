# 안정적인 Python 버전
FROM python:3.12-slim

# Pillow / 이미지 처리 의존성
RUN apt-get update && \
    apt-get install -y libjpeg-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

# 작업 디렉토리
WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 전체 코드 복사
COPY . .

# 🚀 Railway용 FastAPI 실행 (중요)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
