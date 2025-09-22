-- DBeaver에서 사용할 유용한 SQL 쿼리 모음

-- 1. 공고 목록 조회 (태그 포함)
SELECT
    a.bid_notice_no,
    a.title,
    a.organization_name,
    a.estimated_price,
    a.bid_end_date,
    STRING_AGG(t.tag_name, ', ') as tags
FROM bid_announcements a
LEFT JOIN bid_tag_relations tr ON a.bid_notice_no = tr.bid_notice_no
LEFT JOIN bid_tags t ON tr.tag_id = t.tag_id
GROUP BY a.bid_notice_no, a.title, a.organization_name, a.estimated_price, a.bid_end_date
ORDER BY a.created_at DESC;

-- 2. 태그별 공고 수
SELECT
    t.tag_name,
    t.tag_category,
    COUNT(tr.bid_notice_no) as announcement_count
FROM bid_tags t
LEFT JOIN bid_tag_relations tr ON t.tag_id = tr.tag_id
GROUP BY t.tag_name, t.tag_category
ORDER BY announcement_count DESC;

-- 3. 문서 처리 상태 확인
SELECT
    document_type,
    download_status,
    processing_status,
    COUNT(*) as count
FROM bid_documents
GROUP BY document_type, download_status, processing_status;

-- 4. 공고별 상세 정보 (특정 공고)
SELECT * FROM bid_announcements
WHERE bid_notice_no = '20240920-001';

-- 5. 검색 인덱스 확인
SELECT
    bid_notice_no,
    search_title,
    industry_category,
    region,
    price_range
FROM bid_search_index;

-- 6. 첨부파일 현황
SELECT
    a.bid_notice_no,
    ann.title,
    a.file_name,
    a.file_type,
    a.should_download,
    a.is_downloaded
FROM bid_attachments a
JOIN bid_announcements ann ON a.bid_notice_no = ann.bid_notice_no;

-- 7. 가격대별 공고 분포
SELECT
    CASE
        WHEN estimated_price < 100000000 THEN '1억 미만'
        WHEN estimated_price < 1000000000 THEN '1억-10억'
        WHEN estimated_price < 10000000000 THEN '10억-100억'
        ELSE '100억 이상'
    END as price_range,
    COUNT(*) as count,
    AVG(estimated_price) as avg_price
FROM bid_announcements
WHERE estimated_price IS NOT NULL
GROUP BY price_range
ORDER BY avg_price;

-- 8. 계약 방법별 통계
SELECT
    contract_method,
    COUNT(*) as count,
    AVG(estimated_price) as avg_price
FROM bid_announcements
WHERE contract_method IS NOT NULL
GROUP BY contract_method;

-- 9. 전체 테이블 레코드 수
SELECT
    'bid_announcements' as table_name, COUNT(*) as count FROM bid_announcements
UNION ALL
SELECT 'bid_documents', COUNT(*) FROM bid_documents
UNION ALL
SELECT 'bid_attachments', COUNT(*) FROM bid_attachments
UNION ALL
SELECT 'bid_tags', COUNT(*) FROM bid_tags
UNION ALL
SELECT 'bid_tag_relations', COUNT(*) FROM bid_tag_relations
UNION ALL
SELECT 'bid_search_index', COUNT(*) FROM bid_search_index;