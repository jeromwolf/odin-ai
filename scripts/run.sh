#!/bin/bash

# ====================================================
# ODIN-AI 통합 실행 스크립트
# Created: 2025-09-24
# Description: 전체 애플리케이션 실행 관리
# ====================================================

set -e  # 에러 발생 시 즉시 종료

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 로고 출력
print_logo() {
    echo -e "${CYAN}"
    cat << "EOF"
    ╔═══════════════════════════════════════╗
    ║         ODIN-AI Platform              ║
    ║     공공입찰 정보 분석 시스템         ║
    ╚═══════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# 도움말
show_help() {
    echo -e "${WHITE}사용법:${NC}"
    echo -e "  ${GREEN}./run.sh${NC} [command] [options]"
    echo ""
    echo -e "${WHITE}명령어:${NC}"
    echo -e "  ${YELLOW}start${NC}      전체 시스템 시작"
    echo -e "  ${YELLOW}stop${NC}       전체 시스템 중지"
    echo -e "  ${YELLOW}restart${NC}    전체 시스템 재시작"
    echo -e "  ${YELLOW}status${NC}     시스템 상태 확인"
    echo -e "  ${YELLOW}dev${NC}        개발 모드 실행"
    echo -e "  ${YELLOW}prod${NC}       프로덕션 모드 실행"
    echo -e "  ${YELLOW}batch${NC}      배치 작업 실행"
    echo -e "  ${YELLOW}test${NC}       테스트 실행"
    echo -e "  ${YELLOW}setup${NC}      초기 설정"
    echo -e "  ${YELLOW}clean${NC}      클린업"
    echo -e "  ${YELLOW}logs${NC}       로그 확인"
    echo -e "  ${YELLOW}help${NC}       도움말 표시"
    echo ""
    echo -e "${WHITE}옵션:${NC}"
    echo -e "  ${CYAN}--frontend${NC}  프론트엔드만 실행"
    echo -e "  ${CYAN}--backend${NC}   백엔드만 실행"
    echo -e "  ${CYAN}--db${NC}        데이터베이스만 실행"
    echo -e "  ${CYAN}--redis${NC}     Redis만 실행"
    echo -e "  ${CYAN}--all${NC}       모든 서비스 실행 (기본값)"
    echo ""
    echo -e "${WHITE}예제:${NC}"
    echo -e "  ./run.sh start            # 전체 시스템 시작"
    echo -e "  ./run.sh dev --frontend   # 프론트엔드 개발 서버만"
    echo -e "  ./run.sh batch            # 배치 작업 실행"
    echo -e "  ./run.sh logs --backend   # 백엔드 로그 확인"
}

# 환경 변수 체크
check_env() {
    echo -e "${BLUE}🔍 환경 설정 확인 중...${NC}"

    if [ ! -f .env ]; then
        echo -e "${YELLOW}⚠️  .env 파일이 없습니다.${NC}"
        echo -e "${CYAN}📝 .env.example을 복사하여 .env 파일을 생성합니다...${NC}"
        cp .env.example .env
        echo -e "${GREEN}✅ .env 파일 생성 완료${NC}"
        echo -e "${YELLOW}⚠️  .env 파일을 편집하여 필요한 설정을 입력하세요.${NC}"
        exit 1
    fi

    # 환경 변수 로드
    export $(cat .env | grep -v '^#' | xargs)

    # 필수 환경 변수 체크
    if [ -z "$DATABASE_URL" ]; then
        echo -e "${RED}❌ DATABASE_URL이 설정되지 않았습니다.${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ 환경 설정 확인 완료${NC}"
}

# PostgreSQL 체크 및 시작
check_postgres() {
    echo -e "${BLUE}🔍 PostgreSQL 상태 확인 중...${NC}"

    if command -v pg_isready &> /dev/null; then
        if pg_isready -q; then
            echo -e "${GREEN}✅ PostgreSQL 실행 중${NC}"
        else
            echo -e "${YELLOW}⚠️  PostgreSQL이 실행되지 않았습니다.${NC}"
            echo -e "${CYAN}🚀 PostgreSQL 시작 중...${NC}"

            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                brew services start postgresql@15 2>/dev/null || brew services start postgresql 2>/dev/null
            elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
                # Linux
                sudo systemctl start postgresql
            fi

            sleep 3

            if pg_isready -q; then
                echo -e "${GREEN}✅ PostgreSQL 시작 완료${NC}"
            else
                echo -e "${RED}❌ PostgreSQL 시작 실패${NC}"
                exit 1
            fi
        fi
    else
        echo -e "${YELLOW}⚠️  pg_isready 명령을 찾을 수 없습니다.${NC}"
    fi
}

# Redis 체크 및 시작
check_redis() {
    echo -e "${BLUE}🔍 Redis 상태 확인 중...${NC}"

    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✅ Redis 실행 중${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis가 실행되지 않았습니다.${NC}"
        echo -e "${CYAN}🚀 Redis 시작 중...${NC}"

        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            brew services start redis 2>/dev/null
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            sudo systemctl start redis
        fi

        sleep 2

        if redis-cli ping &> /dev/null; then
            echo -e "${GREEN}✅ Redis 시작 완료${NC}"
        else
            echo -e "${YELLOW}⚠️  Redis를 시작할 수 없습니다. (선택사항)${NC}"
        fi
    fi
}

# Python 가상환경 체크
check_venv() {
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}⚠️  Python 가상환경이 없습니다.${NC}"
        echo -e "${CYAN}🔧 가상환경 생성 중...${NC}"
        python3 -m venv venv
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        echo -e "${GREEN}✅ 가상환경 생성 완료${NC}"
    else
        source venv/bin/activate
        echo -e "${GREEN}✅ Python 가상환경 활성화${NC}"
    fi
}

# Node modules 체크
check_node_modules() {
    if [ ! -d "frontend/node_modules" ]; then
        echo -e "${YELLOW}⚠️  Node modules가 설치되지 않았습니다.${NC}"
        echo -e "${CYAN}📦 패키지 설치 중...${NC}"
        cd frontend
        npm install
        cd ..
        echo -e "${GREEN}✅ Node modules 설치 완료${NC}"
    else
        echo -e "${GREEN}✅ Node modules 확인 완료${NC}"
    fi
}

# 백엔드 시작
start_backend() {
    echo -e "${CYAN}🚀 백엔드 서버 시작 중...${NC}"

    check_venv

    # 백엔드 프로세스 확인
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}⚠️  포트 8000이 이미 사용 중입니다.${NC}"
        return
    fi

    # 백엔드 시작 (백그라운드)
    nohup python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
    echo $! > .backend.pid

    sleep 3

    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${GREEN}✅ 백엔드 서버 시작 완료 (http://localhost:8000)${NC}"
        echo -e "${CYAN}📚 API 문서: http://localhost:8000/docs${NC}"
    else
        echo -e "${RED}❌ 백엔드 서버 시작 실패${NC}"
        exit 1
    fi
}

# 프론트엔드 시작
start_frontend() {
    echo -e "${CYAN}🚀 프론트엔드 서버 시작 중...${NC}"

    check_node_modules

    # 프론트엔드 프로세스 확인
    if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}⚠️  포트 3000이 이미 사용 중입니다.${NC}"
        return
    fi

    # 프론트엔드 시작 (백그라운드)
    cd frontend
    nohup npm start > ../logs/frontend.log 2>&1 &
    echo $! > ../.frontend.pid
    cd ..

    sleep 5

    if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${GREEN}✅ 프론트엔드 서버 시작 완료 (http://localhost:3000)${NC}"
    else
        echo -e "${RED}❌ 프론트엔드 서버 시작 실패${NC}"
        exit 1
    fi
}

# 전체 시스템 시작
start_all() {
    print_logo
    echo -e "${MAGENTA}🚀 ODIN-AI 시스템 시작${NC}"
    echo "================================"

    check_env
    check_postgres
    check_redis

    # 로그 디렉토리 생성
    mkdir -p logs

    start_backend
    start_frontend

    echo "================================"
    echo -e "${GREEN}✅ 모든 서비스가 시작되었습니다!${NC}"
    echo ""
    echo -e "${WHITE}접속 URL:${NC}"
    echo -e "  프론트엔드: ${CYAN}http://localhost:3000${NC}"
    echo -e "  백엔드 API: ${CYAN}http://localhost:8000${NC}"
    echo -e "  API 문서:   ${CYAN}http://localhost:8000/docs${NC}"
    echo ""
    echo -e "${YELLOW}종료하려면 './run.sh stop'을 실행하세요.${NC}"
}

# 시스템 중지
stop_all() {
    echo -e "${MAGENTA}🛑 ODIN-AI 시스템 중지${NC}"
    echo "================================"

    # 백엔드 중지
    if [ -f .backend.pid ]; then
        PID=$(cat .backend.pid)
        if kill -0 $PID 2>/dev/null; then
            echo -e "${CYAN}백엔드 서버 중지 중...${NC}"
            kill $PID
            rm .backend.pid
            echo -e "${GREEN}✅ 백엔드 서버 중지됨${NC}"
        else
            rm .backend.pid
        fi
    fi

    # 프론트엔드 중지
    if [ -f .frontend.pid ]; then
        PID=$(cat .frontend.pid)
        if kill -0 $PID 2>/dev/null; then
            echo -e "${CYAN}프론트엔드 서버 중지 중...${NC}"
            kill $PID
            rm .frontend.pid
            echo -e "${GREEN}✅ 프론트엔드 서버 중지됨${NC}"
        else
            rm .frontend.pid
        fi
    fi

    # 포트 확인 및 강제 종료
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}포트 8000 프로세스 강제 종료...${NC}"
        lsof -ti:8000 | xargs kill -9 2>/dev/null
    fi

    if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}포트 3000 프로세스 강제 종료...${NC}"
        lsof -ti:3000 | xargs kill -9 2>/dev/null
    fi

    echo "================================"
    echo -e "${GREEN}✅ 모든 서비스가 중지되었습니다.${NC}"
}

