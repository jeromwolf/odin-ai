-- ============================================
-- ODIN-AI 온톨로지 시드 데이터
-- 공공입찰 도메인 50+ 개념 계층 구조
-- ============================================
-- 생성일: 2026-02-21
-- 대상 테이블: ontology_concepts, ontology_relations
-- 선행 조건: create_ontology_tables.sql 실행 완료
-- ============================================
--
-- 계층 구조 요약:
--   Level 0: 입찰공고 (root) ..................... 1개
--   Level 1: 공사, 용역, 물품 .................... 3개
--   Level 2: 건축공사, 토목공사, IT/SW개발 등 .... 20개
--   Level 3: 신축공사, 도로공사, 웹개발 등 ....... 26개
--   합계: 50개 개념
--
-- 관계(ontology_relations): 15개 cross-category 관계
-- ============================================


BEGIN;

-- ============================================
-- 기존 시드 데이터 정리 (재실행 안전)
-- ============================================
DELETE FROM ontology_relations;
DELETE FROM bid_ontology_mappings;
DELETE FROM ontology_concepts;

-- 시퀀스 리셋
ALTER SEQUENCE ontology_concepts_id_seq RESTART WITH 1;
ALTER SEQUENCE ontology_relations_id_seq RESTART WITH 1;


-- ============================================
-- LEVEL 0: ROOT
-- ============================================
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '입찰공고',
    'bid_announcement',
    NULL,
    0,
    '공공입찰 도메인 최상위 개념. 모든 공사/용역/물품 입찰공고의 루트 노드.',
    ARRAY['입찰', '공고', '조달', '발주', '나라장터'],
    ARRAY['입찰공고', '조달공고', '발주공고', '공공입찰'],
    0
);


-- ============================================
-- LEVEL 1: 대분류 (공사, 용역, 물품)
-- ============================================

-- 1-1. 공사
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '공사',
    'construction',
    (SELECT id FROM ontology_concepts WHERE concept_name = '입찰공고'),
    1,
    '건설, 토목, 전기, 기계 등 물리적 시설물의 시공 및 설치를 포함하는 대분류.',
    ARRAY['공사', '시공', '건설', '설치', '축조'],
    ARRAY['건설공사', '시공공사', '설치공사'],
    1
);

-- 1-2. 용역
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '용역',
    'service',
    (SELECT id FROM ontology_concepts WHERE concept_name = '입찰공고'),
    1,
    'IT 개발, 컨설팅, 연구, 설계, 감리 등 전문 서비스 제공을 포함하는 대분류.',
    ARRAY['용역', '서비스', '컨설팅', '연구'],
    ARRAY['용역사업', '서비스사업', '전문용역'],
    2
);

-- 1-3. 물품
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '물품',
    'goods',
    (SELECT id FROM ontology_concepts WHERE concept_name = '입찰공고'),
    1,
    'IT 장비, 사무용품, 의료기기, 차량 등 유형 재화의 구매/납품을 포함하는 대분류.',
    ARRAY['물품', '구매', '납품', '조달', '공급'],
    ARRAY['물품구매', '물품조달', '물자'],
    3
);


-- ============================================
-- LEVEL 2: 중분류 - 공사 하위
-- ============================================

-- 2-1. 건축공사
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '건축공사',
    'building_construction',
    (SELECT id FROM ontology_concepts WHERE concept_name = '공사'),
    2,
    '건물의 신축, 증축, 리모델링, 실내건축, 철거 등을 포함하는 건축 분야 공사.',
    ARRAY['건축', '건물', '빌딩', '아파트', '주택'],
    ARRAY['건축시공', '건물공사', '건물시공'],
    1
);

-- 2-2. 토목공사
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '토목공사',
    'civil_engineering',
    (SELECT id FROM ontology_concepts WHERE concept_name = '공사'),
    2,
    '도로, 교량, 터널, 하천, 상하수도 등 사회기반시설 건설을 포함하는 토목 분야 공사.',
    ARRAY['토목', '토공', '지반'],
    ARRAY['토목시공', '토목건설', '기반시설공사'],
    2
);

