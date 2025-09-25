#!/bin/bash

# PostgreSQL 인덱스 검증 스크립트

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DB_NAME="odin_db"
DB_USER="blockmeta"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}                PostgreSQL 검색 인덱스 상태${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# PostgreSQL 연결 확인
echo -n "PostgreSQL 연결 확인... "
if psql -U $DB_USER -d $DB_NAME -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 연결됨${NC}\n"
else
    echo -e "${RED}✗ 연결 실패${NC}"
    exit 1
fi

# Full-text search 인덱스 확인
echo -e "${YELLOW}1. Full-text Search 인덱스:${NC}"
psql -U $DB_USER -d $DB_NAME -t << EOF | while read line; do
    if [ ! -z "$line" ]; then
        echo -e "  ${GREEN}✓${NC} $line"
    fi
done
SELECT indexname || ' (' || pg_size_pretty(pg_relation_size(indexname::regclass)) || ')'
FROM pg_indexes
WHERE tablename IN ('bid_announcements', 'bid_documents', 'bid_extracted_info')
AND indexname LIKE '%fts%'
ORDER BY indexname;
EOF

# B-tree 인덱스 확인
echo -e "\n${YELLOW}2. B-tree 인덱스 (검색 필터용):${NC}"
psql -U $DB_USER -d $DB_NAME -t << EOF | while read line; do
    if [ ! -z "$line" ]; then
        echo -e "  ${GREEN}✓${NC} $line"
    fi
done
SELECT indexname || ' (' || pg_size_pretty(pg_relation_size(indexname::regclass)) || ')'
FROM pg_indexes
WHERE tablename IN ('bid_announcements', 'bid_documents')
AND indexname LIKE '%idx%'
AND indexname NOT LIKE '%fts%'
ORDER BY indexname;
EOF

# 인덱스 사용률 확인
echo -e "\n${YELLOW}3. 인덱스 사용 통계:${NC}"
psql -U $DB_USER -d $DB_NAME << EOF
SELECT
    schemaname,
    tablename,
    indexrelname,
    idx_scan as scans,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
AND tablename IN ('bid_announcements', 'bid_documents', 'bid_extracted_info')
ORDER BY idx_scan DESC
LIMIT 10;
EOF

# 테이블 크기 확인
echo -e "\n${YELLOW}4. 테이블 크기:${NC}"
psql -U $DB_USER -d $DB_NAME << EOF
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as total_size,
    pg_size_pretty(pg_relation_size(tablename::regclass)) as table_size,
    pg_size_pretty(pg_total_relation_size(tablename::regclass) - pg_relation_size(tablename::regclass)) as index_size
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('bid_announcements', 'bid_documents', 'bid_extracted_info', 'bid_schedule', 'bid_tags')
ORDER BY pg_total_relation_size(tablename::regclass) DESC;
EOF

# 검색 쿼리 성능 테스트
echo -e "\n${YELLOW}5. 검색 쿼리 성능 테스트:${NC}"

echo -n "  • Full-text search 테스트... "
start=$(date +%s%N)
psql -U $DB_USER -d $DB_NAME -c "
    SELECT COUNT(*) FROM bid_announcements
    WHERE to_tsvector('simple', title) @@ to_tsquery('simple', '건설')
" > /dev/null 2>&1
end=$(date +%s%N)
time_ms=$(((end - start) / 1000000))
echo -e "${GREEN}${time_ms}ms${NC}"

echo -n "  • 날짜 범위 검색 테스트... "
start=$(date +%s%N)
psql -U $DB_USER -d $DB_NAME -c "
    SELECT COUNT(*) FROM bid_announcements
    WHERE announcement_date >= '2025-09-01' AND announcement_date <= '2025-09-30'
" > /dev/null 2>&1
end=$(date +%s%N)
time_ms=$(((end - start) / 1000000))
echo -e "${GREEN}${time_ms}ms${NC}"

echo -n "  • 복합 조건 검색 테스트... "
start=$(date +%s%N)
psql -U $DB_USER -d $DB_NAME -c "
    SELECT COUNT(*) FROM bid_announcements
    WHERE to_tsvector('simple', title) @@ to_tsquery('simple', 'SI')
    AND announcement_date >= '2025-09-01'
    AND expected_price > 10000000
" > /dev/null 2>&1
end=$(date +%s%N)
time_ms=$(((end - start) / 1000000))
echo -e "${GREEN}${time_ms}ms${NC}"

# 인덱스 추천
echo -e "\n${YELLOW}6. 인덱스 최적화 추천:${NC}"
missing_indexes=$(psql -U $DB_USER -d $DB_NAME -t -c "
    SELECT COUNT(*) FROM pg_stat_user_tables
    WHERE schemaname = 'public'
    AND n_tup_upd + n_tup_ins + n_tup_del > 1000
    AND seq_scan > idx_scan
" 2>/dev/null | tr -d ' ')

if [ "$missing_indexes" -gt "0" ]; then
    echo -e "  ${YELLOW}⚠ $missing_indexes 개 테이블에서 순차 스캔이 인덱스 스캔보다 많습니다${NC}"
    psql -U $DB_USER -d $DB_NAME -t << EOF
SELECT '    - ' || tablename || ' (seq_scan: ' || seq_scan || ', idx_scan: ' || idx_scan || ')'
FROM pg_stat_user_tables
WHERE schemaname = 'public'
AND n_tup_upd + n_tup_ins + n_tup_del > 1000
AND seq_scan > idx_scan;
EOF
else
    echo -e "  ${GREEN}✓ 모든 테이블이 효율적으로 인덱싱되어 있습니다${NC}"
fi

echo -e "\n${GREEN}✓ 인덱스 검증 완료${NC}"