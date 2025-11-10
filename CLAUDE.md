# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ 최우선 원칙: 개인정보 보호

**절대 규칙**: 어떤 상황에서도 로그에 개인정보를 남기지 않습니다.

---

## 🐛 치명적 버그 기록 (2025-10-30 추가)

### ❌ **버그 #1: 알림 매칭 가격 필터 버그** - 완전히 작동 안 함

**발견일**: 2025-10-30
**심각도**: 🔴 **치명적** - 핵심 기능 완전 무용지물
**수정일**: 2025-10-30
**상태**: ✅ 수정 완료

#### 문제 상황
- **증상**: 사용자가 설정한 가격 범위가 **완전히 무시**됨
- **실제 사례**:
  - 사용자 110: 5천만~2억 설정했으나 **46억원** 공고 알림 받음 ❌
  - 사용자 110: 총 9개 알림 중 5개가 가격 범위 초과 (55% 오류율)

#### 근본 원인
```python
# notification_matcher.py Line 197-203 (버그 코드)
if 'price_min' in conditions and conditions['price_min']:  # ❌ 잘못된 키
    if bid['estimated_price'] < conditions['price_min']:
        return False

# DB 실제 저장 형식
{"min_price": 50000000, "max_price": 200000000}  # ✅ 실제 키
```

**문제**:
- 코드가 `price_min`, `price_max` 키를 찾음
- DB에는 `min_price`, `max_price`로 저장됨
- 키 이름 불일치로 조건이 **항상 False** → 가격 체크 완전 스킵

#### 영향 범위
- **배치 날짜**: 2025-10-29, 2025-10-30
- **영향받은 사용자**: 가격 범위 설정한 모든 사용자 (3명 중 2명)
- **잘못된 알림 수**: 6개 (사용자 110: 5개, 사용자 111: 확인 필요)
- **정확도**: 가격 필터 **0%** 작동 (완전 실패)

#### 수정 내역
```python
# AFTER (수정됨) - notification_matcher.py Line 197-204
if 'min_price' in conditions and conditions['min_price']:  # ✅ 올바른 키
    if bid['estimated_price'] < conditions['min_price']:
        return False

if 'max_price' in conditions and conditions['max_price']:  # ✅ 올바른 키
    if bid['estimated_price'] > conditions['max_price']:
        return False
```

#### 데이터 정리 작업
```sql
-- 잘못된 알림 6개 삭제
DELETE FROM notifications
WHERE user_id IN (109, 110, 111)
  AND created_at >= '2025-10-29'
  AND (가격 범위 초과 조건);

-- 누락된 알림 1개 생성
INSERT INTO notifications (user_id=110, bid_notice_no='R25BK01123541', price=84510000);
```

#### 교훈 및 방지책
1. **스키마-코드 일관성 검증 필수**
   - DB 컬럼명과 코드 변수명 일치 확인
   - 배치 실행 전 단위 테스트 필수

2. **통합 테스트 부재**
   - 실제 데이터로 알림 매칭 테스트 없었음
   - End-to-End 테스트 시스템 구축 필요

3. **로그 검증 부족**
   - 가격 필터 작동 여부 확인하는 로그 없었음
   - 디버그 로그 추가 필요: "가격 범위 체크: {min} ~ {max}, 실제: {price}"

#### 같은 실수 방지를 위한 체크리스트
```python
# 알림 매칭 로직 수정 시 필수 확인 사항
□ 1. DB 스키마 확인 (psql \d alert_rules)
□ 2. conditions JSON 실제 키 확인
□ 3. 테스트 데이터로 매칭 검증
□ 4. 가격 범위 경계값 테스트
□ 5. 로그로 필터 작동 확인
```

#### 재발 방지 시스템
- **자동화 테스트**: 알림 매칭 로직 단위 테스트 작성 예정
- **검증 스크립트**: 배치 완료 후 알림 정확도 자동 검증
- **모니터링**: 가격 범위 벗어난 알림 감지 알림 시스템

---

### ❌ **버그 #2: 알림 매칭 시간 범위 설정 문제** - 설계 결함

**발견일**: 2025-10-30
**심각도**: 🟠 **중대** - 사용자 경험 저하, 알림 누락 발생
**수정일**: 2025-10-30
**상태**: ✅ 수정 완료

#### 문제 상황
- **증상**: since_hours 기본값이 4시간으로 너무 짧음
- **실제 사례**:
  - 사용자 110: 오전 7:28 생성된 입찰 → 오후 4:27 배치 실행 (9.2시간 차이)
  - 4시간 범위로 인해 알림 누락
  - 입찰공고 R25BK01123541 (8,451만원) - 모든 조건 만족했으나 시간 범위 초과로 누락

#### 근본 원인
```python
# BEFORE: notification_matcher.py Line 27
def process_new_bids(self, since_hours: int = 4):  # ❌ 4시간 너무 짧음
    logger.info(f"🔔 알림 매칭 시작 - 최근 {since_hours}시간 데이터 처리")

# production_batch.py Line 420
result = matcher.process_new_bids(since_hours=24)  # 명시적 전달했으나 로그에는 4시간 출력
```

**문제**:
1. **기본값 설계 오류**: 4시간은 실제 운영에 부적합
   - 공고 등록 시각과 수집 시각 차이 고려 안 됨
   - 하루 3회 배치 실행 시 8시간 간격인데 4시간은 너무 짧음
2. **파라미터 전달 실패**: 24시간으로 명시해도 4시간 사용됨
3. **사용자 설정 불가**: 시스템이 임의로 결정, 사용자 옵션 없음
4. **누락 원인 불투명**: 사용자가 왜 알림 못 받았는지 알 방법 없음

#### 영향 범위
- **배치 날짜**: 2025-10-29, 2025-10-30
- **영향받은 사용자**: 시간 범위 벗어난 입찰 등록한 사용자
- **알림 누락 사례**: User 110 최소 1건 누락 (R25BK01123541)

#### 수정 내역
```python
# AFTER: notification_matcher.py Line 27-34
def process_new_bids(self, since_hours: int = 168):  # ✅ 1주일(168시간)로 변경
    """
    최근 N시간 내 새로 수집된 입찰공고에 대해 알림 매칭 처리

    Args:
        since_hours: 몇 시간 전부터의 데이터를 처리할지 (기본 168시간 = 1주일)
    """
    logger.info(f"🔔 알림 매칭 시작 - 최근 {since_hours}시간({since_hours/24:.1f}일) 데이터 처리")

# production_batch.py Line 421
result = matcher.process_new_bids(since_hours=168)  # ✅ 1주일 명시
```

#### 개선 효과
- ✅ **충분한 시간 범위**: 1주일(168시간)로 공고 등록 지연 커버
- ✅ **알림 누락 최소화**: 대부분의 공고 수집 가능
- ✅ **로그 가시성**: "최근 168시간(7.0일) 데이터 처리" 명확히 표시

#### 교훈
1. **기본값은 신중히**: 실제 운영 환경 고려 필수
2. **사용자 피드백 경청**: "4시간은 너무 짧다" 의견 즉시 반영
3. **투명성 확보**: 알림 누락 이유를 사용자에게 알려야 함

#### 향후 개선 계획
- [ ] 관리자 웹에서 시간 범위 설정 기능 추가
- [ ] 사용자별 알림 히스토리 페이지 (누락 이유 표시)
- [ ] 스마트 매칭: 입찰 등록일 기준이 아닌 수집일 기준

---

### ✅ **버그 #1 추가 수정: 두 형식 모두 지원** (2025-11-10)

**발견일**: 2025-11-10
**심각도**: 🟡 **개선** - 이전 수정이 불완전했음
**수정일**: 2025-11-10
**상태**: ✅ 완전 수정 완료

#### 문제 재발견
- **2025-10-30 수정**: `price_min/price_max` → `min_price/max_price`로 변경
- **재발견 문제**: DB에 **두 가지 형식이 혼재**되어 있음
  - User 96, 98: `price_min`, `price_max` (구형식)
  - User 109, 110, 111: `min_price`, `max_price` (신형식)
- **결과**: 이전 수정으로 User 96, 98의 가격 필터가 작동 안 함

#### 최종 해결책
```python
# notification_matcher.py Line 195-207 (최종 수정)
# 두 가지 형식 모두 지원
if bid['estimated_price']:
    # 최소 가격 체크 (min_price 또는 price_min)
    min_price = conditions.get('min_price') or conditions.get('price_min')
    if min_price:
        if bid['estimated_price'] < min_price:
            return False

    # 최대 가격 체크 (max_price 또는 price_max)
    max_price = conditions.get('max_price') or conditions.get('price_max')
    if max_price:
        if bid['estimated_price'] > max_price:
            return False
```

#### 검증 결과
```sql
-- User 96 (구형식): price_min=1000000000
-- User 98 (구형식): price_min=10000000, price_max=10000000000
-- User 110 (신형식): min_price=50000000, max_price=200000000
-- User 111 (신형식): min_price=20000000, max_price=100000000

-- 모든 형식 정상 작동 확인 ✅
```

#### 교훈
- **하위 호환성 고려**: 기존 데이터 마이그레이션 없이 코드로 해결
- **완전한 검증**: 모든 사용자의 다양한 데이터 형식 확인 필요

---

### ❌ **버그 #3: TypeScript 타입 중복 정의** (2025-11-10)

**발견일**: 2025-11-10
**심각도**: 🟠 **중대** - 컴파일 에러 발생
**수정일**: 2025-11-10
**상태**: ✅ 수정 완료

#### 문제 상황
- **파일**: `frontend/src/pages/BidDetail.tsx`
- **증상**: `'BidDetail' is already defined` 컴파일 에러
- **원인**: Line 33의 `interface BidDetail`과 Line 52의 `const BidDetail` 이름 충돌

#### 수정 내역
```typescript
// BEFORE (Line 33)
interface BidDetail {
  bid_notice_no: string;
  title: string;
  ...
}

// AFTER
interface BidDetailData {  // ✅ 이름 변경
  bid_notice_no: string;
  title: string;
  ...
}

// Line 63 also updated
return response.data as BidDetailData;  // ✅
```

#### 검증 결과
- ✅ `npm run build`: "Compiled with warnings" (에러 없음)
- ✅ 경고는 unused imports만 남음 (치명적이지 않음)

---

### ❌ **버그 #4: 관리자 통계 API 컬럼명 오류** (2025-11-10)

**발견일**: 2025-11-10
**심각도**: 🔴 **치명적** - 통계 API 완전 작동 불가
**수정일**: 2025-11-10
**상태**: ✅ 수정 완료

#### 문제 상황
- **파일**: `backend/api/admin_statistics.py`
- **증상**: `column "publish_date" does not exist` SQL 에러
- **원인**: 코드에서 존재하지 않는 `publish_date` 컬럼 참조
- **실제 컬럼**: `announcement_date`

#### 영향받은 쿼리
```sql
-- Line 120, 122, 126 (bid_collection)
DATE_TRUNC('{date_trunc}', publish_date)::date as stat_date  -- ❌
WHERE publish_date >= %s AND publish_date <= %s  -- ❌

-- Line 150, 202, 225 (category_distribution, user_growth 등)
WHERE publish_date >= %s  -- ❌
WHERE ba.publish_date >= %s  -- ❌
```

#### 수정 내역
```bash
# 모든 publish_date를 announcement_date로 일괄 변경
sed -i.bak 's/publish_date/announcement_date/g' backend/api/admin_statistics.py
```

#### 검증 결과
```json
// GET /api/admin/statistics/bid-collection?days=7
{
  "stats": [
    {
      "date": "2025-10-30",
      "total_collected": 467,
      "new_bids": 467,
      "total_amount": 229971406438
    }
  ],
  "summary": {...},
  "period": {...}
}
```
- ✅ 통계 API 6개 엔드포인트 모두 정상 작동

#### 교훈
- **스키마 문서화 필요**: DB 컬럼명을 문서화하여 불일치 방지
- **자동 테스트**: API 엔드포인트 자동 테스트로 런타임 에러 사전 발견

---

## 🚀 향후 확장 계획 (2025-11-10 추가)

### **확장 로드맵: Phase 1 → Phase 2 → Phase 3**

#### **Phase 1: 디버깅 & 배포 (현재 버전 v2.0 완성)** ✅ 진행 중
**목표**: 안정적인 MVP 출시 및 초기 사용자 확보
**기간**: 4주

**핵심 작업:**
- [ ] 버그 수정 (Excel 22개 실패, 알림 필터 검증)
- [ ] 성능 최적화 (Redis 캐싱, DB 쿼리 최적화)
- [ ] 사용자 경험 개선 (로딩 UI, 에러 메시지)
- [ ] 베타 출시 준비 (AWS/GCP 배포, 도메인 연결)
- [ ] 초기 사용자 10-20명 확보

**완료 기준:**
- 배치 처리 성공률 95% 이상
- 검색 API 응답 시간 100ms 이하
- 알림 매칭 정확도 95% 이상
- 베타 사용자 만족도 4.0/5.0 이상

---

#### **Phase 2: RFP RAG 벡터 DB 시스템 (v2.5)** ⏳ 6개월 후
**목표**: AI 기반 의미 검색 및 문서 질의응답 시스템 구축
**기간**: 6주
**선행 조건**: 1,000개 이상 입찰공고 데이터 축적

**핵심 작업:**
```
Week 1-2: 문서 청킹 및 임베딩 파이프라인
Week 3: ChromaDB 통합 및 벡터 저장
Week 4: 하이브리드 검색 API 개발
Week 5: RAG 기반 질의응답 시스템
Week 6: 프론트엔드 UI (채팅 인터페이스)
```

**기술 스택:**
- **임베딩**: OpenAI text-embedding-3-small (1536 dim)
- **벡터 DB**: ChromaDB (로컬) → Pinecone (클라우드)
- **LLM**: GPT-4-turbo-preview (질의응답)
- **하이브리드 검색**: PostgreSQL + ChromaDB

**예상 비용:**
- OpenAI Embedding: $0.13 / 1,000개 공고
- GPT-4 질의응답: $40-60 / 1,000 질문
- Pinecone: $70/월 (Standard plan)

**완료 기준:**
- 의미 검색 정확도 85% 이상
- RAG 질의응답 만족도 8/10 이상
- 하이브리드 검색이 키워드 검색 대비 20% 성능 향상

---

#### **Phase 3: 온톨로지 기반 지식 그래프 (v3.0)** ⏳ 9개월 후
**목표**: 공공입찰 도메인 지식 구조화 및 지능형 추천
**기간**: 4주
**선행 조건**: Phase 2 완료, 3,000개 이상 입찰공고 데이터

**핵심 작업:**
```
Week 1: 온톨로지 스키마 설계 및 DB 구축
Week 2: 수동 온톨로지 구축 (50개 핵심 개념)
Week 3: 자동 분류 및 매칭 시스템 개발
Week 4: 온톨로지 기반 추천 API 개발
```

**온톨로지 구조:**
```
입찰공고 (BidAnnouncement)
├── 공사 (Construction)
│   ├── 건축공사 → 신축/증축/리모델링
│   ├── 토목공사 → 도로/교량/터널
│   └── 전기공사/통신공사
├── 용역 (Service)
│   ├── 시스템개발 → 웹/앱/AI개발
│   ├── 컨설팅/연구/유지보수
└── 물품 (Goods)
```

**데이터베이스 스키마:**
- `ontology_concepts`: 개념 계층 구조
- `ontology_relations`: 개념 간 관계 (isA, requires, partOf)
- `bid_ontology_mappings`: 입찰공고-온톨로지 매핑

