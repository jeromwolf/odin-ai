#!/bin/bash

# Odin-AI Docker 관리 스크립트
# Usage: ./scripts/manage-docker.sh [command] [options]

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Docker 상태 확인
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker가 실행 중이지 않습니다. Docker Desktop을 시작해주세요."
        exit 1
    fi
}

# 서비스 시작
start_services() {
    local services=$1
    check_docker

    if [ -z "$services" ]; then
        log_info "모든 서비스를 시작합니다..."
        docker-compose -f "$COMPOSE_FILE" up -d
    else
        log_info "선택된 서비스를 시작합니다: $services"
        docker-compose -f "$COMPOSE_FILE" up -d $services
    fi

    log_info "서비스 상태:"
    docker-compose -f "$COMPOSE_FILE" ps
}

# 서비스 중지
stop_services() {
    local services=$1
    check_docker

    if [ -z "$services" ]; then
        log_info "모든 서비스를 중지합니다..."
        docker-compose -f "$COMPOSE_FILE" down
    else
        log_info "선택된 서비스를 중지합니다: $services"
        docker-compose -f "$COMPOSE_FILE" stop $services
    fi
}

# 서비스 재시작
restart_services() {
    local services=$1
    stop_services "$services"
    start_services "$services"
}

# 로그 보기
show_logs() {
    local service=$1
    local follow=$2

    check_docker

    if [ "$follow" == "-f" ] || [ "$follow" == "--follow" ]; then
        docker-compose -f "$COMPOSE_FILE" logs -f $service
    else
        docker-compose -f "$COMPOSE_FILE" logs --tail=50 $service
    fi
}

# 서비스 상태 확인
status() {
    check_docker

    echo "======================================="
    echo "         Docker 서비스 상태"
    echo "======================================="
    docker-compose -f "$COMPOSE_FILE" ps

    echo ""
    echo "======================================="
    echo "         네트워크 상태"
    echo "======================================="
    docker network ls | grep odin

    echo ""
    echo "======================================="
    echo "         볼륨 상태"
    echo "======================================="
    docker volume ls | grep odin
}

# 개발 환경 설정
setup_dev() {
    log_info "개발 환경을 설정합니다..."

    # 필수 디렉토리 생성
    mkdir -p "$PROJECT_ROOT/storage/downloads/"{hwp,pdf,doc,unknown}
    mkdir -p "$PROJECT_ROOT/storage/processed/"{hwp,pdf,doc,unknown}
    mkdir -p "$PROJECT_ROOT/logs"

    # 데이터베이스와 Redis만 먼저 시작
    log_info "데이터베이스 서비스 시작..."
    docker-compose -f "$COMPOSE_FILE" up -d postgres redis

    # 데이터베이스 준비 대기
    log_info "데이터베이스 초기화 대기 중..."
    sleep 10

    # 나머지 서비스 시작
    log_info "애플리케이션 서비스 시작..."
    docker-compose -f "$COMPOSE_FILE" up -d

    log_info "개발 환경 설정 완료!"
    status
}

# 데이터베이스 접속
connect_db() {
    check_docker
    log_info "PostgreSQL 데이터베이스에 접속합니다..."
    docker exec -it odin-ai-postgres psql -U odin_user -d odin_ai
}

# Redis CLI 접속
connect_redis() {
    check_docker
    log_info "Redis CLI에 접속합니다..."
    docker exec -it odin-ai-redis redis-cli
}

# 컨테이너 쉘 접속
shell() {
    local service=$1

    if [ -z "$service" ]; then
        log_error "서비스 이름을 지정해주세요."
        echo "예: ./scripts/manage-docker.sh shell backend"
        exit 1
    fi

    check_docker

    # 서비스 이름을 컨테이너 이름으로 매핑
    case "$service" in
        backend)
            container="odin-ai-backend"
            ;;
        worker)
            container="odin-ai-worker"
            ;;
        hwp-viewer)
            container="odin-hwp-viewer"
            ;;
        pdf-viewer)
            container="odin-pdf-viewer"
            ;;
        *)
            container="$service"
            ;;
    esac

    log_info "$container 컨테이너에 접속합니다..."
    docker exec -it "$container" /bin/bash
}

