# 1. Builder stage: 의존성 설치
FROM python:3.10-slim as builder

WORKDIR /app

# 시스템 의존성 설치 (필요시)
# RUN apt-get update && apt-get install -y ...

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# 2. Final stage: 실제 운영 이미지
FROM python:3.10-slim

WORKDIR /app

# Builder stage에서 설치한 의존성 복사
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# 애플리케이션 코드 복사
COPY app /app/app
COPY crawler /app/crawler
COPY data /app/data
COPY scripts /app/scripts
COPY main.py /app/

# 포트 노출
EXPOSE 8000

# 서버 실행
# --host 0.0.0.0: Docker 외부에서 접근 가능하도록 설정
# --reload: 코드 변경 시 자동 재시작 (개발용)
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"] 