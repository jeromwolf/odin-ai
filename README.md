# Odin-AI 🚀

> AI 기반 공공조달 입찰정보 분석 플랫폼

## 📋 프로젝트 개요

Odin-AI는 나라장터(g2b.go.kr) 입찰정보를 AI로 분석하여 기업에게 맞춤형 프로젝트를 추천하는 B2B SaaS 플랫폼입니다.

**프로젝트 상태**: 📝 기획 단계 (문서 작성 중)

### 핵심 기능
- 🔍 **자동 RFP 모니터링**: 나라장터 입찰공고 실시간 수집
- 🤖 **AI 매칭**: 기업 역량과 RFP 요구사항 자동 매칭
- 📄 **HWP 자동 분석**: 과업지시서 AI 분석 및 요약
- 📊 **패턴 분석**: 주기성/독점 프로젝트 자동 감지
- 📧 **맞춤 알림**: 사용자 설정 시간대 메일 발송

## 🛠 기술 스택

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + Redis
- **Queue**: Celery + Redis
- **AI/ML**: OpenAI GPT-4, LangChain

### Document Processing
- **HWP**: hwp5 + LibreOffice
- **PDF**: PyPDF2, pdfplumber
- **OCR**: Tesseract

### Infrastructure
- **Container**: Docker + Kubernetes
- **Cloud**: AWS
- **Monitoring**: Grafana + Prometheus

## 📁 프로젝트 구조

```
odin-ai/
├── backend/           # FastAPI 백엔드
│   ├── api/          # API 엔드포인트
│   ├── core/         # 핵심 설정
│   ├── models/       # 데이터 모델
│   ├── services/     # 비즈니스 로직
│   └── tasks/        # Celery 태스크
├── crawler/          # 크롤링 시스템
│   ├── g2b/         # 나라장터 크롤러
│   └── api/         # 공공데이터 API
├── ml/              # AI/ML 모듈
│   ├── matcher/     # 매칭 알고리즘
│   └── analyzer/    # 문서 분석
├── docker/          # Docker 설정
└── docs/            # 문서
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

5. **데이터베이스 마이그레이션**
```bash
alembic upgrade head
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

## 📚 프로젝트 문서

### 핵심 문서
- **[PRD.md](PRD.md)** - 제품 요구사항 문서 (Product Requirements Document)
  - 비즈니스 목표, 사용자 스토리, 기능 명세
- **[TECHNICAL_SPEC.md](TECHNICAL_SPEC.md)** - 기술 명세서
  - 시스템 아키텍처, 데이터 수집 전략, 기술 스택
- **[CLAUDE.md](CLAUDE.md)** - AI 도우미 개발 가이드
  - 코딩 컨벤션, 개발 규칙

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