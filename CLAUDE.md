# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ 최우선 원칙: 개인정보 보호

**절대 규칙**: 어떤 상황에서도 로그에 개인정보를 남기지 않습니다.

## Project Context Summary (2025-09-22)

### 🚀 프로젝트 현황
- **현재 날짜**: 2025년 9월 22일
- **단계**: ✅ **문서 처리 파이프라인 구축 및 검증 완료**
- **프로젝트명**: ODIN-AI (공공입찰 정보 분석 플랫폼)

### ✅ 완료된 작업 (2025-09-22 기준)

#### 📊 데이터 수집 및 처리 시스템
- ✅ 공공데이터포털 API 연동 완료 (429개 공고 수집)
- ✅ 대용량 파일 다운로드 시스템 구현 (1,222개 문서)
- ✅ 문서 처리 파이프라인 구축
  - HWP: 100% 성공률 (hwp5txt 사용)
  - PDF: 100% 성공률 (PyPDF2/pdfplumber 사용)
  - HWPX: 100% 성공률 (XML 파싱)
  - Excel: 100% 성공률 (xlrd/openpyxl 사용)

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
- **Database**: PostgreSQL + SQLAlchemy
- **Queue**: Celery + Redis (예정)
- **비동기 처리**: asyncio, aiohttp

#### 문서 처리
- **HWP**: hwp5, hwp-viewer 통합
- **PDF**: PyPDF2, pdfplumber, pymupdf
- **Excel**: pandas, xlrd, openpyxl
- **HWPX**: zipfile + XML 파싱

### 📈 성능 지표

- **API 수집**: 일일 475건+ 가능
- **파일 다운로드**: 1,222개 문서 완료
- **문서 처리 성공률**:
  - HWP: 100% (872개)
  - PDF: 100% (76개)
  - HWPX: 100% (35개)
  - Excel: 100% (216개)
- **처리 속도**: 0.10초/문서 (병렬 처리 시)

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

### 📝 최근 변경사항 (2025-09-22)

- ✅ 테스트 파일 정리 (test_scripts/ 폴더로 이동)
- ✅ Excel 파일 처리 지원 추가
- ✅ 배치 처리 시스템 개선
- ✅ 설정 관리 시스템 구현
- ✅ 문서 처리 100% 성공률 달성

### 🔧 트러블슈팅

**문제**: XLS 파일 처리 실패
- **해결**: `pip install xlrd openpyxl`

**문제**: 대용량 처리 시 타임아웃
- **해결**: config.py에서 batch_size와 timeout 조정

**문제**: HWP 파일 인코딩 오류
- **해결**: hwp5txt fallback 메커니즘 사용