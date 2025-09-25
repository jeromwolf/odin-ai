-- 테스트용 샘플 데이터 생성
-- 이 스크립트는 테스트를 위한 기본 데이터를 생성합니다

-- 1. 샘플 입찰 공고 데이터 삽입
INSERT INTO bid_announcements (
    bid_notice_no,
    title,
    organization,
    demand_agency,
    contract_method,
    input_method,
    bid_qualify,
    bid_start_date,
    bid_close_date,
    open_date,
    delivery_date,
    delivery_place,
    estimated_price,
    status,
    created_at,
    updated_at
) VALUES
    ('20250001', '서울시 도로 공사', '서울특별시', '서울시청', '일반경쟁', '전자입찰',
     '건설업 등록', '2025-09-25 09:00:00', '2025-10-05 17:00:00', '2025-10-06 10:00:00',
     '2025-12-31', '서울시 강남구', 5000000000, 'active', NOW(), NOW()),

    ('20250002', '부산항 확장 공사', '부산광역시', '부산항만공사', '제한경쟁', '전자입찰',
     '토목건축공사업', '2025-09-26 09:00:00', '2025-10-10 17:00:00', '2025-10-11 10:00:00',
     '2026-03-31', '부산시 남구', 10000000000, 'active', NOW(), NOW()),

    ('20250003', 'IT 시스템 구축', '한국정보화진흥원', 'NIA', '협상에의한계약', '전자입찰',
     'SW개발업', '2025-09-20 09:00:00', '2025-09-30 17:00:00', '2025-10-01 10:00:00',
     '2025-12-31', '서울시 중구', 3000000000, 'active', NOW(), NOW()),

    ('20250004', '학교 급식 용역', '서울시교육청', '강남교육지원청', '일반경쟁', '전자입찰',
     '급식업 등록', '2025-09-15 09:00:00', '2025-09-25 17:00:00', '2025-09-26 10:00:00',
     '2025-12-31', '서울시 강남구', 1000000000, 'closed', NOW(), NOW()),

    ('20250005', '의료장비 구매', '서울대학교병원', '구매팀', '일반경쟁', '전자입찰',
     '의료기기 판매업', '2025-09-27 09:00:00', '2025-10-15 17:00:00', '2025-10-16 10:00:00',
     '2025-11-30', '서울시 종로구', 2000000000, 'active', NOW(), NOW())
ON CONFLICT (bid_notice_no) DO NOTHING;

-- 2. 샘플 문서 데이터 삽입
INSERT INTO bid_documents (
    bid_notice_no,
    document_type,
    file_name,
    file_url,
    download_status,
    storage_path,
    processing_status,
    created_at
) VALUES
    ('20250001', 'announcement', '공고문_20250001.hwp',
     'http://example.com/files/20250001.hwp', 'completed',
     '/storage/downloads/20250001.hwp', 'completed', NOW()),

    ('20250002', 'announcement', '공고문_20250002.pdf',
     'http://example.com/files/20250002.pdf', 'completed',
     '/storage/downloads/20250002.pdf', 'completed', NOW()),

    ('20250003', 'specification', '제안요청서_20250003.hwp',
     'http://example.com/files/20250003.hwp', 'completed',
     '/storage/downloads/20250003.hwp', 'completed', NOW())
ON CONFLICT (bid_notice_no, file_name) DO NOTHING;

-- 3. 샘플 추출 정보 데이터
INSERT INTO bid_extracted_info (
    bid_notice_no,
    extracted_data,
    confidence_score,
    extraction_timestamp
) VALUES
    ('20250001', '{"prices": ["5,000,000,000원"], "schedule": ["입찰마감: 2025-10-05"], "qualifications": ["건설업 등록"]}', 0.95, NOW()),
    ('20250002', '{"prices": ["10,000,000,000원"], "schedule": ["입찰마감: 2025-10-10"], "qualifications": ["토목건축공사업"]}', 0.92, NOW()),
    ('20250003', '{"prices": ["3,000,000,000원"], "schedule": ["입찰마감: 2025-09-30"], "qualifications": ["SW개발업"]}', 0.88, NOW())
ON CONFLICT (bid_notice_no) DO NOTHING;

-- 4. 샘플 태그 데이터
INSERT INTO bid_tags (tag_name, category, created_at) VALUES
    ('건설', 'industry', NOW()),
    ('IT', 'industry', NOW()),
    ('의료', 'industry', NOW()),
    ('서울', 'region', NOW()),
    ('부산', 'region', NOW())
ON CONFLICT (tag_name) DO NOTHING;

-- 5. 태그 관계 설정
INSERT INTO bid_tag_relations (bid_notice_no, tag_id)
SELECT '20250001', id FROM bid_tags WHERE tag_name = '건설'
ON CONFLICT DO NOTHING;

INSERT INTO bid_tag_relations (bid_notice_no, tag_id)
SELECT '20250001', id FROM bid_tags WHERE tag_name = '서울'
ON CONFLICT DO NOTHING;

INSERT INTO bid_tag_relations (bid_notice_no, tag_id)
SELECT '20250002', id FROM bid_tags WHERE tag_name = '건설'
ON CONFLICT DO NOTHING;

INSERT INTO bid_tag_relations (bid_notice_no, tag_id)
SELECT '20250002', id FROM bid_tags WHERE tag_name = '부산'
ON CONFLICT DO NOTHING;

INSERT INTO bid_tag_relations (bid_notice_no, tag_id)
SELECT '20250003', id FROM bid_tags WHERE tag_name = 'IT'
ON CONFLICT DO NOTHING;

-- 6. 테스트 사용자 데이터 (이미 auth API로 생성되므로 참고용)
-- INSERT INTO users (email, username, password_hash, full_name, is_active, created_at)
-- VALUES
--     ('test@example.com', 'testuser', '$2b$12$...', 'Test User', true, NOW()),
--     ('admin@example.com', 'admin', '$2b$12$...', 'Admin User', true, NOW())
-- ON CONFLICT (email) DO NOTHING;

-- 7. AI 추천을 위한 유사도 데이터
INSERT INTO bid_similarities (
    source_bid_no,
    target_bid_no,
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
SELECT COUNT(*) as total_documents FROM bid_documents;
SELECT COUNT(*) as total_tags FROM bid_tags;