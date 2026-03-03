# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## 최우선 원칙

1. **개인정보 보호**: 어떤 상황에서도 로그에 개인정보를 남기지 않는다
2. **모듈형 개발**: 공통 파일(api.ts, main.py) 직접 수정 금지, 새 기능은 새 파일에
3. **한 번에 하나씩**: 여러 기능 동시 작업 금지, 각 단계마다 테스트

---

## 프로젝트 개요

**ODIN-AI**: 나라장터 공공입찰 정보를 자동 수집/분석하여 맞춤형 알림을 제공하는 B2B SaaS 플랫폼

- **핵심 가치**: 사용자 맞춤형 입찰공고 알림 (알림이 메인 서비스)
- **현재 단계**: MVP → Beta 전환 중 (기반 안정화 필요)
- **데이터**: 입찰공고 ~19,000건, 사용자 112명

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | FastAPI (Python 3.11+), Port 9000 |
| Database | PostgreSQL 15 + pgvector |
| Frontend | React 18 + TypeScript + Material-UI 5 |
| State | React Query v5 |
| Cache | Redis 7 (선택적) |
| Graph DB | Neo4j 5.15 |
| Embedding | sentence-transformers KURE-v1 (1024dim) |
| LLM | Ollama (exaone3.5:7.8b) |
| E2E Test | Playwright |
| Auth | JWT (python-jose + bcrypt) |

---

## 프로젝트 구조

```
odin-ai/
├── backend/                  # FastAPI 백엔드
│   ├── api/                  # 20개 API 라우터
│   │   ├── auth.py           # 사용자 인증
│   │   ├── search.py         # 입찰 검색
│   │   ├── bookmarks.py      # 북마크
│   │   ├── notifications.py  # 알림 설정
│   │   ├── dashboard.py      # 대시보드
│   │   ├── rag_search.py     # RAG 벡터 검색
│   │   ├── graph_search.py   # 그래프 탐색
│   │   ├── admin_*.py        # 관리자 API (8개)
│   │   └── ...
│   ├── services/             # 비즈니스 로직 (11개)
│   │   ├── email_service.py
│   │   ├── notification_service.py
│   │   ├── embedding_service.py
│   │   ├── hybrid_search.py
│   │   └── ...
│   ├── tests/                # pytest (9개)
│   └── database.py           # DB 커넥션 풀 (psycopg2)
├── batch/                    # 배치 처리 시스템
│   ├── modules/
│   │   ├── collector.py      # Phase 1: API 수집
│   │   ├── award_collector.py# Phase 1.5: 낙찰정보
│   │   ├── downloader.py     # Phase 2: 파일 다운로드
│   │   ├── processor.py      # Phase 3: 문서 처리
│   │   ├── embedding_generator.py  # Phase 3.5: 임베딩
│   │   ├── neo4j_syncer.py   # Phase 3.6: 그래프 동기화
│   │   ├── graphrag_indexer.py     # Phase 3.7: GraphRAG
│   │   ├── notification_matcher.py # Phase 4: 알림 매칭
│   │   ├── email_reporter.py # Phase 5: 보고서
│   │   └── daily_digest.py   # Phase 5.5: 일일 다이제스트
│   └── production_batch.py   # 메인 오케스트레이터
├── frontend/                 # React 프론트엔드
│   ├── src/
│   │   ├── pages/            # 16개 사용자 페이지
│   │   ├── pages/admin/      # 9개 관리자 페이지
│   │   ├── components/       # 공통 컴포넌트
│   │   └── services/         # API 클라이언트
│   ├── e2e/                  # Playwright E2E (24 스펙, 59건)
│   └── docker-compose.yml    # 전체 스택 Docker
├── sql/                      # DB 스키마 (16개 SQL)
│   ├── init.sql              # 마스터 초기화
│   ├── create_alert_tables.sql
│   ├── create_rag_tables.sql
│   └── ...
├── src/                      # 핵심 문서 처리 (레거시)
├── services/                 # 별도 알림 서비스
├── storage/                  # 파일 저장소 (문서 3.7GB)
└── .env                      # 환경변수 설정
```

---

## 주요 명령어

```bash
# 가상환경 활성화 (필수!)
source venv/bin/activate

# 백엔드 실행
cd backend && DATABASE_URL="postgresql://blockmeta@localhost:5432/odin_db" \
  python -m uvicorn main:app --reload --port 9000

# 프론트엔드 실행
cd frontend && npm start    # Port 3000, proxy → 9000

# 배치 실행 (프로덕션 - 증분 업데이트)
DATABASE_URL="postgresql://blockmeta@localhost:5432/odin_db" \
  python batch/production_batch.py

# 배치 실행 (전체 초기화)
DB_FILE_INIT=true TEST_MODE=false \
  DATABASE_URL="postgresql://blockmeta@localhost:5432/odin_db" \
  python batch/production_batch.py

# 테스트
cd backend && pytest tests/                    # 단위 테스트
cd frontend && npx playwright test             # E2E 테스트
```

