#!/bin/bash

# ====================================================
# ODIN-AI 빠른 시작 스크립트
# Created: 2025-09-24
# Description: 한 번에 모든 서비스 실행
# ====================================================

# 색상
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🚀 ODIN-AI 빠른 시작${NC}"
echo "========================"

# 백엔드 시작 (터미널 1)
echo -e "${GREEN}[1/3] 백엔드 서버 시작...${NC}"
osascript -e 'tell app "Terminal"
    do script "cd '"$(pwd)"' && source venv/bin/activate && python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
end tell' 2>/dev/null || {
    # macOS가 아닌 경우 새 터미널에서 실행
    gnome-terminal -- bash -c "cd $(pwd) && source venv/bin/activate && python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000; exec bash" 2>/dev/null ||
    xterm -e "cd $(pwd) && source venv/bin/activate && python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000; bash" 2>/dev/null &
}

# 프론트엔드 시작 (터미널 2)
echo -e "${GREEN}[2/3] 프론트엔드 서버 시작...${NC}"
osascript -e 'tell app "Terminal"
    do script "cd '"$(pwd)/frontend"' && npm start"
end tell' 2>/dev/null || {
    gnome-terminal -- bash -c "cd $(pwd)/frontend && npm start; exec bash" 2>/dev/null ||
    xterm -e "cd $(pwd)/frontend && npm start; bash" 2>/dev/null &
}

# 대기
sleep 5

# 브라우저 열기
echo -e "${GREEN}[3/3] 브라우저 열기...${NC}"
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:3000
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open http://localhost:3000 2>/dev/null
fi

echo -e "\n${GREEN}✅ 시작 완료!${NC}"
echo -e "${CYAN}프론트엔드:${NC} http://localhost:3000"
echo -e "${CYAN}백엔드 API:${NC} http://localhost:8000"
echo -e "${CYAN}API 문서:${NC} http://localhost:8000/docs"
echo -e "\n${YELLOW}종료하려면 각 터미널에서 Ctrl+C를 누르세요.${NC}"