# 시스템 상태 확인
check_status() {
    print_logo
    echo -e "${MAGENTA}📊 시스템 상태${NC}"
    echo "================================"

    # PostgreSQL 상태
    if command -v pg_isready &> /dev/null && pg_isready -q; then
        echo -e "PostgreSQL:  ${GREEN}● 실행 중${NC}"
    else
        echo -e "PostgreSQL:  ${RED}○ 중지됨${NC}"
    fi

    # Redis 상태
    if redis-cli ping &> /dev/null; then
        echo -e "Redis:       ${GREEN}● 실행 중${NC}"
    else
        echo -e "Redis:       ${YELLOW}○ 중지됨 (선택)${NC}"
    fi

    # 백엔드 상태
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "백엔드:      ${GREEN}● 실행 중${NC} (http://localhost:8000)"
    else
        echo -e "백엔드:      ${RED}○ 중지됨${NC}"
    fi

    # 프론트엔드 상태
    if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "프론트엔드:  ${GREEN}● 실행 중${NC} (http://localhost:3000)"
    else
        echo -e "프론트엔드:  ${RED}○ 중지됨${NC}"
    fi

    echo "================================"
}

# 개발 모드
dev_mode() {
    print_logo
    echo -e "${MAGENTA}👨‍💻 개발 모드${NC}"
    echo "================================"

    check_env
    check_postgres
    check_redis

    # 로그 디렉토리 생성
    mkdir -p logs

    echo -e "${CYAN}개발 서버를 시작합니다...${NC}"
    echo -e "${YELLOW}Ctrl+C를 눌러 종료할 수 있습니다.${NC}"
    echo ""

    # tmux 또는 screen이 있으면 사용
    if command -v tmux &> /dev/null; then
        echo -e "${CYAN}tmux 세션을 시작합니다...${NC}"
        tmux new-session -d -s odin-backend 'source venv/bin/activate && python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000'
        tmux new-session -d -s odin-frontend 'cd frontend && npm start'
        echo -e "${GREEN}✅ tmux 세션 시작 완료${NC}"
        echo -e "${YELLOW}백엔드 로그: tmux attach -t odin-backend${NC}"
        echo -e "${YELLOW}프론트엔드 로그: tmux attach -t odin-frontend${NC}"
    else
        # 병렬 실행
        check_venv
        check_node_modules

        (
            trap 'kill 0' SIGINT
            python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
            cd frontend && npm start &
            wait
        )
    fi
}

