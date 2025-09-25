#!/bin/bash

# ODIN-AI 실시간 모니터링 대시보드

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

DB_NAME="odin_db"
DB_USER="blockmeta"
API_URL="http://localhost:8000"

# 화면 지우기 및 커서 숨기기
clear
tput civis

# 종료 시 커서 복원
trap 'tput cnorm; exit' INT TERM

while true; do
    clear

    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                     ODIN-AI 실시간 모니터링 대시보드                         ║${NC}"
    echo -e "${CYAN}║                    $(date '+%Y-%m-%d %H:%M:%S')                              ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}\n"

    # 1. 서비스 상태
    echo -e "${YELLOW}▶ 서비스 상태${NC}"
    echo "┌────────────────┬──────────┬────────────────────────────┐"

    # Backend API
    if curl -s -o /dev/null -w "%{http_code}" $API_URL/health | grep -q "200"; then
        api_status="${GREEN}● 정상${NC}"
        api_response=$(curl -s -o /dev/null -w "%{time_total}" $API_URL/health)
        api_time="${api_response}s"
    else
        api_status="${RED}● 오류${NC}"
        api_time="N/A"
    fi
    printf "│ Backend API    │ %-17s │ Response: %-16s │\n" "$api_status" "$api_time"

    # Frontend
    if lsof -i:3000 > /dev/null 2>&1; then
        frontend_status="${GREEN}● 실행중${NC}"
    else
        frontend_status="${YELLOW}● 중지됨${NC}"
    fi
    printf "│ Frontend       │ %-17s │ Port: 3000                 │\n" "$frontend_status"

    # PostgreSQL
    if psql -U $DB_USER -d $DB_NAME -c "SELECT 1" > /dev/null 2>&1; then
        pg_status="${GREEN}● 연결됨${NC}"
        pg_connections=$(psql -U $DB_USER -d $DB_NAME -t -c "SELECT count(*) FROM pg_stat_activity" 2>/dev/null | tr -d ' ')
        pg_info="Connections: $pg_connections"
    else
        pg_status="${RED}● 오류${NC}"
        pg_info="N/A"
    fi
    printf "│ PostgreSQL     │ %-17s │ %-26s │\n" "$pg_status" "$pg_info"

    # Redis
    if redis-cli ping > /dev/null 2>&1; then
        redis_status="${GREEN}● 실행중${NC}"
        redis_keys=$(redis-cli dbsize 2>/dev/null | cut -d' ' -f2)
        redis_info="Keys: $redis_keys"
    else
        redis_status="${YELLOW}● 중지됨${NC}"
        redis_info="Optional service"
    fi
    printf "│ Redis Cache    │ %-17s │ %-26s │\n" "$redis_status" "$redis_info"
    echo "└────────────────┴──────────┴────────────────────────────┘"

    # 2. 데이터베이스 통계
    echo -e "\n${YELLOW}▶ 데이터베이스 통계${NC}"
    echo "┌────────────────────────┬──────────────┬──────────────────┐"

    # 데이터 수집
    if [ "$pg_status" == "${GREEN}● 연결됨${NC}" ]; then
        bid_count=$(psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM bid_announcements" 2>/dev/null | tr -d ' ')
        doc_count=$(psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM bid_documents" 2>/dev/null | tr -d ' ')
        tag_count=$(psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(DISTINCT tag_id) FROM bid_tag_relations" 2>/dev/null | tr -d ' ')

        printf "│ 입찰공고              │ %12s │ Active records   │\n" "$bid_count"
        printf "│ 문서                  │ %12s │ Processed docs   │\n" "$doc_count"
        printf "│ 태그                  │ %12s │ Unique tags      │\n" "$tag_count"
    else
        echo "│ Database unavailable   │              │                  │"
    fi
    echo "└────────────────────────┴──────────────┴──────────────────┘"

    # 3. 검색 성능
    echo -e "\n${YELLOW}▶ 검색 성능 메트릭${NC}"
    echo "┌────────────────────────┬──────────────────────────────┐"

    if [ "$api_status" == "${GREEN}● 정상${NC}" ]; then
        # API 메트릭 가져오기
        metrics=$(curl -s $API_URL/api/v1/search/metrics 2>/dev/null || echo "{}")

        # 평균 응답시간
        avg_time=$(echo $metrics | grep -o '"avgResponseTime":[0-9]*' | cut -d: -f2)
        [ -z "$avg_time" ] && avg_time="N/A" || avg_time="${avg_time}ms"

        # 캐시 히트율
        cache_hit=$(echo $metrics | grep -o '"cacheHitRate":[0-9.]*' | cut -d: -f2)
        [ -z "$cache_hit" ] && cache_hit="N/A" || cache_hit="$(echo "scale=1; $cache_hit * 100" | bc)%"

        # 총 검색 수
        total_searches=$(echo $metrics | grep -o '"totalSearches":[0-9]*' | cut -d: -f2)
        [ -z "$total_searches" ] && total_searches="0"

        printf "│ 평균 응답시간         │ %-28s │\n" "$avg_time"
        printf "│ 캐시 히트율           │ %-28s │\n" "$cache_hit"
        printf "│ 총 검색 횟수          │ %-28s │\n" "$total_searches"
    else
        echo "│ Metrics unavailable    │                              │"
    fi
    echo "└────────────────────────┴──────────────────────────────┘"

    # 4. 시스템 리소스
    echo -e "\n${YELLOW}▶ 시스템 리소스${NC}"
    echo "┌────────────────────────┬──────────────────────────────┐"

    # CPU 사용률
    cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
    printf "│ CPU 사용률            │ %-28s │\n" "${cpu_usage}%"

    # 메모리 사용률
    mem_info=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
    mem_total=$(sysctl -n hw.memsize)
    mem_free=$((mem_info * 4096))
    mem_used=$((mem_total - mem_free))
    mem_percent=$((mem_used * 100 / mem_total))
    printf "│ 메모리 사용률         │ %-28s │\n" "${mem_percent}%"

    # 디스크 사용률
    disk_usage=$(df -h / | awk 'NR==2 {print $5}')
    printf "│ 디스크 사용률         │ %-28s │\n" "$disk_usage"
    echo "└────────────────────────┴──────────────────────────────┘"

    # 5. 최근 활동
    echo -e "\n${YELLOW}▶ 최근 활동${NC}"
    echo "┌──────────────────────────────────────────────────────┐"

    if [ "$pg_status" == "${GREEN}● 연결됨${NC}" ]; then
        # 최근 공고
        recent=$(psql -U $DB_USER -d $DB_NAME -t -c "
            SELECT '│ ' || TO_CHAR(created_at, 'HH24:MI:SS') || ' - 새 공고: ' ||
                   LEFT(title, 30) || '...' || REPEAT(' ', 15) || '│'
            FROM bid_announcements
            WHERE created_at > NOW() - INTERVAL '1 hour'
            ORDER BY created_at DESC
            LIMIT 3
        " 2>/dev/null)

        if [ ! -z "$recent" ]; then
            echo "$recent"
        else
            echo "│ 최근 1시간 내 활동 없음                              │"
        fi
    else
        echo "│ Database unavailable                                 │"
    fi
    echo "└──────────────────────────────────────────────────────┘"

    # 6. 알림
    echo -e "\n${YELLOW}▶ 시스템 알림${NC}"

    # 경고 체크
    warnings=""

    if [ "$mem_percent" -gt 80 ]; then
        warnings="${warnings}${YELLOW}⚠ 메모리 사용률 높음 (${mem_percent}%)${NC}\n"
    fi

    if [ "$pg_connections" -gt 50 ]; then
        warnings="${warnings}${YELLOW}⚠ DB 연결 수 많음 (${pg_connections})${NC}\n"
    fi

    if [ ! -z "$warnings" ]; then
        echo -e "$warnings"
    else
        echo -e "${GREEN}✓ 시스템 정상 작동중${NC}"
    fi

    echo -e "\n${CYAN}──────────────────────────────────────────────────────────${NC}"
    echo -e "${CYAN}[Ctrl+C to exit] | Refresh: 5s${NC}"

    # 5초 대기
    sleep 5
done