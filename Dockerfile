# 1. 베이스 이미지
FROM python:3.11-slim

# 2. 작업 폴더 설정
WORKDIR /app

# 3. 필수 패키지 설치 (psycopg2 등)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 4. 라이브러리 목록 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 소스 코드 전체 복사
COPY . .

# 6. Streamlit 포트 열기
EXPOSE 8501

# 7. 실행 명령어
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]