-- 2-3. 조경공사
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '조경공사',
    'landscaping',
    (SELECT id FROM ontology_concepts WHERE concept_name = '공사'),
    2,
    '공원, 녹지, 식재, 정원 조성 등 조경 분야 공사.',
    ARRAY['조경', '녹지', '공원', '식재', '잔디', '수목', '정원'],
    ARRAY['조경시공', '녹화공사', '공원조성'],
    3
);

-- 2-4. 전기공사
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '전기공사',
    'electrical_construction',
    (SELECT id FROM ontology_concepts WHERE concept_name = '공사'),
    2,
    '전력설비, 조명, 태양광 등 전기 분야 공사.',
    ARRAY['전기', '전력', '배전', '수전', '변전', '조명', '발전'],
    ARRAY['전기시공', '전기설비공사', '전력공사'],
    4
);

-- 2-5. 통신공사
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '통신공사',
    'telecommunications',
    (SELECT id FROM ontology_concepts WHERE concept_name = '공사'),
    2,
    '정보통신, 네트워크, 광케이블, CCTV 등 통신 분야 공사.',
    ARRAY['통신', '정보통신', 'ICT', '네트워크', '광케이블', 'CCTV'],
    ARRAY['통신시공', '정보통신공사', 'ICT공사'],
    5
);

-- 2-6. 기계설비공사
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '기계설비공사',
    'mechanical_construction',
    (SELECT id FROM ontology_concepts WHERE concept_name = '공사'),
    2,
    '냉난방, 소방, 승강기, 배관 등 기계설비 분야 공사.',
    ARRAY['기계', '설비', '냉난방', 'HVAC', '배관', '펌프', '공조'],
    ARRAY['기계시공', '설비공사', '기계설비시공'],
    6
);

-- 2-7. 포장공사
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '포장공사',
    'paving_construction',
    (SELECT id FROM ontology_concepts WHERE concept_name = '공사'),
    2,
    '아스콘, 콘크리트 포장 등 도로/보도 포장 분야 공사.',
    ARRAY['포장', '아스콘', '콘크리트포장', '보차도'],
    ARRAY['포장시공', '도로포장공사', '노면포장'],
    7
);


-- ============================================
-- LEVEL 2: 중분류 - 용역 하위
-- ============================================

-- 2-8. IT/SW개발
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    'IT/SW개발',
    'it_sw_development',
    (SELECT id FROM ontology_concepts WHERE concept_name = '용역'),
    2,
    '소프트웨어 개발, 시스템 구축, 웹/앱 개발, AI/빅데이터, 클라우드 인프라 등 IT 분야 용역.',
    ARRAY['소프트웨어', 'SW', 'IT', '개발', '프로그램', '시스템'],
    ARRAY['IT개발', 'SW개발', '소프트웨어개발', '정보시스템개발', 'SI'],
    1
);

-- 2-9. 컨설팅
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '컨설팅',
    'consulting',
    (SELECT id FROM ontology_concepts WHERE concept_name = '용역'),
    2,
    '경영, 기술, 정책 등 전문 분야 자문 및 진단 용역.',
    ARRAY['컨설팅', '자문', '진단', '평가', '분석'],
    ARRAY['자문용역', '진단용역', '평가용역', '전문상담'],
    2
);

-- 2-10. 연구용역
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '연구용역',
    'research',
    (SELECT id FROM ontology_concepts WHERE concept_name = '용역'),
    2,
    '학술 연구, 정책 연구, 기초 조사 등 연구 분야 용역.',
    ARRAY['연구', '조사', '분석', '학술', '기획'],
    ARRAY['연구사업', '학술용역', '조사연구', '기초연구'],
    3
);

-- 2-11. 유지보수
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '유지보수',
    'maintenance',
    (SELECT id FROM ontology_concepts WHERE concept_name = '용역'),
    2,
    '시설, 소프트웨어, 장비의 유지관리, 운영, 점검 등 유지보수 분야 용역.',
    ARRAY['유지보수', '유지관리', '운영', '점검', '보전'],
    ARRAY['유지보수용역', '운영관리', '관리용역'],
    4
);

