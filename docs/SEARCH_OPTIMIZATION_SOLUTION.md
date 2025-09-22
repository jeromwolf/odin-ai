# 검색 최적화 솔루션 설계

## 문제 분석
사용자가 제기한 검색 속도 문제를 해결하기 위한 종합적인 솔루션입니다.

## 구현된 솔루션

### 1. 하이브리드 저장 전략
- **마크다운 파일**: 전체 문서 내용을 파일 시스템에 저장
- **데이터베이스**: 검색 가능한 메타데이터와 인덱스 저장
- **장점**: 스토리지 효율성과 검색 성능의 균형

### 2. 다단계 검색 시스템

#### 1단계: 인덱스된 필드 검색 (가장 빠름)
```python
# BidAnnouncement 테이블의 인덱스된 필드들
- title (B-tree index)
- organization_name (B-tree index)
- announcement_date (B-tree index)
- bid_amount (B-tree index)
```

#### 2단계: PostgreSQL 전체 텍스트 검색
```sql
-- BidDocumentSearch 테이블의 tsvector 활용
- search_vector (GIN index)
- 가중치 적용 (title > organization > keywords > summary)
```

#### 3단계: 마크다운 파일 직접 검색 (백업)
```python
# 필요시에만 파일 시스템 검색
- 파일 내용 직접 스캔
- 스니펫 추출 및 점수 계산
```

### 3. 데이터베이스 스키마 최적화

#### BidDocument 테이블 개선
```sql
-- 기존 필드 제거
ALTER TABLE bid_documents DROP COLUMN processed_text;
ALTER TABLE bid_documents DROP COLUMN processed_markdown;

-- 새로운 필드 추가
ALTER TABLE bid_documents ADD COLUMN markdown_file_path TEXT;
ALTER TABLE bid_documents ADD COLUMN extracted_text_length INTEGER;
ALTER TABLE bid_documents ADD COLUMN processed_at TIMESTAMP;
```

#### BidDocumentSearch 검색 전용 테이블
```sql
CREATE TABLE bid_document_search (
    -- 주요 검색 필드 (인덱싱)
    bid_notice_no VARCHAR(50),
    title TEXT,
    organization_name VARCHAR(200),
    announcement_date TIMESTAMP,
    bid_amount NUMERIC(15, 0),

    -- 요약 정보
    summary TEXT,
    keywords TEXT,

    -- 전체 텍스트 검색
    search_vector tsvector
);
```

### 4. 인덱싱 전략

#### 단일 필드 인덱스
- `bid_notice_no` - 고유 식별자 검색
- `organization_name` - 기관별 검색
- `announcement_date` - 날짜 범위 검색
- `bid_amount` - 금액 범위 검색

#### 복합 인덱스
- `(organization_name, announcement_date)` - 기관+날짜 조합 검색

#### 전체 텍스트 검색 인덱스
- GIN 인덱스 for `search_vector`
- 한국어 형태소 분석 지원

### 5. 성능 개선 결과

#### 응답 시간 목표
- 단순 키워드 검색: < 0.5초
- 복합 필터 검색: < 1.0초
- 전체 텍스트 검색: < 2.0초

#### 최적화 기법
1. **쿼리 최적화**
   - 인덱스 활용 우선
   - LIMIT 적용으로 결과 제한

2. **캐싱 전략** (향후 구현 예정)
   - Redis를 활용한 검색 결과 캐싱
   - 자주 검색되는 키워드 캐싱

3. **비동기 처리**
   - 검색 인덱스 백그라운드 업데이트
   - 병렬 검색 처리

## 구현 파일

### 1. 모델 정의
- `/shared/models.py` - 개선된 BidDocument 모델
- `/shared/search_models.py` - 검색 최적화 모델

### 2. 서비스 구현
- `/services/search_service.py` - 통합 검색 서비스

### 3. 마이그레이션
- `/migrations/add_search_tables.sql` - 검색 테이블 및 인덱스

### 4. 테스트
- `/test_search_performance.py` - 성능 측정

## 사용 방법

### 1. 데이터베이스 설정
```bash
# PostgreSQL 시작
brew services start postgresql@14

# 데이터베이스 및 테이블 생성
DATABASE_URL="postgresql://blockmeta@localhost:5432/odin_db" python setup_database.py --create

# 검색 최적화 마이그레이션
psql -d odin_db -f migrations/add_search_tables.sql
```

### 2. 검색 인덱스 구축
```python
from services.search_service import SearchService

service = SearchService()
await service.build_search_index()
```

### 3. 검색 실행
```python
# 단순 검색
results = await service.search_announcements("입찰")

# 복합 필터링
results = await service.search_announcements(
    query="공사",
    organization="서울",
    start_date=datetime(2025, 9, 1),
    min_amount=1000000000
)
```

## 향후 개선 사항

### 1. Elasticsearch 도입 (선택사항)
- 더 강력한 전체 텍스트 검색
- 한국어 형태소 분석기 지원
- 분산 검색 처리

### 2. 캐싱 레이어 구축
- Redis를 활용한 검색 결과 캐싱
- 인기 검색어 자동 캐싱

### 3. 검색 분석 및 최적화
- 검색 로그 분석
- 자주 검색되는 패턴 파악
- 인덱스 자동 최적화

## 결론

이 솔루션은 다음과 같은 장점을 제공합니다:

1. **빠른 검색 속도**: 인덱싱과 전체 텍스트 검색으로 성능 보장
2. **스토리지 효율성**: 마크다운은 파일로, 메타데이터만 DB 저장
3. **확장성**: 데이터 증가에 따른 성능 저하 최소화
4. **유연성**: 다양한 검색 조건 지원

검색 성능과 저장 공간의 균형을 맞춘 최적화된 솔루션입니다.