---

## DB 스키마 핵심 테이블

| 테이블 | PK | 역할 |
|--------|-----|------|
| `bid_announcements` | `bid_notice_no` (VARCHAR 20) | 입찰공고 메인 |
| `bid_documents` | `document_id` (SERIAL) | 문서 메타 |
| `bid_extracted_info` | `info_id` (SERIAL) | 추출 정보 (JSONB) |
| `bid_tags` / `bid_tag_relations` | M:N | 태그 시스템 |
| `users` | `id` (SERIAL) | 사용자 |
| `alert_rules` | `rule_id` (SERIAL) | 알림 규칙 |
| `notifications` | `id` (SERIAL) | 발송된 알림 |
| `rfp_chunks` | `chunk_id` (SERIAL) | RAG 벡터 (1024dim) |
| `graphrag_entities` | `id` (SERIAL) | GraphRAG 엔티티 |

### alert_rules.conditions JSON 구조
```json
{
  "keywords": ["도로", "포장"],
  "min_price": 50000000,    // 신형식
  "max_price": 200000000,
  "price_min": 50000000,    // 구형식 (하위 호환)
  "price_max": 200000000,
  "regions": ["경기도", "서울특별시"]
}
```
**주의**: `min_price`/`max_price`와 `price_min`/`price_max` 두 형식이 혼재. 코드에서 양쪽 모두 지원해야 함.

---

## 알림 매칭 시스템 (핵심 비즈니스)

### 배치 파이프라인
```
API 수집 → 다운로드 → 문서 처리 → [임베딩] → [Neo4j] → [GraphRAG]
→ 알림 매칭 → 이메일 발송 → 보고서
```

### 알림 매칭 로직 수정 시 필수 체크리스트
1. DB 스키마 확인: `psql -d odin_db -c "\d alert_rules"`
2. conditions JSON 실제 키 확인 (min_price vs price_min)
3. 테스트 데이터로 매칭 검증
4. 가격 범위 경계값 테스트
5. 로그로 필터 작동 확인

---

## 개발 규칙

### 기능 추가 전 체크리스트
```
[ ] 현재 작동 중인 기능 확인
[ ] 영향 범위 분석 (새 파일만 수정하는지)
[ ] 각 단계마다 기존 기능 테스트
[ ] 문제 발생 시 즉시 롤백
```

### 절대 금지
- 공통 파일 직접 수정 (`api.ts`, `main.py` 최소 수정)
- 여러 기능 동시 작업
- import 경로 일괄 변경
- 테스트 없이 커밋
- 기존 테이블/컬럼 삭제 (운영 중)
- 로그에 개인정보 포함

### 환경변수 주의사항
- SMTP: `EMAIL_HOST` / `EMAIL_PASSWORD` 사용 (Gmail 앱 비밀번호, 스페이스 제거)
- .env에서 따옴표 금지: `EMAIL_PASSWORD=abcdefgh` (O) / `EMAIL_PASSWORD="abcdefgh"` (X)

---

## 알려진 기술 부채

### 즉시 해결 필요
1. **스키마 이중화**: `init.sql`과 `create_alert_tables.sql`의 `alert_matches` 정의 불일치
2. **이메일 코드 5중 분산**: `email_service.py`, `notification_service.py`, `notifications.py`, `notification_matcher.py`, `services/alert/sender.py`
3. **notification_matcher.py 테스트 없음**: 핵심 비즈니스 로직에 단위 테스트 0개

### 중기 과제
4. **ORM 미사용**: SQLAlchemy 모델 정의되어 있으나 전부 raw SQL (psycopg2) 사용
5. **거대 파일**: Search.tsx (1,103줄), notifications.py (920줄) 분할 필요
6. **레거시 코드**: `src/services/document_processor.py`가 `batch/modules/processor.py`와 중복

---

## 과거 버그 교훈 (요약)

| # | 버그 | 근본 원인 | 교훈 |
|---|------|-----------|------|
| 1 | 가격 필터 무작동 | `price_min` vs `min_price` 키 불일치 | DB 스키마-코드 일관성 검증 필수 |
| 2 | 알림 시간 범위 부족 | `since_hours=4` 기본값 너무 짧음 | 운영 환경 기본값 신중히 |
| 3 | TS 타입 중복 | interface/const 이름 충돌 | 네이밍 규칙 준수 |
| 4 | 통계 API 컬럼명 오류 | `publish_date` vs `announcement_date` | 쿼리 전 DB 스키마 확인 |

상세 기록: `docs/CHANGELOG.md`

---

## 확장 로드맵

| Phase | 목표 | 상태 |
|-------|------|------|
| Phase 1 | MVP 안정화, 배포 | 진행 중 |
| Phase 2 | RAG 벡터 검색 고도화 | 임베딩 45.7% |
| Phase 3 | 온톨로지 기반 지식 그래프 | 스키마 존재, 미활성 |