-- 2-12. 설계용역
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '설계용역',
    'design_service',
    (SELECT id FROM ontology_concepts WHERE concept_name = '용역'),
    2,
    '건축설계, 토목설계, 기본설계, 실시설계, 타당성조사 등 설계 분야 용역.',
    ARRAY['설계', '기본설계', '실시설계', '타당성'],
    ARRAY['설계사업', '설계업무', '기본계획'],
    5
);

-- 2-13. 감리용역
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '감리용역',
    'supervision',
    (SELECT id FROM ontology_concepts WHERE concept_name = '용역'),
    2,
    '시공감리, 책임감리, 건설사업관리 등 감리/감독 분야 용역.',
    ARRAY['감리', '감독', '시공감리', '책임감리'],
    ARRAY['감리업무', '건설사업관리', 'CM', '감독업무'],
    6
);

-- 2-14. 교육/훈련
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '교육/훈련',
    'education_training',
    (SELECT id FROM ontology_concepts WHERE concept_name = '용역'),
    2,
    '직원 교육, 기술 훈련, 연수, 워크숍, 세미나 등 교육 분야 용역.',
    ARRAY['교육', '훈련', '연수', '워크샵', '세미나'],
    ARRAY['교육사업', '훈련용역', '연수사업', '역량강화'],
    7
);


-- ============================================
-- LEVEL 2: 중분류 - 물품 하위
-- ============================================

-- 2-15. IT장비
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    'IT장비',
    'it_equipment',
    (SELECT id FROM ontology_concepts WHERE concept_name = '물품'),
    2,
    '컴퓨터, 서버, 네트워크 장비, 모니터, 프린터 등 IT 분야 물품.',
    ARRAY['컴퓨터', 'PC', '서버', '네트워크장비', '모니터', '프린터'],
    ARRAY['IT장비구매', '전산장비', '정보화장비'],
    1
);

-- 2-16. 사무용품
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '사무용품',
    'office_supplies',
    (SELECT id FROM ontology_concepts WHERE concept_name = '물품'),
    2,
    '가구, 비품, 문구, 소모품 등 사무용 물품.',
    ARRAY['사무', '가구', '비품', '문구', '소모품'],
    ARRAY['사무용품구매', '사무가구', '사무비품'],
    2
);

-- 2-17. 의료기기
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '의료기기',
    'medical_equipment',
    (SELECT id FROM ontology_concepts WHERE concept_name = '물품'),
    2,
    '의료장비, 의약품, 진단기기, 치료기기 등 의료 분야 물품.',
    ARRAY['의료', '의약', '의료기기', '진단', '치료'],
    ARRAY['의료장비구매', '의약품조달', '의료물품'],
    3
);

-- 2-18. 차량/운송
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '차량/운송',
    'vehicles_transport',
    (SELECT id FROM ontology_concepts WHERE concept_name = '물품'),
    2,
    '차량, 트럭, 버스, 특수차량 등 운송 관련 물품.',
    ARRAY['차량', '자동차', '트럭', '버스', '운송'],
    ARRAY['차량구매', '차량조달', '운송장비'],
    4
);

-- 2-19. 식품/급식
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '식품/급식',
    'food_catering',
    (SELECT id FROM ontology_concepts WHERE concept_name = '물품'),
    2,
    '식품, 식자재, 급식 등 식품 관련 물품.',
    ARRAY['식품', '급식', '식자재', '식재료', '음식'],
    ARRAY['식품구매', '급식재료', '식자재조달'],
    5
);

-- 2-20. 보안장비
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '보안장비',
    'security_equipment',
    (SELECT id FROM ontology_concepts WHERE concept_name = '물품'),
    2,
    'CCTV, 출입통제, 방범, 경비 장비 등 보안 관련 물품.',
    ARRAY['보안', 'CCTV', '출입통제', '방범', '경비'],
    ARRAY['보안장비구매', '방범장비', '보안시스템물품'],
    6
);


-- ============================================
-- LEVEL 3: 소분류 - 건축공사 하위
-- ============================================

