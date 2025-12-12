
# 안정적인 Python 버전인 3.12를 기반 이미지로 사용합니다. (3.13 대신)
FROM python:3.12-slim
 
# Pillow 빌드에 필요한 시스템 종속성을 설치합니다.
# RUN 명령어는 읽기 전용이 아닌 Docker 빌드 단계에서 실행됩니다.
RUN apt-get update && \
    apt-get install -y libjpeg-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*
 
# 작업 디렉토리를 설정합니다.
WORKDIR /app
 
# requirements.txt 파일을 복사하고 Python 패키지를 설치합니다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
# 나머지 코드를 복사합니다.
COPY . .
 
# 서버 실행 명령어 (프로젝트에 맞게 'main.py'나 'app:app' 부분을 수정해야 함)
# 예시: FastAPI 앱이 main.py에 있고 uvicorn으로 실행하는 경우
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
