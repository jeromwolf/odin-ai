#!/bin/bash

# Redis 캐시 검증 스크립트

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}                    Redis 캐시 상태 확인${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# Redis 실행 확인
echo -n "1. Redis 서버 상태... "
if pgrep -x "redis-server" > /dev/null; then
    echo -e "${GREEN}✓ 실행중${NC}"
else
    echo -e "${RED}✗ 실행되지 않음${NC}"
    echo -e "${YELLOW}   Redis 시작: redis-server${NC}"
    exit 1
fi

# Redis 연결 테스트
echo -n "2. Redis 연결 테스트... "
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 연결 성공${NC}"
else
    echo -e "${RED}✗ 연결 실패${NC}"
    exit 1
fi

# Redis 메모리 사용량
echo -n "3. 메모리 사용량... "
memory=$(redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
echo -e "${BLUE}$memory${NC}"

# 캐시 키 수
echo -n "4. 저장된 캐시 키... "
key_count=$(redis-cli dbsize | cut -d' ' -f2)
echo -e "${BLUE}$key_count 개${NC}"

# 검색 캐시 키 확인
echo -n "5. 검색 캐시 키... "
search_keys=$(redis-cli keys "search:*" 2>/dev/null | wc -l)
echo -e "${BLUE}$search_keys 개${NC}"

# 최근 캐시 항목 표시
echo -e "\n${YELLOW}최근 캐시된 검색어:${NC}"
redis-cli keys "search:*" 2>/dev/null | head -5 | while read key; do
    query=$(echo $key | sed 's/search://')
    ttl=$(redis-cli ttl "$key" 2>/dev/null)
    echo -e "  • $query (TTL: ${ttl}초)"
done

# 캐시 통계
echo -e "\n${YELLOW}캐시 통계:${NC}"
hits=$(redis-cli info stats | grep keyspace_hits | cut -d: -f2 | tr -d '\r')
misses=$(redis-cli info stats | grep keyspace_misses | cut -d: -f2 | tr -d '\r')

if [ ! -z "$hits" ] && [ ! -z "$misses" ]; then
    total=$((hits + misses))
    if [ $total -gt 0 ]; then
        hit_rate=$((hits * 100 / total))
        echo -e "  • 캐시 히트: ${GREEN}$hits${NC}"
        echo -e "  • 캐시 미스: ${YELLOW}$misses${NC}"
        echo -e "  • 히트율: ${BLUE}${hit_rate}%${NC}"
    else
        echo -e "  ${YELLOW}아직 캐시 사용 기록 없음${NC}"
    fi
fi

echo -e "\n${GREEN}✓ Redis 캐시가 정상적으로 작동중입니다${NC}"