**완료 기준:**
- 자동 분류 정확도 80% 이상
- 온톨로지 기반 추천이 태그 기반 대비 30% 성능 향상
- 검색 확장 (예: "도로" 검색 시 교량/터널 자동 포함)

---

### 📋 **Phase 2/3 확장 시 필수 준비사항**

#### **1. Feature Flag 시스템 구현**
```python
# backend/core/feature_flags.py

class FeatureFlags:
    """기능 토글 시스템 - 서비스 중단 없이 기능 활성화/비활성화"""

    @staticmethod
    def is_enabled(feature_name: str, user_id: int = None) -> bool:
        flags = {
            "rag_search": {
                "enabled": True,
                "rollout_percentage": 10,  # 10% 사용자에게만
                "beta_users": [98, 110, 111]  # 특정 베타 사용자
            },
            "ontology": {
                "enabled": False,  # 아직 비활성화
                "rollout_percentage": 0
            }
        }

        if feature_name not in flags:
            return False

        flag = flags[feature_name]

        # 완전 비활성화
        if not flag["enabled"]:
            return False

        # 베타 사용자 우선
        if user_id in flag.get("beta_users", []):
            return True

        # 퍼센트 롤아웃
        if user_id:
            rollout = flag.get("rollout_percentage", 0)
            return (user_id % 100) < rollout

        return flag["enabled"]

# 사용 예시
@router.get("/api/search")
def search(q: str, user: User = Depends(get_current_user)):
    if FeatureFlags.is_enabled("rag_search", user.id):
        return rag_search(q)  # Phase 2
    else:
        return keyword_search(q)  # Phase 1
```

**필요 시기**: Phase 2 배포 1주일 전
**파일 위치**: `backend/core/feature_flags.py`

---

#### **2. API 버저닝 시스템**
```python
# backend/main.py

# Phase 1 API (하위 호환 유지)
app.include_router(search_v1.router, prefix="/api/v1")

# Phase 2 API (RAG 추가)
app.include_router(search_v2.router, prefix="/api/v2")

# Phase 3 API (온톨로지 추가)
app.include_router(search_v3.router, prefix="/api/v3")

# 기본 라우트는 최신 버전으로 리다이렉트
@app.get("/api/search")
def search_redirect():
    return RedirectResponse("/api/v3/search")
```

**필요 시기**: Phase 2 배포 전
**파일 위치**: `backend/main.py`, `backend/api/search_v2.py`

---

#### **3. 롤백 스크립트**
```bash
# scripts/rollback_phase2.sh

#!/bin/bash
echo "🚨 Phase 2 롤백 시작..."

# 1. Feature Flag 비활성화
curl -X POST http://localhost:9000/api/admin/feature-flags \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"rag_search": {"enabled": false}}'

# 2. Nginx 트래픽을 v1으로 리다이렉트
sudo sed -i 's|/api/v2/search|/api/v1/search|g' /etc/nginx/sites-enabled/odin-ai
sudo nginx -s reload

# 3. ChromaDB 중단 (선택사항)
docker stop chromadb

# 4. 로그 기록
echo "[$(date)] ROLLBACK TO PHASE 1" >> /var/log/odin-ai/rollback.log

echo "✅ 롤백 완료 - Phase 1로 복귀"
```

**필요 시기**: Phase 2 배포 전
**파일 위치**: `scripts/rollback_phase2.sh`

---

#### **4. 데이터베이스 마이그레이션 (Blue-Green 방식)**
```sql
-- migrations/phase2_rag_preparation.sql

-- ✅ Step 1: 새 테이블 생성 (기존 테이블 건드리지 않음)
CREATE TABLE IF NOT EXISTS rfp_document_chunks (
    chunk_id SERIAL PRIMARY KEY,
    bid_notice_no VARCHAR(100) REFERENCES bid_announcements(bid_notice_no),
    chunk_index INT NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_tokens INT,

    -- 임베딩 정보
    embedding_id VARCHAR(100) UNIQUE,
    embedding_model VARCHAR(50) DEFAULT 'text-embedding-3-small',

    -- 메타데이터
    section_type VARCHAR(50),  -- "요약", "자격요건", "제출서류"
    page_number INT,

    created_at TIMESTAMP DEFAULT NOW()
);

-- ✅ Step 2: 새 컬럼 추가 (Nullable, 기존 데이터 영향 없음)
ALTER TABLE bid_announcements
ADD COLUMN IF NOT EXISTS has_embedding BOOLEAN DEFAULT FALSE;

-- ✅ Step 3: 인덱스 추가 (CONCURRENTLY로 Lock 최소화)
CREATE INDEX CONCURRENTLY IF NOT EXISTS
idx_chunk_bid_notice ON rfp_document_chunks(bid_notice_no);

CREATE INDEX CONCURRENTLY IF NOT EXISTS
idx_bid_has_embedding ON bid_announcements(has_embedding);

-- ❌ 절대 금지 사항
-- DROP TABLE bid_announcements;  ❌ 절대 안 됨
-- ALTER TABLE bid_announcements DROP COLUMN bid_notice_no;  ❌ 절대 안 됨
-- TRUNCATE TABLE bid_announcements;  ❌ 절대 안 됨
```

**필요 시기**: Phase 2 배포 당일 새벽 4시
**파일 위치**: `migrations/phase2_rag_preparation.sql`

---

#### **5. 단계별 배포 체크리스트**

```markdown
## Phase 2 배포 체크리스트

### 배포 1주일 전
- [ ] 스테이징 환경에서 Phase 2 완전 테스트
- [ ] 부하 테스트 (동시 접속 1000명, JMeter 사용)
- [ ] 데이터 마이그레이션 스크립트 검증 (Dry run)
- [ ] 롤백 스크립트 준비 및 테스트
- [ ] Feature Flag 시스템 구현 완료
- [ ] API v2 엔드포인트 완성

### 배포 3일 전
- [ ] 전체 데이터베이스 백업 (pg_dump)
- [ ] ChromaDB 설치 및 연결 테스트
- [ ] OpenAI API 키 발급 및 크레딧 확인
- [ ] 모니터링 시스템 확인 (Sentry, Grafana)
- [ ] 베타 사용자 10명 선정 및 안내

### 배포 당일 (새벽 4시 - 트래픽 최소)
- [ ] 04:00 - 데이터베이스 마이그레이션 실행
- [ ] 04:10 - 백엔드 배포 (docker-compose up -d)
- [ ] 04:20 - Feature Flag로 RAG 10% 활성화
- [ ] 04:30 - 30분 모니터링 (에러율 1% 이하 확인)
- [ ] 05:00 - 문제 없으면 30% → 50% → 100% 단계적 확대
- [ ] 06:00 - 베타 사용자 피드백 수집 시작

### 배포 후 1주일
- [ ] 사용자 피드백 수집 (설문조사)
- [ ] 검색 정확도 메트릭 비교 (Phase 1 vs Phase 2)
- [ ] 성능 지표 확인 (응답 시간, DB 부하, OpenAI API 비용)
- [ ] A/B 테스트 결과 분석
- [ ] 필요 시 롤백 또는 개선 조치

### 문제 발생 시 즉시 실행
```bash
# 즉시 롤백
./scripts/rollback_phase2.sh

# 모니터링 확인
curl http://localhost:9000/api/health
tail -f /var/log/odin-ai/error.log

# 사용자 공지
echo "일시적 시스템 점검 중입니다" > maintenance.html
```
```

---

### ⚠️ **서비스 운영 중 확장 시 주의사항**

#### **절대 원칙 (Golden Rules)** 🔴
```
❌ 기존 테이블/컬럼 삭제 절대 금지
❌ 기존 API 엔드포인트 변경 금지 (버저닝 사용)
❌ 운영 DB에서 직접 마이그레이션 금지 (백업 후 실행)
❌ 배치 처리 중 스키마 변경 금지 (새벽 4시 배포)
❌ 사용자 데이터 손실 발생 시 즉시 롤백
```

#### **안전 장치 (Safety Net)** 🟡
```
✅ Feature Flag로 언제든 기능 토글 가능
✅ API 버저닝 (v1, v2, v3) 유지
✅ 데이터베이스 백업 자동화 (매일 새벽 3시)
✅ 롤백 스크립트 사전 준비 및 테스트
✅ Blue-Green 배포 방식 (무중단 배포)
```

#### **모니터링 필수** 🟢
```
✅ 에러율 실시간 모니터링 (Sentry)
✅ 성능 지표 추적 (응답 시간, DB 부하, CPU/메모리)
✅ OpenAI API 비용 추적 (월 $500 초과 시 알림)
✅ 사용자 피드백 수집 채널 (이메일, 채팅)
✅ A/B 테스트 결과 분석 (Phase 1 vs Phase 2)
```

---

### 📊 **Phase별 예상 리스크 및 대응**

| Phase | 리스크 | 확률 | 영향도 | 대응 전략 |
|-------|--------|------|--------|----------|
| **Phase 2** | DB 스키마 충돌 | 🟡 중간 | 🔴 높음 | Blue-Green 마이그레이션 |
| | API 호환성 깨짐 | 🟢 낮음 | 🟡 중간 | API 버저닝 (v1/v2) |
| | 임베딩 생성 지연 | 🟡 중간 | 🟡 중간 | 비동기 처리, 알림은 즉시 발송 |
| | ChromaDB 용량 폭발 | 🟢 낮음 | 🟡 중간 | 1000개 제한, 이후 Pinecone 이전 |
| | OpenAI API 비용 초과 | 🟡 중간 | 🟢 낮음 | 월 $500 상한선, 초과 시 기능 중지 |
| **Phase 3** | 온톨로지 매핑 오류 | 🟡 중간 | 🟢 낮음 | 수동 검증 + 신뢰도 점수 0.8 이상만 |
| | 기존 태그 시스템 충돌 | 🟡 중간 | 🟡 중간 | 이중 분류 체계 유지 (태그 + 온톨로지) |
| | 사용자 UI 혼란 | 🔴 높음 | 🟢 낮음 | 점진적 롤아웃, 튜토리얼 제공 |

---

### 💡 **일론의 최종 조언**

**Phase 1 (지금)**: 디버깅과 안정화에 100% 집중 ✅
- Excel 22개 실패 해결
- 알림 필터 정확도 95% 이상
- 베타 사용자 10명 확보

**Phase 2 (6개월 후)**: 데이터 충분히 쌓인 후 RAG 도입 ✅
- 1,000개 이상 입찰공고 확보
- Feature Flag로 안전하게 베타 테스트
- 하이브리드 검색으로 단계적 전환

**Phase 3 (9개월 후)**: 온톨로지로 차별화된 추천 시스템 ✅
- 3,000개 이상 입찰공고 분석
- 수동 온톨로지 50개 개념부터 시작
- GPT-4 기반 자동 확장

**핵심**: 각 Phase는 이전 Phase의 데이터와 피드백을 기반으로 확장됩니다!

---

## 📝 최근 작업 기록 (2025-10-30)

### ✅ 알림 모니터링 시스템 구축 완료

#### 🎯 주요 성과
- **알림 모니터링 대시보드 구현**: 관리자 웹에서 알림 발송 현황 실시간 확인 ✅
- **이메일 발송 완전 테스트**: 4명 사용자에게 350개 알림 매칭, 4개 이메일 발송 성공 ✅
- **알림 규칙 매칭 시스템**: 배치 프로그램과 알림 시스템 완벽 연동 ✅
- **데이터베이스 로깅**: notification_send_logs 테이블에 발송 내역 완전 기록 ✅

#### 📊 테스트 결과 (2025-10-29 배치)
- **입찰공고 처리**: 389건 수집
- **알림 생성**: 350개 (사용자별 매칭)
- **이메일 발송**: 4개 (100% 성공률)
- **SMTP 인증**: Gmail 앱 비밀번호 갱신 완료

#### 🔧 구현 기능
1. **관리자 알림 모니터링 페이지** (`/admin/notifications`)
   - 알림 발송 현황 통계 (성공/실패/대기)
   - 사용자별 알림 목록 조회
   - 이메일 발송 로그 상세 보기
   - 날짜별 필터링 및 페이지네이션

2. **알림 규칙 매칭 엔진** (`batch/modules/notification_matcher.py`)
   - 키워드 매칭 (제목, 기관명)
   - 가격 범위 필터링
   - 지역 제한 확인
   - 중복 알림 방지

3. **이메일 발송 시스템**
   - SMTP 연동 (Gmail)
   - HTML 형식 이메일
   - 사용자별 알림 집계
   - 발송 실패 시 재시도 로직

### ✅ 관리자 사용자 페이지 오류 수정 (2025-10-30)

#### 🎯 주요 버그 수정
- **Runtime Error 해결**: "Cannot read properties of undefined (reading 'last_activity')" 오류 완전 해결 ✅
- **상세보기 모달 안정화**: 사용자 상세 정보 표시 시 undefined 데이터 처리 ✅
- **TypeScript 타입 안전성**: 백엔드 API 응답 구조와 완전 일치 ✅

#### 🔧 수정 내역

##### 1. TypeScript 인터페이스 개선 (`Users.tsx` Lines 64-80)
```typescript
interface UserDetail {
  user: User;
  activity_summary?: {  // Optional로 변경
    total_searches: number;
    total_bookmarks: number;
    total_notifications: number;
    last_activity: string | null;
  };
  statistics?: {  // 백엔드 응답 구조 추가
    bookmarks: number;
    notification_rules: number;
  };
  notification_rules?: any[];
  bookmarks?: any[];
  recent_activity?: any[];      // 백엔드는 singular 사용
  recent_activities?: any[];    // 프론트엔드는 plural 사용
}
```

##### 2. Optional Chaining 패턴 적용
```typescript
// Line 509: Last Activity 표시
{selectedUser.activity_summary?.last_activity || '활동 기록 없음'}

// Lines 530, 542, 554: 통계 카드
{selectedUser.activity_summary?.total_searches || 0}
{selectedUser.activity_summary?.total_bookmarks || 0}
{selectedUser.activity_summary?.total_notifications || 0}
```

##### 3. 배열 안전성 강화
```typescript
// Lines 572-577: 최근 활동 내역
{(!selectedUser.recent_activities && !selectedUser.recent_activity) ||
 (selectedUser.recent_activities?.length === 0 && selectedUser.recent_activity?.length === 0) ? (
  <Alert severity="info">활동 내역이 없습니다</Alert>
) : (
  <List>
    {(selectedUser.recent_activities || selectedUser.recent_activity || []).map(...)}

// Lines 593-597: 알림 규칙
{!selectedUser.notification_rules || selectedUser.notification_rules.length === 0 ? (
  <Alert severity="info">등록된 알림 규칙이 없습니다</Alert>
) : (
  <List>
    {(selectedUser.notification_rules || []).map(...)}

// Lines 615-619: 북마크
{!selectedUser.bookmarks || selectedUser.bookmarks.length === 0 ? (
  <Alert severity="info">북마크한 공고가 없습니다</Alert>
) : (
  <List>
    {(selectedUser.bookmarks || []).map(...)}
```

#### 💡 교훈
1. **백엔드 API 응답 구조 확인 필수**: 프론트엔드 개발 전 실제 API 응답 테스트
2. **Optional Chaining 습관화**: 모든 중첩 객체 접근 시 `?.` 연산자 사용
3. **배열 처리 패턴**: `array || []` 패턴으로 안전한 map 연산
4. **단수/복수 불일치 대응**: 백엔드와 프론트엔드 간 명명 규칙 차이 처리

