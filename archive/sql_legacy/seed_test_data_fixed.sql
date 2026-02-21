-- 테스트용 샘플 데이터 생성 (실제 스키마에 맞춰 수정)
-- 이 스크립트는 테스트를 위한 기본 데이터를 생성합니다

-- 1. 샘플 입찰 공고 데이터 삽입
INSERT INTO bid_announcements (
    bid_notice_no,
    title,
    organization_name,
    department_name,
    bid_method,
    contract_method,
    bid_start_date,
    bid_end_date,
    opening_date,
    estimated_price,
    status,
    created_at,
    updated_at
) VALUES
    ('20250001', '서울시 도로 공사', '서울특별시', '서울시청', '일반경쟁', '전자입찰',
     '2025-09-25 09:00:00', '2025-10-05 17:00:00', '2025-10-06 10:00:00',
     5000000000, 'active', NOW(), NOW()),

    ('20250002', '부산항 확장 공사', '부산광역시', '부산항만공사', '제한경쟁', '전자입찰',
     '2025-09-26 09:00:00', '2025-10-10 17:00:00', '2025-10-11 10:00:00',
     10000000000, 'active', NOW(), NOW()),

    ('20250003', 'IT 시스템 구축', '한국정보화진흥원', 'NIA', '협상에의한계약', '전자입찰',
     '2025-09-20 09:00:00', '2025-09-30 17:00:00', '2025-10-01 10:00:00',
     3000000000, 'active', NOW(), NOW()),

    ('20250004', '학교 급식 용역', '서울시교육청', '강남교육지원청', '일반경쟁', '전자입찰',
     '2025-09-15 09:00:00', '2025-09-25 17:00:00', '2025-09-26 10:00:00',
     1000000000, 'closed', NOW(), NOW()),

    ('20250005', '의료장비 구매', '서울대학교병원', '구매팀', '일반경쟁', '전자입찰',
     '2025-09-27 09:00:00', '2025-10-15 17:00:00', '2025-10-16 10:00:00',
     2000000000, 'active', NOW(), NOW())
ON CONFLICT (bid_notice_no) DO NOTHING;

-- 2. AI 추천을 위한 유사도 데이터
INSERT INTO bid_similarities (
    bid_notice_no_1,
    bid_notice_no_2,
    similarity_score,
    similarity_type,
    calculated_at
) VALUES
    ('20250001', '20250002', 0.85, 'content', NOW()),
    ('20250001', '20250004', 0.45, 'content', NOW()),
    ('20250002', '20250001', 0.85, 'content', NOW()),
    ('20250003', '20250005', 0.30, 'content', NOW())
ON CONFLICT DO NOTHING;

-- 데이터 확인
SELECT COUNT(*) as total_announcements FROM bid_announcements;
SELECT COUNT(*) as total_similarities FROM bid_similarities;