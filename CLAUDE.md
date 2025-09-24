# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ 최우선 원칙: 개인정보 보호

**절대 규칙**: 어떤 상황에서도 로그에 개인정보를 남기지 않습니다.

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

## Project Context Summary (2025-09-25 업데이트)

### 🚀 프로젝트 현황
- **현재 날짜**: 2025년 9월 25일
- **단계**: ✅ **Phase 2 검색 및 대시보드 완성**
- **프로젝트명**: ODIN-AI (공공입찰 정보 분석 플랫폼)

### ✅ 완료된 작업 (2025-09-25 기준)

#### 🔍 검색 시스템 완성 (2025-09-25)
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

### 📝 최근 변경사항 (2025-09-23)

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
# 프로덕션 실행
python batch/production_batch.py

# 테스트 모드 (DB 초기화 포함)
TEST_MODE=true python batch/production_batch.py

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