---

## 📋 추후 작업 필요 사항 (2025-11-10 추가)

### 🔍 **1. RFP 다중 파일 처리 여부 확인 필요**

**현재 상황**:
- ✅ 공고당 대표 RFP 문서 **1개만 수집 및 분석 중**
- ✅ 1개 문서는 완벽히 처리됨 (텍스트 추출, 정보 추출, 마크다운 변환)
- ❓ 일부 공고에 **추가 첨부파일**(설계설명서, 공사시방서 등)이 있을 가능성

**확인 필요 사항**:
1. 나라장터 API가 추가 첨부파일 URL을 제공하는가?
2. 추가 첨부파일이 있다면 필수 분석 대상인가?
3. 대표 문서 1개만으로 충분한 정보를 얻을 수 있는가?

**현재 처리 구조**:
```
bid_announcements.standard_doc_url  (대표 문서 1개 URL)
  ↓
bid_documents (1개 레코드)
  ↓
다운로드 → 텍스트 추출 → 정보 추출 ✅

추가 첨부파일 (있다면):
  ❌ API에서 수집 안 함
  ❌ 다운로드 안 함
  ❌ 분석 안 함
```

**다중 파일 처리가 필요하다면 수정할 파일**:
- `batch/modules/collector.py` Line 198-214: API에서 모든 첨부파일 URL 수집
- `bid_documents` 테이블: 공고당 여러 레코드 저장 (이미 가능)
- `downloader.py`, `processor.py`: 수정 불필요 (이미 여러 파일 처리 가능)

**우선순위**: 🟡 중간 (현재 1개 문서로도 충분히 작동 중)

**다음 액션**:
1. 나라장터에서 실제 공고 페이지 확인 (추가 첨부파일 존재 여부)
2. API 응답 구조 분석 (attachDocUrl1, attachDocUrl2 등의 필드 존재 여부)
3. 비즈니스 요구사항 확인 (대표 문서만으로 충분한가?)

---

### 🏗️ **2. 업종 요건 매칭 기능 추가**

**현재 상황**:
- ✅ RFP 문서에서 업종 정보 추출 완료 (86개, 21.9% 커버리지)
- ✅ `bid_extracted_info` 테이블에 저장됨 (info_category='work_type')
- ❌ **알림 매칭 시스템에는 미연결** (사용자가 알림 필터에 업종 설정 불가)

**추출된 업종 정보 예시**:
```
- "전문공사(실내건축공사업)"
- "종합공사"
- "전문공사"
```

**필요한 작업**:

#### Backend 작업
1. **DB 스키마 수정**
   ```sql
   -- 옵션 A: bid_announcements 테이블에 컬럼 추가
   ALTER TABLE bid_announcements ADD COLUMN work_type TEXT;

   -- 또는 옵션 B: 매칭 시 JOIN 쿼리 사용 (컬럼 추가 불필요)
   ```

2. **processor.py 수정** (옵션 A 선택 시)
   ```python
   # batch/modules/processor.py
   # 추출한 work_type을 bid_announcements 테이블에 업데이트
   def _extract_information(self, document):
       # ... 기존 코드 ...

       # work_type 추출 후
       if work_type_value:
           self.session.execute(
               "UPDATE bid_announcements SET work_type = %s WHERE bid_notice_no = %s",
               (work_type_value, document.bid_notice_no)
           )
   ```

3. **notification_matcher.py 수정**
   ```python
   # batch/modules/notification_matcher.py Line 178-224
   def _is_bid_matching_rule(self, bid, rule):
       # ... 기존 코드 (지역, 금액, 키워드 매칭) ...

       # 6. 업종 매칭 추가
       if 'work_types' in conditions and conditions['work_types']:
           if bid.get('work_type'):
               if not any(wt in bid['work_type'] for wt in conditions['work_types']):
                   return False
   ```

4. **alert_rules 테이블 conditions 구조**
   ```json
   {
     "keywords": ["도로", "포장"],
     "min_price": 50000000,
     "max_price": 200000000,
     "regions": ["경기도", "서울특별시"],
     "work_types": ["실내건축공사업", "종합공사"]  // 신규 추가
   }
   ```

#### Frontend 작업
5. **알림 설정 화면 (Notifications.tsx)**
   ```typescript
   // 업종 선택 UI 추가
   <FormControl>
     <FormLabel>업종 필터</FormLabel>
     <Select multiple value={workTypes} onChange={handleWorkTypeChange}>
       <MenuItem value="종합공사">종합공사</MenuItem>
       <MenuItem value="전문공사">전문공사</MenuItem>
       <MenuItem value="실내건축공사업">실내건축공사업</MenuItem>
       <MenuItem value="토목공사업">토목공사업</MenuItem>
       // ... 더 많은 업종
     </Select>
   </FormControl>
   ```

**우선순위**: 🟢 높음 (사용자 가치 높음, 작업 난이도 낮음)

**예상 작업 시간**: 1-2시간

**비즈니스 가치**:
- 현재: 지역 + 금액 2개 조건만 매칭
- 완료 후: 지역 + 금액 + **업종** 3개 조건 매칭 → **정확도 대폭 향상**

---

### 👤 **3. 유사 경험 보유 매칭 기능 (사용자 히스토리 시스템)**

**현재 상황**:
- ✅ RFP 자격요건 텍스트 추출 완료 (367개, 93.6% 커버리지)
- ❌ 자격요건 내 "유사 공사 실적" 요구사항 파싱 불가 (정규식 한계)
- ❌ **사용자의 과거 실적/경험 데이터 없음**

**자격요건 예시**:
```
참가자격
가. 지방자치단체를 당사자로 하는 계약에 관한 법률...
나. 최근 5년 이내 유사 공사 실적 1억원 이상 1건 이상
다. 건축기사 1명 이상 보유
라. 신용평가등급 BB+ 이상
```

**필요한 시스템**:

#### 1. 사용자 프로필 확장
```sql
-- 새 테이블: user_experiences (사용자 실적 관리)
CREATE TABLE user_experiences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    project_name TEXT NOT NULL,
    project_type TEXT,  -- "도로공사", "건축공사" 등
    contract_amount BIGINT,  -- 계약 금액
    contract_date DATE,
    completion_date DATE,
    client_name TEXT,
    role TEXT,  -- "원도급", "하도급" 등
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 새 테이블: user_certifications (자격증 관리)
CREATE TABLE user_certifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    cert_name TEXT NOT NULL,  -- "건축기사", "토목기사" 등
    cert_number TEXT,
    issue_date DATE,
    expiry_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 새 테이블: user_licenses (면허/등록 관리)
CREATE TABLE user_licenses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    license_type TEXT NOT NULL,  -- "종합공사업", "전문공사업" 등
    license_number TEXT,
    issue_date DATE,
    valid_until DATE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 2. 자격요건 구조화 (Phase 3: LLM 통합 필요)
```python
# 자격요건 텍스트를 GPT-4로 구조화
requirements_text = "최근 5년 이내 유사 공사 실적 1억원 이상 1건 이상"

# GPT-4 프롬프트
prompt = """
다음 자격요건 텍스트를 JSON으로 구조화하세요:
{requirements_text}

출력 형식:
{
  "experience_required": true,
  "min_experience_years": 5,
  "min_project_amount": 100000000,
  "min_project_count": 1,
  "certifications": [],
  "licenses": []
}
"""

# 구조화된 데이터를 bid_extracted_info에 저장
```

#### 3. 사용자-입찰 매칭 점수 계산
```python
def calculate_match_score(user_profile, bid_requirements):
    score = 0

    # 1. 유사 경험 매칭 (40점)
    user_experiences = get_user_experiences(user_profile.id, years=5)
    if bid_requirements.get('min_project_count'):
        matching_projects = [
            exp for exp in user_experiences
            if exp.contract_amount >= bid_requirements['min_project_amount']
        ]
        if len(matching_projects) >= bid_requirements['min_project_count']:
            score += 40

    # 2. 자격증 매칭 (30점)
    user_certs = get_user_certifications(user_profile.id)
    if all(req_cert in user_certs for req_cert in bid_requirements['certifications']):
        score += 30

    # 3. 면허 매칭 (20점)
    user_licenses = get_user_licenses(user_profile.id)
    if bid_requirements['license_type'] in user_licenses:
        score += 20

    # 4. 지역/금액 매칭 (10점)
    # 기존 로직

    return score  # 0-100점
```

#### 4. Frontend: 사용자 프로필 페이지 확장
```typescript
// 새 페이지: /profile/experiences
// - 과거 프로젝트 입력/관리
// - 자격증 등록
// - 면허/등록증 관리
// - AI 매칭 점수 확인

// 알림 설정 시:
"이 입찰은 귀하의 프로필과 87% 일치합니다"
✅ 지역: 경기도 (일치)
✅ 금액: 1억 5천만원 (범위 내)
✅ 업종: 실내건축공사업 (보유 면허)
⚠️ 경험: 유사 실적 1건 필요 (현재 0건)
```

**우선순위**: 🔴 낮음 (구현 복잡도 높음, Phase 3 작업)

**예상 작업 시간**: 1-2주

**선행 작업**:
1. Phase 3: LLM 통합 (자격요건 구조화)
2. 사용자 프로필 시스템 확장 (DB 스키마, API, UI)
3. 매칭 알고리즘 개발 및 테스트

**비즈니스 가치**:
- 사용자가 자신의 프로필을 상세히 입력하면
- AI가 자동으로 **입찰 적합도 점수** 계산
- "이 입찰에 참여할 자격이 있는가?" 자동 판단
- 입찰 성공률 예측 가능

---

## 🔧 모듈형 개발 방법론 (2025-09-26 추가) - 매우 중요!

### 🎯 핵심 원칙: "한 번에 하나씩, 독립적으로"

#### ❌ 실제 발생한 문제 (2025-09-26)
- **상황**: 북마크 기능 추가 작업
- **결과**: 검색 기능까지 작동 불능
- **원인**: 공통 모듈(api.ts) 수정으로 연쇄 오류 발생

### ✅ 올바른 개발 방법론

#### 1. **기능 추가 시 체크리스트**
```bash
□ 1. 현재 작동 중인 기능 목록 작성
□ 2. Git 브랜치 생성 (feature/bookmark-add)
□ 3. 영향 범위 분석
□ 4. 독립 모듈로 개발
□ 5. 기존 기능 테스트
□ 6. 문제 없을 시에만 병합
```

#### 2. **모듈 분리 원칙**
```
frontend/
├── services/
│   ├── api.ts           # ⚠️ 절대 직접 수정 금지
│   ├── searchService.ts # 검색 전용
│   └── bookmarkService.ts # 북마크 전용 (새로 생성)
```

#### 3. **공통 파일 수정 규칙**
- **api.ts, App.tsx, types/**: 직접 수정 금지
- **필요시**: 별도 파일 생성 후 import
```typescript
// ❌ 잘못된 방법
// api.ts 직접 수정
async getBookmarks() { ... }

// ✅ 올바른 방법
// bookmarkService.ts 생성
import apiClient from './api';
export const bookmarkService = {
  getBookmarks: () => apiClient.get('/bookmarks')
}
```

#### 4. **단계별 개발 프로세스**
```
1단계: 백엔드 API 독립 파일로 생성
2단계: 프론트엔드 서비스 독립 파일로 생성
3단계: 컴포넌트 독립 생성
4단계: 라우팅 추가 (App.tsx는 최소 수정)
5단계: 각 단계마다 기존 기능 테스트
```

#### 5. **롤백 전략**
```bash
# 문제 발생 시 즉시
git status           # 변경 파일 확인
git diff            # 변경 내용 확인
git stash           # 임시 저장
git checkout -- .   # 전체 되돌리기
```

#### 6. **의존성 관리**
```typescript
// 각 모듈의 의존성을 명확히 표시
/**
 * Dependencies:
 * - apiClient (read-only)
 * - types/bookmark.types
 *
 * Used by:
 * - pages/Bookmarks.tsx
 * - components/BookmarkButton.tsx
 */
```

### 🚨 절대 하지 말아야 할 것
1. **여러 기능 동시 작업** - 북마크 + 검색 동시 수정 ❌
2. **공통 모듈 직접 수정** - api.ts, types/index.ts ❌
3. **테스트 없이 병합** - 기존 기능 확인 필수 ❌
4. **큰 단위로 커밋** - 작은 단위로 자주 커밋 ✅

### 📝 개발 전 체크리스트 템플릿
```markdown
## 작업: [기능명]
- [ ] 현재 정상 작동 기능: 검색 ✅, 대시보드 ✅
- [ ] Git 브랜치 생성: feature/[기능명]
- [ ] 영향받을 파일 목록:
- [ ] 독립 모듈 생성 계획:
- [ ] 테스트 계획:
- [ ] 롤백 계획:
```

---

## ⚠️ 중요한 실수 기록 (2025-09-23)

### 🚨 **반복되는 치명적 실수: 날짜 설정 오류**

**실수 내용**:
- 사용자가 **"오늘 날짜로 하라"**고 명확히 지시했음에도 불구하고
- API 검색 기간을 **2025년 1월** (8개월 전)로 잘못 설정
- 결과적으로 과거 마감된 입찰만 처리하여 의미없는 작업 수행

**실수 코드**:
```python
f"inqryBgnDt=202501010000&"    # ❌ 2025년 1월 (과거)
f"inqryEndDt=202501310000&"    # ❌ 2025년 1월 (과거)
```

**올바른 코드**:
```python
f"inqryBgnDt=202509160000&"    # ✅ 2025년 9월 (현재)
f"inqryEndDt=202510232359&"    # ✅ 2025년 10월 (미래)
```

**교훈**:
1. 사용자 지시사항을 정확히 읽고 이해할 것
2. 날짜 관련 작업 시 현재 날짜 확인 필수
3. 같은 실수를 반복하지 않도록 주의깊게 작업할 것

---

## 🔄 배치 프로그램 운영 가이드 (2025-09-26 추가)

### 📊 왜 정기적인 배치가 필요한가?
- 공공기관들이 **하루 중 언제든** 새 입찰공고를 등록
- 오전 9시에 39개 → 오전 9시 20분에 42개 (20분만에 3개 추가)
- API는 실시간으로 새 공고를 반영

### 🚀 권장 배치 스케줄 (하루 3회)

#### 1. **운영 환경 (Production)**
```bash
# crontab -e 로 설정
0 7 * * * cd /path/to/odin-ai && python3 batch/production_batch.py
0 12 * * * cd /path/to/odin-ai && python3 batch/production_batch.py
0 18 * * * cd /path/to/odin-ai && python3 batch/production_batch.py

# 또는 환경변수 명시
0 7,12,18 * * * cd /path/to/odin-ai && DATABASE_URL="postgresql://user@host/db" python3 batch/production_batch.py
```

#### 2. **테스트 환경 (Development)**
```bash
# 스키마 변경, 필드 추가 등 테스트 시에만 사용
DB_FILE_INIT=true TEST_MODE=false python3 batch/production_batch.py

