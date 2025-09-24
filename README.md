# Odin-AI 🚀

> AI 기반 공공조달 입찰정보 분석 플랫폼

## 📋 프로젝트 개요

Odin-AI는 나라장터(g2b.go.kr) 입찰정보를 AI로 분석하여 기업에게 맞춤형 프로젝트를 추천하는 B2B SaaS 플랫폼입니다.

**프로젝트 상태**: ✅ Phase 1 MVP 완료 및 배치 시스템 검증 (2025-09-24)

### 핵심 기능
- 🔍 **자동 RFP 모니터링**: 나라장터 입찰공고 실시간 수집 ✅
- 🤖 **문서 처리**: HWP/PDF/XLSX 자동 파싱 및 정보 추출 ✅
- 📄 **표 파싱**: 입찰 정보 테이블 100% 추출 성공 ✅
- 📊 **고도화 분석**: 공사기간, 지역제한, 하도급 정보 추출 ✅
- 🔄 **배치 시스템**: 자동화된 수집-처리-분석 파이프라인 ✅
- 📧 **이메일 리포트**: HTML/JSON 형식 자동 보고서 ✅

## 📊 최신 성능 지표 (2025-09-24)

### 배치 실행 결과
- **API 수집**: 69개 공고 (오늘 날짜)
- **파일 다운로드**: 67개 (100% 성공)
- **문서 처리**: 63개 성공, 3개 실패, 1개 스킵 (94% 성공률)
- **정보 추출**: 63개 문서에서 335개 정보 추출
- **처리 시간**: 90.3초

### 지원 파일 형식
| 형식 | 지원 | 처리 개수 | 성공률 |
|------|------|-----------|--------|
| HWP  | ✅   | 52        | 100%   |
| PDF  | ✅   | 6         | 100%   |
| HWPX | ✅   | 4         | 25%    |
| XLSX | ✅   | 2         | 100%   |
| XLS  | ✅   | 2         | 100%   |
| ZIP  | ❌   | 1         | -      |

## 🛠 기술 스택

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + Redis
- **Queue**: Celery + Redis
- **AI/ML**: OpenAI GPT-4, LangChain

### Document Processing
- **HWP**: hwp5txt (100% 성공률)
- **PDF**: PyPDF2, pdfplumber
- **표 파싱**: regex 기반 패턴 매칭
- **정보 추출**: EnhancedInfoExtractor

### Infrastructure
- **Container**: Docker + Kubernetes
- **Cloud**: AWS
- **Monitoring**: Grafana + Prometheus

## 📁 프로젝트 구조

```
odin-ai/
├── batch/                    # 배치 시스템 (모듈화)
│   ├── modules/             # 개별 모듈
│   │   ├── collector.py     # API 수집
│   │   ├── downloader.py    # 파일 다운로드
│   │   ├── processor.py     # 문서 처리
│   │   └── email_reporter.py # 보고서 발송
│   └── production_batch.py  # 메인 오케스트레이터
├── backend/                 # FastAPI 백엔드
│   ├── api/                # API 엔드포인트
│   ├── services/           # 비즈니스 로직
│   └── database/           # DB 모델
├── src/                     # 핵심 모듈
│   ├── collector/          # 데이터 수집
│   ├── services/           # 문서 처리
│   ├── database/           # DB 모델 (확장)
│   └── core/               # 설정 관리
├── storage/                 # 파일 저장소
│   ├── documents/          # 다운로드 문서
│   └── markdown/           # 변환된 MD
├── testing/                 # 테스트 스크립트
│   ├── test_scripts/       # 기능 테스트
│   ├── integration/        # 통합 테스트
│   └── reports/            # 테스트 보고서
└── docs/                   # 프로젝트 문서
    ├── BATCH_PRODUCTION_REQUIREMENTS.md  # 배치 요구사항
    ├── BATCH_IMPROVEMENTS.md             # 개선사항
    └── FULL_TEST_TASKS_V4.md            # 테스트 태스크
```

