# ODIN-AI: 공공입찰 정보 분석 플랫폼

나라장터(g2b.go.kr) 입찰정보를 자동 수집/분석하여 기업에게 맞춤형 알림을 제공하는 B2B SaaS 플랫폼

## 핵심 기능

- **자동 수집**: 공공데이터포털 API로 입찰공고 자동 수집 (~19,000건)
- **문서 분석**: HWP/PDF/XLSX 자동 파싱, 정보 추출 (93.9% 성공률)
- **맞춤 알림**: 키워드/가격/지역 기반 사용자별 이메일 알림
- **하이브리드 검색**: 키워드 + RAG 벡터 + 그래프 검색
- **관리자 대시보드**: 배치 모니터링, 사용자 관리, 통계 분석

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | FastAPI (Python 3.11+) |
| Database | PostgreSQL 15 + pgvector + Neo4j 5.15 |
| Frontend | React 18 + TypeScript + Material-UI 5 |
| AI/ML | sentence-transformers (KURE-v1), Ollama (exaone3.5) |
| Infra | Docker Compose, Redis, Nginx |
| Test | Playwright E2E (59건), pytest |

## 빠른 시작

```bash
# 1. 클론 및 환경 설정
git clone https://github.com/yourusername/odin-ai.git
cd odin-ai
cp .env.example .env   # 환경변수 편집

# 2. Docker로 실행
docker-compose -f frontend/docker-compose.yml up -d

# 또는 로컬 실행
source venv/bin/activate
cd backend && DATABASE_URL="postgresql://user@localhost:5432/odin_db" \
  python -m uvicorn main:app --reload --port 9000
cd frontend && npm start
```

### 접속 URL

| 서비스 | URL |
|--------|-----|
| 프론트엔드 | http://localhost:3000 |
| 백엔드 API | http://localhost:9000 |
| API 문서 (Swagger) | http://localhost:9000/docs |
| 관리자 패널 | http://localhost:3000/admin |

## 프로젝트 구조

```
odin-ai/
├── backend/                  # FastAPI 백엔드
│   ├── api/                  # API 라우터 (20개)
│   ├── services/             # 비즈니스 로직 (11개)
│   └── tests/                # pytest
├── batch/                    # 배치 처리 시스템
│   ├── modules/              # 수집/다운로드/처리/알림 (10개 모듈)
│   └── production_batch.py   # 오케스트레이터
├── frontend/                 # React 프론트엔드
│   ├── src/pages/            # 사용자 16 + 관리자 9 페이지
│   ├── e2e/                  # Playwright E2E 테스트
│   └── docker-compose.yml    # 전체 스택 Docker
├── sql/                      # DB 스키마 (16개 SQL)
└── storage/                  # 문서 저장소
```

## 배치 파이프라인

```
Phase 1:   API 수집 (collector.py)
Phase 1.5: 낙찰정보 수집 (award_collector.py)
Phase 2:   파일 다운로드 (downloader.py)
Phase 3:   문서 처리 (processor.py)
Phase 3.5: 임베딩 생성 (embedding_generator.py)
Phase 3.6: Neo4j 동기화 (neo4j_syncer.py)
Phase 3.7: GraphRAG 인덱싱 (graphrag_indexer.py)
Phase 4:   알림 매칭 (notification_matcher.py)
Phase 5:   이메일 보고서 (email_reporter.py)
```

```bash
# 배치 실행 (증분)
source venv/bin/activate
DATABASE_URL="postgresql://user@localhost:5432/odin_db" \
  python batch/production_batch.py

# 배치 실행 (전체 초기화)
DB_FILE_INIT=true python batch/production_batch.py
```

## 검색 API

```http
GET /api/search?q=도로공사&min_price=100000000&organization=서울
```

| 파라미터 | 설명 | 예시 |
|---------|------|------|
| `q` | 검색어 | 건설, 소프트웨어 |
| `start_date` / `end_date` | 기간 | 2025-09-01 |
| `min_price` / `max_price` | 가격 범위 | 100000000 |
| `organization` | 기관명 | 서울, 경기 |
| `sort` | 정렬 | price_desc, date_asc |

## 테스트

```bash
# Backend 단위 테스트
cd backend && pytest tests/

# Frontend E2E 테스트
cd frontend && npx playwright test

# 특정 테스트만
npx playwright test e2e/admin/
```

## 주요 문서

| 문서 | 설명 |
|------|------|
| [CLAUDE.md](CLAUDE.md) | 개발 가이드 및 프로젝트 컨텍스트 |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | 변경 이력 및 버그 수정 기록 |
| [TODO_FUTURE_TASKS.md](TODO_FUTURE_TASKS.md) | 향후 작업 계획 |

## 라이선스

MIT License