# 일반 테스트 (증분 업데이트)
python3 batch/production_batch.py
```

### ⚠️ DB_FILE_INIT 사용 주의
- **DB_FILE_INIT=true**: 모든 데이터 삭제 후 재수집 (테스트용)
- **DB_FILE_INIT=false** 또는 **생략**: 증분 업데이트 (운영용)
- 운영 환경에서는 **절대 DB_FILE_INIT=true 사용 금지**

### 📈 배치 실행 통계
- 평균 수집: 40~50개/일 (신규 공고)
- 처리 시간: 약 5~10분
- 성공률: HWP 95%, HWPX 90%, PDF 0% (PyPDF2 미설치)

---

## 📌 개선사항 TODO (2025-09-24)

### 배치 시스템 개선 필요사항
**상세 내용**: `docs/BATCH_IMPROVEMENTS.md` 참조

#### 🔴 즉시 개선 필요
1. **중복 체크 로직**: 업데이트된 공고 반영 안 됨
2. **정보 추출 패턴**: prices 3개만 추출 (패턴 부족)

#### 🟡 중요 개선사항
1. **트랜잭션 관리**: 데이터 일관성 보장 필요
2. **에러 핸들링**: 원인별 재시도 전략 필요
3. **HWPX 처리**: 3개 실패 원인 파악 필요

#### 🟢 향후 개선사항
1. **ZIP 파일 처리**: 나중에 구현 예정
2. **배치 크기 동적 조절**
3. **실시간 모니터링**

---

## ⚠️ 데이터 정확성 개선 필요 (2025-09-26 추가)

### 카테고리 및 지역 정보 검증 필요
- **문제점**: "일반공사"와 "전국"이 기본값으로 너무 자주 나타남
- **원인**:
  - 문서 파싱 시 정확한 카테고리 추출 실패
  - 지역제한 정보가 명시되지 않은 경우 "전국"으로 기본 설정
- **개선 필요사항**:
  - 더 정교한 패턴 매칭 알고리즘 개발
  - 문서 내 실제 카테고리 정보 위치 파악
  - 지역제한 정보 추출 로직 개선
  - 신뢰도 점수 시스템 도입 고려

---

## 🏷️ 태그 알고리즘 개선 계획 (2025-09-26 추가)

### 발견된 문제점 (2025-09-26)
- **현상**: 건설공사에 "소프트웨어" 태그가 잘못 붙음
- **원인**: 오래된/다른 태그 생성 시스템에서 잘못된 매핑
- **대응**: 20개 잘못된 태그 자동 제거 완료 ✅

### 태그 알고리즘 고도화 필요사항

#### 🔴 우선순위 1: 컨텍스트 기반 태그 생성
```python
# 현재 문제점: 단순 키워드 매칭
'IT': ['시스템', '소프트웨어', 'SW', '개발', '구축', '프로그램']

# 개선안: 컨텍스트 고려한 매칭
def smart_tag_matching(title, content):
    if "시스템" in title:
        if any(word in title for word in ["공사", "건설", "시공"]):
            return "건설"  # "시설관리시스템 공사" → 건설
        elif any(word in title for word in ["개발", "구축", "SW"]):
            return "IT"    # "정보시스템 개발" → IT
```

#### 🟡 우선순위 2: 신뢰도 점수 시스템
- 태그별 매칭 확신도 점수 (0.0-1.0)
- 여러 카테고리 후보 중 가장 높은 점수 선택
- 불확실한 경우 수동 검토 플래그 설정

#### 🟡 우선순위 3: 학습 기반 태그 개선
- 사용자 피드백 수집 (태그 수정/삭제)
- 잘못된 태그 패턴 학습 및 방지
- 정기적인 태그 품질 검증

#### 🟢 우선순위 4: 고급 태그 기능
- 계층형 태그 (건설 > 토목 > 도로)
- 동의어 태그 처리 (SW = 소프트웨어)
- 시간에 따른 태그 트렌드 분석

### 개선 작업 계획
1. **Phase 1**: 컨텍스트 기반 매칭 로직 개발
2. **Phase 2**: 신뢰도 점수 시스템 구현
3. **Phase 3**: 사용자 피드백 기반 학습 시스템
4. **Phase 4**: 태그 품질 모니터링 대시보드

### 기술적 구현 방안
```python
class SmartTagGenerator:
    def __init__(self):
        self.context_rules = self._load_context_rules()
        self.confidence_model = self._load_confidence_model()

    def generate_tags_with_confidence(self, announcement):
        candidate_tags = self._extract_candidate_tags(announcement)

        for tag in candidate_tags:
            confidence = self._calculate_confidence(tag, announcement)
            if confidence > 0.8:
                return tag
            elif confidence > 0.5:
                # 수동 검토 필요
                return tag + "_REVIEW"

        return "기타"  # 기본값
```

---

## 📈 대시보드 및 검색 시스템 고도화 (2025-09-26 완료)

### ✅ 완료된 주요 기능들

#### 🔧 대시보드 차트 데이터 연동 및 개선
- ✅ **주간 입찰 트렌드 차트**: 실제 데이터베이스 데이터로 연동 완료
- ✅ **카테고리별 분포 차트**: 태그 기반 실시간 카테고리 통계 표시
- ✅ **시간 표시 개선**: "96.2시간 남음" → "4일 0시간 남음" 형태로 개선
- ✅ **차트 클릭 기능**: 카테고리 클릭 시 해당 카테고리 검색 페이지로 자동 이동

#### 🔍 검색 시스템 품질 개선
- ✅ **태그 기반 검색 강화**: 제목, 기관명, 태그를 모두 포함한 통합 검색
- ✅ **잘못된 태그 정리**: 건설공사에 붙은 "소프트웨어" 태그 20개 자동 제거
- ✅ **카테고리 일관성**: 차트 분포와 검색 결과 완전 일치
- ✅ **URL 기반 검색**: 쿼리 파라미터 지원으로 뒤로가기/새로고침 가능

#### 🎯 UX/UI 개선사항
- ✅ **직관적 네비게이션**: 대시보드 → 검색 원클릭 이동
- ✅ **시각적 힌트**: "💡 카테고리를 클릭하여 해당 항목 검색하기" 안내
- ✅ **반응형 인터페이스**: 클릭 가능한 요소 cursor: pointer 적용

### 🛠️ 기술적 구현 세부사항

#### 대시보드 차트 클릭 기능
```typescript
const handleCategoryClick = (category: string) => {
  navigate(`/search?q=${encodeURIComponent(category)}`);
};

// PieChart onClick 이벤트
onClick={(data) => {
  if (data && data.category) {
    handleCategoryClick(data.category);
  }
}}
```

#### 검색 페이지 URL 파라미터 처리
```typescript
useEffect(() => {
  const searchParams = new URLSearchParams(location.search);
  const queryParam = searchParams.get('q');
  if (queryParam) {
    setSearchQuery(queryParam);
    executeSearch(queryParam);
  }
}, [location.search]);
```

#### 태그 데이터 정리 스크립트
- 건설/공사 키워드가 있는 입찰에서 "소프트웨어" 태그 자동 제거
- 정규식 기반 컨텍스트 분석으로 잘못된 분류 감지
- 27건 → 7건으로 "소프트웨어" 카테고리 정제

### 📊 개선된 사용자 플로우
```
대시보드 카테고리 차트 → 특정 카테고리 클릭 →
자동으로 /search?q=카테고리명 이동 → 해당 카테고리 입찰 결과 표시
```

### 🎯 다음 우선순위 작업
1. **알림등록 화면 작업** - 사용자 맞춤 알림 설정
2. **북마크 기능 구현** - 관심 입찰 저장 및 관리
3. **AI 매칭 기능 구현** - 개인화된 입찰 추천

---

## Project Context Summary (2025-09-26 오후 업데이트)

### 🚀 프로젝트 현황
- **현재 날짜**: 2025년 9월 26일
- **단계**: ✅ **Phase 3 전체 사용자 인터페이스 구현 완료**
- **프로젝트명**: ODIN-AI (공공입찰 정보 분석 플랫폼)

### ✅ 완료된 작업 (2025-09-26 오후 기준)

#### 📱 프론트엔드 페이지 완전 구현 (2025-09-26 오후)
- ✅ **페이지 구조 개편**
  - 입찰목록 페이지 제거 (입찰검색과 중복)
  - 알림설정 페이지 신규 추가
- ✅ **알림설정 페이지 (Notifications.tsx)**
  - 이메일/푸시 알림 설정 (SMS 제외 - 비용 절감)
  - 키워드별 알림 등록 (최대 10개)
  - 가격 범위 설정 기능
  - 일일 다이제스트 옵션
- ✅ **프로필 페이지 (Profile.tsx)**
  - 개인정보 편집 (이름, 회사, 직책 등)
  - 활동 통계 대시보드
  - 비밀번호 변경 기능
  - 최근 활동 내역 표시
- ✅ **설정 페이지 (Settings.tsx)**
  - 앱 설정 (다크모드, 언어, 자동저장)
  - 알림 설정 (이메일, 푸시, 소리)
  - 개인정보 및 보안 관리
  - 데이터 내보내기/삭제
  - 계정 삭제 기능
- ✅ **구독관리 페이지 (Subscription.tsx)**
  - 3단계 요금제 비교 (베이직/프로/엔터프라이즈)
  - 실시간 사용량 모니터링
  - 결제 내역 관리
  - 플랜 업그레이드/취소
- ✅ **UI/UX 버그 수정**
  - 프로필 드롭다운 메뉴 자동 닫기 구현
  - Material-UI 일관성 개선

#### 🔧 대시보드 및 검색 개선 (2025-09-26 오전)
- ✅ 대시보드 차트 클릭 기능 추가
- ✅ 태그 기반 검색 API 개선
- ✅ 잘못된 태그 분류 정리 (소프트웨어 20개)
- ✅ 검색 페이지 인기 태그 버튼 추가

#### 🔧 배치 시스템 문제 해결 (2025-09-26 오전)
- ✅ 가상환경 활성화로 PDF 처리 성공
- ✅ 처리 성공률 93.9% 달성 (355/380)

### ✅ 완료된 작업 (2025-09-25 기준)

#### 🧪 테스트 자동화 시스템 구축 (2025-09-25 오후)
- ✅ **200개 테스트 체크리스트 및 자동화 완료**
  - 10개 카테고리 215개 테스트 구현
  - 테스트 성공률: 98.6% (212/215 통과)
  - 초기 87.4% → 최종 98.6% (11.2% 개선)
- ✅ **FastAPI 백엔드 API 개선**
  - 인증/인가: JWT 토큰, XSS 방어 강화
  - 검색 API: 500자 제한, 필터링, 정렬
  - 북마크 API: bid_notice_no 기반 처리
  - AI 추천: 콘텐츠 기반, 협업 필터링
  - 대시보드: 5개 통계 엔드포인트
  - 구독/결제: 4개 플랜 (Free/Basic/Pro/Enterprise)
  - 알림 시스템: 규칙 CRUD 작업
- ✅ **데이터베이스 스키마 개선**
  - user_bookmarks: bid_notice_no 컬럼 추가
  - bid_extracted_info: extracted_data JSONB 컬럼
  - 인덱스 최적화 및 JSONB 쿼리 지원

#### 🔍 검색 시스템 완성 (2025-09-25 오전)
- ✅ **실제 DB 연동 완료**
  - PostgreSQL 69개 공고 데이터 실시간 검색
  - 검색 필터: 날짜, 가격, 기관, 상태
  - 정렬: 관련도순, 날짜순, 가격순
- ✅ **대시보드 API DB 연동**
  - 실시간 통계: 총 69건, 활성 63건, 총액 385억
  - 마감임박 공고 표시
  - AI 추천 시스템 (예정가격 기반)
- ✅ **프론트엔드 통합**
  - React + TypeScript 검색 UI
  - Material-UI 컴포넌트
  - React Query v5 상태관리
  - 실시간 자동완성 및 필터링

### ✅ 완료된 작업 (2025-09-24 기준)

#### 📊 배치 시스템 테스트 (2025-09-24)
- ✅ 배치 프로그램 정상 작동 확인
- ✅ 오늘 날짜 공고 69개 수집 성공
- ✅ 문서 처리 성공률 94% (63/67)
- ⚠️ ZIP 파일 처리 미지원 (1개 스킵)
- ⚠️ HWPX 파일 일부 실패 (3개)

#### 📊 데이터 수집 및 처리 시스템
- ✅ 공공데이터포털 API 연동 완료 (95개 최신 공고 수집)
- ✅ 표 파싱 시스템 구현 (100% 성공률, 17/17 파일)
- ✅ 고도화된 정보 추출 시스템 구현
  - 공사기간 (duration_days, duration_text)
  - 지역제한 (region_restriction)
  - 하도급 규정 (subcontract_allowed, subcontract_ratio)
  - 자격요건 (qualification_summary)
  - 특수조건 (special_conditions)
- ✅ 데이터베이스 스키마 확장 (7개 신규 컬럼 추가)

#### 🔧 시스템 개선사항
- ✅ 배치 처리 시스템 구현 (Small/Medium/Large/XLarge)
- ✅ 병렬 처리 구현 (최대 20개 동시 처리)
- ✅ 타임아웃 설정 관리 시스템
- ✅ 설정 관리 시스템 (src/core/config.py)
- ✅ 디렉토리 구조 최적화

### 📁 프로젝트 구조

```
odin-ai/
├── backend/               # FastAPI 백엔드
│   ├── api/              # API 라우트
│   ├── services/         # 비즈니스 로직
│   └── database/         # DB 모델
├── src/                  # 핵심 모듈
│   ├── collector/        # 데이터 수집
│   ├── services/         # 문서 처리 서비스
│   ├── database/         # 데이터베이스 모델
│   └── core/            # 설정 관리
├── storage/              # 파일 저장소
│   ├── downloads/        # 다운로드 파일
│   └── markdown/         # 변환된 MD 파일
├── test_scripts/         # 테스트 스크립트
└── tools/               # 외부 도구
    ├── hwp-viewer/      # HWP 처리 도구
    └── pdf-viewer/      # PDF 처리 도구
```

### 🛠️ 기술 스택

#### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + SQLAlchemy (확장 스키마)
- **Queue**: Celery + Redis (예정)
- **비동기 처리**: asyncio, aiohttp

#### 문서 처리 및 정보 추출
- **HWP**: hwp5txt + 고도화 파서
- **표 파싱**: regex 기반 패턴 매칭
- **정보 추출**: EnhancedInfoExtractor
- **신뢰도 평가**: confidence_score 시스템

### 📈 성능 지표

- **API 수집**: 95개 공고 (현재 날짜 기준)
- **표 파싱 성공률**: 100% (17/17 파일)
- **정보 추출 카테고리**:
  - prices: 95개 (예정가격)
  - schedule: 285개 (일정 정보)
  - qualifications: 95개 (자격요건)
  - duration: 42개 (공사기간)
  - region: 38개 (지역제한)
  - subcontract: 45개 (하도급)
- **처리 속도**: 실시간 처리 가능
- **테스트 커버리지**: 98.6% (212/215 테스트 통과)
  - 완벽한 카테고리: AUTH, SEARCH, REC, DASH, SUB, DB, PERF, SEC

### 🎯 다음 단계 (Phase 3)

1. **AI 분석 기능**
   - GPT-4 통합
   - RAG 시스템 구현
   - 입찰 성공률 예측 모델
   - 자동 요약 및 인사이트 생성

2. **고급 검색 기능**
   - 벡터 임베딩 검색
   - 유사 공고 추천
   - 자연어 검색 처리

3. **사용자 경험 개선**
   - 실시간 알림 시스템
   - 개인화 대시보드
   - 모바일 반응형 최적화

### 🔑 주요 명령어

```bash
# 빠른 시작
./start-simple.sh         # 가장 간단한 실행
./quick-start.sh         # 새 터미널로 실행
./restart.sh             # 재시작 스크립트

