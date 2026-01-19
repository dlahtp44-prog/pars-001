FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway/Render often provide PORT env. Use 8080 if not set.
CMD ["bash","-lc","uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
