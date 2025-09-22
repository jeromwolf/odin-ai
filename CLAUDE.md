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

## Project Context Summary (2025-09-23)

### 🚀 프로젝트 현황
- **현재 날짜**: 2025년 9월 23일
- **단계**: ✅ **Phase 1 MVP 완전 구현 및 검증 완료**
- **프로젝트명**: ODIN-AI (공공입찰 정보 분석 플랫폼)

### ✅ 완료된 작업 (2025-09-23 기준)

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

### 🎯 다음 단계 (Phase 2)

1. **검색 시스템 구현**
   - PostgreSQL Full-text search
   - 벡터 검색 (임베딩)
   - 실시간 자동완성

2. **AI 분석 기능**
   - GPT-4 통합
   - RAG 시스템 구현
   - 입찰 성공률 예측 모델

3. **사용자 인터페이스**
   - React 프론트엔드
   - 대시보드 구현
   - 실시간 알림 시스템

### 🔑 주요 명령어

```bash
# 환경 설정
source venv/bin/activate
export DATABASE_URL="postgresql://blockmeta@localhost:5432/odin_db"

# 테스트 실행
python test_scripts/test_small_batch.py  # 작은 배치 테스트
python test_scripts/test_improved_batch.py  # 개선된 배치 테스트

# 서버 실행
uvicorn backend.main:app --reload --port 8000

# 데이터베이스 초기화
python setup_database.py --create
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