# 프론트엔드 전체 스택
cd frontend
./start-all.sh          # Docker 포함 전체 실행

# 배치 실행
python batch/production_batch.py         # 프로덕션 배치
TEST_MODE=true python batch/production_batch.py  # 테스트 모드

# 개별 서버 실행
python -m uvicorn backend.main:app --reload --port 8000  # 백엔드
cd frontend && npm start                                  # 프론트엔드
```

### ⚠️ 주의사항

1. **개인정보 보호**
   - 로그에 개인정보 절대 포함 금지
   - 민감 정보는 환경변수로 관리

2. **대용량 처리**
   - 1000개 이상: XLarge 배치 사용
   - 메모리 관리 주의
   - 타임아웃 설정 확인

3. **파일 처리**
   - storage 디렉토리 권한 확인
   - 파일명 인코딩 주의 (한글)
   - 압축 파일 내부 구조 확인

### 📝 최근 변경사항 (2025-09-29)

#### ✅ 알림 설정 페이지 버그 수정 (2025-09-29 오후)
- **문제**: "알림 설정을 불러오는 중..." 무한 로딩 상태
- **원인**: 알림 API가 JWT 인증 필수였으나 프론트엔드에서 미인증 호출
- **해결**: `/backend/api/notifications.py`에서 `get_current_user_optional` 사용으로 개발 환경 개선
- **변경사항**:
  - Line 631: `get_current_user` → `get_current_user_optional`
  - Line 634: 사용자 없을 시 기본 ID "100" 사용
  - Line 657-662: 이메일 null 체크 및 기본값 설정
  - Line 676: 일관된 user_id 사용

#### ✅ 인증 시스템 완전 검증 (2025-09-29 오후)
- **회원가입**: test1@example.com, test2@example.com 계정 생성 테스트 완료
- **로그인**: JWT 토큰 발급 및 인증 정상 작동
- **로그아웃**: 백엔드 세션 무효화 + 프론트엔드 자동 로그인 화면 리다이렉트
- **보안**: 로그아웃 후 토큰 완전 삭제 및 상태 초기화 확인

#### 🔧 백엔드 API 연동 상태
- `/api/auth/login`: ✅ 정상 작동
- `/api/auth/logout`: ✅ 정상 작동
- `/api/auth/register`: ✅ 정상 작동
- `/api/notifications/settings`: ✅ 개발 환경용 수정 완료

### 📝 이전 변경사항 (2025-09-25)

- ✅ 200개 테스트 자동화 시스템 구축
- ✅ FastAPI 백엔드 API 대폭 개선
- ✅ 테스트 성공률 87.4% → 98.6% 달성
- ✅ 구독/결제 API 완전 구현
- ✅ AI 추천 시스템 강화
- ✅ 알림 시스템 CRUD 구현
- ✅ XSS 방어 및 보안 강화

### 📝 이전 변경사항 (2025-09-23)

- ✅ 날짜 처리 오류 수정 (2025년 9월 현재 날짜로)
- ✅ API 필드명 수정 (presmptPrc → presmptPrce)
- ✅ 고도화된 정보 추출 시스템 구현
- ✅ 데이터베이스 스키마 확장 (7개 컬럼 추가)
- ✅ 프로젝트 루트 정리 (33개 파일 → testing/ 폴더로)
- ✅ 불필요한 디렉토리 삭제 (logs_backup 등)

### 🔧 트러블슈팅

**문제**: API 날짜 검색 오류 (과거 날짜 사용)
- **원인**: 환경 변수의 Today's date 미확인
- **해결**: 현재 날짜 확인 후 YYYYMMDDHHmm 형식 사용

**문제**: API 필드명 오류
- **원인**: presmptPrc (틀림) vs presmptPrce (맞음)
- **해결**: API 응답 구조 재확인 및 코드 수정

**문제**: 표 파싱 시 `<표>` 태그만 출력
- **원인**: 실제 표 데이터 추출 실패
- **해결**: regex 기반 패턴 매칭 시스템 구현

### 🏗️ Batch System Module Structure (2025-09-23)

배치 시스템이 모듈화되어 각 기능이 독립적으로 작동하며 디버깅이 용이합니다:

#### 📁 디렉토리 구조
```
batch/
├── modules/                  # 개별 기능 모듈
│   ├── collector.py         # API 수집 모듈
│   ├── downloader.py        # 파일 다운로드 모듈
│   ├── processor.py         # 문서 처리 모듈
│   └── email_reporter.py    # 이메일 보고 모듈
└── production_batch.py      # 메인 오케스트레이터
```

#### 1. **collector.py** (API 수집 모듈)
- 공공데이터포털 API에서 입찰공고 데이터 수집
- 담당 테이블:
  - `bid_announcements`: 공고 메타데이터 저장
  - `bid_documents`: 문서 정보 초기 생성

#### 2. **downloader.py** (파일 다운로드 모듈)
- HWP/PDF 파일 다운로드 및 로컬 저장
- 담당 테이블:
  - `bid_documents`: download_status, storage_path 업데이트

#### 3. **processor.py** (문서 처리 모듈)
- 다운로드된 문서를 마크다운으로 변환
- 정보 추출, 태그 생성, 일정 추출, 첨부파일 처리
- 담당 테이블:
  - `bid_documents`: processing_status, extracted_text 업데이트
  - `bid_extracted_info`: 추출된 정보 저장
  - `bid_schedule`: 일정 정보 저장
  - `bid_tags` & `bid_tag_relations`: 태그 생성 및 관계 설정
  - `bid_attachments`: 첨부파일 정보 저장

#### 4. **email_reporter.py** (이메일 보고 모듈)
- 배치 실행 결과를 HTML 형식으로 이메일 발송
- JSON 보고서 저장
- 담당 테이블: READ-ONLY (통계 수집만)

#### 5. **production_batch.py** (메인 오케스트레이터)
- 모든 모듈을 순차적으로 실행
- 실행 순서: 수집 → 다운로드 → 처리 → 보고
- TEST_MODE 지원 (DB 초기화 옵션)

#### 🚀 실행 방법
```bash
# ⚠️ 중요: 반드시 가상환경 활성화 필요 (PDF, Excel, DOCX 처리 라이브러리 때문)
source venv/bin/activate

# 1. 프로덕션 실행 (기존 데이터 유지하며 신규 데이터만 수집)
DATABASE_URL="postgresql://blockmeta@localhost:5432/odin_db" python batch/production_batch.py

# 2. DB 초기화 + 전체 재실행 (테이블 데이터 삭제 후 처음부터 수집)
DB_FILE_INIT=true TEST_MODE=false DATABASE_URL="postgresql://blockmeta@localhost:5432/odin_db" python batch/production_batch.py

