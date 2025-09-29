# 🏛️ ODIN-AI: 공공입찰 정보 분석 플랫폼

<div align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue.svg" />
  <img src="https://img.shields.io/badge/python-3.11+-green.svg" />
  <img src="https://img.shields.io/badge/react-18.0-61dafb.svg" />
  <img src="https://img.shields.io/badge/postgresql-15.0-336791.svg" />
  <img src="https://img.shields.io/badge/status-production-success.svg" />
</div>

## 📋 프로젝트 개요

ODIN-AI는 나라장터(g2b.go.kr) 입찰정보를 AI로 분석하여 기업에게 맞춤형 프로젝트를 추천하는 B2B SaaS 플랫폼입니다.

**프로젝트 상태**: ✅ Phase 3 전체 사용자 인터페이스 구현 완료 (2025-09-26)

### ✨ 핵심 기능
- 🔍 **고도화된 검색**: 태그 기반 통합검색, URL 파라미터 지원 ✅
- 📊 **인터랙티브 대시보드**: 클릭 가능한 차트, 실시간 드릴다운 ✅
- 🎯 **스마트 네비게이션**: 차트→검색 원클릭 이동 ✅
- 🤖 **문서 처리**: HWP/PDF/XLSX 자동 파싱 및 정보 추출 ✅
- 🏷️ **스마트 태그**: 자동 카테고리 분류 및 품질 검증 ✅
- 📄 **표 파싱**: 입찰 정보 테이블 100% 추출 성공 ✅
- 🎨 **모던 UI**: React + TypeScript + Material-UI 반응형 디자인 ✅
- 🔔 **알림 설정**: 키워드 및 가격대별 맞춤 알림 (이메일/푸시) ✅
- 👤 **프로필 관리**: 사용자 정보 편집 및 활동 통계 ✅
- ⚙️ **환경 설정**: 테마, 언어, 데이터 관리 기능 ✅
- 💳 **구독 관리**: 3단계 요금제 (베이직/프로/엔터프라이즈) ✅
- 🔄 **배치 시스템**: 자동화된 수집-처리-분석 파이프라인 ✅
- 📧 **이메일 리포트**: HTML/JSON 형식 자동 보고서 ✅

## 🚀 빠른 시작

```bash
# 1. 저장소 클론
git clone https://github.com/yourusername/odin-ai.git
cd odin-ai

# 2. 가장 간단한 실행
./start-simple.sh

# 또는 새 터미널로 실행
./quick-start.sh
```

### 접속 URL
- 🌐 **프론트엔드**: http://localhost:3000
- 🔧 **백엔드 API**: http://localhost:8000
- 📚 **API 문서**: http://localhost:8000/docs

### 🎯 테스트 계정 정보
- **이메일**: demo@odin-ai.com
- **비밀번호**: demo123456
- **사용자명**: demo_user

## 📊 최신 성능 지표 (2025-09-29)

### 시스템 현황
- **DB 저장 공고**: 469개 (실시간 검색 가능)
- **활성 입찰**: 410개
- **총 예정가격**: 1,250억원
- **문서 처리 성공률**: 93.9% (355/380)
- **검색 응답 시간**: ~100ms (Redis 캐시)

## 🆕 최근 업데이트 (2025-09-29)

### 🔧 버그 수정 및 개선
- **대시보드 시간 표시 수정**: "NaN시간 남음" → 정상 시간 표시 ✅
- **파이차트 퍼센트 수정**: "undefined%" → 정상 퍼센트 표시 ✅
- **통계 API 구현**: `/api/dashboard/statistics` 엔드포인트 추가 ✅
- **데이터베이스 연동 개선**: RealDictCursor 사용으로 인한 KeyError 해결 ✅

## 📝 이전 업데이트 (2025-09-26)

### ✨ Phase 3 - 전체 사용자 인터페이스 완성

#### 🔔 **알림 설정 페이지 (NEW)**
- **키워드 알림**: 관심 키워드별 알림 설정 및 가격 범위 지정
- **채널 선택**: 이메일/푸시 알림 개별 설정
- **비용 최적화**: SMS 알림 제외 (비용 절감)
- **일일 다이제스트**: 매일 오전 9시 주요 입찰 요약 전송

