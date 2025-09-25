#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# 현재 날짜
TODAY=$(date +"%Y-%m-%d")

echo -e "${PURPLE}=========================================="
echo -e "🚀 ODIN-AI 배치 실행 및 모니터링"
echo -e "==========================================${NC}"
echo ""

# 배치 프로그램 실행 함수
run_batch() {
    echo -e "${BLUE}📦 배치 프로그램을 시작합니다...${NC}"
    echo -e "${YELLOW}실행 시간: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo ""

    # 로그 파일 이름 생성
    LOG_FILE="logs/batch_${TODAY}_$(date +%H%M%S).log"

    # 배치 실행 (백그라운드)
    DB_FILE_INIT=false TEST_MODE=false DATABASE_URL="postgresql://blockmeta@localhost:5432/odin_db" \
        python batch/production_batch.py > "$LOG_FILE" 2>&1 &

    BATCH_PID=$!
    echo -e "${GREEN}✅ 배치 프로세스 시작됨 (PID: $BATCH_PID)${NC}"
    echo -e "${GREEN}📄 로그 파일: $LOG_FILE${NC}"
    echo ""

    # 실시간 모니터링
    monitor_batch "$LOG_FILE" "$BATCH_PID"
}

# 모니터링 함수
monitor_batch() {
    local log_file=$1
    local pid=$2

    echo -e "${BLUE}📊 실시간 모니터링 시작...${NC}"
    echo -e "종료하려면 Ctrl+C를 누르세요 (배치는 계속 실행됩니다)"
    echo ""
    echo -e "${YELLOW}──────────────────────────────────────────${NC}"

    # 진행 상황 추적 변수들
    last_phase=""
    collected=0
    downloaded=0
    processed=0
    errors=0

    # 실시간 로그 모니터링
    while kill -0 $pid 2>/dev/null; do
        if [ -f "$log_file" ]; then
            # Phase 변경 감지
            current_phase=$(grep "Phase" "$log_file" | tail -1)
            if [ "$current_phase" != "$last_phase" ]; then
                echo -e "\n${PURPLE}📌 $current_phase${NC}"
                last_phase="$current_phase"
            fi

            # 통계 업데이트
            collected=$(grep "신규 저장" "$log_file" 2>/dev/null | wc -l | tr -d ' ')
            downloaded=$(grep "다운로드 성공" "$log_file" 2>/dev/null | wc -l | tr -d ' ')
            processed=$(grep "처리 성공" "$log_file" 2>/dev/null | wc -l | tr -d ' ')
            errors=$(grep -E "ERROR|실패|❌" "$log_file" 2>/dev/null | wc -l | tr -d ' ')

            # 상태바 표시
            printf "\r${GREEN}수집: %d${NC} | ${BLUE}다운로드: %d${NC} | ${PURPLE}처리: %d${NC} | ${RED}오류: %d${NC}" \
                   "$collected" "$downloaded" "$processed" "$errors"

            # 최신 로그 메시지 표시 (중요한 것만)
            tail -1 "$log_file" | grep -E "완료|성공|실패|ERROR" | while read line; do
                echo -e "\n${YELLOW}└─${NC} $line"
            done
        fi

        sleep 2
    done

    echo -e "\n\n${GREEN}✅ 배치 프로그램 완료!${NC}"
    echo -e "${YELLOW}──────────────────────────────────────────${NC}"

    # 최종 결과 표시
    show_summary "$log_file"
}

# 요약 정보 표시
show_summary() {
    local log_file=$1

    echo -e "\n${PURPLE}📊 실행 결과 요약${NC}"
    echo -e "${YELLOW}──────────────────────────────────────────${NC}"

    # 최종 통계
    if [ -f "$log_file" ]; then
        echo -e "${GREEN}✅ 성공 통계:${NC}"
        grep "수집 완료" "$log_file" | tail -1
        grep "다운로드 완료" "$log_file" | tail -1
        grep "처리 완료" "$log_file" | tail -1

        # 오류가 있으면 표시
        error_count=$(grep -E "ERROR|실패" "$log_file" | wc -l | tr -d ' ')
        if [ "$error_count" -gt 0 ]; then
            echo -e "\n${RED}⚠️  오류 발생: $error_count 건${NC}"
            echo -e "${RED}오류 상세:${NC}"
            grep -E "ERROR|실패" "$log_file" | head -5
        fi
    fi

    # DB 상태 확인
    echo -e "\n${BLUE}💾 데이터베이스 현황:${NC}"
    python3 -c "
from sqlalchemy import create_engine, text
try:
    engine = create_engine('postgresql://blockmeta@localhost:5432/odin_db')
    with engine.connect() as conn:
        announcements = conn.execute(text('SELECT COUNT(*) FROM bid_announcements')).scalar()
        documents = conn.execute(text('SELECT COUNT(*) FROM bid_documents')).scalar()
        extracted = conn.execute(text('SELECT COUNT(*) FROM bid_extracted_info')).scalar()
        print(f'  • 공고: {announcements}개')
        print(f'  • 문서: {documents}개')
        print(f'  • 추출정보: {extracted}개')
except Exception as e:
    print(f'  DB 연결 오류: {e}')
"

    echo -e "\n${GREEN}로그 파일: $log_file${NC}"
}

# 메인 메뉴
show_menu() {
    echo -e "${BLUE}선택하세요:${NC}"
    echo "1) 배치 프로그램 실행 및 모니터링"
    echo "2) 최근 로그 확인"
    echo "3) DB 상태만 확인"
    echo "4) 종료"
    echo -n "선택 [1-4]: "
    read choice

    case $choice in
        1)
            run_batch
            ;;
        2)
            echo -e "${BLUE}최근 로그 파일:${NC}"
            ls -lt logs/batch_*.log 2>/dev/null | head -5
            echo ""
            echo -n "확인할 로그 파일명 입력 (전체 경로): "
            read logfile
            if [ -f "$logfile" ]; then
                show_summary "$logfile"
            else
                echo -e "${RED}파일을 찾을 수 없습니다: $logfile${NC}"
            fi
            ;;
        3)
            show_summary ""
            ;;
        4)
            echo -e "${GREEN}종료합니다.${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}잘못된 선택입니다.${NC}"
            ;;
    esac
}

# 스크립트 시작
if [ "$1" == "--run" ]; then
    # 직접 실행 모드
    run_batch
else
    # 메뉴 모드
    show_menu
fi