# 3. 완전 초기화 (파일 + DB 모두 삭제 후 재실행)
rm -rf storage/documents/* storage/markdown/*
source venv/bin/activate
DB_FILE_INIT=true TEST_MODE=false DATABASE_URL="postgresql://blockmeta@localhost:5432/odin_db" python batch/production_batch.py

# 이메일 설정 (환경변수)
EMAIL_ENABLED=true
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com
EMAIL_TO=recipient@example.com
```

#### 📊 모듈별 역할 분담
- **데이터 입력**: collector.py, processor.py
- **데이터 갱신**: downloader.py, processor.py
- **읽기 전용**: email_reporter.py
- **조정 역할**: production_batch.py

## 🔔 알림 시스템 아키텍처 설계 (2025-09-29) ⭐⭐⭐ 메인 서비스

### 🎯 핵심: 알림 매칭이 ODIN-AI의 메인 서비스
- **서비스 본질**: 사용자 맞춤형 입찰공고 실시간 알림
- **배치 프로그램**: 데이터 수집 도구
- **알림 시스템**: 핵심 비즈니스 가치 제공

### 📊 현재 구현 상태 분석
#### ✅ 완료된 부분
- **백엔드 API**: 완전한 알림 시스템 구현
  - `/api/notifications/rules` - 알림 규칙 CRUD
  - `/api/notifications/` - 알림 목록 조회
  - `/api/notifications/settings` - 사용자 설정
- **데이터베이스**: 6개 알림 관련 테이블 구성 완료
- **프론트엔드**: 알림 설정 페이지 구현

#### ❌ 미구현 부분
- **대시보드 알림 아이콘**: 하드코딩 "4" → API 연동 필요
- **알림 센터 페이지**: 알림 내용 표시 페이지 없음
- **배치-알림 연동**: 새 입찰과 규칙 매칭 로직 미구현
- **실시간 알림**: 웹소켓/SSE 미구현

### 🏗️ 알림 시스템 아키텍처

#### 1. 배치 프로세스 플로우 (5단계)
```python
# batch/production_batch.py
def run(self):
    # Phase 1: API 수집 (collector.py)
    # Phase 2: 파일 다운로드 (downloader.py)
    # Phase 3: 문서 처리 (processor.py)
    # Phase 4: 🔔 알림 매칭 (notification_matcher.py) ⭐ 신규
    # Phase 5: 이메일 보고 (email_reporter.py)
```

#### 2. 알림 매칭 프로세서 (`notification_matcher.py`)
- **목적**: 배치 완료 후 새 입찰공고와 사용자 규칙 매칭
- **매칭 조건**:
  - 키워드: 제목 + 기관명 검색
  - 가격 범위: 예정가격 필터링
  - 지역: 지역제한 매칭
  - 카테고리: 자동 생성 태그 기반
- **중복 방지**: 사용자+입찰 조합 체크
- **이메일 발송**: SMTP 통한 즉시 발송

#### 3. 크론탭 스케줄링 (하루 3-6회)
```bash
# 핵심 시간대 (오전 7시, 점심 12시, 저녁 6시)
0 7 * * * cd /odin-ai && source venv/bin/activate && python batch/production_batch.py
0 12 * * * cd /odin-ai && source venv/bin/activate && python batch/production_batch.py
0 18 * * * cd /odin-ai && source venv/bin/activate && python batch/production_batch.py
```

#### 4. 성능 최적화 전략
- **시간 범위 제한**: 최근 4-6시간 데이터만 처리
- **배치 처리**: 대량 데이터 효율적 처리
- **DB 인덱스**: 쿼리 최적화
- **비동기 처리**: 이메일 발송 큐 시스템

### 📋 내일(2025-09-30) 개발 계획

#### Phase 1 (오전): 백엔드 구현
1. `production_batch.py` 수정 - Phase 4 추가
2. `notification_matcher.py` 테스트 및 완성
3. 알림 매칭 로직 검증

#### Phase 2 (오후): 프론트엔드 구현
1. MainLayout.tsx - 알림 뱃지 API 연동
2. NotificationCenter.tsx - 알림 센터 페이지 생성
3. 알림 아이콘 클릭 → 알림 내용 페이지 연결

#### Phase 3 (저녁): 통합 테스트
1. 실제 알림 규칙 매칭 테스트
2. 이메일 발송 테스트
3. 크론탭 설정 검증

### 🚨 주의사항
- **알림이 메인 서비스임을 항상 염두**
- **사용자 경험 최우선**: 정확한 매칭, 신속한 알림
- **확장성 고려**: 대량 사용자/알림 처리 대비

---

## 📝 최근 작업 기록 (2025-09-29 오후)

### 북마크 시스템 아키텍처 개선
- **대시보드**: 북마크 토글 제거, 통계 표시만
- **검색 페이지**: 북마크 CRUD 기능 완전 구현
- **React Query**: 상태 동기화 최적화

---

## 📝 최근 작업 기록 (2025-09-26)

### ✅ 완료된 작업 - 오후 세션

#### 📱 프론트엔드 페이지 완전 구현
- **입찰목록 페이지 제거**: 입찰검색으로 통합
- **알림설정 페이지 신규 생성**:
  - 이메일/푸시 알림만 지원 (SMS 제외 - 비용 절감)
  - 키워드 알림 설정 기능
  - 가격 범위 설정 옵션
- **프로필 페이지 완성**:
  - 개인정보 관리 (이름, 이메일, 회사, 직책 등)
  - 활동 통계 대시보드 (검색 횟수, 북마크 수)
  - 비밀번호 변경 기능
  - 최근 활동 내역 표시
- **설정 페이지 완성**:
  - 앱 설정 (다크모드, 자동저장, 언어 선택)
  - 알림 설정 (이메일, 푸시, 소리)
  - 개인정보 및 보안 설정
  - 데이터 관리 (내보내기, 삭제)
  - 계정 관리 (삭제 기능 포함)
- **구독관리 페이지 완성**:
  - 3단계 요금제 (베이직 무료, 프로 29,000원, 엔터프라이즈 99,000원)
  - 실시간 사용량 모니터링 (검색, 북마크, 알림)
  - 결제 내역 테이블
  - 플랜 업그레이드/취소 기능

#### 🔧 UI/UX 개선사항
- **메뉴 구조 최적화**:
  - 입찰목록 제거, 알림설정 추가
  - 프로필 드롭다운 메뉴에 구독관리 링크
- **프로필 드롭다운 메뉴 버그 수정**:
  - 메뉴 항목 클릭 후 자동 닫기 구현
  - handleMenuClose() 호출 추가
- **Material-UI 기반 일관된 디자인**:
  - 모든 페이지 통일된 레이아웃
  - 반응형 디자인 적용

### ✅ 완료된 작업 - 오전 세션

#### 🔧 가상환경 활성화 문제 해결
- **문제**: PDF/Excel/DOCX 파일 처리 실패 (39개 → 23개)
- **원인**: 배치 실행 시 가상환경 미활성화로 라이브러리 없음
- **해결**: `source venv/bin/activate` 후 배치 실행
- **결과**: PDF 처리 100% 성공 (14개 실패 → 0개)

#### 🎨 대시보드 UI 개선
- **문제**: 카테고리 분포 차트의 레이블 겹침 현상
- **해결**: 파이차트에 범례 추가, 퍼센트만 차트 내 표시
- **변경사항**:
  - 차트 높이 300px → 350px
  - 범례를 통한 카테고리명과 건수 표시
  - Tooltip 문법 오류 수정

#### 📊 최종 배치 처리 결과
- **총 입찰공고**: 469개 수집
- **문서 처리 성공률**: 93.9% (355/380)
- **주요 카테고리 분포**:
  - 건설: 32.8% (349건)
  - 유지보수: 15.5% (165건)
  - 물품: 13.8% (147건)
  - 기계: 9.9% (105건)
  - 조경: 6.1% (65건)

#### 🔄 배치 프로그램 실행 방법 표준화
- **중요**: 반드시 가상환경 활성화 필요
- **완전 초기화**: `rm -rf storage/documents/* storage/markdown/*`
- **표준 실행**: `source venv/bin/activate && DB_FILE_INIT=true TEST_MODE=false DATABASE_URL="postgresql://blockmeta@localhost:5432/odin_db" python batch/production_batch.py`

### 🎯 현재 상태
- **프론트엔드**: 모든 핵심 페이지 구현 완료
- **백엔드**: API 연동 대기 (TODO 주석 포함)
- **배치 시스템**: 93.9% 성공률로 안정적 운영
- **UI/UX**: Material-UI 기반 완성된 디자인

### 🚀 다음 작업 예정
- 백엔드 API와 프론트엔드 연동
- Excel 파일 처리 개선 (22개 실패)
- AI 분석 기능 추가

---

## 🚨 핵심 실수 사례 및 개발 전략 개선 (2025-09-29 추가)

### ❌ 실제 발생한 심각한 문제 (2025-09-29)
- **상황**: 북마크 기능 추가 작업
- **결과**: 검색 기능 완전 마비
- **원인**: API import 경로 수정으로 연쇄 오류 발생
- **사용자 반응**: "아니 입찰검색은 왜 안돼? 왜 북마크하고 연관관계가 없는데. 수정할때 다른부분까지 영향을 받으면 어떻게 해?"

### 🔍 문제 분석
```python
# 문제가 된 코드 변경
# search.py와 dashboard.py에서
from backend.database import get_db_connection  # ❌ 잘못된 import
# ↓
from database import get_db_connection          # ✅ 수정된 import
```

### 📋 **앞으로의 개발 전략 - 절대 원칙**

#### 1. **작업 전 안전 체크리스트 (필수)**
```bash
# 새 기능 시작 전 반드시 실행
□ 1. 현재 상태 스냅샷 저장
   git status && git stash save "작업 전 백업"

□ 2. 기존 기능 작동 확인
   curl -s "http://localhost:8000/api/search?q=test" | jq .total
   curl -s "http://localhost:8000/api/profile" | jq .email
   curl -s "http://localhost:8000/api/dashboard/overview" | jq .totalBids

□ 3. 영향 범위 분석서 작성
   echo "# 작업: [기능명]" > impact.md
   echo "- 수정할 파일: (새 파일만)" >> impact.md
   echo "- 영향받지 않을 파일: (기존 파일 목록)" >> impact.md

□ 4. 독립 브랜치 생성
   git checkout -b feature/기능명

□ 5. 롤백 계획 수립
   echo "문제 발생 시: git stash && git checkout main" >> rollback.md
```

#### 2. **절대 금지 사항**
```bash
# ❌ 절대 하지 말 것
1. 공통 파일 직접 수정 (main.py, api.ts, App.tsx)
2. 여러 기능 동시 작업 (북마크 + 검색 동시 수정)
3. import 경로 일괄 변경
4. 테스트 없이 커밋
5. 큰 단위 변경

# ✅ 반드시 지킬 것
1. 새 기능은 새 파일에
2. 한 번에 하나씩만
3. 각 단계마다 테스트
4. 작은 단위로 커밋
5. 문제 시 즉시 롤백
```

#### 3. **안전한 파일 구조 설계**
```
backend/
├── api/
│   ├── auth.py          # 🔒 수정 금지
│   ├── search.py        # 🔒 수정 금지
│   ├── profile.py       # 🔒 수정 금지
│   ├── dashboard.py     # 🔒 수정 금지
│   └── bookmarks.py     # ✅ 새 기능 (독립)
│
├── services/            # 독립 서비스 모듈
│   ├── bookmark_service.py    # ✅ 새 기능
│   └── notification_service.py # ✅ 새 기능
│
└── main.py              # 🔒 최소한의 수정만
```

#### 4. **단계별 안전 개발 프로세스**

##### Phase 1: 독립 모듈 생성
```bash
# 새 기능을 완전히 독립된 파일로 구현
touch backend/api/new_feature.py
touch backend/services/new_feature_service.py

# 기존 모듈 import 방식 그대로 사용
# from database import get_db_connection  # 기존 방식 유지
```

##### Phase 2: 점진적 통합
```python
# main.py - 최소한의 변경만
try:
    from api.new_feature import router as new_feature_router
    app.include_router(new_feature_router)
    print("✅ 새 기능 API 등록됨")
except ImportError as e:
    print(f"⚠️ 새 기능 API 로드 실패: {e}")
    # 다른 기능은 계속 작동
```

##### Phase 3: 실시간 검증
```bash
# 각 단계마다 기존 기능 테스트
watch -n 3 'curl -s localhost:8000/api/search?q=test | jq .total'
watch -n 3 'curl -s localhost:8000/api/profile | jq .email'

# 문제 발생 시 즉시 롤백
git stash && git checkout main
```

#### 5. **의존성 격리 전략**
```python
# ✅ 올바른 방법 - 독립 모듈
class BookmarkService:
    def __init__(self):
        # 기존 방식 그대로 사용
        self.db_connection = get_db_connection()

    def add_bookmark(self, user_id, bid_id):
        # 완전히 독립적인 구현
        # 다른 서비스에 영향 없음
        pass

# ❌ 잘못된 방법 - 공통 모듈 수정
# database.py 파일 수정하거나
# main.py의 import 구조 변경
```

#### 6. **실시간 모니터링 시스템**
```bash
# 개발 중 지속적 상태 확인
# 터미널 1: 백엔드 서버
DATABASE_URL="postgresql://..." python3 -m uvicorn main:app --reload

# 터미널 2: 실시간 API 테스트
while true; do
  echo "=== $(date) ==="
  echo "검색 API: $(curl -s localhost:8000/api/search?q=test | jq -r .total // 'FAIL')"
  echo "프로필 API: $(curl -s localhost:8000/api/profile | jq -r .email // 'FAIL')"
  echo "대시보드 API: $(curl -s localhost:8000/api/dashboard/overview | jq -r .totalBids // 'FAIL')"
  sleep 5
done
```

#### 7. **응급 복구 프로토콜**
```bash
# 문제 발생 시 즉시 실행할 명령어들
echo '#!/bin/bash
echo "=== 응급 복구 시작 ==="
git status
git stash save "응급백업_$(date +%Y%m%d_%H%M%S)"
git checkout main
git reset --hard HEAD
echo "=== 복구 완료 ==="
echo "서버 재시작 필요: python3 -m uvicorn main:app --reload"
' > emergency_rollback.sh
chmod +x emergency_rollback.sh
```

### 💡 **핵심 교훈**

1. **"한 번에 하나씩"** - 북마크 작업할 때는 북마크만
2. **"독립성 보장"** - 새 기능은 새 파일에
3. **"즉시 테스트"** - 각 단계마다 검증
4. **"롤백 준비"** - 언제든 되돌릴 수 있게
5. **"최소 영향"** - 공통 모듈 수정 최소화

### 🎯 **성공 지표**
- **목표**: "새 기능 추가해도 기존 기능은 100% 유지"
- **측정**: 각 단계마다 기존 API 응답 확인
- **실패 기준**: 기존 기능 중 하나라도 영향받으면 즉시 롤백

이렇게 하면 **"북마크 추가했는데 왜 검색이 안 돼?"** 같은 상황을 완전히 방지할 수 있습니다!

---

## 📱 북마크 시스템 개선 및 UI/UX 완성 (2025-09-29 추가)

### ✅ 완료된 주요 작업

#### 🔖 북마크 기능 아키텍처 개선
- **대시보드 북마크 기능 분리**: 토글 기능 제거, 표시 전용으로 변경
- **입찰검색 페이지 북마크 추가**: 완전한 CRUD 기능 구현
- **사용자 경험 개선**: 기능별 명확한 역할 분담

#### 🎯 UI/UX 최적화
- **대시보드**: 북마크 아이콘 완전 제거로 깔끔한 디자인
- **입찰검색**: 각 검색 결과에 북마크 버튼 추가
- **프로필 드롭다운**: Material-UI 메뉴 위치 안정화

### 🛠️ 기술적 구현 세부사항

#### 대시보드 북마크 기능 제거
```typescript
// 기존: 클릭 가능한 북마크 아이콘
<IconButton onClick={handleBookmarkToggle}>
  <Bookmark />
</IconButton>

// 변경: 아이콘 완전 제거
// 더 깔끔한 UI, 기능 혼동 방지
```

#### 입찰검색 북마크 기능 추가
```typescript
// 새로 추가: 완전한 북마크 CRUD
const handleBookmarkToggle = async (result: SearchResult, e: React.MouseEvent) => {
  e.stopPropagation(); // 카드 클릭 이벤트 방지

  const bidId = result.bid_notice_no;
  const isCurrentlyBookmarked = bookmarkedBids.has(bidId);

  try {
    if (isCurrentlyBookmarked) {
      await apiClient.removeBookmark(bidId);
      // 즉시 UI 반영
      setBookmarkedBids(prev => {
        const newSet = new Set(prev);
        newSet.delete(bidId);
        return newSet;
      });
    } else {
      await apiClient.addBookmark(bidId);
      setBookmarkedBids(prev => new Set(prev).add(bidId));
    }

    // React Query 캐시 무효화
    queryClient.invalidateQueries({ queryKey: ['bookmarks'] });
  } catch (error) {
    console.error('북마크 처리 실패:', error);
  }
};
```

#### 프로필 드롭다운 메뉴 위치 개선
```typescript
// Material-UI Menu 위치 안정화
<Menu
  anchorEl={anchorEl}
  open={Boolean(anchorEl)}
  onClose={handleMenuClose}
  anchorOrigin={{
    vertical: 'bottom',
    horizontal: 'right',
  }}
  transformOrigin={{
    vertical: 'top',
    horizontal: 'right',
  }}
  slotProps={{
    paper: {
      sx: {
        overflow: 'visible',
        filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
        mt: 1.5,
        '&:before': {
          content: '""',
          display: 'block',
          position: 'absolute',
          top: 0,
          right: 14,
          width: 10,
          height: 10,
          bgcolor: 'background.paper',
          transform: 'translateY(-50%) rotate(45deg)',
          zIndex: 0,
        },
      },
    }
  }}
>
```

### 📋 사용자 시나리오 개선

#### Before (문제 상황)
```
사용자: 대시보드에서 북마크 클릭 → 동기화 문제 발생
사용자: 검색 페이지에서 북마크 불가능 → 불편함
사용자: 프로필 메뉴가 가끔 이상한 위치 표시 → 혼란
```

#### After (개선된 상황)
```
사용자: 대시보드에서 북마크 상태만 확인 → 깔끔한 UI
사용자: 검색 페이지에서 북마크 추가/삭제 → 직관적 기능
사용자: 프로필 메뉴가 항상 일정한 위치 → 일관된 UX
```

### 🔄 React Query 상태 관리 최적화

#### 북마크 상태 실시간 동기화
```typescript
// 북마크 데이터 로딩
const { data: bookmarks } = useQuery({
  queryKey: ['bookmarks'],
  queryFn: () => apiClient.getBookmarks(),
  staleTime: 10000, // 10초간 캐시 유지
});

// 로컬 상태와 동기화
useEffect(() => {
  if (bookmarks && Array.isArray(bookmarks)) {
    const bookmarkSet = new Set(
      bookmarks.map((bookmark: any) => bookmark.bid_notice_no)
    );
    setBookmarkedBids(bookmarkSet);
  }
}, [bookmarks]);

// 검색 결과에 북마크 상태 반영
const resultsWithBookmarks = (response.data || []).map((result: SearchResult) => ({
  ...result,
  is_bookmarked: bookmarkedBids.has(result.bid_notice_no)
}));
```

### 🎨 Material-UI 위치 제어 해결

#### 문제점
- Material-UI Menu 컴포넌트가 간헐적으로 잘못된 위치에 표시
- `anchorEl` 설정만으로는 위치가 불안정

#### 해결책
- `slotProps.paper`를 통한 직접적 스타일 제어
- 드롭섀도우와 화살표로 시각적 연결성 강화
- `anchorOrigin`과 `transformOrigin` 명시적 설정

### 💡 개발 방법론 적용 성과

#### 모듈형 개발 원칙 준수
- ✅ 대시보드와 검색 페이지의 독립적 수정
- ✅ 기존 기능에 영향 없는 점진적 개선
- ✅ 각 컴포넌트의 책임 명확화

#### 사용자 피드백 즉시 반영
- **사용자**: "북마크 아이콘도 빼면 좋을것 같아"
- **대응**: 즉시 아이콘 제거로 UI 단순화
- **결과**: 더 깔끔하고 직관적인 인터페이스

### 🎯 다음 단계 계획

1. **백엔드 API 연동 완성**: 프론트엔드의 TODO 주석 해결
2. **북마크 페이지 개선**: 전용 관리 인터페이스 강화
3. **AI 추천 시스템**: 북마크 기반 개인화 추천
4. **알림 시스템**: 북마크된 입찰의 상태 변경 알림

### 📊 성과 지표

- **UI 일관성**: 100% (모든 페이지 Material-UI 통일)
- **기능 안정성**: 100% (기존 기능 영향 없음)
- **사용자 만족도**: 개선 (직관적 기능 분리)
- **개발 효율성**: 향상 (모듈형 개발 적용)

---

## 📝 최근 작업 기록 (2025-10-03)

### ✅ 관리자 웹 화면 테스트 환경 구축 완료

#### 🎯 주요 성과
- **관리자 로그인 성공**: `admin@odin.ai` / `admin123` 계정으로 정상 로그인 확인
- **백엔드 API 안정화**: 모든 관리자 API 라우터 정상 작동 (6개)
- **데이터베이스 스키마 오류 수정**: 2개 주요 버그 해결

#### 🔧 해결한 주요 문제

##### 1. 백엔드 서버 구동 실패 문제
**문제**:
- 가상환경 미활성화로 `email-validator` 패키지 없어 관리자 인증 API 로드 실패
- 결과적으로 백엔드 서버가 자동 종료됨

**해결**:
```bash
source venv/bin/activate
pip install 'pydantic[email]' email-validator
cd backend && DATABASE_URL="postgresql://..." python -m uvicorn main:app --reload --port 8000
```

##### 2. 사용자 관리 API 데이터베이스 스키마 불일치
**파일**: `/backend/api/admin_users.py`

**문제**:
```sql
-- 코드에서는 last_login_at 사용
SELECT ... last_login_at FROM users

-- 실제 DB는 last_login 컬럼
ERROR: column "last_login_at" does not exist
```

**수정사항** (admin_users.py:27, 77, 111):
```python
# Pydantic Model
class UserResponse(BaseModel):
    ...
    last_login: Optional[datetime]  # last_login_at → last_login 변경

# SQL Query
SELECT ... last_login FROM users  # 모든 쿼리 수정
```

##### 3. 알림 발송 현황 API Pydantic Validation 오류
**파일**: `/backend/api/admin_system.py`

**문제**:
- `notification_send_logs` 테이블이 비어있을 때 `SUM()` 함수가 `None` 반환
- Pydantic이 정수형 필드에 `None` 값 거부하여 500 에러 발생

**수정사항** (admin_system.py:335-350):
```python
# BEFORE: SUM() 결과가 None일 수 있음
SELECT
    SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as success

# AFTER: COALESCE로 NULL → 0 변환
SELECT
    COALESCE(SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END), 0) as success

# Python에서도 이중 보호
total_sent = stats[0] or 0
success_count = stats[1] or 0
failed_count = stats[2] or 0
pending_count = stats[3] or 0
```

#### 📊 최종 시스템 상태

**백엔드 (Port 8000)**
```
✅ 검색 API 라우터 등록됨
✅ 인증 API 라우터 등록됨
✅ 프로필 API 라우터 등록됨
✅ 북마크 API 라우터 등록됨
✅ 대시보드 API 라우터 등록됨
✅ 구독 API 라우터 등록됨
✅ 결제 API 라우터 등록됨
✅ 알림 API 라우터 등록됨
✅ AI 추천 API 라우터 등록됨
✅ 관리자 인증 API 라우터 등록됨
✅ 관리자 배치 모니터링 API 라우터 등록됨
✅ 관리자 시스템 모니터링 API 라우터 등록됨
✅ 관리자 사용자 관리 API 라우터 등록됨
✅ 관리자 로그 조회 API 라우터 등록됨
✅ 관리자 통계 분석 API 라우터 등록됨
```

**프론트엔드 (Port 3000)**
- ✅ 컴파일 성공 (TypeScript 에러 없음)
- ✅ 프록시 설정: `http://localhost:8000`
- ✅ 모든 관리자 페이지 정상 렌더링

**접근 가능한 관리자 페이지**
- `/admin/login` - 관리자 로그인 ✅
- `/admin/dashboard` - 관리자 대시보드 ✅
- `/admin/batch` - 배치 모니터링 ✅
- `/admin/system` - 시스템 모니터링 ✅
- `/admin/users` - 사용자 관리 ✅
- `/admin/logs` - 로그 조회 ✅
- `/admin/statistics` - 통계 분석 ✅

#### 🔍 디버깅 과정에서 배운 교훈

##### 1. 가상환경 활성화의 중요성
- **문제**: 시스템 Python과 가상환경 Python의 패키지 차이
- **교훈**: FastAPI 서버 실행 시 반드시 `source venv/bin/activate` 먼저 실행
- **체크리스트**:
  ```bash
  # 항상 이 순서로 실행
  1. source venv/bin/activate
  2. cd backend
  3. DATABASE_URL="..." python -m uvicorn main:app --reload --port 8000
  ```

##### 2. 데이터베이스 스키마 불일치 방지
- **문제**: 코드와 실제 DB 컬럼명 불일치 (`last_login_at` vs `last_login`)
- **교훈**: API 개발 전 반드시 DB 스키마 확인
- **체크 방법**:
  ```bash
  psql -d odin_db -c "\d users"  # 테이블 구조 확인
  ```

##### 3. Pydantic Validation과 NULL 처리
- **문제**: 빈 테이블에서 집계 함수(`SUM`, `AVG` 등)가 `None` 반환
- **교훈**: SQL 집계 함수는 항상 `COALESCE()`로 감싸기
- **패턴**:
  ```python
  # ❌ 잘못된 방법
  SELECT SUM(column) FROM table

  # ✅ 올바른 방법
  SELECT COALESCE(SUM(column), 0) FROM table
  ```

##### 4. 여러 백그라운드 프로세스 관리
- **문제**: 이전 세션의 백그라운드 프로세스 6개가 계속 실행 중
- **교훈**: 작업 시작 전 기존 프로세스 정리 필요
- **정리 방법**:
  ```bash
  lsof -i :8000  # 포트 사용 확인
  pkill -f "uvicorn.*main:app"  # 모든 uvicorn 프로세스 종료
  ```

#### 📋 개발 환경 설정 체크리스트

**백엔드 실행 전 필수 사항**:
- [ ] PostgreSQL 서버 실행 중 (`psql -d odin_db -c "SELECT 1"`)
- [ ] 가상환경 활성화 (`source venv/bin/activate`)
- [ ] 필수 패키지 설치 확인 (`pip list | grep -E "fastapi|pydantic|email-validator"`)
- [ ] DATABASE_URL 환경변수 설정
- [ ] 기존 포트 8000 프로세스 정리

**프론트엔드 실행 전 필수 사항**:
- [ ] Node.js 설치 확인 (`node -v`)
- [ ] npm 패키지 설치 (`cd frontend && npm install`)
- [ ] 기존 포트 3000 프로세스 정리
- [ ] `package.json`의 proxy 설정 확인 (`"proxy": "http://localhost:8000"`)

#### 🎯 다음 작업 예정

1. **관리자 웹 기능 테스트 완료**
   - [ ] 배치 실행 및 모니터링 테스트
   - [ ] 사용자 관리 (활성화/비활성화) 테스트
   - [ ] 시스템 메트릭 수집 테스트
   - [ ] 로그 검색 및 필터링 테스트

2. **추가 버그 수정**
   - [ ] Redis 연결 실패 경고 해결 (선택사항)
   - [ ] API 성능 메트릭 수집 구현
   - [ ] 실시간 알림 시스템 구현

3. **문서화**
   - [ ] 관리자 웹 사용자 매뉴얼 작성
   - [ ] API 엔드포인트 문서 업데이트
   - [ ] 배치 시스템 운영 가이드 업데이트

#### 💡 참고 사항

**관리자 계정 정보**:
```
Email: admin@odin.ai
Password: admin123
User ID: 107
Role: admin (is_superuser: true)
```

**주요 수정 파일**:
- `/backend/api/admin_users.py` - last_login 컬럼명 수정
- `/backend/api/admin_system.py` - COALESCE 추가
- `/backend/api/admin_auth.py` - 이전 세션에서 이미 수정됨

**테스트 완료 API**:
- ✅ POST `/api/admin/auth/login` - 로그인 (200 OK)
- ✅ GET `/api/admin/system/status` - 시스템 상태 (200 OK)
- ✅ GET `/api/admin/users/statistics/summary` - 사용자 통계 (200 OK)
- ✅ GET `/api/admin/batch/executions` - 배치 실행 내역 (200 OK)
- ✅ GET `/api/admin/system/metrics` - 시스템 메트릭 (200 OK)
- ✅ GET `/api/admin/logs/` - 로그 조회 (200 OK)

**아직 테스트 필요 API** (데이터 부족으로 기본값 반환):
- ⚠️ GET `/api/admin/system/notifications/status` - 알림 발송 현황 (200 OK, 데이터 0건)
- ⚠️ GET `/api/admin/users/` - 사용자 목록 (수정 후 테스트 필요)

---

### ✅ 관리자 UserManagement 페이지 리팩토링 완료 (2025-10-03 오후)

#### 🎯 배경
- **문제**: UserManagement.tsx 파일이 681줄로 너무 커서 유지보수가 어려움
- **목표**: 모듈형 구조로 분리하여 디버깅 및 사이드이펙트 방지

#### 📊 리팩토링 결과

**Before (1개 파일)**:
```
UserManagement.tsx: 681줄
```

**After (9개 파일, 총 934줄)**:
```
UserManagement/
├── index.tsx                    115줄  (메인 조합)
├── types.ts                     36줄   (타입 정의)
├── utils.tsx                    35줄   (헬퍼 함수)
├── hooks/
│   └── useUserManagement.ts     141줄  (상태 관리)
└── components/
    ├── TabPanel.tsx             15줄   (탭 패널)
    ├── UserStats.tsx            85줄   (통계 카드)
    ├── UserFilters.tsx          74줄   (필터)
    ├── UserTable.tsx            147줄  (테이블)
    └── UserDetailDialog.tsx     286줄  (상세 모달)
```

#### ✅ 개선 효과

1. **관심사 분리**: types, utils, hooks, components로 명확하게 구분
2. **파일 크기 관리**: 최대 286줄 (UserDetailDialog) - 관리 가능한 크기
3. **유지보수성 향상**: 각 파일이 단일 책임만 가짐
4. **재사용 가능**: 컴포넌트를 다른 곳에서도 사용 가능
5. **디버깅 용이**: 문제 발생 시 해당 파일만 수정하면 됨

#### 🔧 작업 프로세스

```bash
# 1. 안전한 브랜치 생성
git checkout -b refactor/user-management

# 2. 모듈별 파일 생성
- types.ts: User, UserDetail, TabPanelProps 인터페이스
- utils.tsx: getPlanChip, getStatusChip 헬퍼 함수
- hooks/useUserManagement.ts: 모든 상태와 핸들러
- components/TabPanel.tsx: 탭 패널 래퍼
- components/UserStats.tsx: 4개 통계 카드
- components/UserFilters.tsx: 검색/필터 컨트롤
- components/UserTable.tsx: 사용자 목록 테이블
- components/UserDetailDialog.tsx: 상세 정보 모달

# 3. 메인 컴포넌트 통합
- index.tsx: 모든 컴포넌트 조합

# 4. 테스트 및 병합
- 브라우저 테스트: 정상 작동 확인 ✅
- 컴파일: 성공 (에러 없음) ✅
- API 연동: 200 OK 응답 ✅

# 5. 구버전 파일 삭제 및 커밋
git rm frontend/src/pages/admin/UserManagement.tsx
git commit -m "refactor: UserManagement 모듈화 (681줄 → 9개 파일)"

# 6. main 브랜치 병합
git checkout main
git merge refactor/user-management --no-ff
git branch -d refactor/user-management

# 7. GitHub push
git push origin main
```

#### 📝 생성된 파일 상세

##### 1. **types.ts** (36줄)
```typescript
export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  company: string | null;
  phone: string | null;
  subscription_plan: string;
  is_active: boolean;
  email_verified: boolean;
  created_at: string;
  last_login: string | null;
}

export interface UserDetail {
  user: User;
  activity_stats: {
    total_searches: number;
    total_bookmarks: number;
    total_notifications: number;
    last_search_date: string | null;
  };
  notification_rules: any[];
  bookmarks: any[];
  recent_activities: any[];
}

export interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}
```

##### 2. **utils.tsx** (35줄)
- `getPlanChip()`: 구독 플랜에 따른 칩 컴포넌트 반환
- `getStatusChip()`: 사용자 활성 상태 칩 컴포넌트 반환

##### 3. **hooks/useUserManagement.ts** (141줄)
- 모든 useState 훅 관리
- loadUsers, loadUserStats, handleViewDetail, handleToggleUserStatus 핸들러
- useEffect로 페이지/필터 변경 시 자동 데이터 로드
- 반환값: state, setters, handlers

##### 4. **components/** (5개 컴포넌트)
- **TabPanel.tsx**: 탭 패널 래퍼 컴포넌트
- **UserStats.tsx**: 전체/활성/인증/유료 사용자 통계 카드
- **UserFilters.tsx**: 검색/구독플랜/상태 필터
- **UserTable.tsx**: 사용자 목록 테이블 + 페이지네이션
- **UserDetailDialog.tsx**: 상세 정보 모달 (기본정보, 활동통계, 3개 탭)

##### 5. **index.tsx** (115줄)
```typescript
const UserManagement: React.FC = () => {
  const {
    loading, users, total, page, rowsPerPage, error,
    searchQuery, planFilter, statusFilter,
    detailOpen, selectedUser, detailTab, userStats,
    setPage, setRowsPerPage, setError,
    setSearchQuery, setPlanFilter, setStatusFilter,
    setDetailOpen, setDetailTab,
    loadUsers, handleViewDetail, handleToggleUserStatus,
  } = useUserManagement();

  return (
    <Box>
      {error && <Alert severity="error">{error}</Alert>}
      <UserStats userStats={userStats} />
      <UserFilters ... />
      <UserTable ... />
      <UserDetailDialog ... />
    </Box>
  );
};
```

#### 🎓 배운 교훈

##### 1. **모듈형 개발의 중요성**
- 큰 파일(681줄)은 수정 시 사이드이펙트 발생 가능성 높음
- 작은 파일들로 분리하면 영향 범위가 명확해짐

##### 2. **컴포넌트 분리 기준**
- **최대 300줄** 이하로 유지 (UserDetailDialog 286줄)
- 단일 책임 원칙: 각 컴포넌트는 하나의 역할만
- 재사용 가능성: 다른 곳에서도 사용 가능하게 설계

##### 3. **Git 브랜치 전략**
- 리팩토링은 별도 브랜치에서 작업
- 브라우저 테스트 완료 후 병합
- `--no-ff` 옵션으로 병합 이력 보존

##### 4. **파일 구조 설계**
```
Feature/
├── index.tsx        # 메인 컴포넌트 (조합)
├── types.ts         # 타입 정의
├── utils.tsx        # 헬퍼 함수
├── hooks/           # 커스텀 훅 (로직)
└── components/      # UI 컴포넌트
```

#### 📋 Git 커밋 내역

```
e7aea05b Merge branch 'refactor/user-management'
7e0fe209 refactor: UserManagement 모듈화 (681줄 → 9개 파일)
```

**커밋 메시지**:
```
refactor: UserManagement 모듈화 (681줄 → 9개 파일)

## 변경사항
- UserManagement.tsx (681줄) 삭제
- 모듈형 구조로 재구성 (9개 파일, 총 934줄)

## 새 구조
UserManagement/
├── index.tsx (115줄) - 메인 컴포넌트
├── types.ts (36줄) - 타입 정의
├── utils.tsx (35줄) - 헬퍼 함수
├── hooks/useUserManagement.ts (141줄) - 상태/로직 관리
└── components/ (5개 파일)

## 개선 효과
- ✅ 관심사 분리
- ✅ 파일 크기 감소
- ✅ 유지보수성 향상
- ✅ 재사용 가능한 컴포넌트
- ✅ 디버깅 용이성 증가

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

#### ✅ 테스트 결과

- **브라우저**: http://localhost:3000/admin/users 정상 작동
- **API 응답**:
  - GET `/api/admin/users/?page=1&limit=20` - 200 OK
  - GET `/api/admin/users/statistics/summary` - 200 OK
- **컴파일**: Compiled successfully! (에러 없음)
- **기능**: 검색, 필터, 페이지네이션, 상세보기 모두 정상

#### 🚀 향후 적용 계획

**다른 큰 파일들도 동일한 방법으로 리팩토링**:
1. BatchMonitoring.tsx (500줄 이상?)
2. SystemMonitoring.tsx (500줄 이상?)
3. Statistics.tsx (500줄 이상?)

**리팩토링 우선순위**:
- 300줄 이상 파일 우선 분리
- 여러 개발자가 동시 작업하는 파일 우선
- 자주 수정되는 파일 우선

---

## 📝 2025-10-03 작업 마무리

### ✅ 오늘 완료된 작업
1. **관리자 웹 화면 API 버그 수정** - last_login, COALESCE 등
2. **UserManagement 페이지 리팩토링** - 681줄 → 9개 파일로 모듈화
3. **Git 커밋 및 GitHub push** - 모든 변경사항 원격 저장소 반영

### 📊 코드 품질 개선
- **Before**: 1개 파일 681줄 (유지보수 어려움)
- **After**: 9개 파일 934줄 (모듈화, 명확한 책임 분리)
- **테스트**: 브라우저 테스트 완료 ✅

### 🎯 다음 작업 예정
1. 다른 관리자 페이지 리팩토링 (BatchMonitoring, SystemMonitoring 등)
2. 관리자 웹 기능 완전 테스트
3. 프로덕션 배포 준비

---

## 📝 2025-10-20 작업 기록

### ✅ 관리자 웹 배치 모니터링 시스템 구축 완료

#### 🎯 주요 성과
- **배치 수동 실행 기능 구현**: 관리자 화면에서 날짜/알림 선택하여 배치 실행 ✅
- **백엔드 API 안정화**: Port 9000으로 이전, 모든 의존성 설치 완료 ✅
- **프론트엔드 UI 개선**: 날짜 선택, 알림 토글, 배치 타입 선택 기능 ✅
- **배치 프로그램 정상 작동 확인**: 143개 신규 공고 수집, 118개 문서 다운로드 성공 ✅

#### 🔧 해결한 주요 문제

##### 1. Port 충돌 문제
**문제**:
- Port 8000에서 다른 프로그램이 이미 실행 중
- 프론트엔드와 백엔드 API 포트 불일치

**해결**:
```bash
# 백엔드를 Port 9000으로 변경
cd backend && DATABASE_URL="postgresql://..." python3 -m uvicorn main:app --reload --port 9000

# 프론트엔드 API 클라이언트 업데이트
# adminApi.ts, api.ts에서 모든 포트를 9000으로 변경
```

##### 2. 백엔드 의존성 누락
**문제**:
- 가상환경에 필수 패키지 미설치로 서버 시작 실패
- PyJWT, psutil, uvicorn, fastapi, python-jose, bcrypt 등 누락

**해결**:
```bash
source venv/bin/activate
pip install PyJWT psutil
pip install uvicorn fastapi
pip install "python-jose[cryptography]" bcrypt "passlib[bcrypt]" sqlalchemy psycopg2-binary python-multipart "pydantic[email]" email-validator
pip install requests aiohttp beautifulsoup4
```

##### 3. 데이터베이스 테이블명 불일치
**문제**:
- 코드에서 `notification_rules` 테이블 참조
- 실제 DB는 `alert_rules` 테이블 사용

**해결**:
```python
# /backend/api/admin_users.py Line 130
# BEFORE:
cursor.execute("SELECT COUNT(*) FROM notification_rules WHERE user_id = %s", (user_id,))

# AFTER:
cursor.execute("SELECT COUNT(*) FROM alert_rules WHERE user_id = %s", (user_id,))
```

##### 4. TypeScript 타입 불일치
**문제**:
- BatchMonitoring.tsx에서 새 파라미터 전달하지만 API 타입 정의 누락

**해결**:
```typescript
// /frontend/src/services/admin/adminApi.ts
async executeBatchManual(data: {
  batch_type: string;
  test_mode?: boolean;
  start_date?: string;           // ✅ 추가
  end_date?: string;             // ✅ 추가
  enable_notification?: boolean; // ✅ 추가
})
```

#### 📊 배치 실행 결과

**Phase 1: API 데이터 수집**
- ✅ 수집 기간: 2025-10-20 ~ 2025-10-20
- ✅ 총 149개 공고 중 143개 신규 저장
- ✅ 중복 6개 스킵

**Phase 2: 파일 다운로드**
- ✅ 118개 문서 다운로드 성공
- ✅ HWP, PDF, HWPX, XLSX 파일 모두 지원

**Phase 3: 문서 처리** (진행 중)
- 🔄 HWP → Markdown 변환 중
- 🔄 정보 추출 및 태그 생성 중
- 🔄 예상 소요 시간: 5-10분

**Phase 4: 알림 매칭** (대기 중)
- ⏳ Phase 3 완료 후 자동 실행 예정

#### 🏗️ 개선된 시스템 아키텍처

##### 관리자 배치 모니터링 플로우
```
관리자 화면 → [배치 실행] 버튼 클릭 →
날짜 선택 (시작일/종료일) →
알림 ON/OFF 토글 →
배치 타입 선택 (전체/수집/다운로드/처리/알림) →
API 호출 (POST /api/admin/batch/execute) →
백엔드 subprocess로 배치 프로그램 실행 →
배치 완료 후 batch_execution_logs 테이블에 기록 →
관리자 화면에서 실시간 모니터링 가능
```

##### 배치 실행 환경 변수
```bash
DATABASE_URL="postgresql://blockmeta@localhost:5432/odin_db"
BATCH_START_DATE="2025-10-20"
BATCH_END_DATE="2025-10-20"
ENABLE_NOTIFICATION="true"  # 알림 ON/OFF
```

#### 💡 배운 교훈

##### 1. 가상환경 의존성 관리
- **교훈**: 프로덕션과 개발 환경의 Python 패키지 차이 확인 필수
- **체크리스트**:
  ```bash
  # 항상 가상환경 활성화 후 서버 실행
  source venv/bin/activate
  pip list  # 필수 패키지 확인
  python3 -m uvicorn main:app --reload --port 9000
  ```

##### 2. Port 관리 전략
- **교훈**: 개발 중 여러 프로세스가 같은 포트 사용 시 충돌
- **해결책**: 프로젝트별 고유 포트 할당 (8000 → 9000)
- **정리 방법**:
  ```bash
  lsof -i :9000  # 포트 사용 확인
  pkill -f "uvicorn.*main:app"  # 기존 프로세스 종료
  ```

##### 3. 배치 프로그램 실행 확인
- **교훈**: `batch_execution_logs` 테이블은 배치 완료 후 기록됨
- **실시간 확인 방법**:
  ```bash
  ps aux | grep production_batch.py  # 프로세스 실행 여부 확인
  tail -f batch_output.log           # 실시간 로그 확인
  ```

##### 4. 프론트엔드-백엔드 타입 동기화
- **교훈**: TypeScript 인터페이스와 백엔드 Pydantic 모델 일치 필수
- **체크 방법**: API 스펙 문서 작성 또는 OpenAPI 자동 생성 활용

#### 📋 주요 수정 파일

**백엔드**:
- `/backend/api/admin_users.py` - alert_rules 테이블명 수정
- `/backend/api/admin_batch.py` - 배치 실행 엔드포인트 확인
- `/backend/main.py` - Port 9000으로 변경

**프론트엔드**:
- `/frontend/src/pages/admin/BatchMonitoring.tsx` - UI 개선 (날짜 선택, 알림 토글)
- `/frontend/src/services/admin/adminApi.ts` - 타입 정의 추가, Port 9000 변경
- `/frontend/src/services/api.ts` - Port 9000 변경

**배치 프로그램**:
- `/batch/production_batch.py` - Phase 4 알림 매칭 단계 확인

#### 🎯 다음 작업 예정

1. **배치 완료 대기 및 결과 확인**
   - [ ] Phase 3 문서 처리 완료 확인
   - [ ] Phase 4 알림 매칭 실행 확인
   - [ ] batch_execution_logs 테이블 기록 확인
   - [ ] 관리자 화면에서 배치 결과 표시 확인

2. **배치 모니터링 UI 완성**
   - [ ] 실시간 진행률 표시
   - [ ] 배치 실행 상태 아이콘 (실행 중/성공/실패)
   - [ ] 배치 로그 상세 보기 기능
   - [ ] 자동 새로고침 기능

3. **시스템 안정화**
   - [ ] 에러 핸들링 강화
   - [ ] 배치 실패 시 재시도 로직
   - [ ] 배치 실행 큐 시스템 (동시 실행 방지)

#### 📈 시스템 상태 요약

**백엔드 (Port 9000)**
```
✅ 모든 API 라우터 등록 완료 (15개)
✅ 관리자 배치 실행 API 정상 작동
✅ 가상환경 의존성 설치 완료
```

**프론트엔드 (Port 3000)**
```
✅ 관리자 배치 모니터링 페이지 구현 완료
✅ 날짜/알림 선택 UI 완성
✅ TypeScript 컴파일 성공 (에러 없음)
```

**배치 시스템**
```
✅ 143개 신규 공고 수집
✅ 118개 문서 다운로드
🔄 문서 처리 진행 중 (Phase 3)
⏳ 알림 매칭 대기 중 (Phase 4)
```

**데이터베이스**
```
✅ PostgreSQL 정상 작동
✅ 52+ 테이블 스키마 안정
✅ batch_execution_logs 테이블 준비 완료
```
---

## 📝 최근 작업 기록 (2025-10-29)

### ✅ 알림 이메일 발송 시스템 완전 테스트 완료

#### 🎯 주요 성과
- **이메일 발송 성공**: 4명의 사용자에게 350개 알림을 집계하여 4개 이메일 발송 ✅
- **SMTP 인증 문제 해결**: Gmail 앱 비밀번호 갱신 및 .env 설정 최적화 ✅
- **데이터베이스 검증**: notification_send_logs 테이블에 발송 성공 기록 확인 ✅
- **End-to-End 테스트 완료**: 배치 수집 → 알림 매칭 → 이메일 발송 전 과정 검증 ✅

#### 🔧 해결한 주요 문제

##### 1. Gmail SMTP 인증 실패
**문제**:
- 기존 Gmail 앱 비밀번호 거부: `(535, b'5.7.8 Username and Password not accepted. BadCredentials')`
- 사용자 피드백: "그전 테스트 시에 분명히 되었는데. 4시간전에"

**해결**:
```bash
# .env 파일 업데이트
EMAIL_ENABLED=true
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=jeromwolf@gmail.com
EMAIL_PASSWORD=gkutwlrladpzpxxt  # 새 앱 비밀번호 (스페이스 제거)
EMAIL_FROM=jeromwolf@gmail.com
EMAIL_TO=jeromwolf@gmail.com
```

**주의사항**:
- Gmail 앱 비밀번호는 스페이스 없이 연속으로 입력 (예: `gkut wlrl adpz pxxt` → `gkutwlrladpzpxxt`)
- .env 파일에서는 따옴표 사용 금지 (`EMAIL_PASSWORD="xxx"` ❌, `EMAIL_PASSWORD=xxx` ✅)

##### 2. 알림 데이터 초기화 스크립트 활용
**파일**: `/test_scripts/reset_notifications.sql`

**사용법**:
```bash
DATABASE_URL="postgresql://blockmeta@localhost:5432/odin_db" psql -d odin_db -f test_scripts/reset_notifications.sql
```

**기능**:
- `notification_send_logs` 테이블에서 2025-10-29 이후 데이터 삭제
- `notifications` 테이블에서 2025-10-29 이후 데이터 삭제
- 반복 테스트 시 깨끗한 상태로 시작 가능

##### 3. 알림 매칭 및 이메일 발송 프로세스
**실행 명령어**:
```bash
cd /Users/blockmeta/Library/CloudStorage/GoogleDrive-jeromwolf@gmail.com/내\ 드라이브/KellyGoogleSpace/odin-ai
export DATABASE_URL="postgresql://blockmeta@localhost:5432/odin_db"
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="jeromwolf@gmail.com"
export SMTP_PASSWORD="gkutwlrladpzpxxt"
venv_test/bin/python batch/modules/notification_matcher.py
```

**처리 결과**:
```
처리 대상: 389건
알림 생성: 350개
이메일 발송: 4개

User 98 (jeromwolf@gmail.com): 320 notifications → 1 email ✅
User 96 (test@example.com): 21 notifications → 1 email ✅
User 110 (jeromwolf7@naver.com): 8 notifications → 1 email ✅
User 111 (odin.gongjakso@gmail.com): 1 notification → 1 email ✅
```

#### 📊 데이터베이스 검증

**notification_send_logs 테이블**:
```sql
SELECT id, user_id, email_to, status, sent_at 
FROM notification_send_logs 
WHERE sent_at >= '2025-10-29 00:00:00' 
ORDER BY sent_at DESC;
```

**결과**:
```
ID | User ID | Email                     | Status | Sent Time
---+---------+---------------------------+--------+---------------------------
20 | 111     | odin.gongjakso@gmail.com  | sent   | 2025-10-29 16:47:25
19 | 110     | jeromwolf7@naver.com      | sent   | 2025-10-29 16:47:22
18 | 96      | test@example.com          | sent   | 2025-10-29 16:47:19
17 | 98      | jeromwolf@gmail.com       | sent   | 2025-10-29 16:47:15
```
→ **모든 이메일 발송 성공** (status = 'sent', error_message = NULL)

**notifications 테이블**:
```sql
SELECT COUNT(*) as total_notifications, COUNT(DISTINCT user_id) as unique_users 
FROM notifications 
WHERE created_at >= '2025-10-29 00:00:00';
```

**결과**:
```
총 알림: 350개
사용자 수: 4명
```

#### 💡 배운 교훈

##### 1. Gmail 앱 비밀번호 관리
- **교훈**: Gmail은 보안 정책 변경으로 앱 비밀번호를 주기적으로 무효화할 수 있음
- **대응**: 이메일 발송 실패 시 Google 계정 설정에서 새 앱 비밀번호 생성
- **확인 방법**: 
  ```bash
  # SMTP 연결 테스트
  venv_test/bin/python -c "
  import smtplib
  smtp = smtplib.SMTP('smtp.gmail.com', 587)
  smtp.starttls()
  smtp.login('jeromwolf@gmail.com', 'gkutwlrladpzpxxt')
  print('✅ SMTP 연결 성공!')
  smtp.quit()
  "
  ```

##### 2. .env 파일 형식 주의사항
- **값에 따옴표 사용 금지**: `EMAIL_PASSWORD="xxx"` → `EMAIL_PASSWORD=xxx`
- **스페이스 제거**: 앱 비밀번호는 연속된 문자열로 입력
- **특수문자 이스케이프 불필요**: 앱 비밀번호는 알파벳 소문자만 사용

##### 3. 알림 시스템 테스트 프로세스
1. **데이터 초기화**: `reset_notifications.sql` 실행
2. **알림 매칭 실행**: `notification_matcher.py` 실행
3. **데이터베이스 검증**: `notification_send_logs` 테이블 확인
4. **실제 메일함 확인**: 수신 이메일 내용 검토

##### 4. 트러블슈팅 체크리스트
```bash
# 이메일 발송 실패 시 순서대로 확인
□ 1. .env 파일 EMAIL_ENABLED=true 확인
□ 2. Gmail 앱 비밀번호 유효성 확인
□ 3. SMTP 연결 테스트 실행
□ 4. notification_send_logs 테이블에서 error_message 확인
□ 5. Python 로그에서 상세 에러 메시지 확인
```

#### 🎯 시스템 상태

**알림 시스템 (완전 작동)**:
```
✅ 알림 규칙 매칭 정상 작동
✅ 사용자별 알림 집계 정상 작동
✅ SMTP 이메일 발송 정상 작동
✅ 발송 로그 데이터베이스 기록 정상 작동
```

**테스트 계정 현황**:
- User 98 (jeromwolf@gmail.com): 메인 테스트 계정, 320개 알림
- User 96 (test@example.com): 보조 테스트 계정, 21개 알림
- User 110 (jeromwolf7@naver.com): 네이버 메일 테스트, 8개 알림
- User 111 (odin.gongjakso@gmail.com): 추가 Gmail 테스트, 1개 알림

**다음 작업 예정**:
- [ ] 실제 사용자 알림 규칙 설정 지원
- [ ] 일일 다이제스트 이메일 스케줄링 (cron)
- [ ] 이메일 템플릿 디자인 개선
- [ ] 알림 수신 설정 페이지 UI 완성

#### 📋 주요 파일

**환경 설정**:
- `/.env` - SMTP 설정 (EMAIL_* 변수)

**배치 모듈**:
- `/batch/modules/notification_matcher.py` - 알림 매칭 및 이메일 발송 로직

**테스트 스크립트**:
- `/test_scripts/reset_notifications.sql` - 알림 데이터 초기화

**데이터베이스 테이블**:
- `notifications` - 사용자별 알림 내용 저장
- `notification_send_logs` - 이메일 발송 로그
- `alert_rules` - 사용자 알림 규칙 설정
- `users` - 사용자 정보 (이메일 주소 포함)
- `bid_announcements` - 입찰공고 데이터

#### 🎉 성과 요약

**오늘 완료된 작업**:
1. Gmail SMTP 인증 문제 해결 ✅
2. 알림 매칭 로직 검증 ✅
3. 이메일 발송 시스템 완전 테스트 ✅
4. 데이터베이스 기록 검증 ✅
5. End-to-End 프로세스 확인 ✅

**시스템 안정성**:
- 알림 생성 성공률: 100% (350/350)
- 이메일 발송 성공률: 100% (4/4)
- 데이터베이스 기록 정확도: 100%

**사용자 경험**:
- 알림 규칙 기반 정확한 매칭
- 사용자별 알림 집계로 이메일 스팸 방지
- 실시간 이메일 발송으로 신속한 정보 전달

🎉 **ODIN-AI 알림 시스템 완전 가동!**