#### 👤 **프로필 관리 (NEW)**
- **정보 편집**: 개인정보, 회사 정보, 연락처 수정
- **활동 통계**: 총 검색 횟수, 북마크 수, 최근 활동 현황
- **비밀번호 변경**: 안전한 비밀번호 변경 기능
- **프로필 사진**: 아바타 업로드 및 관리

#### ⚙️ **설정 페이지 (NEW)**
- **앱 설정**: 다크모드, 언어 선택 (한/영/일/중), 자동 저장
- **알림 설정**: 이메일/푸시/소리 개별 설정
- **개인정보**: 프로필 공개 여부, 통계 수집 동의
- **데이터 관리**: 데이터 내보내기/가져오기, 계정 삭제

#### 💳 **구독 관리 (NEW)**
- **3단계 요금제**: 베이직(무료), 프로(29,000원/월), 엔터프라이즈(99,000원/월)
- **사용량 모니터링**: 실시간 사용량 표시 (검색, 북마크, 알림)
- **결제 내역**: 상세 결제 이력 및 영수증 다운로드
- **플랜 비교**: 기능별 상세 비교표 제공

#### 🎯 **UX/UI 개선**
- **메뉴 구조 최적화**: 입찰목록 제거, 알림설정 추가
- **드롭다운 메뉴 개선**: 선택 후 자동 닫힘 구현
- **일관된 디자인**: Material-UI 컴포넌트 통일
- **반응형 레이아웃**: 모든 페이지 모바일 최적화

### ✨ 오전 작업 (대시보드 & 검색)

#### 📊 **인터랙티브 대시보드**
- **클릭 가능한 차트**: 카테고리별 분포 차트에서 특정 카테고리 클릭 시 해당 검색 결과로 자동 이동
- **스마트 네비게이션**: 대시보드 → 검색 페이지 원클릭 탐색
- **실시간 데이터**: 주간 트렌드 및 카테고리 분포에 실제 데이터베이스 연동

#### 🔍 **고도화된 검색 시스템**
- **태그 기반 통합검색**: 제목, 기관명, 자동생성 태그를 모두 포함한 포괄적 검색
- **URL 파라미터 지원**: 검색 결과 URL 공유 및 뒤로가기 지원
- **데이터 품질 개선**: 잘못 분류된 태그 20개 자동 정리

### 🔄 사용자 플로우 예시
```
대시보드 방문 → "물품(27건)" 차트 클릭 →
자동으로 /search?q=물품 이동 → 물품 관련 입찰 27건 즉시 표시
```

## 🔍 검색 기능

### API 엔드포인트
```http
GET /api/search?q=검색어&min_price=100000000&organization=서울
```

### 지원 필터
| 파라미터 | 설명 | 예시 |
|---------|------|------|
| `q` | 검색어 | 건설, 소프트웨어 |
| `start_date` | 시작일 | 2025-09-01 |
| `end_date` | 종료일 | 2025-09-30 |
| `min_price` | 최소 가격 | 100000000 |
| `max_price` | 최대 가격 | 1000000000 |
| `organization` | 기관명 | 서울, 경기 |
| `sort` | 정렬 | price_desc, date_asc |

## 🏗️ 프로젝트 구조

```
odin-ai/
├── 📦 batch/              # 배치 처리 시스템
│   └── modules/          # 수집/다운로드/처리/보고
├── 🚀 backend/            # FastAPI 백엔드 (DB 연동)
├── 💻 frontend/           # React 프론트엔드
│   └── src/
│       ├── pages/        # Dashboard, Search, Profile, Settings, Subscription, Notifications
│       └── components/   # 검색바, 필터, 레이아웃
├── 📊 src/                # 핵심 비즈니스 로직
└── 🛠️ tools/              # HWP/PDF 처리 도구
```

## 🛠 기술 스택

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15 + SQLAlchemy
- **Cache**: Redis (예정)
- **문서 처리**: hwp5txt, PDFPlumber

### Frontend
- **Framework**: React 18 + TypeScript
- **UI**: Material-UI v5
- **상태관리**: React Query v5 + Redux
- **스타일**: Styled Components

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