-- 3-1. 신축공사
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '신축공사',
    'new_building',
    (SELECT id FROM ontology_concepts WHERE concept_name = '건축공사'),
    3,
    '새 건물의 신설 공사.',
    ARRAY['신축', '신설', '새건물'],
    ARRAY['건물신축', '신축시공', '건물신설'],
    1
);

-- 3-2. 증축공사
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '증축공사',
    'building_extension',
    (SELECT id FROM ontology_concepts WHERE concept_name = '건축공사'),
    3,
    '기존 건물의 확장 또는 증설 공사.',
    ARRAY['증축', '확장', '증설'],
    ARRAY['건물증축', '시설확장', '증축시공'],
    2
);

-- 3-3. 리모델링
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '리모델링',
    'remodeling',
    (SELECT id FROM ontology_concepts WHERE concept_name = '건축공사'),
    3,
    '기존 건물의 개보수, 수선, 개선 공사.',
    ARRAY['리모델링', '개보수', '보수', '수선', '개선'],
    ARRAY['건물리모델링', '시설개보수', '건물보수', '수리공사'],
    3
);

-- 3-4. 실내건축
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '실내건축',
    'interior_construction',
    (SELECT id FROM ontology_concepts WHERE concept_name = '건축공사'),
    3,
    '실내 인테리어, 내장, 내부 마감 공사.',
    ARRAY['실내', '인테리어', '내장', '내부'],
    ARRAY['실내건축공사', '인테리어공사', '내장공사', '실내마감'],
    4
);

-- 3-5. 철거공사
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '철거공사',
    'demolition',
    (SELECT id FROM ontology_concepts WHERE concept_name = '건축공사'),
    3,
    '기존 건물의 철거, 해체, 멸실 공사.',
    ARRAY['철거', '해체', '멸실'],
    ARRAY['건물철거', '해체공사', '구조물철거'],
    5
);


-- ============================================
-- LEVEL 3: 소분류 - 토목공사 하위
-- ============================================

-- 3-6. 도로공사
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '도로공사',
    'road_construction',
    (SELECT id FROM ontology_concepts WHERE concept_name = '토목공사'),
    3,
    '도로 신설, 확장, 포장, 노면 보수 등 도로 관련 공사.',
    ARRAY['도로', '포장', '아스팔트', '노면', '차도', '보도'],
    ARRAY['도로건설', '도로시공', '노면공사', '도로개설'],
    1
);

-- 3-7. 교량공사
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '교량공사',
    'bridge_construction',
    (SELECT id FROM ontology_concepts WHERE concept_name = '토목공사'),
    3,
    '교량, 육교, 고가도로 등 교량 관련 공사.',
    ARRAY['교량', '다리', '육교', '고가'],
    ARRAY['교량건설', '교량시공', '다리공사', '고가도로공사'],
    2
);

-- 3-8. 터널공사
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '터널공사',
    'tunnel_construction',
    (SELECT id FROM ontology_concepts WHERE concept_name = '토목공사'),
    3,
    '터널, 지하도, 갱도 등 지하 구조물 공사.',
    ARRAY['터널', '지하도', '갱도'],
    ARRAY['터널건설', '터널시공', '지하도공사', '굴착공사'],
    3
);

-- 3-9. 하천공사
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '하천공사',
    'river_construction',
    (SELECT id FROM ontology_concepts WHERE concept_name = '토목공사'),
    3,
    '하천 정비, 배수, 수로, 제방, 호안 등 하천 관련 공사.',
    ARRAY['하천', '하수', '배수', '수로', '제방', '호안'],
    ARRAY['하천정비', '하천시공', '배수공사', '제방공사'],
    4
);

-- 3-10. 상수도공사
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '상수도공사',
    'water_supply',
    (SELECT id FROM ontology_concepts WHERE concept_name = '토목공사'),
    3,
    '상수도, 급수, 취수, 정수, 배수지 등 상수 관련 공사.',
    ARRAY['상수도', '급수', '취수', '정수', '배수지'],
    ARRAY['상수도시공', '급수공사', '정수시설공사'],
    5
);

