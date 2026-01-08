FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y libjpeg-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

# 🔴 여기 중요: WORKDIR은 루트
WORKDIR /

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 🔴 app/main.py 기준
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
