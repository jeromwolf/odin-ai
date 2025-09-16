# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ 최우선 원칙: 개인정보 보호

**절대 규칙**: 어떤 상황에서도 로그에 개인정보를 남기지 않습니다.

## Project Context Summary (2025-09-17)

### 프로젝트 현황
- **현재 날짜**: 2025년 9월 17일
- **단계**: ✅ **핵심 기능 구현 가능성 100% 검증 완료**
- **완료된 작업**:
  - ✅ PRD (제품 요구사항 문서) 작성
  - ✅ 기술 명세서 v2.0.0 확정
  - ✅ 경쟁사 분석 완료
  - ✅ 태스크 관리 시스템 구축
  - ✅ GitHub 워크플로우 정의
  - ✅ **공공데이터포털 API 완전 연동 및 검증**
  - ✅ **stdNtceDocUrl 필드 발견 - HWP 파일 다운로드 URL 확인**
  - ✅ **API + Selenium 하이브리드 전략 검증**
  - ✅ **실제 HWP/PDF 파일 다운로드 테스트 완료**

### 🎯 **2025-09-17 핵심 성과**

#### **API 데이터 구조 완전 파악**
- **stdNtceDocUrl**: HWP/PDF 파일 직접 다운로드 URL ✅
- **bidNtceDtlUrl**: 상세 페이지 URL ✅
- **ntceSpecFileNm1**: 실제 파일명 확인 ✅
- **일일 수집량**: 475건 이상 확인 ✅

#### **HWP 문서 처리 시스템 완전 구현** 🎉
- **HWP Viewer 통합**: tools/hwp-viewer를 백엔드에 완전 통합 ✅
- **실제 파일 처리**: 128KB HWP 파일에서 10,340자 텍스트 추출 ✅
- **고도화 마크다운**: 45,883 bytes 구조화된 문서 생성 ✅
- **자동 정보 추출**: 날짜, 기관명, 특이사항 자동 인식 및 강조 ✅
- **압축파일 지원**: ZIP 파일 내 문서 자동 처리 ✅
- **완전 자동화**: API → 다운로드 → 파싱 → 마크다운 파이프라인 ✅

#### **실제 API 응답 예시 (검증 완료)**
```json
{
  "bidNtceNm": "어린이보호구역 (신안초등학교) 보행로 조성사업",
  "stdNtceDocUrl": "https://www.g2b.go.kr/pn/pnp/pnpe/UntyAtchFile/downloadFile.do?bidPbancNo=R25BK01060027&bidPbancOrd=000&fileType=&fileSeq=1",
  "ntceSpecFileNm1": "수의계약안내공고[어린이보호구역(신안초등학교) 보행로 조성사업].hwp",
  "bidNtceDtlUrl": "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R25BK01060027&bidPbancOrd=000",
  "total_count": 475
}
```

#### **검증된 구현 전략**
1. **메타데이터 수집**: 공공데이터포털 API (100% 활용)
2. **파일 다운로드**: stdNtceDocUrl + Selenium (직접 다운로드)
3. **문서 처리**: HWP Viewer (우선) → hwp5txt (대체) → 마크다운 변환
4. **키워드 검색**: 클라이언트 사이드 필터링
5. **실시간 모니터링**: 일일 475건+ 수집 가능

#### **실제 처리 결과 예시**
```
📥 다운로드: 수의계약안내공고[어린이보호구역(신안초등학교) 보행로 조성사업].hwp (128,512 bytes)
🔧 처리방법: HWP Viewer 고도화 파서
📄 텍스트: 10,340자 추출
📝 단락수: 8개
🎨 마크다운: 45,883 bytes (핵심 정보 자동 강조)
📅 주요 일정: 2019.6.19 자동 인식
🏢 관련 기관: 산청군 공무원부조리신고센터 등 자동 추출
⚠️ 특이사항: PQ심사 표준하도급계약서 등 자동 강조
```

### 핵심 기술 결정사항 (업데이트)
1. **데이터 수집**: 공공데이터포털 API (90%) + Selenium 파일 다운로드 (10%)
2. **데이터 저장**: PostgreSQL (메타데이터) + 파일 시스템 (HWP/PDF 원본)
3. **HWP 처리**: hwp5 + LibreOffice + AI 분석
4. **문서 접근**: stdNtceDocUrl 필드 활용한 직접 다운로드
5. **수집 성능**: 일일 475건+ 공고, 실시간 모니터링 가능