-- 3-11. 하수도공사
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '하수도공사',
    'sewerage',
    (SELECT id FROM ontology_concepts WHERE concept_name = '토목공사'),
    3,
    '하수도, 오수, 우수, 맨홀, 관로 등 하수 관련 공사.',
    ARRAY['하수도', '오수', '우수', '맨홀', '관로'],
    ARRAY['하수도시공', '하수관로공사', '오수처리공사'],
    6
);


-- ============================================
-- LEVEL 3: 소분류 - 전기공사 하위
-- ============================================

-- 3-12. 전력설비
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '전력설비',
    'power_facilities',
    (SELECT id FROM ontology_concepts WHERE concept_name = '전기공사'),
    3,
    '고압/저압 전력설비, 변압기, 차단기 등 전력 인프라 공사.',
    ARRAY['전력', '고압', '저압', '변압기', '차단기'],
    ARRAY['전력설비공사', '수변전설비', '전력인프라'],
    1
);

-- 3-13. 조명공사
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '조명공사',
    'lighting',
    (SELECT id FROM ontology_concepts WHERE concept_name = '전기공사'),
    3,
    '가로등, LED 조명, 등기구 설치 등 조명 관련 공사.',
    ARRAY['조명', '가로등', 'LED', '등기구'],
    ARRAY['조명설비공사', 'LED공사', '가로등공사', '조명시공'],
    2
);

-- 3-14. 태양광
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '태양광',
    'solar_power',
    (SELECT id FROM ontology_concepts WHERE concept_name = '전기공사'),
    3,
    '태양광, 태양열, 신재생에너지 설비 공사.',
    ARRAY['태양광', '태양열', '신재생', '솔라'],
    ARRAY['태양광발전', '태양광설비', '신재생에너지공사', '솔라패널'],
    3
);


-- ============================================
-- LEVEL 3: 소분류 - 기계설비공사 하위
-- ============================================

-- 3-15. 냉난방설비
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '냉난방설비',
    'hvac',
    (SELECT id FROM ontology_concepts WHERE concept_name = '기계설비공사'),
    3,
    '냉방, 난방, 보일러, 에어컨, 히트펌프 등 냉난방 설비 공사.',
    ARRAY['냉방', '난방', '보일러', '에어컨', '히트펌프'],
    ARRAY['냉난방공사', 'HVAC공사', '공조설비', '냉난방시공'],
    1
);

-- 3-16. 소방설비
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '소방설비',
    'fire_protection',
    (SELECT id FROM ontology_concepts WHERE concept_name = '기계설비공사'),
    3,
    '소방, 소화, 스프링클러, 화재경보 등 소방 설비 공사.',
    ARRAY['소방', '소화', '스프링클러', '화재', '경보'],
    ARRAY['소방설비공사', '소화설비', '화재경보공사', '소방시공'],
    2
);

-- 3-17. 승강기
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '승강기',
    'elevator',
    (SELECT id FROM ontology_concepts WHERE concept_name = '기계설비공사'),
    3,
    '엘리베이터, 에스컬레이터, 리프트 등 승강 설비 공사.',
    ARRAY['승강기', '엘리베이터', '에스컬레이터', '리프트'],
    ARRAY['승강기공사', '엘리베이터설치', '승강설비'],
    3
);


-- ============================================
-- LEVEL 3: 소분류 - IT/SW개발 하위
-- ============================================

-- 3-18. 웹개발
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '웹개발',
    'web_development',
    (SELECT id FROM ontology_concepts WHERE concept_name = 'IT/SW개발'),
    3,
    '웹사이트, 홈페이지, 포털 시스템 구축 용역.',
    ARRAY['웹', '홈페이지', '포털', '웹사이트'],
    ARRAY['웹개발용역', '홈페이지구축', '포털개발', '웹시스템'],
    1
);

-- 3-19. 앱개발
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '앱개발',
    'app_development',
    (SELECT id FROM ontology_concepts WHERE concept_name = 'IT/SW개발'),
    3,
    '모바일 앱, 어플리케이션 개발 용역.',
    ARRAY['앱', '모바일', '어플', '애플리케이션'],
    ARRAY['앱개발용역', '모바일개발', '어플개발', '모바일앱'],
    2
);

