#!/bin/bash

# ====================================================
# ODIN-AI 재시작 스크립트
# 모든 관련 프로세스를 종료하고 다시 시작
# ====================================================

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════╗
║        ODIN-AI 재시작 스크립트        ║
╚═══════════════════════════════════════╝
EOF
echo -e "${NC}"

# 1. 기존 프로세스 종료
echo -e "${YELLOW}🛑 기존 프로세스 종료중...${NC}"
echo "================================"

# Python/uvicorn 프로세스 종료
echo -e "${BLUE}▶ Backend 프로세스 확인 및 종료${NC}"
BACKEND_PIDS=$(lsof -ti:8000 2>/dev/null)
if [ ! -z "$BACKEND_PIDS" ]; then
    for PID in $BACKEND_PIDS; do
        echo "  - PID $PID 종료"
        kill -9 $PID 2>/dev/null
    done
    echo -e "${GREEN}✅ Backend 프로세스 종료 완료${NC}"
else
    echo -e "${CYAN}ℹ️  실행 중인 Backend 없음${NC}"
fi

# 추가 포트 확인 (8001)
BACKEND_ALT_PIDS=$(lsof -ti:8001 2>/dev/null)
if [ ! -z "$BACKEND_ALT_PIDS" ]; then
    echo "  - 대체 포트(8001) 프로세스 종료"
    kill -9 $BACKEND_ALT_PIDS 2>/dev/null
fi

# Node.js/React 프로세스 종료
echo -e "\n${BLUE}▶ Frontend 프로세스 확인 및 종료${NC}"
FRONTEND_PIDS=$(lsof -ti:3000 2>/dev/null)
if [ ! -z "$FRONTEND_PIDS" ]; then
    for PID in $FRONTEND_PIDS; do
        echo "  - PID $PID 종료"
        kill -9 $PID 2>/dev/null
    done
    echo -e "${GREEN}✅ Frontend 프로세스 종료 완료${NC}"
else
    echo -e "${CYAN}ℹ️  실행 중인 Frontend 없음${NC}"
fi

# uvicorn 프로세스 추가 확인
echo -e "\n${BLUE}▶ 잔여 uvicorn 프로세스 확인${NC}"
UVICORN_PIDS=$(ps aux | grep "[u]vicorn" | awk '{print $2}')
if [ ! -z "$UVICORN_PIDS" ]; then
    for PID in $UVICORN_PIDS; do
        echo "  - uvicorn PID $PID 종료"
        kill -9 $PID 2>/dev/null
    done
fi

# npm 프로세스 확인
NPM_PIDS=$(ps aux | grep "[n]pm start" | awk '{print $2}')
if [ ! -z "$NPM_PIDS" ]; then
    for PID in $NPM_PIDS; do
        echo "  - npm PID $PID 종료"
        kill -9 $PID 2>/dev/null
    done
fi

# 잠시 대기
sleep 2

# 포트 상태 최종 확인
echo -e "\n${BLUE}▶ 포트 상태 확인${NC}"
PORT_8000=$(lsof -ti:8000 2>/dev/null)
PORT_3000=$(lsof -ti:3000 2>/dev/null)

if [ -z "$PORT_8000" ]; then
    echo -e "  ${GREEN}✓${NC} 포트 8000: 사용 가능"
else
    echo -e "  ${RED}✗${NC} 포트 8000: 여전히 사용 중"
fi

if [ -z "$PORT_3000" ]; then
    echo -e "  ${GREEN}✓${NC} 포트 3000: 사용 가능"
else
    echo -e "  ${RED}✗${NC} 포트 3000: 여전히 사용 중"
fi

echo -e "\n${GREEN}✅ 모든 프로세스 종료 완료${NC}"
echo "================================"

# 2. 서비스 재시작 옵션
echo -e "\n${CYAN}🚀 서비스를 시작하시겠습니까?${NC}"
echo "  1) 전체 재시작 (Backend + Frontend)"
echo "  2) Backend만 재시작"
echo "  3) Frontend만 재시작"
echo "  4) 종료만 (재시작 안 함)"
echo -n "선택 [1-4]: "
read choice

case $choice in
    1)
        echo -e "\n${GREEN}🚀 전체 서비스 재시작${NC}"
        echo "================================"

        # Backend 시작
        echo -e "${BLUE}▶ Backend 시작${NC}"
        cd /Users/blockmeta/Desktop/blockmeta/project/odin-ai
        source venv/bin/activate 2>/dev/null || true
        python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
        BACKEND_PID=$!
        echo "  Backend PID: $BACKEND_PID"

        # Frontend 시작
        echo -e "${BLUE}▶ Frontend 시작${NC}"
        cd frontend
        npm start > ../logs/frontend.log 2>&1 &
        FRONTEND_PID=$!
        echo "  Frontend PID: $FRONTEND_PID"

        echo -e "\n${GREEN}✅ 서비스 재시작 완료!${NC}"
        echo "================================"
        echo -e "${CYAN}접속 URL:${NC}"
        echo "  • Frontend: http://localhost:3000"
        echo "  • Backend:  http://localhost:8000"
        echo "  • API Docs: http://localhost:8000/docs"
        echo ""
        echo -e "${YELLOW}로그 확인:${NC}"
        echo "  • Backend:  tail -f logs/backend.log"
        echo "  • Frontend: tail -f logs/frontend.log"
        ;;

    2)
        echo -e "\n${GREEN}🚀 Backend만 재시작${NC}"
        cd /Users/blockmeta/Desktop/blockmeta/project/odin-ai
        source venv/bin/activate 2>/dev/null || true
        python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
        echo -e "${GREEN}✅ Backend 시작됨${NC}"
        ;;

    3)
        echo -e "\n${GREEN}🚀 Frontend만 재시작${NC}"
        cd /Users/blockmeta/Desktop/blockmeta/project/odin-ai/frontend
        npm start &
        echo -e "${GREEN}✅ Frontend 시작됨${NC}"
        ;;

    4)
        echo -e "\n${YELLOW}ℹ️  프로세스만 종료하고 재시작하지 않습니다.${NC}"
        ;;

    *)
        echo -e "\n${RED}❌ 잘못된 선택입니다.${NC}"
        ;;
esac

echo -e "\n${CYAN}================================${NC}"
echo -e "${GREEN}✨ 작업 완료${NC}"
echo -e "${CYAN}================================${NC}"