#!/bin/bash

# ====================================================
# ODIN-AI 초기 설정 스크립트
# Created: 2025-09-24
# Description: 프로젝트 초기 설정 자동화
# ====================================================

set -e

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
║      ODIN-AI 초기 설정 스크립트      ║
╚═══════════════════════════════════════╝
EOF
echo -e "${NC}"

# OS 확인
echo -e "${BLUE}🖥  운영체제 확인 중...${NC}"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
    echo -e "${GREEN}✅ macOS 감지됨${NC}"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
    echo -e "${GREEN}✅ Linux 감지됨${NC}"
else
    echo -e "${RED}❌ 지원하지 않는 운영체제입니다.${NC}"
    exit 1
fi

# 필수 소프트웨어 확인 및 설치
echo -e "\n${BLUE}📦 필수 소프트웨어 확인 중...${NC}"

# Python 3.8+ 확인
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo -e "${GREEN}✅ Python $PYTHON_VERSION 설치됨${NC}"
else
    echo -e "${RED}❌ Python3가 설치되지 않았습니다.${NC}"
    if [[ "$OS" == "macOS" ]]; then
        echo -e "${YELLOW}brew install python3 명령으로 설치하세요.${NC}"
    else
        echo -e "${YELLOW}apt-get install python3 명령으로 설치하세요.${NC}"
    fi
    exit 1
fi

# Node.js 확인
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js $NODE_VERSION 설치됨${NC}"
else
    echo -e "${RED}❌ Node.js가 설치되지 않았습니다.${NC}"
    if [[ "$OS" == "macOS" ]]; then
        echo -e "${YELLOW}brew install node 명령으로 설치하세요.${NC}"
    else
        echo -e "${YELLOW}NodeSource 저장소를 통해 설치하세요.${NC}"
    fi
    exit 1
fi

# PostgreSQL 확인
if command -v psql &> /dev/null; then
    PSQL_VERSION=$(psql --version | awk '{print $3}')
    echo -e "${GREEN}✅ PostgreSQL $PSQL_VERSION 설치됨${NC}"
else
    echo -e "${YELLOW}⚠️  PostgreSQL이 설치되지 않았습니다.${NC}"
    echo -e "${CYAN}PostgreSQL 설치를 진행하시겠습니까? (y/n)${NC}"
    read -r response
    if [[ "$response" == "y" ]]; then
        if [[ "$OS" == "macOS" ]]; then
            brew install postgresql@15
            brew services start postgresql@15
        else
            sudo apt-get update
            sudo apt-get install postgresql postgresql-contrib
            sudo systemctl start postgresql
        fi
    fi
fi

# Redis 확인 (선택사항)
if command -v redis-cli &> /dev/null; then
    echo -e "${GREEN}✅ Redis 설치됨 (선택사항)${NC}"
else
    echo -e "${YELLOW}ℹ️  Redis가 설치되지 않았습니다. (선택사항)${NC}"
fi

# Python 가상환경 생성
echo -e "\n${BLUE}🐍 Python 가상환경 설정 중...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ 가상환경 생성 완료${NC}"
else
    echo -e "${YELLOW}ℹ️  가상환경이 이미 존재합니다.${NC}"
fi

# 가상환경 활성화 및 패키지 설치
source venv/bin/activate
echo -e "${CYAN}📦 Python 패키지 설치 중...${NC}"
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

echo -e "${GREEN}✅ Python 패키지 설치 완료${NC}"

# Node.js 패키지 설치
echo -e "\n${BLUE}📦 Node.js 패키지 설치 중...${NC}"
cd frontend
npm install
cd ..
echo -e "${GREEN}✅ Node.js 패키지 설치 완료${NC}"

# 환경 변수 파일 설정
echo -e "\n${BLUE}⚙️  환경 변수 설정 중...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}✅ .env 파일 생성 완료${NC}"

    # 기본값 설정
    echo -e "${CYAN}기본 환경 변수를 설정하시겠습니까? (y/n)${NC}"
    read -r response
    if [[ "$response" == "y" ]]; then
        # SECRET_KEY 생성
        SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
        sed -i.bak "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env

        # DATABASE_URL 설정
        echo -e "${CYAN}PostgreSQL 사용자명을 입력하세요 (기본값: $USER):${NC}"
        read -r db_user
        db_user=${db_user:-$USER}

        echo -e "${CYAN}데이터베이스 이름을 입력하세요 (기본값: odin_db):${NC}"
        read -r db_name
        db_name=${db_name:-odin_db}

        DATABASE_URL="postgresql://$db_user@localhost:5432/$db_name"
        sed -i.bak "s|DATABASE_URL=.*|DATABASE_URL=$DATABASE_URL|" .env

        echo -e "${GREEN}✅ 환경 변수 설정 완료${NC}"
    fi