### 주요 문서 위치
- `PRD.md`: 비즈니스 요구사항 및 사용자 스토리
- `TECHNICAL_SPEC.md`: 확정된 기술 사양 (v2.0.0)
- `docs/TASK_MANAGEMENT.md`: 8개월 개발 태스크 체크리스트
- `competitor_analysis.md`: 케이비드, 인포21C 등 경쟁사 분석
- **NEW**: `test_api_raw_response.py`: API 응답 구조 검증
- **NEW**: `test_final_hwp_download.py`: HWP 다운로드 테스트

### 다음 단계 (Phase 1 - MVP) - 업데이트
1. ✅ 공공데이터포털 API 연동 (완료)
2. 실제 HWP 파일 처리 파이프라인 구현
3. PostgreSQL 데이터베이스 설계 및 구현
4. stdNtceDocUrl 기반 자동 다운로드 시스템
5. 키워드 검색 및 필터링 시스템

## Project Overview

**Odin-AI** is a public procurement platform that analyzes Korean government tender information (나라장터) using AI. The platform provides automated bid monitoring, AI-based success prediction, and customized project recommendations for businesses.

## Key Business Context

- **Target Market**: Korean public procurement system (나라장터 - https://www.g2b.go.kr/)
- **Main Users**: SMEs, IT service companies, construction/engineering firms, consulting companies
- **Core Value**: Automated monitoring of tender notices, AI-powered bid success prediction, and RFP document analysis

## Technical Architecture

### Backend Stack
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + Redis
- **Queue System**: Celery + Redis
- **AI/ML Stack**:
  - OpenAI GPT-4 or Claude for NLP
  - LangChain for RAG implementation
  - Pinecone/Weaviate for vector database
  - scikit-learn for predictive models

### Document Processing
- **HWP Processing**: hwp5 library + LibreOffice headless conversion
- **PDF Processing**: PyPDF2, pdfplumber, tabula-py for table extraction
- **OCR**: Tesseract for image documents

### Infrastructure
- **Containerization**: Docker + Kubernetes
- **Cloud**: AWS/GCP with auto-scaling
- **Monitoring**: Grafana + Prometheus
- **CI/CD**: GitHub Actions

## Development Commands

Since the project is in initial setup phase, here are the expected commands once the project structure is established:

### Python/FastAPI Backend
```bash
# Virtual environment setup
python -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --port 8000

# Run tests
pytest

# Run linting
ruff check .
black .

# Database migrations
alembic upgrade head
```

### Docker Commands
```bash
# Build containers
docker-compose build

# Run all services
docker-compose up

# Run specific service
docker-compose up backend
```

## Core Features to Implement

1. **Data Collection System**
   - 나라장터 (https://www.g2b.go.kr/) crawler with 30-minute update cycle
   - Duplicate removal and data normalization
   - Emergency procurement information handling

2. **AI Analysis System**
   - RAG-based document search using vector embeddings
   - Natural language Q&A for RFP documents
   - Bid success probability prediction model
   - Competition analysis and scoring

3. **User Features**
   - Personalized dashboard with color-coded success probabilities
   - Real-time notification system (email, SMS, push)
   - RFP summary and key points extraction
   - Proposal writing guidelines

4. **Analytics**
   - Market trend analysis by sector
   - Budget distribution analysis
   - Procurement agency pattern analysis
   - Company performance benchmarking

## Development Phases

**Phase 1 (MVP - 3 months)**
- 나라장터 (g2b.go.kr) crawling system
- Basic search and filtering
- User authentication and subscription management
- Email notification system

**Phase 2 (AI Features - 3 months)**
- HWP/PDF document processing
- RAG search system implementation
- Basic bid success prediction
- Dashboard UI/UX

**Phase 3 (Advanced - 6 months)**
- Advanced AI analysis features
- Detailed statistics and reporting
- Mobile app development
- API service provision

## Important Considerations

1. **Legal Compliance**
   - Only use publicly available information
   - Implement data transformation to avoid copyright issues
   - Follow minimal data collection principles for privacy

2. **Technical Challenges**
   - HWP file compatibility requires dual processing (LibreOffice + hwp5)
   - Implement IP rotation and delay mechanisms for crawler resilience
   - Continuous model training with new data for accuracy improvement

3. **Performance Requirements**
   - Crawling success rate: 99.5%
   - Search response time: < 2 seconds
   - AI prediction accuracy: 70% (initial) → 85% (after 1 year)

## File Structure Guidelines

When implementing, organize code as follows:
```
odin-ai/
├── backend/
│   ├── api/           # FastAPI routes
│   ├── core/          # Core configurations
│   ├── models/        # Database models
│   ├── services/      # Business logic
│   ├── tasks/         # Celery tasks
│   └── ml/            # ML models and pipelines
├── crawler/           # 나라장터 (g2b.go.kr) crawler
├── document_processor/ # HWP/PDF processing
├── tests/             # Test files
└── docker/            # Docker configurations
```

## Testing Strategy

- Unit tests for all services and utilities
- Integration tests for API endpoints
- Mock external services (g2b.go.kr, AI APIs) in tests
- Test document processing with sample HWP/PDF files
- Load testing for crawler and API performance

## Development Guidelines

### Working Approach
- **천천히, 차분히 접근**: 서두르지 않고 단계별로 진행
- **깊이 있는 사고**: 각 단계에서 충분한 검토와 분석
- **체계적 진행**: 명확한 순서와 구조를 가지고 작업
- **워크플로우**: 요구사항 분석 → 태스크 분할 → 개발 → 테스트 → 로깅 → 검토 → 배포
- **현실적 접근**: 더미 데이터 최소화, 실제 데이터 기반 검증

### Task Management
- **세부 단위로 분할**: 각 태스크는 2-4시간 내에 완료 가능한 크기
- **의존성 고려**: 태스크 간 의존관계를 명확히 정의
- **우선순위 설정**: 중요도와 긴급도에 따른 순서 결정
- **문서화**: 목표, 범위, 선행조건, 예상시간, 완료조건, 위험요소 명시

### Logging and Privacy Protection

#### ⚠️ CRITICAL: Personal Data Protection in Logs
개인정보는 어떤 상황에서도 로그에 남겨서는 안 됩니다.

**절대 금지 항목**:
- 이메일, 전화번호, 주민번호 직접 로깅
- 신용카드 번호, 비밀번호 로깅
- 사용자 프로필 객체 전체 로깅
- 민감 정보가 포함된 request/response 로깅

**올바른 로깅 방법**:
```javascript
// ✅ 권장: 익명 식별자 사용
logger.error('Login failed for userId: usr_123abc456');
logger.info('Payment processed for sessionId: sess_789def012');

// ✅ 권장: 자동 sanitization
const secureLogger = {
  info: (message, data) => logger.info(message, sanitize(data)),
  error: (message, data) => logger.error(message, sanitize(data))
};
```

**자동 개인정보 마스킹 시스템 구현**:
```javascript
const personalDataPatterns = {
  email: /[\w\.-]+@[\w\.-]+\.\w+/g,
  phone: /\d{2,3}-\d{3,4}-\d{4}/g,
  creditCard: /\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}/g,
  koreanId: /\d{6}-\d{7}/g
};

// 모든 로그에 자동 적용
const logSanitizer = {
  sanitize: (data) => {
    let sanitized = JSON.stringify(data);
    Object.entries(personalDataPatterns).forEach(([type, pattern]) => {
      sanitized = sanitized.replace(pattern, `[${type.toUpperCase()}_MASKED]`);
    });
    return JSON.parse(sanitized);
  }
};
```

**개인정보 대체 전략**:
- 사용자 이메일 → SHA256 해시 기반 익명 ID (`usr_8자리해시`)
- 전화번호 → 해시 기반 익명 ID (`ph_8자리해시`)
- 신용카드 → 마지막 4자리 + 카드 타입만 저장

### Data Management

#### Dummy Data Usage Policy
더미 데이터는 개발 초기와 단위 테스트에서만 사용하고, 실제 비즈니스 로직 검증을 회피하는 수단이 되어서는 안 됩니다.

**허용되는 경우**:
- 단위 테스트의 개별 함수 검증
- 개발 초기 UI 컴포넌트 개발
- 프로토타입 단계

**금지되는 경우**:
- 통합 테스트에서 실제 API 호출 회피
- 실제 데이터베이스 연동 없이 더미로 대체
- 프로덕션 코드에 하드코딩된 더미 값

**데이터 검증 단계**:
1. Phase 1 (프로토타입): 더미 데이터 OK
2. Phase 2 (알파): 실제 API 스키마로 전환
3. Phase 3 (베타): 프로덕션 데이터 서브셋 사용
4. Phase 4 (프로덕션): 100% 실제 데이터

**프로덕션 배포 전 체크**:
```javascript
// 자동화된 더미 데이터 검출
const productionReadinessCheck = {
  noDummyData: () => {
    // 'dummy', 'mock', 'fake' 키워드 검색
    // 테스트 파일 외에서 발견 시 배포 차단
  },
  realAPIIntegration: () => {
    // 모든 외부 서비스 실제 연결 확인
  }
};
```

### Security Considerations

- **입력값 검증**: 모든 사용자 입력 유효성 검사
- **SQL Injection 방지**: Parameterized queries 사용
- **XSS 방지**: 출력 데이터 이스케이핑
- **환경변수**: 민감 정보는 환경변수로 관리
- **HTTPS 강제**: 모든 통신 암호화
- **개인정보**: 로그 및 에러 메시지에서 완전 제거

### Odin-AI 특화 가이드라인

#### 나라장터 크롤링 윤리
- **robots.txt 준수**: 항상 확인하고 준수
- **요청 간격**: 최소 2-3초 딜레이
- **User-Agent 명시**: 'Odin-AI/1.0 (contact@odin-ai.kr)'
- **과도한 요청 금지**: 서버 부하 최소화

#### HWP 문서 처리
- **개인정보 스캔**: HWP 파일 내 개인정보 자동 감지
- **안전한 저장**: 추출된 텍스트만 저장, 원본은 처리 후 삭제
- **접근 제어**: 문서 접근 로그 기록 (익명 ID로)

#### 기업 정보 보호
- **사업자번호 암호화**: 저장 시 암호화
- **기업명 로깅 금지**: 기업 ID만 사용
- **매칭 결과 보안**: 타 기업에 노출 금지

### Code Quality Standards

- **네이밍 컨벤션**: camelCase (JS), snake_case (Python)
- **함수 크기**: 50줄 이내
- **순환 복잡도**: 10 이하
- **테스트 커버리지**: 80% 이상
- **코드 리뷰**: 모든 PR은 리뷰 필수

### Performance Requirements

- **크롤링 성공률**: 99.9%
- **API 응답시간**: < 500ms
- **페이지 로드**: < 1초
- **데이터베이스 쿼리**: < 100ms
- **문서 처리 성공률**: 95% 이상

## Task Management and GitHub Workflow

### 태스크 관리 체계

#### 1. 태스크 구조
```
메인 태스크 (Epic)
├── 서브 태스크 (Story)
│   └── 상세 태스크 (Task)
│       └── 체크리스트 항목
```

#### 2. 태스크 완료 프로세스
1. **개발**: 코드 작성 및 기능 구현
2. **테스트**: 단위 테스트 및 통합 테스트 작성/실행
3. **문서화**: 코드 문서화 및 README 업데이트
4. **리뷰**: 코드 리뷰 및 피드백 반영
5. **컨펌**: 최종 확인 및 승인

#### 3. 테스트 전략
```python
# 각 태스크 완료 시 필수 테스트
def task_completion_tests():
    """
    1. 단위 테스트: 개별 함수/메서드 테스트
    2. 통합 테스트: 모듈 간 상호작용 테스트
    3. E2E 테스트: 전체 플로우 테스트 (주요 기능)
    4. 성능 테스트: 응답시간, 처리량 측정
    """
    
    # 테스트 실행 명령
    pytest tests/unit/          # 단위 테스트
    pytest tests/integration/   # 통합 테스트
    pytest tests/e2e/           # E2E 테스트
    pytest tests/performance/   # 성능 테스트
```

### GitHub 워크플로우

#### 1. 브랜치 전략
```bash
main                    # 프로덕션 배포 브랜치
├── develop            # 개발 통합 브랜치
│   ├── feature/      # 기능 개발 브랜치
│   ├── bugfix/       # 버그 수정 브랜치
│   └── hotfix/       # 긴급 수정 브랜치

# 브랜치 네이밍 규칙
feature/phase1-data-collection   # Phase별 기능
bugfix/api-response-error        # 버그 수정
hotfix/critical-security-patch   # 긴급 패치
```

#### 2. 커밋 메시지 컨벤션
```bash
# 타입: 제목 (최대 50자)
# |<----  최대 50자  ---->|

# 본문 (선택사항, 최대 72자 줄바꿈)
# |<----  최대 72자  --------------------------------->|

# 꼬리말 (선택사항)
# Issue: #123
# Refs: #456

# 타입 종류
feat:     # 새로운 기능
fix:      # 버그 수정
docs:     # 문서 수정
style:    # 코드 포맷팅
refactor: # 코드 리팩토링
test:     # 테스트 추가/수정
chore:    # 빌드, 패키지 관련

# 예시
feat: 공공데이터포털 API 클라이언트 구현

- API 키 관리 시스템 추가
- Rate limiting 구현
- 재시도 로직 추가

Issue: #15
```

#### 3. Pull Request 프로세스
```markdown
## PR 템플릿

### 📋 작업 내용
- [ ] 구현한 기능 설명
- [ ] 변경 사항 요약

### 🧪 테스트
- [ ] 단위 테스트 통과
- [ ] 통합 테스트 통과
- [ ] 수동 테스트 완료

### 📝 체크리스트
- [ ] 코드 스타일 가이드라인 준수
- [ ] 문서 업데이트
- [ ] 테스트 커버리지 80% 이상
- [ ] PR 리뷰어 지정

### 🔗 관련 이슈
- Closes #번호
```

#### 4. 메인 태스크별 GitHub 업로드 규칙

##### Phase 1 완료 시
```bash
# 브랜치 생성 및 병합
git checkout -b feature/phase1-mvp
git add .
git commit -m "feat: Phase 1 MVP 완료

- 데이터 수집 시스템 구현
- 문서 처리 파이프라인 구축  
- 사용자 인증 및 기본 기능 완성

Closes #1, #2, #3"

git push origin feature/phase1-mvp
# PR 생성 → 리뷰 → develop 병합
```

##### Phase 2 완료 시
```bash
git checkout -b feature/phase2-alpha
# ... 작업 ...
git commit -m "feat: Phase 2 Alpha 기능 완료

- AI 통합 (GPT-4)
- 패턴 분석 시스템
- 매칭 알고리즘 구현

Closes #10, #11, #12"
```

#### 5. GitHub Actions CI/CD
```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run tests
        run: |
          pytest tests/ --cov=backend --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          file: ./coverage.xml
      
      - name: Lint code
        run: |
          ruff check .
          black --check .
```

#### 6. 릴리즈 관리
```bash
# 태그 생성 규칙
v1.0.0-mvp      # Phase 1 MVP
v1.1.0-alpha    # Phase 2 Alpha
v1.2.0-beta     # Phase 3 Beta
v2.0.0          # Phase 4 Launch

# 릴리즈 노트 포함 사항
- 새로운 기능
- 버그 수정
- 주요 변경사항
- 알려진 이슈
- 다음 릴리즈 계획
```

### 태스크 파일 관리

태스크 관리 문서는 `docs/TASK_MANAGEMENT.md`에서 관리되며, 다음과 같이 활용됩니다:

1. **체크박스 관리**: 각 태스크 완료 시 체크박스 업데이트
2. **진행 상황 추적**: 대시보드에서 전체 진행률 확인
3. **테스트 실행**: 각 태스크별 테스트 명령 실행
4. **컨펌 프로세스**: 완료된 태스크 리뷰 및 승인

```bash
# 태스크 상태 확인
cat docs/TASK_MANAGEMENT.md | grep "\- \["

# 완료된 태스크 카운트
cat docs/TASK_MANAGEMENT.md | grep "\- \[x\]" | wc -l

# 미완료 태스크 확인
cat docs/TASK_MANAGEMENT.md | grep "\- \[ \]"
```