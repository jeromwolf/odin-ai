#!/bin/bash

# ODIN-AI 전체 스택 실행 스크립트

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}                    ODIN-AI 전체 스택 시작${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# PID 파일 경로
BACKEND_PID_FILE="/tmp/odin-backend.pid"
FRONTEND_PID_FILE="/tmp/odin-frontend.pid"

# 기존 프로세스 종료
cleanup() {
    echo -e "\n${YELLOW}기존 프로세스 정리중...${NC}"

    # Backend 종료
    if [ -f "$BACKEND_PID_FILE" ]; then
        PID=$(cat "$BACKEND_PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "Backend 프로세스 종료 (PID: $PID)"
            kill $PID 2>/dev/null
        fi
        rm -f "$BACKEND_PID_FILE"
    fi

    # Frontend 종료
    if [ -f "$FRONTEND_PID_FILE" ]; then
        PID=$(cat "$FRONTEND_PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "Frontend 프로세스 종료 (PID: $PID)"
            kill $PID 2>/dev/null
        fi
        rm -f "$FRONTEND_PID_FILE"
    fi

    # 포트 확인 및 강제 종료
    for PORT in 8000 3000; do
        PID=$(lsof -ti:$PORT)
        if [ ! -z "$PID" ]; then
            echo "포트 $PORT 사용중인 프로세스 종료 (PID: $PID)"
            kill -9 $PID 2>/dev/null
        fi
    done
}

# Ctrl+C 처리
trap 'echo -e "\n${RED}중단됨. 프로세스 정리중...${NC}"; cleanup; exit' INT

# 환경 확인
check_environment() {
    echo -e "${YELLOW}1. 환경 확인${NC}"

    # Python 확인
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗ Python3가 설치되지 않았습니다${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Python3 확인됨${NC}"

    # Node.js 확인
    if ! command -v node &> /dev/null; then
        echo -e "${RED}✗ Node.js가 설치되지 않았습니다${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Node.js 확인됨${NC}"

    # PostgreSQL 확인
    if ! psql -U blockmeta -d odin_db -c "SELECT 1" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠ PostgreSQL 연결 실패 (선택사항)${NC}"
    else
        echo -e "${GREEN}✓ PostgreSQL 연결됨${NC}"
    fi

    echo
}

# Backend 시작
start_backend() {
    echo -e "${YELLOW}2. Backend 서버 시작${NC}"

    # 프로젝트 루트로 이동
    cd /Users/blockmeta/Desktop/blockmeta/project/odin-ai

    # 가상환경 활성화 및 백엔드 시작
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi

    # 필수 패키지 설치 (빠른 확인)
    pip install -q fastapi uvicorn loguru python-dotenv 2>/dev/null

    # 환경변수 설정
    export DATABASE_URL="postgresql://blockmeta@localhost:5432/odin_db"
    export ENVIRONMENT="development"
    export LOG_LEVEL="INFO"

    # Backend 시작 (백그라운드)
    echo "Backend 시작중..."
    python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/odin-backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$BACKEND_PID_FILE"

    # Backend 시작 대기
    for i in {1..10}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Backend 서버 시작됨 (http://localhost:8000)${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done

    if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${RED}✗ Backend 시작 실패${NC}"
        echo "로그 확인: tail -f /tmp/odin-backend.log"
        exit 1
    fi

    echo
}

# Frontend 시작
start_frontend() {
    echo -e "${YELLOW}3. Frontend 서버 시작${NC}"

    cd /Users/blockmeta/Desktop/blockmeta/project/odin-ai/frontend

    # node_modules 확인
    if [ ! -d "node_modules" ]; then
        echo "의존성 설치중..."
        npm install --silent
    fi

    # Frontend 시작 (백그라운드)
    echo "Frontend 시작중..."
    npm start > /tmp/odin-frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$FRONTEND_PID_FILE"

    # Frontend 시작 대기
    for i in {1..20}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Frontend 서버 시작됨 (http://localhost:3000)${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done

    if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠ Frontend 아직 시작중... (컴파일 진행중)${NC}"
    fi

    echo
}

# 상태 표시
show_status() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✓ ODIN-AI가 성공적으로 시작되었습니다!${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    echo -e "${YELLOW}접속 URL:${NC}"
    echo -e "  • Frontend:  ${GREEN}http://localhost:3000${NC}"
    echo -e "  • Backend:   ${GREEN}http://localhost:8000${NC}"
    echo -e "  • API Docs:  ${GREEN}http://localhost:8000/docs${NC}"

    echo -e "\n${YELLOW}로그 확인:${NC}"
    echo -e "  • Backend:  tail -f /tmp/odin-backend.log"
    echo -e "  • Frontend: tail -f /tmp/odin-frontend.log"

    echo -e "\n${YELLOW}종료하려면:${NC}"
    echo -e "  • Ctrl+C를 누르세요"

    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# 메인 실행
main() {
    # 기존 프로세스 정리
    cleanup

    # 환경 확인
    check_environment

    # Backend 시작
    start_backend

    # Frontend 시작
    start_frontend

    # 상태 표시
    show_status

    # 로그 모니터링 (선택사항)
    echo -e "\n${YELLOW}실시간 로그 보기 (Ctrl+C로 종료):${NC}\n"

    # 두 로그를 동시에 표시
    tail -f /tmp/odin-backend.log /tmp/odin-frontend.log 2>/dev/null
}

# 실행
main