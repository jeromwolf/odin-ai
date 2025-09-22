# Odin-AI 🚀

> AI 기반 공공조달 입찰정보 분석 플랫폼

## 📋 프로젝트 개요

Odin-AI는 나라장터(g2b.go.kr) 입찰정보를 AI로 분석하여 기업에게 맞춤형 프로젝트를 추천하는 B2B SaaS 플랫폼입니다.

**프로젝트 상태**: ✅ Phase 1 MVP 완료 (2025-09-23)

### 핵심 기능
- 🔍 **자동 RFP 모니터링**: 나라장터 입찰공고 실시간 수집 ✅
- 🤖 **문서 처리**: HWP/PDF 자동 파싱 및 정보 추출 ✅
- 📄 **표 파싱**: 입찰 정보 테이블 100% 추출 성공 ✅
- 📊 **고도화 분석**: 공사기간, 지역제한, 하도급 정보 추출 ✅
- 📧 **데이터베이스**: PostgreSQL 확장 스키마 구현 ✅

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
├── backend/           # FastAPI 백엔드
│   ├── api/          # API 엔드포인트
│   ├── services/     # 비즈니스 로직
│   └── database/     # DB 모델
├── src/              # 핵심 모듈
│   ├── collector/    # 데이터 수집
│   ├── services/     # 문서 처리
│   ├── database/     # DB 모델 (확장)
│   └── core/         # 설정 관리
├── storage/          # 파일 저장소
│   ├── documents/    # 다운로드 문서
│   └── markdown/     # 변환된 MD
├── testing/          # 테스트 스크립트
│   ├── test_scripts/ # 기능 테스트
│   ├── integration/  # 통합 테스트
│   └── completed/    # 완료 테스트
└── docs/            # 프로젝트 문서
    ├── PRD.md       # 제품 기획서
    └── TECHNICAL_SPEC.md  # 기술 명세서
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

```bash
# 단위 테스트
pytest tests/unit

# 통합 테스트
pytest tests/integration

# 커버리지 확인
pytest --cov=backend tests/
```

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