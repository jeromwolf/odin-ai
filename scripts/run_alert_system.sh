#!/bin/bash

# ODIN-AI 알림 시스템 실행 스크립트
# 날짜 파라미터 지원 및 오류 처리

set -e  # 오류 발생시 즉시 중단

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 사용법 출력
usage() {
    echo -e "${BLUE}ODIN-AI 알림 시스템 실행${NC}"
    echo ""
    echo "사용법:"
    echo "  $0 [옵션] [날짜]"
    echo ""
    echo "옵션:"
    echo "  batch       배치 프로세스만 실행"
    echo "  alert       알림 서비스만 실행"
    echo "  both        배치 + 알림 모두 실행 (기본값)"
    echo "  test        테스트 실행"
    echo "  check       시스템 체크"
    echo ""
    echo "날짜:"
    echo "  YYYY-MM-DD  특정 날짜 (예: 2025-09-25)"
    echo "  (생략시 오늘 날짜 사용)"
    echo ""
    echo "예제:"
    echo "  $0                    # 오늘 날짜, 모든 프로세스"
    echo "  $0 batch              # 오늘 날짜, 배치만"
    echo "  $0 batch 2025-09-25   # 특정 날짜, 배치만"
    echo "  $0 both 2025-09-25    # 특정 날짜, 모든 프로세스"
    echo "  $0 test               # 시스템 테스트"
    echo "  $0 check              # 시스템 상태 체크"
}

# 시스템 체크
check_system() {
    echo -e "${BLUE}🔍 시스템 체크 시작${NC}"
    echo "================================"

    # 1. PostgreSQL 체크
    echo -n "PostgreSQL 연결... "
    if psql -U blockmeta -d odin_db -c "SELECT 1" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        echo -e "${RED}오류: PostgreSQL에 연결할 수 없습니다${NC}"
        exit 1
    fi

    # 2. Redis 체크
    echo -n "Redis 연결... "
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}⚠ Redis 미실행 (알림 서비스 제한)${NC}"
    fi

    # 3. 테이블 체크
    echo -n "알림 테이블... "
    TABLE_EXISTS=$(psql -U blockmeta -d odin_db -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alert_rules')")
    if [ "$TABLE_EXISTS" = "t" ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        echo -e "${YELLOW}테이블 생성 중...${NC}"
        psql -U blockmeta -d odin_db -f sql/create_alert_tables.sql
        echo -e "${GREEN}테이블 생성 완료${NC}"
    fi

    # 4. Python 패키지 체크
    echo -n "Python 패키지... "
    if python3 -c "import redis, sqlalchemy, jinja2" 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}⚠ 일부 패키지 누락${NC}"
        echo "  pip install redis sqlalchemy jinja2 loguru"
    fi

    echo "================================"
    echo -e "${GREEN}✓ 시스템 체크 완료${NC}"
}

# 배치 실행
run_batch() {
    local DATE=$1
    echo -e "${BLUE}📦 배치 프로세스 시작${NC}"

    if [ -n "$DATE" ]; then
        echo "날짜: $DATE"
        python3 batch/production_batch.py "$DATE"
    else
        echo "날짜: 오늘"
        python3 batch/production_batch.py
    fi

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 배치 완료${NC}"
    else
        echo -e "${RED}✗ 배치 실패${NC}"
        return 1
    fi
}

# 알림 서비스 실행
run_alert() {
    local DATE=$1
    echo -e "${BLUE}🔔 알림 서비스 시작${NC}"

    # Redis 체크
    if ! redis-cli ping > /dev/null 2>&1; then
        echo -e "${RED}오류: Redis가 실행되지 않았습니다${NC}"
        echo "Redis를 먼저 시작하세요: redis-server"
        return 1
    fi

    if [ -n "$DATE" ]; then
        echo "날짜: $DATE"
        python3 services/alert/main.py --date "$DATE"
    else
        echo "날짜: 오늘"
        python3 services/alert/main.py
    fi

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 알림 서비스 완료${NC}"
    else
        echo -e "${RED}✗ 알림 서비스 실패${NC}"
        return 1
    fi
}

# 테스트 실행
run_test() {
    echo -e "${BLUE}🧪 시스템 테스트${NC}"
    echo "================================"

    # 알림 시스템 테스트
    python3 test_alert_system.py

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 테스트 통과${NC}"
    else
        echo -e "${RED}✗ 테스트 실패${NC}"
        return 1
    fi
}

# 메인 로직
MODE=${1:-both}
DATE=$2

# 도움말 확인
if [ "$MODE" = "--help" ] || [ "$MODE" = "-h" ]; then
    usage
    exit 0
fi

# 시스템 체크
if [ "$MODE" = "check" ]; then
    check_system
    exit 0
fi

# 테스트 모드
if [ "$MODE" = "test" ]; then
    check_system
    run_test
    exit 0
fi

# 날짜 유효성 검사
if [ -n "$DATE" ]; then
    if ! date -j -f "%Y-%m-%d" "$DATE" > /dev/null 2>&1; then
        echo -e "${RED}오류: 잘못된 날짜 형식 ($DATE)${NC}"
        echo "올바른 형식: YYYY-MM-DD (예: 2025-09-25)"
        exit 1
    fi
fi

# 실행 모드
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ODIN-AI 알림 시스템${NC}"
echo -e "${GREEN}========================================${NC}"
echo "모드: $MODE"
echo "날짜: ${DATE:-오늘}"
echo ""

# 시스템 체크
check_system

case $MODE in
    batch)
        run_batch "$DATE"
        ;;
    alert)
        run_alert "$DATE"
        ;;
    both)
        # 배치 먼저 실행
        if run_batch "$DATE"; then
            echo ""
            echo "5초 후 알림 서비스 시작..."
            sleep 5
            run_alert "$DATE"
        else
            echo -e "${RED}배치 실패로 알림 서비스 스킵${NC}"
            exit 1
        fi
        ;;
    *)
        echo -e "${RED}오류: 알 수 없는 모드 ($MODE)${NC}"
        usage
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  작업 완료${NC}"
echo -e "${GREEN}========================================${NC}"