# 배치 실행
run_batch() {
    print_logo
    echo -e "${MAGENTA}📦 배치 작업 실행${NC}"
    echo "================================"

    check_env
    check_postgres
    check_venv

    echo -e "${CYAN}배치 작업을 시작합니다...${NC}"

    # 배치 옵션 확인
    if [ "$2" == "--test" ]; then
        echo -e "${YELLOW}테스트 모드로 실행합니다.${NC}"
        export TEST_MODE=true
    fi

    if [ "$2" == "--init" ]; then
        echo -e "${YELLOW}DB 초기화 모드로 실행합니다.${NC}"
        export DB_FILE_INIT=true
    fi

    # 배치 실행
    python batch/production_batch.py

    echo -e "${GREEN}✅ 배치 작업 완료${NC}"
}

# 테스트 실행
run_tests() {
    echo -e "${MAGENTA}🧪 테스트 실행${NC}"
    echo "================================"

    check_venv

    echo -e "${CYAN}백엔드 테스트 실행 중...${NC}"
    pytest tests/ -v

    echo -e "${CYAN}프론트엔드 테스트 실행 중...${NC}"
    cd frontend
    npm test -- --watchAll=false
    cd ..

    echo -e "${GREEN}✅ 테스트 완료${NC}"
}

# 로그 확인
show_logs() {
    if [ "$2" == "--backend" ]; then
        echo -e "${CYAN}백엔드 로그:${NC}"
        tail -f logs/backend.log
    elif [ "$2" == "--frontend" ]; then
        echo -e "${CYAN}프론트엔드 로그:${NC}"
        tail -f logs/frontend.log
    else
        echo -e "${CYAN}모든 로그:${NC}"
        tail -f logs/*.log
    fi
}

# 초기 설정
setup() {
    print_logo
    echo -e "${MAGENTA}🔧 초기 설정${NC}"
    echo "================================"

    # Python 가상환경 생성
    echo -e "${CYAN}Python 가상환경 생성 중...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt

    # Node modules 설치
    echo -e "${CYAN}Node modules 설치 중...${NC}"
    cd frontend
    npm install
    cd ..

    # .env 파일 생성
    if [ ! -f .env ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠️  .env 파일을 편집하여 설정을 완료하세요.${NC}"
    fi

    # 디렉토리 생성
    mkdir -p logs
    mkdir -p storage/downloads
    mkdir -p storage/markdown
    mkdir -p reports

    echo -e "${GREEN}✅ 초기 설정 완료${NC}"
}

# 클린업
cleanup() {
    echo -e "${MAGENTA}🧹 클린업${NC}"
    echo "================================"

    echo -e "${CYAN}캐시 및 임시 파일 삭제 중...${NC}"

    # Python 캐시 삭제
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true

    # Node 캐시 삭제
    rm -rf frontend/node_modules/.cache 2>/dev/null || true

    # 로그 파일 정리
    if [ "$2" == "--logs" ]; then
        rm -rf logs/*.log
        echo -e "${GREEN}✅ 로그 파일 삭제됨${NC}"
    fi

    echo -e "${GREEN}✅ 클린업 완료${NC}"
}

# 메인 실행 로직
case "$1" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        sleep 2
        start_all
        ;;
    status)
        check_status
        ;;
    dev)
        dev_mode
        ;;
    batch)
        run_batch "$@"
        ;;
    test)
        run_tests
        ;;
    setup)
        setup
        ;;
    clean|cleanup)
        cleanup "$@"
        ;;
    logs)
        show_logs "$@"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_logo
        if [ -n "$1" ]; then
            echo -e "${RED}❌ 알 수 없는 명령: $1${NC}"
            echo ""
        fi
        show_help
        exit 1
        ;;
esac