else
    echo -e "${YELLOW}ℹ️  .env 파일이 이미 존재합니다.${NC}"
fi

# 필요한 디렉토리 생성
echo -e "\n${BLUE}📁 디렉토리 구조 생성 중...${NC}"
directories=(
    "logs"
    "storage/downloads"
    "storage/markdown"
    "reports"
    "batch/logs"
    "testing/reports"
)

for dir in "${directories[@]}"; do
    mkdir -p "$dir"
    echo -e "  ${GREEN}✓${NC} $dir"
done

# 데이터베이스 설정
echo -e "\n${BLUE}🗄  데이터베이스 설정${NC}"
echo -e "${CYAN}데이터베이스를 생성하시겠습니까? (y/n)${NC}"
read -r response
if [[ "$response" == "y" ]]; then
    source .env

    # 데이터베이스 존재 확인
    if psql -lqt | cut -d \| -f 1 | grep -qw odin_db; then
        echo -e "${YELLOW}ℹ️  odin_db 데이터베이스가 이미 존재합니다.${NC}"
    else
        createdb odin_db
        echo -e "${GREEN}✅ 데이터베이스 생성 완료${NC}"
    fi

    # 테이블 생성
    echo -e "${CYAN}테이블을 생성하시겠습니까? (y/n)${NC}"
    read -r response
    if [[ "$response" == "y" ]]; then
        python -c "
from src.database.connection import engine
from src.database.models import Base
Base.metadata.create_all(engine)
print('✅ 테이블 생성 완료')
"
    fi

    # 검색 인덱스 생성
    if [ -f "sql/search_indexes.sql" ]; then
        echo -e "${CYAN}검색 인덱스를 생성하시겠습니까? (y/n)${NC}"
        read -r response
        if [[ "$response" == "y" ]]; then
            psql -d odin_db -f sql/search_indexes.sql
            echo -e "${GREEN}✅ 검색 인덱스 생성 완료${NC}"
        fi
    fi
fi

# Git hooks 설정
echo -e "\n${BLUE}🔗 Git hooks 설정${NC}"
if [ -d ".git" ]; then
    # pre-commit hook
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Python linting
if command -v flake8 &> /dev/null; then
    flake8 . --exclude=venv,__pycache__
fi

# Frontend linting
cd frontend && npm run lint
EOF
    chmod +x .git/hooks/pre-commit
    echo -e "${GREEN}✅ Git hooks 설정 완료${NC}"
fi

# 실행 권한 설정
echo -e "\n${BLUE}🔐 실행 권한 설정 중...${NC}"
chmod +x run.sh
chmod +x batch/*.sh 2>/dev/null || true
echo -e "${GREEN}✅ 실행 권한 설정 완료${NC}"

# 설정 요약
echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ ODIN-AI 초기 설정이 완료되었습니다!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${WHITE}다음 단계:${NC}"
echo -e "1. ${YELLOW}.env${NC} 파일을 확인하고 필요한 API 키를 입력하세요."
echo -e "2. ${CYAN}./run.sh start${NC} 명령으로 애플리케이션을 시작하세요."
echo -e "3. ${CYAN}http://localhost:3000${NC}에서 프론트엔드에 접속하세요."
echo -e "4. ${CYAN}http://localhost:8000/docs${NC}에서 API 문서를 확인하세요."

echo -e "\n${CYAN}유용한 명령어:${NC}"
echo -e "  ./run.sh start    - 전체 시스템 시작"
echo -e "  ./run.sh dev      - 개발 모드 실행"
echo -e "  ./run.sh batch    - 배치 작업 실행"
echo -e "  ./run.sh status   - 시스템 상태 확인"
echo -e "  ./run.sh help     - 도움말 표시"

# 환경 변수 체크
echo -e "\n${YELLOW}⚠️  주의사항:${NC}"
if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
    echo -e "  - OpenAI API 키가 설정되지 않았습니다."
fi
if ! grep -q "DATA_SERVICE_KEY=" .env 2>/dev/null || grep -q "DATA_SERVICE_KEY=your_api_key" .env 2>/dev/null; then
    echo -e "  - 공공데이터포털 API 키가 설정되지 않았습니다."
fi

echo -e "\n${GREEN}준비가 완료되었습니다! 🚀${NC}"