-- 3-20. AI/빅데이터
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    'AI/빅데이터',
    'ai_bigdata',
    (SELECT id FROM ontology_concepts WHERE concept_name = 'IT/SW개발'),
    3,
    '인공지능, 빅데이터, 머신러닝, 딥러닝 관련 개발 용역.',
    ARRAY['AI', '인공지능', '빅데이터', '머신러닝', '딥러닝'],
    ARRAY['AI개발', '인공지능개발', '빅데이터분석', '데이터사이언스'],
    3
);

-- 3-21. 클라우드/인프라
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '클라우드/인프라',
    'cloud_infrastructure',
    (SELECT id FROM ontology_concepts WHERE concept_name = 'IT/SW개발'),
    3,
    '클라우드 서비스, 서버 인프라, IDC, 데이터센터 구축 용역.',
    ARRAY['클라우드', '서버', '인프라', 'IDC', '데이터센터'],
    ARRAY['클라우드구축', '인프라구축', 'IaaS', 'PaaS', 'SaaS'],
    4
);


-- ============================================
-- LEVEL 3: 소분류 - 유지보수 하위
-- ============================================

-- 3-22. 시설유지보수
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '시설유지보수',
    'facility_maintenance',
    (SELECT id FROM ontology_concepts WHERE concept_name = '유지보수'),
    3,
    '건물관리, 청소, 경비 등 시설 유지관리 용역.',
    ARRAY['시설', '건물관리', '청소', '경비'],
    ARRAY['시설관리', '건물유지보수', '시설운영', 'FM'],
    1
);

-- 3-23. SW유지보수
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    'SW유지보수',
    'sw_maintenance',
    (SELECT id FROM ontology_concepts WHERE concept_name = '유지보수'),
    3,
    '소프트웨어 유지보수, 시스템 운영, SM 등 IT 유지관리 용역.',
    ARRAY['SW유지보수', '시스템운영', 'SM', '운영관리'],
    ARRAY['소프트웨어유지보수', '시스템유지보수', 'IT운영', '정보시스템운영'],
    2
);

-- 3-24. 장비유지보수
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '장비유지보수',
    'equipment_maintenance',
    (SELECT id FROM ontology_concepts WHERE concept_name = '유지보수'),
    3,
    '장비, 기기 수리, 정비 등 장비 유지관리 용역.',
    ARRAY['장비', '기기', '수리', '정비'],
    ARRAY['장비수리', '기기정비', '장비관리', '설비정비'],
    3
);


-- ============================================
-- LEVEL 3: 소분류 - 설계용역 하위
-- ============================================

-- 3-25. 건축설계
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '건축설계',
    'architectural_design',
    (SELECT id FROM ontology_concepts WHERE concept_name = '설계용역'),
    3,
    '건축물 설계, 건축사 설계, 설계도면 작성 용역.',
    ARRAY['건축설계', '건축사', '설계도'],
    ARRAY['건축설계용역', '건물설계', '건축도면'],
    1
);

-- 3-26. 토목설계
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '토목설계',
    'civil_design',
    (SELECT id FROM ontology_concepts WHERE concept_name = '설계용역'),
    3,
    '토목 설계, 측량, 지질조사 등 토목 분야 설계 용역.',
    ARRAY['토목설계', '측량', '지질조사'],
    ARRAY['토목설계용역', '측량설계', '지질조사용역', '기반시설설계'],
    2
);


-- ============================================
-- CROSS-CATEGORY RELATIONS (ontology_relations)
-- 비계층적 관계: relatedTo, requires, similarTo
-- ============================================

