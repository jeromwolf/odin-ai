# Odin-AI 프로젝트 구조

## 디렉토리 구조

```
odin-ai/
├── backend/                # 메인 백엔드 서비스
│   ├── api/               # FastAPI 라우터
│   ├── core/              # 핵심 설정
│   ├── models/            # 데이터베이스 모델
│   └── services/          # 비즈니스 로직
│       ├── document_processor.py           # 로컬 문서 처리
│       └── integrated_document_processor.py # Docker 통합 처리
│
├── tools/                  # 문서 처리 도구 (통합됨)
│   ├── hwp-viewer/        # HWP 문서 처리 서비스
│   └── pdf-viewer/        # PDF 문서 처리 서비스
│
├── tests/                  # 테스트 파일 (정리됨)
│   ├── test_document_processor.py
│   ├── test_docker_integration.py
│   └── test_integration.py
│
├── storage/                # 파일 저장소
│   ├── downloads/         # 다운로드된 원본 파일
│   │   ├── hwp/
│   │   ├── pdf/
│   │   ├── doc/
│   │   └── unknown/
│   └── processed/         # 처리된 파일 (MD 변환)
│       ├── hwp/
│       ├── pdf/
│       ├── doc/
│       └── unknown/
│
├── scripts/                # 관리 스크립트
│   └── manage-docker.sh   # Docker 통합 관리 스크립트
│
├── docs/                   # 프로젝트 문서
│   └── TASK_MANAGEMENT.md # 태스크 관리 체크리스트
│
├── docker-compose.yml      # Docker 통합 설정 (tools 포함)
├── Dockerfile             # 메인 애플리케이션 Dockerfile
├── requirements.txt       # Python 의존성
├── .env                   # 환경 변수
├── CLAUDE.md             # Claude AI 가이드라인
├── PRD.md                # 제품 요구사항 문서
└── TECHNICAL_SPEC.md     # 기술 명세서

```

## 주요 변경사항 (2025-09-16)

### 1. tools 디렉토리 통합
- 기존 별도 관리되던 tools 디렉토리를 odin-ai 프로젝트로 통합
- GitHub 저장소에 모든 코드가 포함되도록 구성
- Docker Compose에서 통합 관리

### 2. 테스트 파일 정리
- 루트 디렉토리의 test_*.py 파일들을 tests/ 폴더로 이동
- 깔끔한 프로젝트 구조 유지

### 3. Docker 관리 개선
- docker-compose.yml 업데이트: HWP/PDF 서비스 포함
- scripts/manage-docker.sh: 통합 관리 스크립트
- 서비스 간 네트워크 통합 및 볼륨 공유

### 4. 문서 처리 시스템 강화
- IntegratedDocumentProcessor: Docker 서비스 우선 사용
- 자동 폴백 메커니즘: Docker 실패 시 로컬 처리
- 병렬 처리 지원

## Docker 서비스 구성

| 서비스 | 포트 | 설명 |
|--------|------|------|
| postgres | 5432 | PostgreSQL 데이터베이스 |
| redis | 6379 | Redis 캐시/큐 |
| backend | 8123 | FastAPI 백엔드 |
| worker | - | Celery 워커 |
| hwp-viewer | 8002 | HWP 문서 처리 |
| pdf-viewer | 8003 | PDF 문서 처리 |

## 빠른 시작

```bash
# 1. Docker 서비스 시작
./scripts/manage-docker.sh setup

# 2. 상태 확인
./scripts/manage-docker.sh status

# 3. 테스트 실행
./scripts/manage-docker.sh test

# 4. 로그 확인
./scripts/manage-docker.sh logs backend -f
```

## GitHub 업로드

이제 모든 코드가 odin-ai 디렉토리 내에 통합되어 GitHub에 완전히 업로드됩니다:

```bash
git add -A
git commit -m "feat: Docker 통합 완료 - tools 디렉토리 통합 및 프로젝트 구조 정리"
git push origin main
```

## 환경 변수 설정

`.env` 파일에 다음 설정 추가:
```
# Docker 서비스 URL
HWP_SERVICE_URL=http://hwp-viewer:8002
PDF_SERVICE_URL=http://pdf-viewer:8003
```