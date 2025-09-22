# Odin-AI 기술 명세서 (Technical Specification)

> 최종 업데이트: 2025-09-11
> 
> 이 문서는 Odin-AI 프로젝트의 확정된 기술 사양을 담고 있습니다.

## 목차
1. [데이터 수집 전략](#1-데이터-수집-전략)
2. [데이터베이스 설계](#2-데이터베이스-설계)
3. [HWP 문서 처리](#3-hwp-문서-처리)
4. [시스템 아키텍처](#4-시스템-아키텍처)
5. [API 설계](#5-api-설계)
6. [보안 및 인증](#6-보안-및-인증)
7. [이메일 시스템](#7-이메일-시스템)
8. [배포 전략](#8-배포-전략)
9. [모니터링](#9-모니터링)
10. [개발 로드맵](#10-개발-로드맵)

## 1. 데이터 수집 전략

### 1.1 데이터 소스 아키텍처
```
[Primary Source]
공공데이터포털 API (70%)
├── 입찰공고 기본정보
├── 낙찰정보
└── 발주계획

[Secondary Source]  
나라장터 크롤링 (30%)
├── 상세 정보
├── 첨부파일 (HWP/PDF)
└── 실시간 업데이트
```

### 1.2 공공데이터포털 API 활용

#### API 엔드포인트
```python
# 조달청_나라장터 입찰공고정보서비스
BASE_URL = "https://apis.data.go.kr/1230000/BidPublicInfoService04"

# 주요 오퍼레이션
- getBidPblancListInfoServc  # 입찰공고목록
- getBidPblancListInfoServcPPSSrch  # 사전규격공개
- getPublicPrcureThngInfoServc  # 공공구매정보
```

#### API 지연 시간 및 활용 전략
- **업데이트 주기**: 일 1-2회 (새벽 2-4시)
- **평균 지연**: 12-24시간
- **활용 전략**: 
  - Phase 1: API 100% (MVP)
  - Phase 2: API 70% + 크롤링 30% (긴급건)
  - Phase 3: 실시간 크롤링 + API 백업

### 1.3 크롤링 시스템 설계

#### 단계별 크롤링 전략
```python
# Phase 1: MVP (LOW RISK)
class SafeCrawler:
    """공공데이터 API 중심, 최소 크롤링"""
    - API 우선 사용
    - 크롤링: 첨부파일만
    - 일일 100건 제한
    - 5초 딜레이

# Phase 2: GROWTH (MEDIUM RISK)  
class SmartCrawler:
    """하이브리드 방식"""
    - API: 기본정보
    - 크롤링: 상세+파일
    - 일일 1000건
    - 3초 딜레이
    - IP 로테이션 (5개)

# Phase 3: SCALE (MANAGED RISK)
class EnterpriseCrawler:
    """전면 크롤링 + 백업"""
    - 실시간 모니터링
    - 일일 10000건+
    - 2초 딜레이
    - IP 풀 (100개+)
    - 자동 복구 시스템
```

#### 크롤링 회피 기술
```python
# 1. User-Agent 로테이션
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15',
    # ... 50개 이상
]

# 2. IP 프록시 관리
PROXY_POOL = [
    'http://proxy1.server.com:8080',
    'http://proxy2.server.com:8080',
    # ... 필요시 확장
]

# 3. 요청 패턴 랜덤화
def random_delay():
    return random.uniform(2.0, 5.0)

# 4. 세션 관리
def rotate_session():
    if request_count > 100:
        create_new_session()
```

### 1.4 리스크 관리

#### 차단 대응 프로토콜
```
1. 1차 차단 감지
   → IP 변경
   → 딜레이 증가 (2배)
   
2. 2차 차단
   → 프록시 서버 전환
   → 크롤링 일시 중단 (1시간)
   
3. 3차 차단
   → API 전용 모드 전환
   → 24시간 대기
```

## 2. 데이터베이스 설계

### 2.1 하이브리드 저장 전략
```
PostgreSQL: 핵심 메타데이터 + 검색용 정보
MD 파일: 전체 RFP 내용 + 추출된 텍스트  
S3/Storage: 원본 HWP/PDF 파일
```

### 2.2 핵심 테이블 구조

```sql
-- RFP 메타데이터 (검색/필터링용)
CREATE TABLE rfps (
    id SERIAL PRIMARY KEY,
    bid_number VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    organization VARCHAR(200),
    
    -- 중요 날짜
    announcement_date TIMESTAMP,
    closing_date TIMESTAMP,
    
    -- 금액 정보
    budget_amount BIGINT,
    
    -- 분류/태그
    category VARCHAR(50),
    keywords TEXT[],
    
    -- 파일 경로
    md_file_path VARCHAR(500),  -- '/data/rfps/2024/11/공고번호.md'
    original_file_url VARCHAR(500),  -- S3 URL
    
    -- AI 분석 결과
    ai_summary TEXT,
    match_keywords TEXT[],
    requirements JSONB,
    
    -- 패턴 분석
    is_recurring BOOLEAN DEFAULT FALSE,
    previous_winner VARCHAR(200),
    monopoly_score INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- 기업-RFP 매칭 결과
CREATE TABLE matching_scores (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    rfp_id INTEGER REFERENCES rfps(id),
    score INTEGER,
    matched_keywords TEXT[],
    notified_at TIMESTAMP,
    UNIQUE(company_id, rfp_id)
);

-- 인덱스
CREATE INDEX idx_rfps_closing_date ON rfps(closing_date);
CREATE INDEX idx_rfps_keywords ON rfps USING GIN(keywords);
```

### 2.3 파일 시스템 구조
```
/data/rfps/
├── 2024/
│   ├── 11/
│   │   ├── 20241111-001/
│   │   │   ├── metadata.json
│   │   │   ├── content.md
│   │   │   ├── summary.md
│   │   │   └── original/
│   │   │       ├── 입찰공고문.hwp
│   │   │       └── 과업지시서.hwp
```

## 3. HWP 문서 처리

### 3.1 변환 파이프라인
```
HWP → Text 추출 → 구조 분석 → Markdown 생성 → DB 저장
```

### 3.2 변환 구현 방식

#### Level 1: 기본 (olefile)
```python
# 텍스트만 추출, 표/이미지 손실
# 품질: 60-70%, 속도: 빠름
import olefile
```

#### Level 2: 표준 (LibreOffice)
```python
# Docker 컨테이너로 실행
# 품질: 80-90%, 속도: 보통
libreoffice --headless --convert-to txt
```

#### Level 3: 고급 (LibreOffice + AI)
```python
# OCR + GPT 정제
# 품질: 95%+, 속도: 느림
```

### 3.3 Markdown 템플릿
```markdown
# [공고번호] 제목

## 📋 기본 정보
| 항목 | 내용 |
|------|------|
| 공고번호 | xxx |
| 마감일 | xxx |

## 🎯 AI 분석 요약
[AI 생성 요약]

## 📄 원본 내용
[HWP 추출 텍스트]
```

## 4. 시스템 아키텍처

### 4.1 전체 아키텍처

```python
# 1. HWP 자동 분석 엔진
class HWPAnalyzer:
    """경쟁사 없는 독자 기술"""
    - LibreOffice 변환
    - OCR 텍스트 추출
    - GPT-4 요약/분석
    
# 2. AI 매칭 알고리즘
class AIMatcher:
    """기업-RFP 자동 매칭"""
    - 기업 역량 벡터화
    - RFP 요구사항 추출
    - 코사인 유사도 계산
    - 매칭 스코어 (0-100)

# 3. 패턴 분석 엔진
class PatternAnalyzer:
    """프로젝트 패턴 분석"""
    - 주기성 감지 (시계열 분석)
    - 독점업체 판별
    - 재입찰 예측
```

## 5. API 설계

### 5.1 RESTful API 엔드포인트

#### 인증 API
```python
POST   /api/auth/register     # 회원가입
POST   /api/auth/login        # 로그인
POST   /api/auth/refresh      # 토큰 갱신
POST   /api/auth/logout       # 로그아웃
```

#### RFP API
```python
GET    /api/rfps              # RFP 목록 조회
GET    /api/rfps/{id}         # RFP 상세 조회
GET    /api/rfps/{id}/files   # 첨부파일 목록
GET    /api/rfps/{id}/analysis # AI 분석 결과
POST   /api/rfps/search       # 고급 검색
```

#### 매칭 API
```python
GET    /api/matching/scores   # 매칭 점수 조회
POST   /api/matching/calculate # 매칭 점수 계산
GET    /api/matching/recommendations # 추천 RFP
```

#### 알림 설정 API
```python
GET    /api/notifications/settings  # 알림 설정 조회
PUT    /api/notifications/settings  # 알림 설정 변경
POST   /api/notifications/keywords  # 키워드 추가
DELETE /api/notifications/keywords/{id} # 키워드 삭제
```

### 5.2 응답 형식

```json
{
    "success": true,
    "data": {
        // 실제 데이터
    },
    "message": "성공",
    "timestamp": "2024-11-11T10:00:00Z"
}
```

### 5.3 에러 처리

```json
{
    "success": false,
    "error": {
        "code": "AUTH_001",
        "message": "인증 실패",
        "details": "토큰이 만료되었습니다"
    },
    "timestamp": "2024-11-11T10:00:00Z"
}
```

## 6. 보안 및 인증

### 6.1 인증 시스템

#### JWT 토큰 관리
```python
# 토큰 구조
ACCESS_TOKEN_EXPIRE = 30  # 30분
REFRESH_TOKEN_EXPIRE = 7 * 24 * 60  # 7일

# 토큰 페이로드
payload = {
    "user_id": "uuid",
    "email": "user@example.com",
    "subscription_tier": "premium",
    "exp": "timestamp"
}
```

#### 구독 등급별 권한
```python
SUBSCRIPTION_TIERS = {
    "free": {
        "daily_searches": 10,
        "email_alerts": False,
        "api_access": False
    },
    "basic": {
        "daily_searches": 100,
        "email_alerts": True,
        "api_access": False
    },
    "premium": {
        "daily_searches": "unlimited",
        "email_alerts": True,
        "api_access": True
    }
}
```

### 6.2 데이터 보안

#### 암호화 정책
```python
# 전송 보안
- HTTPS 전용 (TLS 1.3)
- HSTS 헤더 적용
- CSP 헤더 설정

# 저장 보안
- 비밀번호: bcrypt (라운드 12)
- 개인정보: AES-256-GCM
- 파일: S3 서버사이드 암호화
```

#### 개인정보 보호
```python
# 로그 마스킹
def mask_personal_data(data):
    data = re.sub(r'[\w.-]+@[\w.-]+', '[EMAIL_MASKED]', data)
    data = re.sub(r'\d{3}-\d{4}-\d{4}', '[PHONE_MASKED]', data)
    return data

# DB 저장시 암호화
encrypted_email = encrypt(email, KEY)
```

### 6.3 법적 준수사항

```
✅ 준수 사항
- robots.txt 확인 및 준수
- 저작권법 (데이터 가공/변형)
- 개인정보보호법 (PIPA)
- 정보통신망법
- 공공데이터법

⚠️ 주의 사항
- 과도한 크롤링 금지 (분당 20회 제한)
- 서버 부하 최소화
- 영리 목적 명시
- DDoS 방지 메커니즘
```

## 7. 이메일 시스템

### 7.1 이메일 발송 시스템

#### 발송 시간 설정
```python
# 사용자별 맞춤 발송 시간
class EmailSchedule:
    user_id: str
    send_time: str  # "08:00", "12:00", "18:00"
    timezone: str   # "Asia/Seoul"
    frequency: str  # "daily", "weekly", "instant"
    keywords: List[str]
```

#### 이메일 템플릿
```html
<!-- 일일 알림 템플릿 -->
<h2>오늘의 입찰 공고 📋</h2>
<p>안녕하세요 {user_name}님,</p>
<p>관심 키워드와 매칭되는 {count}건의 새로운 입찰공고가 있습니다.</p>

<!-- RFP 카드 -->
<div class="rfp-card">
  <h3>{title}</h3>
  <p>공고번호: {bid_number}</p>
  <p>마감일: {closing_date}</p>
  <p>예산: {budget}</p>
  <p>매칭점수: {score}점</p>
  <a href="{link}">자세히 보기</a>
</div>
```

### 7.2 이메일 서비스 구현

```python
# 이메일 발송 큐
CELERY_BEAT_SCHEDULE = {
    'send-daily-emails': {
        'task': 'tasks.send_daily_emails',
        'schedule': crontab(minute=0),  # 매시 정각
    },
}

# 발송 로직
@celery.task
def send_daily_emails():
    current_hour = datetime.now(KST).hour
    users = get_users_by_send_time(f"{current_hour:02d}:00")
    
    for user in users:
        rfps = get_matching_rfps(user.keywords)
        if rfps:
            send_email(
                to=user.email,
                subject=f"오늘의 입찰공고 {len(rfps)}건",
                template="daily_digest",
                context={"user": user, "rfps": rfps}
            )
```

## 8. 배포 전략

### 8.1 컨테이너 구성

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis

  crawler:
    build: ./crawler
    environment:
      - CRAWL_INTERVAL=1800  # 30분
    depends_on:
      - postgres
      - redis

  celery:
    build: ./backend
    command: celery -A app.celery worker -l info
    depends_on:
      - redis

  postgres:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=odin_ai
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### 8.2 CI/CD 파이프라인

```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster odin-ai-cluster \
            --service odin-ai-service \
            --force-new-deployment
```

### 8.3 환경별 설정

```python
# 개발 환경
DEV_CONFIG = {
    "debug": True,
    "crawl_delay": 5,
    "max_workers": 2
}

# 스테이징 환경
STAGING_CONFIG = {
    "debug": False,
    "crawl_delay": 3,
    "max_workers": 5
}

# 프로덕션 환경
PROD_CONFIG = {
    "debug": False,
    "crawl_delay": 2,
    "max_workers": 10,
    "use_cdn": True,
    "enable_monitoring": True
}
```

## 9. 모니터링

### 9.1 모니터링 스택

```python
# Prometheus 메트릭
from prometheus_client import Counter, Histogram, Gauge

# 메트릭 정의
crawl_success = Counter('crawl_success_total', 'Total successful crawls')
crawl_failure = Counter('crawl_failure_total', 'Total failed crawls')
api_latency = Histogram('api_latency_seconds', 'API latency')
active_users = Gauge('active_users', 'Currently active users')
```

### 9.2 알림 규칙

```yaml
# alerts.yml
alerts:
  - name: CrawlerDown
    condition: crawl_success_rate < 90
    duration: 5m
    action: email, slack
    
  - name: HighAPILatency
    condition: api_latency_p95 > 1000
    duration: 3m
    action: pagerduty
    
  - name: DatabaseConnectionPool
    condition: db_connections > 80
    duration: 1m
    action: scale_up
```

### 9.3 대시보드 구성

```
Grafana 대시보드:
├── 시스템 개요
│   ├── CPU/메모리 사용률
│   ├── 네트워크 I/O
│   └── 디스크 사용량
├── 비즈니스 메트릭
│   ├── 일일 크롤링 건수
│   ├── 신규 RFP 등록
│   ├── 활성 사용자 수
│   └── 이메일 발송 성공률
└── 에러 모니터링
    ├── 에러율 추이
    ├── 에러 타입별 분포
    └── 에러 상세 로그
```

## 10. 성능 목표

### 10.1 SLA (Service Level Agreement)

```
📊 성능 목표
- API 응답시간: < 500ms (P95)
- 크롤링 성공률: > 99.5%
- 가동시간: 99.9% (월 43분 이하)
- 데이터 최신성: 30분 이내
- HWP 변환 성공률: > 95%
```

### 10.2 처리 용량

```
🚀 일일 처리 목표
- 크롤링: 10,000건/일
- 동시 사용자: 1,000명
- 이메일 발송: 50,000건/일
- HWP 처리: 1,000건/시간
- API 호출: 100,000건/일
```

### 10.3 확장성 목표

```python
# 단계별 확장 계획
SCALING_MILESTONES = {
    "MVP": {
        "users": 100,
        "daily_rfps": 1000,
        "infrastructure": "단일 서버"
    },
    "GROWTH": {
        "users": 1000,
        "daily_rfps": 5000,
        "infrastructure": "로드밸런서 + 2대"
    },
    "SCALE": {
        "users": 10000,
        "daily_rfps": 20000,
        "infrastructure": "쿠버네티스 클러스터"
    }
}
```

## 11. 개발 로드맵

### Phase 1: MVP (3개월)
#### 월 1 - 데이터 수집
- [ ] 공공데이터포털 API 연동
- [ ] 기본 데이터 모델 설계
- [ ] PostgreSQL + MD 파일 저장 구조
- [ ] 기본 크롤러 (하루 100건)

#### 월 2 - 문서 처리
- [ ] HWP → Text 변환 (olefile)
- [ ] MD 파일 생성 파이프라인
- [ ] 기본 검색 기능
- [ ] 이메일 알림 시스템

#### 월 3 - 사용자 기능
- [ ] 회원가입/로그인
- [ ] 키워드 알림 설정
- [ ] 기본 대시보드
- [ ] 이메일 발송 시간 설정

### Phase 2: Alpha (2개월)
#### 월 4 - AI 기능
- [ ] GPT-4 연동
- [ ] RFP 요약 생성
- [ ] 기업-RFP 매칭 알고리즘
- [ ] 매칭 점수 계산

#### 월 5 - 패턴 분석
- [ ] 주기성 프로젝트 감지
- [ ] 독점 업체 분석
- [ ] 재입찰 패턴 분석
- [ ] 통계 대시보드

### Phase 3: Beta (2개월)
#### 월 6 - 고도화
- [ ] 크롤링 확장 (하루 1000건)
- [ ] LibreOffice HWP 변환
- [ ] 실시간 알림
- [ ] 고급 검색 필터

#### 월 7 - 확장
- [ ] API 서비스 개발
- [ ] 모바일 앱 (React Native)
- [ ] 결제 시스템 연동
- [ ] 기업 인증 시스템

### Phase 4: Launch (1개월)
#### 월 8 - 출시 준비
- [ ] 성능 최적화
- [ ] 보안 감사
- [ ] 부하 테스트
- [ ] 사용자 매뉴얼
- [ ] 마케팅 자료 준비
- [ ] 베타 테스터 모집

## 12. 위험 관리

### 12.1 기술적 위험

| 위험 요소 | 영향도 | 대응 방안 |
|----------|--------|----------|
| 나라장터 차단 | 높음 | API 우선, 프록시 풀, 딜레이 조정 |
| HWP 변환 실패 | 중간 | 멀티 파서, 수동 처리 옵션 |
| API 제한/변경 | 중간 | 크롤링 백업, 버전 관리 |
| 대용량 트래픽 | 낮음 | 오토스케일링, 캐싱 |

### 12.2 사업적 위험

| 위험 요소 | 영향도 | 대응 방안 |
|----------|--------|----------|
| 경쟁사 진입 | 중간 | 차별화 기능 강화 |
| 법적 이슈 | 높음 | 법률 검토, 컴플라이언스 |
| 사용자 이탈 | 중간 | UX 개선, 피드백 반영 |

## 13. 성공 지표 (KPI)

### 13.1 비즈니스 지표
```
- MAU (Monthly Active Users): 1,000명 (6개월)
- 유료 전환율: 10%
- 이탈률: < 20%
- NPS Score: > 50
```

### 13.2 기술 지표
```
- 크롤링 커버리지: 95%
- AI 매칭 정확도: 85%
- 시스템 가동률: 99.9%
- 평균 응답시간: < 500ms
```

---

**문서 정보**
- 최종 업데이트: 2025-09-11
- 버전: 2.0.0
- 작성자: Odin-AI Team
- 검토자: Technical Lead

**변경 이력**
- v2.0.0 (2025-09-11): 확정된 기술 사양 전면 업데이트
- v1.0.0 (2025-09-10): 초기 문서 작성