-- R1. 건축공사 relatedTo 건축설계 (weight: 0.8)
INSERT INTO ontology_relations (source_concept_id, target_concept_id, relation_type, weight, description)
VALUES (
    (SELECT id FROM ontology_concepts WHERE concept_name = '건축공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '건축설계'),
    'relatedTo',
    0.8,
    '건축공사는 건축설계를 기반으로 수행됨. 건축설계 완료 후 건축공사 발주가 일반적.'
);

-- R2. 토목공사 relatedTo 토목설계 (weight: 0.8)
INSERT INTO ontology_relations (source_concept_id, target_concept_id, relation_type, weight, description)
VALUES (
    (SELECT id FROM ontology_concepts WHERE concept_name = '토목공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '토목설계'),
    'relatedTo',
    0.8,
    '토목공사는 토목설계를 기반으로 수행됨. 설계-시공 연계가 밀접함.'
);

-- R3. 전기공사 relatedTo 조명공사 (weight: 0.7)
INSERT INTO ontology_relations (source_concept_id, target_concept_id, relation_type, weight, description)
VALUES (
    (SELECT id FROM ontology_concepts WHERE concept_name = '전기공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '조명공사'),
    'relatedTo',
    0.7,
    '조명공사는 전기공사의 하위 분야이며, 전기 인프라를 전제로 함.'
);

-- R4. 통신공사 relatedTo IT/SW개발 (weight: 0.6)
INSERT INTO ontology_relations (source_concept_id, target_concept_id, relation_type, weight, description)
VALUES (
    (SELECT id FROM ontology_concepts WHERE concept_name = '통신공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = 'IT/SW개발'),
    'relatedTo',
    0.6,
    '통신 인프라 구축 후 IT/SW 시스템이 운영됨. 네트워크-소프트웨어 연계.'
);

-- R5. IT/SW개발 relatedTo SW유지보수 (weight: 0.8)
INSERT INTO ontology_relations (source_concept_id, target_concept_id, relation_type, weight, description)
VALUES (
    (SELECT id FROM ontology_concepts WHERE concept_name = 'IT/SW개발'),
    (SELECT id FROM ontology_concepts WHERE concept_name = 'SW유지보수'),
    'relatedTo',
    0.8,
    'SW개발 완료 후 SW유지보수로 전환됨. 개발-운영 생명주기 연계.'
);

-- R6. 건축공사 requires 감리용역 (weight: 0.7)
INSERT INTO ontology_relations (source_concept_id, target_concept_id, relation_type, weight, description)
VALUES (
    (SELECT id FROM ontology_concepts WHERE concept_name = '건축공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '감리용역'),
    'requires',
    0.7,
    '일정 규모 이상 건축공사는 법적으로 감리 의무. 건설기술진흥법 시행령 기준.'
);

-- R7. 토목공사 requires 감리용역 (weight: 0.7)
INSERT INTO ontology_relations (source_concept_id, target_concept_id, relation_type, weight, description)
VALUES (
    (SELECT id FROM ontology_concepts WHERE concept_name = '토목공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '감리용역'),
    'requires',
    0.7,
    '일정 규모 이상 토목공사는 법적으로 감리 의무. 건설기술진흥법 시행령 기준.'
);

-- R8. 도로공사 relatedTo 포장공사 (weight: 0.9)
INSERT INTO ontology_relations (source_concept_id, target_concept_id, relation_type, weight, description)
VALUES (
    (SELECT id FROM ontology_concepts WHERE concept_name = '도로공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '포장공사'),
    'relatedTo',
    0.9,
    '도로공사는 대부분 포장공사를 포함함. 아스팔트/콘크리트 포장이 핵심 공정.'
);

-- R9. 도로공사 relatedTo 교량공사 (weight: 0.7)
INSERT INTO ontology_relations (source_concept_id, target_concept_id, relation_type, weight, description)
VALUES (
    (SELECT id FROM ontology_concepts WHERE concept_name = '도로공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '교량공사'),
    'relatedTo',
    0.7,
    '도로 노선에 교량이 포함되는 경우가 많음. 도로-교량 복합 공사 빈번.'
);

-- R10. 도로공사 relatedTo 터널공사 (weight: 0.6)
INSERT INTO ontology_relations (source_concept_id, target_concept_id, relation_type, weight, description)
VALUES (
    (SELECT id FROM ontology_concepts WHERE concept_name = '도로공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '터널공사'),
    'relatedTo',
    0.6,
    '산악 지형 도로에 터널이 포함됨. 도로-터널 복합 공사.'
);

-- R11. 하천공사 relatedTo 하수도공사 (weight: 0.7)
INSERT INTO ontology_relations (source_concept_id, target_concept_id, relation_type, weight, description)
VALUES (
    (SELECT id FROM ontology_concepts WHERE concept_name = '하천공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '하수도공사'),
    'relatedTo',
    0.7,
    '하천 정비와 하수도 정비가 연계되는 경우가 많음. 배수 체계 통합 관리.'
);

-- R12. 상수도공사 relatedTo 하수도공사 (weight: 0.6)
INSERT INTO ontology_relations (source_concept_id, target_concept_id, relation_type, weight, description)
VALUES (
    (SELECT id FROM ontology_concepts WHERE concept_name = '상수도공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '하수도공사'),
    'relatedTo',
    0.6,
    '상수도와 하수도는 물 순환 체계의 양면. 동시 발주되는 경우 있음.'
);

-- R13. 냉난방설비 relatedTo 기계설비공사 (weight: 0.9)
INSERT INTO ontology_relations (source_concept_id, target_concept_id, relation_type, weight, description)
VALUES (
    (SELECT id FROM ontology_concepts WHERE concept_name = '냉난방설비'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '기계설비공사'),
    'relatedTo',
    0.9,
    '냉난방설비는 기계설비공사의 핵심 구성 요소. 배관/펌프/공조와 밀접.'
);

-- R14. 소방설비 relatedTo 전기공사 (weight: 0.6)
INSERT INTO ontology_relations (source_concept_id, target_concept_id, relation_type, weight, description)
VALUES (
    (SELECT id FROM ontology_concepts WHERE concept_name = '소방설비'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '전기공사'),
    'relatedTo',
    0.6,
    '소방설비(화재경보, 비상전원)는 전기 인프라에 의존함. 전기-소방 연계 시공.'
);

-- R15. 통신공사(CCTV) similarTo 보안장비(물품) (weight: 0.7)
INSERT INTO ontology_relations (source_concept_id, target_concept_id, relation_type, weight, description)
VALUES (
    (SELECT id FROM ontology_concepts WHERE concept_name = '통신공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '보안장비'),
    'similarTo',
    0.7,
    'CCTV는 통신공사(설치)와 보안장비(물품 구매) 양쪽에 걸침. 공사-물품 경계 개념.'
);


COMMIT;


-- ============================================
-- VERIFICATION QUERIES (트랜잭션 외부)
-- 시드 데이터 정상 삽입 확인용
-- ============================================

-- 1. 레벨별 개념 수 집계
SELECT
    level,
    CASE level
        WHEN 0 THEN 'Root (최상위)'
        WHEN 1 THEN 'Level 1 (대분류)'
        WHEN 2 THEN 'Level 2 (중분류)'
        WHEN 3 THEN 'Level 3 (소분류)'
    END AS level_name,
    COUNT(*) AS concept_count
FROM ontology_concepts
GROUP BY level
ORDER BY level;

-- 2. 대분류별 하위 개념 수
SELECT
    p.concept_name AS parent_category,
    p.level AS parent_level,
    COUNT(c.id) AS child_count
FROM ontology_concepts p
LEFT JOIN ontology_concepts c ON c.parent_id = p.id
WHERE p.level IN (0, 1)
GROUP BY p.concept_name, p.level
ORDER BY p.level, p.display_order;

-- 3. 관계(ontology_relations) 타입별 집계
SELECT
    relation_type,
    COUNT(*) AS relation_count,
    ROUND(AVG(weight)::numeric, 2) AS avg_weight
FROM ontology_relations
GROUP BY relation_type
ORDER BY relation_count DESC;

-- 4. 전체 요약
SELECT
    (SELECT COUNT(*) FROM ontology_concepts) AS total_concepts,
    (SELECT COUNT(*) FROM ontology_concepts WHERE level = 0) AS root_count,
    (SELECT COUNT(*) FROM ontology_concepts WHERE level = 1) AS level1_count,
    (SELECT COUNT(*) FROM ontology_concepts WHERE level = 2) AS level2_count,
    (SELECT COUNT(*) FROM ontology_concepts WHERE level = 3) AS level3_count,
    (SELECT COUNT(*) FROM ontology_relations) AS total_relations;