## 🚀 시작하기

### 사전 요구사항
- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Docker & Docker Compose

### 설치 방법

1. **저장소 클론**
```bash
git clone https://github.com/yourusername/odin-ai.git
cd odin-ai
```

2. **가상환경 설정**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **의존성 설치**
```bash
pip install -r requirements.txt
```

4. **환경변수 설정**
```bash
cp .env.example .env
# .env 파일 수정
```

5. **데이터베이스 설정**
```bash
export DATABASE_URL="postgresql://username@localhost:5432/odin_db"
python setup_database.py --create
```

6. **개발 서버 실행**
```bash
uvicorn backend.main:app --reload --port 8000
```

### Docker 실행

```bash
docker-compose up -d
```

## 📊 API 문서

서버 실행 후 접속:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 테스트

### 배치 시스템 실행
```bash
# 프로덕션 모드 (일일 배치)
python batch/production_batch.py

# 테스트 모드 (DB 초기화 포함)
TEST_MODE=true python batch/production_batch.py

# 완전 초기화 모드 (DB DROP + 파일 삭제)
DB_FILE_INIT=true python batch/production_batch.py
```

### 단위 테스트
```bash
# 단위 테스트
pytest tests/unit

# 통합 테스트
pytest tests/integration

# 커버리지 확인
pytest --cov=backend tests/
```

## 📈 개선 계획

### 🔴 즉시 개선 필요
1. **중복 체크 로직**: 업데이트된 공고 반영
2. **정보 추출 패턴**: 다양한 표현 방식 지원

### 🟡 중요 개선사항
1. **트랜잭션 관리**: 데이터 일관성 보장
2. **에러 핸들링**: 원인별 재시도 전략
3. **HWPX 처리**: 실패 원인 분석 및 개선

### 🟢 향후 개선사항
1. **ZIP 파일 처리**: 압축 파일 내부 문서 처리
2. **실시간 모니터링**: 진행률 및 성능 메트릭
3. **AI 분석**: GPT-4 통합 및 RAG 시스템

상세 내용: [`docs/BATCH_IMPROVEMENTS.md`](docs/BATCH_IMPROVEMENTS.md)

## 📈 현재 성과 (2025-09-23)

### Phase 1 MVP 완료
- ✅ **API 연동**: 95개 최신 공고 수집
- ✅ **표 파싱**: 100% 성공률 (17/17 파일)
- ✅ **정보 추출**: 7개 카테고리 600+ 데이터포인트
- ✅ **DB 확장**: 고도화된 정보 저장 스키마
- ✅ **프로젝트 정리**: 체계적 디렉토리 구조

### 주요 성능 지표
- 문서 처리 성공률: 100%
- 표 파싱 정확도: 100%
- 정보 추출 카테고리: prices, schedule, qualifications, duration, region, subcontract
- 신뢰도 점수: 평균 0.85 이상

## 📚 프로젝트 문서

### 핵심 문서
- **[PRD.md](PRD.md)** - 제품 요구사항 문서 (Product Requirements Document)
  - 비즈니스 목표, 사용자 스토리, 기능 명세
- **[TECHNICAL_SPEC.md](TECHNICAL_SPEC.md)** - 기술 명세서
  - 시스템 아키텍처, 데이터 수집 전략, 기술 스택
- **[CLAUDE.md](CLAUDE.md)** - 개발 가이드 및 프로젝트 컨텍스트
  - 최신 진행 상황, 주의사항, 트러블슈팅

### 분석 문서  
- **[competitor_analysis.md](competitor_analysis.md)** - 경쟁사 분석
  - 케이비드, 인포21C 등 벤치마킹

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 문의

- Email: contact@odin-ai.kr
- Website: https://odin-ai.kr

## 🙏 감사의 글

- 나라장터 공공데이터
- OpenAI GPT-4
- FastAPI Community

---

**Odin-AI** - 공공조달의 미래를 AI와 함께 🚀