# 테스트 실행
run_tests() {
    check_docker
    log_info "테스트를 실행합니다..."

    # 테스트 환경 설정
    export TESTING=true
    export DATABASE_URL=postgresql://odin_user:odin_password@localhost:5432/odin_ai

    # Python 테스트 실행
    cd "$PROJECT_ROOT"
    source venv/bin/activate

    # 단위 테스트
    log_info "단위 테스트 실행..."
    pytest tests/unit/ -v

    # 통합 테스트
    log_info "통합 테스트 실행..."
    pytest tests/integration/ -v

    # 문서 처리 테스트
    log_info "문서 처리 테스트 실행..."
    python tests/test_document_processor.py

    log_info "테스트 완료!"
}

# 클린업
cleanup() {
    check_docker

    log_warning "모든 컨테이너, 볼륨, 네트워크를 삭제합니다. 계속하시겠습니까? (y/n)"
    read -r response

    if [ "$response" == "y" ]; then
        docker-compose -f "$COMPOSE_FILE" down -v
        rm -rf "$PROJECT_ROOT/storage/downloads/"*
        rm -rf "$PROJECT_ROOT/storage/processed/"*
        log_info "클린업 완료!"
    else
        log_info "작업이 취소되었습니다."
    fi
}

# 도움말
show_help() {
    cat << EOF
Odin-AI Docker 관리 스크립트

사용법: ./scripts/manage-docker.sh [명령] [옵션]

명령:
  start [서비스]     - 서비스 시작 (서비스 미지정시 전체 시작)
  stop [서비스]      - 서비스 중지 (서비스 미지정시 전체 중지)
  restart [서비스]   - 서비스 재시작
  status            - 모든 서비스 상태 확인
  logs [서비스] [-f] - 로그 확인 (-f: 실시간 추적)
  setup             - 개발 환경 초기 설정
  test              - 테스트 실행
  db                - PostgreSQL 데이터베이스 접속
  redis             - Redis CLI 접속
  shell [서비스]    - 컨테이너 쉘 접속
  cleanup           - 모든 Docker 리소스 정리
  help              - 도움말 표시

서비스 이름:
  postgres          - PostgreSQL 데이터베이스
  redis             - Redis 캐시
  backend           - Odin AI 백엔드 API
  worker            - Celery 워커
  hwp-viewer        - HWP 문서 처리 서비스
  pdf-viewer        - PDF 문서 처리 서비스
  flower            - Celery 모니터링

예제:
  ./scripts/manage-docker.sh start                    # 모든 서비스 시작
  ./scripts/manage-docker.sh start postgres redis     # DB만 시작
  ./scripts/manage-docker.sh logs backend -f          # 백엔드 로그 실시간 확인
  ./scripts/manage-docker.sh restart hwp-viewer       # HWP 서비스 재시작
  ./scripts/manage-docker.sh shell backend            # 백엔드 컨테이너 접속
  ./scripts/manage-docker.sh test                     # 테스트 실행
EOF
}

# 메인 실행
case "$1" in
    start)
        shift
        start_services "$@"
        ;;
    stop)
        shift
        stop_services "$@"
        ;;
    restart)
        shift
        restart_services "$@"
        ;;
    status)
        status
        ;;
    logs)
        shift
        show_logs "$@"
        ;;
    setup)
        setup_dev
        ;;
    test)
        run_tests
        ;;
    db)
        connect_db
        ;;
    redis)
        connect_redis
        ;;
    shell)
        shift
        shell "$@"
        ;;
    cleanup)
        cleanup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "알 수 없는 명령: $1"
        show_help
        exit 1
        ;;
esac