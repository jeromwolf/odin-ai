#!/bin/bash

# Docker Compose 관리 스크립트

set -e

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 사용법
usage() {
    echo -e "${BLUE}Docker Compose 관리${NC}"
    echo ""
    echo "사용법: $0 [명령]"
    echo ""
    echo "명령어:"
    echo "  up        전체 시스템 시작"
    echo "  down      전체 시스템 중지"
    echo "  restart   재시작"
    echo "  logs      로그 보기"
    echo "  status    상태 확인"
    echo "  build     이미지 빌드"
    echo "  init      초기 설정"
    echo ""
    echo "개별 서비스:"
    echo "  batch     배치만 실행"
    echo "  alert     알림만 실행"
    echo "  web       웹만 실행"
}

# 초기 설정
init_setup() {
    echo -e "${BLUE}🔧 초기 설정 시작${NC}"

    # .env 파일 생성
    if [ ! -f .env ]; then
        echo "환경변수 파일 생성..."
        cp .env.example .env
        echo -e "${YELLOW}⚠️ .env 파일을 수정하세요${NC}"
    fi

    # 디렉토리 생성
    mkdir -p storage/{documents,markdown}
    mkdir -p logs/{batch,alert}

    # 권한 설정
    chmod -R 755 storage logs

    echo -e "${GREEN}✅ 초기 설정 완료${NC}"
}

# 시스템 시작
start_system() {
    echo -e "${BLUE}🚀 시스템 시작${NC}"
    docker-compose up -d
    echo -e "${GREEN}✅ 시스템 시작 완료${NC}"

    echo ""
    echo "접속 정보:"
    echo "  - Web API: http://localhost:8000"
    echo "  - Frontend: http://localhost:3000"
    echo "  - pgAdmin: http://localhost:5050 (profile: tools)"
    echo "  - Monitor: http://localhost:8080 (profile: monitoring)"
}

# 시스템 중지
stop_system() {
    echo -e "${BLUE}🛑 시스템 중지${NC}"
    docker-compose down
    echo -e "${GREEN}✅ 시스템 중지 완료${NC}"
}

# 상태 확인
check_status() {
    echo -e "${BLUE}📊 시스템 상태${NC}"
    docker-compose ps

    echo ""
    echo -e "${BLUE}🔍 헬스체크${NC}"

    # PostgreSQL
    echo -n "PostgreSQL: "
    if docker-compose exec -T postgres pg_isready > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
    fi

    # Redis
    echo -n "Redis: "
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
    fi

    # Web
    echo -n "Web API: "
    if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
    fi
}

# 로그 보기
view_logs() {
    SERVICE=$1
    if [ -z "$SERVICE" ]; then
        docker-compose logs -f --tail=100
    else
        docker-compose logs -f --tail=100 $SERVICE
    fi
}

# 빌드
build_images() {
    echo -e "${BLUE}🔨 이미지 빌드${NC}"
    docker-compose build
    echo -e "${GREEN}✅ 빌드 완료${NC}"
}

# 메인 로직
case "$1" in
    up)
        init_setup
        start_system
        ;;
    down)
        stop_system
        ;;
    restart)
        stop_system
        sleep 2
        start_system
        ;;
    logs)
        view_logs $2
        ;;
    status)
        check_status
        ;;
    build)
        build_images
        ;;
    init)
        init_setup
        ;;
    batch)
        docker-compose up -d batch
        ;;
    alert)
        docker-compose up -d alert
        ;;
    web)
        docker-compose up -d web
        ;;
    *)
        usage
        exit 1
        ;;
esac