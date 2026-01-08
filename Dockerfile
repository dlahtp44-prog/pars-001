FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y libjpeg-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

# 🔹 repo root 기준
WORKDIR /

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 🔹 main.py가 루트에 있으므로
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
