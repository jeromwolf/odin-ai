#!/bin/bash

# ODIN-AI 검색 기능 테스트 스크립트
# 모든 검색 관련 기능을 테스트합니다

set -e  # 에러 발생시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# API 엔드포인트
API_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"

# 테스트 성공/실패 카운터
PASSED=0
FAILED=0

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}       ODIN-AI 검색 기능 통합 테스트${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# 테스트 함수
test_api() {
    local endpoint=$1
    local description=$2
    local method=${3:-GET}
    local data=${4:-}

    echo -n "Testing: $description... "

    if [ "$method" == "GET" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL$endpoint")
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" -X $method -H "Content-Type: application/json" -d "$data" "$API_URL$endpoint")
    fi

    if [ "$response" == "200" ] || [ "$response" == "201" ]; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED (HTTP $response)${NC}"
        ((FAILED++))
        return 1
    fi
}

# 서비스 체크
check_service() {
    local service=$1
    local port=$2

    echo -n "Checking $service (port $port)... "
    if lsof -i:$port > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not running${NC}"
        return 1
    fi
}

echo -e "${YELLOW}1. 서비스 상태 확인${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_service "Backend API" 8000
check_service "Frontend" 3000
check_service "PostgreSQL" 5432
check_service "Redis" 6379 || echo -e "${YELLOW}  (Optional - for caching)${NC}"
echo

echo -e "${YELLOW}2. API 엔드포인트 테스트${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Health check
test_api "/health" "Health check endpoint"
test_api "/api/v1/search/health" "Search service health"

# 검색 API 테스트
test_api "/api/v1/search?query=건설" "Basic search query"
test_api "/api/v1/search?query=소프트웨어&type=bid" "Filtered search (bid only)"
test_api "/api/v1/search?query=SI사업&page=1&size=10" "Paginated search"
test_api "/api/v1/search?query=서버&sort=date_desc" "Sorted search (by date)"
test_api "/api/v1/search?query=네트워크&price_min=10000000&price_max=100000000" "Price range filter"

# 자동완성 테스트
test_api "/api/v1/search/suggestions?query=시스" "Search suggestions"
test_api "/api/v1/search/suggestions?query=건" "Short query suggestions"

# Facets 테스트
test_api "/api/v1/search/facets?type=all" "Get search facets"
test_api "/api/v1/search/facets?type=bid" "Get bid facets"

# 최근 검색어
test_api "/api/v1/search/recent" "Get recent searches"
echo

echo -e "${YELLOW}3. 데이터베이스 검증${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# PostgreSQL 연결 테스트
echo -n "Checking PostgreSQL connection... "
if psql -U blockmeta -d odin_db -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Connected${NC}"

    # 인덱스 확인
    echo -n "Checking search indexes... "
    index_count=$(psql -U blockmeta -d odin_db -t -c "SELECT COUNT(*) FROM pg_indexes WHERE tablename LIKE 'bid_%' AND indexname LIKE '%fts%'" 2>/dev/null | tr -d ' ')
    if [ "$index_count" -gt "0" ]; then
        echo -e "${GREEN}✓ $index_count FTS indexes found${NC}"
    else
        echo -e "${YELLOW}⚠ No FTS indexes found${NC}"
    fi

    # 데이터 확인
    echo -n "Checking bid data... "
    bid_count=$(psql -U blockmeta -d odin_db -t -c "SELECT COUNT(*) FROM bid_announcements" 2>/dev/null | tr -d ' ')
    echo -e "${BLUE}ℹ $bid_count bid announcements${NC}"
else
    echo -e "${RED}✗ Connection failed${NC}"
fi
echo

echo -e "${YELLOW}4. 캐시 성능 테스트${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 첫 번째 요청 (캐시 미스)
echo -n "First request (cache miss)... "
start_time=$(date +%s%N)
curl -s "$API_URL/api/v1/search?query=테스트" > /dev/null
end_time=$(date +%s%N)
first_time=$((($end_time - $start_time) / 1000000))
echo -e "${BLUE}${first_time}ms${NC}"

# 두 번째 요청 (캐시 히트)
echo -n "Second request (cache hit)... "
start_time=$(date +%s%N)
curl -s "$API_URL/api/v1/search?query=테스트" > /dev/null
end_time=$(date +%s%N)
second_time=$((($end_time - $start_time) / 1000000))
echo -e "${BLUE}${second_time}ms${NC}"

if [ $second_time -lt $first_time ]; then
    improvement=$((100 - (second_time * 100 / first_time)))
    echo -e "${GREEN}✓ Cache working (${improvement}% faster)${NC}"
else
    echo -e "${YELLOW}⚠ Cache may not be working${NC}"
fi
echo

echo -e "${YELLOW}5. 검색 품질 테스트${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 검색 결과 품질 확인
test_queries=("소프트웨어" "건설" "SI사업" "네트워크" "서버")

for query in "${test_queries[@]}"; do
    echo -n "Testing query '$query'... "
    result=$(curl -s "$API_URL/api/v1/search?query=$query" | grep -o '"totalCount":[0-9]*' | cut -d':' -f2)
    if [ ! -z "$result" ] && [ "$result" -gt "0" ]; then
        echo -e "${GREEN}✓ $result results${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ No results${NC}"
        ((FAILED++))
    fi
done
echo

echo -e "${YELLOW}6. 프론트엔드 통합 테스트${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 프론트엔드 접근 가능 확인
echo -n "Frontend accessibility... "
if curl -s -o /dev/null -w "%{http_code}" $FRONTEND_URL | grep -q "200\|304"; then
    echo -e "${GREEN}✓ Accessible${NC}"

    # 번들 사이즈 체크
    echo -n "Checking bundle size... "
    bundle_size=$(du -sh frontend/build 2>/dev/null | cut -f1)
    if [ ! -z "$bundle_size" ]; then
        echo -e "${BLUE}ℹ Bundle size: $bundle_size${NC}"
    else
        echo -e "${YELLOW}⚠ Build not found${NC}"
    fi
else
    echo -e "${RED}✗ Not accessible${NC}"
fi
echo

echo -e "${YELLOW}7. 에러 처리 테스트${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 잘못된 요청 테스트
test_api "/api/v1/search" "Empty query handling" GET || echo -e "${YELLOW}  (Expected behavior)${NC}"
test_api "/api/v1/search?query=" "Blank query handling" GET || echo -e "${YELLOW}  (Expected behavior)${NC}"
test_api "/api/v1/search?query=test&page=0" "Invalid page number" GET || echo -e "${YELLOW}  (Expected behavior)${NC}"
test_api "/api/v1/search?query=test&size=1000" "Large page size" GET
echo

# 결과 요약
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}                     테스트 결과 요약${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

TOTAL=$((PASSED + FAILED))
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ 모든 테스트 통과! ($PASSED/$TOTAL)${NC}"
    exit 0
else
    echo -e "${RED}✗ 일부 테스트 실패${NC}"
    echo -e "  ${GREEN}통과: $PASSED${NC}"
    echo -e "  ${RED}실패: $FAILED${NC}"
    echo -e "  성공률: $((PASSED * 100 / TOTAL))%"
    exit 1
fi