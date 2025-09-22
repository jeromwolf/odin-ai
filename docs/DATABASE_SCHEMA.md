# 데이터베이스 스키마

## 📊 전체 테이블 구조

```
odin_db
├── bid_announcements      # 입찰 공고 메인 테이블
├── bid_documents          # 첨부 문서 정보
├── bid_document_search    # 검색 최적화 테이블
├── collection_logs        # 데이터 수집 로그
├── search_keywords        # 검색 키워드 통계
├── users                  # 사용자 정보
└── user_bid_bookmarks     # 사용자 북마크
```

## 📋 테이블 상세 스키마

### 1. bid_announcements (입찰 공고)
```sql
CREATE TABLE bid_announcements (
    id                        SERIAL PRIMARY KEY,
    bid_notice_no             VARCHAR(50) UNIQUE NOT NULL,  -- 입찰공고번호
    title                     TEXT NOT NULL,                -- 제목
    organization_name         VARCHAR(200) NOT NULL,        -- 발주기관
    contact_info              TEXT,                         -- 연락처

    -- 날짜 정보
    announcement_date         TIMESTAMP NOT NULL,           -- 공고일
    document_submission_start TIMESTAMP,                    -- 서류제출 시작
    document_submission_end   TIMESTAMP,                    -- 서류제출 마감
    opening_date              TIMESTAMP,                    -- 개찰일

    -- 금액 정보
    bid_amount                NUMERIC(15,0),                -- 입찰금액
    currency                  VARCHAR(10) DEFAULT 'KRW',    -- 통화

    -- 분류 정보
    industry_type             VARCHAR(100),                 -- 산업분류
    location                  VARCHAR(100),                 -- 지역
    bid_method                VARCHAR(50),                  -- 입찰방식
    qualification             TEXT,                         -- 자격요건
    notes                     TEXT,                         -- 비고

    -- URL 정보
    detail_url                TEXT,                         -- 상세페이지 URL
    document_url              TEXT,                         -- 문서 URL

    -- 상태 관리
    status                    VARCHAR(20) DEFAULT 'active', -- 상태
    is_processed              BOOLEAN DEFAULT FALSE,        -- 처리여부

    -- 타임스탬프
    created_at                TIMESTAMP,
    updated_at                TIMESTAMP
);

-- 인덱스
- PRIMARY KEY: id
- UNIQUE: bid_notice_no
- INDEX: id
```

### 2. bid_documents (첨부 문서)
```sql
CREATE TABLE bid_documents (
    id                    SERIAL PRIMARY KEY,
    bid_announcement_id   INTEGER NOT NULL REFERENCES bid_announcements(id),

    -- 파일 정보
    file_name             VARCHAR(255) NOT NULL,        -- 파일명
    file_path             TEXT,                         -- 저장 경로
    file_size             INTEGER,                      -- 파일 크기
    file_type             VARCHAR(10),                  -- 파일 타입 (hwp, pdf 등)

    -- 다운로드 정보
    download_url          TEXT,                         -- 다운로드 URL
    download_status       VARCHAR(20) DEFAULT 'pending', -- 다운로드 상태

    -- 처리 정보 (최적화됨)
    markdown_file_path    TEXT,                         -- 마크다운 파일 경로
    extracted_text_length INTEGER,                      -- 추출된 텍스트 길이
    processed_at          TIMESTAMP,                    -- 처리 시간
    processing_status     VARCHAR(20) DEFAULT 'pending', -- 처리 상태
    processing_error      TEXT,                         -- 에러 메시지

    -- 메타데이터
    file_metadata         JSON,                         -- 추가 메타데이터

    -- 타임스탬프
    created_at            TIMESTAMP,
    updated_at            TIMESTAMP
);

-- 인덱스
- PRIMARY KEY: id
- FOREIGN KEY: bid_announcement_id → bid_announcements(id)
- INDEX: id
```

