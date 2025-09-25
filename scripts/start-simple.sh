#!/bin/bash

# ====================================================
# ODIN-AI 간단 실행 스크립트
# 최소 설정으로 바로 실행
# ====================================================

echo "🚀 ODIN-AI 간단 실행"
echo "===================="

# 1. 필수 패키지만 설치
echo "📦 필수 패키지 설치 중..."
pip install fastapi uvicorn requests beautifulsoup4 loguru python-dotenv

# 2. 프론트엔드 패키지 설치
echo "📦 프론트엔드 설치 중..."
cd frontend
npm install
cd ..

# 3. .env 파일 생성 (없으면)
if [ ! -f .env ]; then
    echo "⚙️ 환경 설정 파일 생성..."
    cat > .env << EOF
SECRET_KEY=test-secret-key-123
DATABASE_URL=postgresql://blockmeta@localhost:5432/odin_db
DEBUG=True
EOF
fi

# 4. 서버 시작
echo ""
echo "✅ 준비 완료! 서버를 시작합니다..."
echo ""
echo "백엔드: http://localhost:8000"
echo "프론트엔드: http://localhost:3000"
echo ""
echo "종료: Ctrl+C"
echo "===================="

# 백엔드와 프론트엔드 동시 실행
(
    trap 'kill 0' SIGINT
    echo "🔵 백엔드 시작..."
    python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &

    echo "🟢 프론트엔드 시작..."
    cd frontend && npm start &

    wait
)