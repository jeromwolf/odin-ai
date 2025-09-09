# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

**자동 개인정보 마스킹 패턴**:
- Email: `[EMAIL_MASKED]`
- Phone: `[PHONE_MASKED]`
- Credit Card: `[CARD_MASKED]`
- SSN/주민번호: `[ID_MASKED]`

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

### Security Considerations

- **입력값 검증**: 모든 사용자 입력 유효성 검사
- **SQL Injection 방지**: Parameterized queries 사용
- **XSS 방지**: 출력 데이터 이스케이핑
- **환경변수**: 민감 정보는 환경변수로 관리
- **HTTPS 강제**: 모든 통신 암호화
- **개인정보**: 로그 및 에러 메시지에서 완전 제거

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