### 3. bid_document_search (검색 최적화)
```sql
CREATE TABLE bid_document_search (
    id                  SERIAL PRIMARY KEY,
    bid_announcement_id INTEGER NOT NULL REFERENCES bid_announcements(id),
    bid_document_id     INTEGER NOT NULL REFERENCES bid_documents(id),

    -- 검색 필드 (빠른 검색용)
    bid_notice_no       VARCHAR(50) NOT NULL,           -- 입찰공고번호
    title               TEXT NOT NULL,                  -- 제목
    organization_name   VARCHAR(200) NOT NULL,          -- 발주기관
    announcement_date   TIMESTAMP NOT NULL,             -- 공고일
    bid_amount          NUMERIC(15,0),                  -- 입찰금액

    -- 문서 요약 정보
    summary             TEXT,                           -- 요약 (첫 500자)
    keywords            TEXT,                           -- 추출된 키워드
    important_dates     TEXT,                           -- 중요 날짜들
    requirements        TEXT,                           -- 주요 요구사항

    -- PostgreSQL 전체 텍스트 검색
    search_vector       tsvector,                       -- 검색 벡터

    -- 파일 참조
    markdown_file_path  TEXT,                           -- 마크다운 경로

    -- 타임스탬프
    created_at          TIMESTAMP,
    updated_at          TIMESTAMP
);

-- 인덱스 (총 19개 - 매우 최적화됨)
- PRIMARY KEY: id
- FOREIGN KEY: bid_announcement_id, bid_document_id
- B-tree 인덱스:
  - bid_announcement_id
  - bid_document_id
  - bid_notice_no
  - organization_name
  - announcement_date
  - bid_amount
- 복합 인덱스:
  - (organization_name, announcement_date)
- GIN 인덱스:
  - search_vector (전체 텍스트 검색)
- 트리거:
  - update_bid_document_search_vector (자동 벡터 업데이트)
```

### 4. collection_logs (수집 로그)
```sql
CREATE TABLE collection_logs (
    id               SERIAL PRIMARY KEY,
    collection_type  VARCHAR(50) NOT NULL,     -- 'api', 'crawler', 'manual'
    collection_date  TIMESTAMP NOT NULL,

    -- 결과 정보
    total_found      INTEGER DEFAULT 0,        -- 발견된 총 개수
    new_items        INTEGER DEFAULT 0,        -- 새 항목
    updated_items    INTEGER DEFAULT 0,        -- 업데이트 항목
    failed_items     INTEGER DEFAULT 0,        -- 실패 항목

    -- 상태 정보
    status           VARCHAR(20) NOT NULL,     -- 'running', 'completed', 'failed'
    start_time       TIMESTAMP NOT NULL,
    end_time         TIMESTAMP,

    -- 오류 정보
    error_message    TEXT,
    error_details    JSON,
    notes            TEXT,

    created_at       TIMESTAMP
);
```

### 5. search_keywords (검색 키워드)
```sql
CREATE TABLE search_keywords (
    id            SERIAL PRIMARY KEY,
    keyword       VARCHAR(100) NOT NULL UNIQUE,
    search_count  INTEGER DEFAULT 1,
    last_searched TIMESTAMP,
    created_at    TIMESTAMP,
    updated_at    TIMESTAMP
);

-- 인덱스
- PRIMARY KEY: id
- UNIQUE: keyword
- INDEX: keyword
```

### 6. users (사용자)
```sql
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    name            VARCHAR(100) NOT NULL,
    company         VARCHAR(200),

    -- 인증 정보
    hashed_password VARCHAR(255) NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    is_verified     BOOLEAN DEFAULT FALSE,

    created_at      TIMESTAMP,
    updated_at      TIMESTAMP
);
```

### 7. user_bid_bookmarks (북마크)
```sql
CREATE TABLE user_bid_bookmarks (
    id                  SERIAL PRIMARY KEY,
    user_id             INTEGER NOT NULL REFERENCES users(id),
    bid_announcement_id INTEGER NOT NULL REFERENCES bid_announcements(id),

    bookmark_date       TIMESTAMP,
    notes               TEXT,
    created_at          TIMESTAMP
);
```

## 🔍 검색 최적화 전략

### 1. 인덱싱 전략
- **단일 필드 인덱스**: 자주 검색되는 필드
- **복합 인덱스**: 조합 검색 패턴
- **GIN 인덱스**: 전체 텍스트 검색
- **트리거**: 자동 검색 벡터 업데이트

### 2. 스토리지 최적화
- **마크다운 파일**: 파일 시스템 저장 (대용량 텍스트)
- **메타데이터**: 데이터베이스 저장 (검색용)
- **검색 벡터**: PostgreSQL tsvector (전체 텍스트 검색)

### 3. 성능 목표
- 단순 검색: < 0.5초
- 복합 검색: < 1.0초
- 전체 텍스트: < 2.0초

## 📈 확장성
- 수평 확장 가능 (파티셔닝 지원)
- 읽기 복제본 추가 가능
- Elasticsearch 연동 가능 (향후)