# Python 3.11 기반 이미지
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    # HWP 처리를 위한 LibreOffice
    libreoffice \
    # OCR을 위한 Tesseract
    tesseract-ocr \
    tesseract-ocr-kor \
    # 이미지 처리
    libmagick++-dev \
    # PDF 처리
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# storage 디렉토리 생성
RUN mkdir -p /app/storage/documents /app/storage/temp /app/storage/processed

# 포트 노출
EXPOSE 8000

# 기본 명령어
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]