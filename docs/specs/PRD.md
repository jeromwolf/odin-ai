# Product Requirements Document (PRD)
## Odin-AI - 공공조달 AI 분석 플랫폼

### 1. 프로젝트 개요

**제품명**: Odin-AI  
**프로젝트 기간**: 2024년 - MVP 6개월, 정식 출시 12개월  
**목표**: 나라장터(g2b.go.kr) 입찰정보의 AI 기반 분석 및 맞춤형 추천 서비스
**비전**: 대한민국 공공조달 시장의 디지털 혁신을 선도하는 AI 플랫폼

### 2. 문제 정의

**현재 상황**:
- 매일 500개 이상의 입찰공고가 나라장터(g2b.go.kr)에 게시
- 기업들이 수동으로 "데이터", "인공지능", "통계", "분석", "예측" 등 키워드로 검색
- 매일 사이트 방문하여 수동으로 RFP 확인 필요
- RFP 문서(HWP/PDF) 분석에 전문 인력 투입 필요
- 수주 가능성 판단의 주관성과 경험 의존도 높음
- 중요한 입찰 기회를 놓치는 경우 빈번 발생
- 특정 업체가 반복 수주하는 프로젝트 파악 어려움

**해결하려는 문제**:
- 입찰정보 모니터링 자동화 및 맞춤형 메일링
- AI 기반 HWP 문서 분석 및 기업-RFP 자동 매칭
- 주기성/일회성 프로젝트 패턴 분석
- 과거 수주업체 히스토리 추적 및 데이터베이스화
- 특정 업체 독점 프로젝트 자동 필터링
- 사용자 맞춤 시간대 메일 발송

### 3. 타겟 사용자

**Primary Users**:
- 중소/중견기업 사업개발팀
- IT 솔루션/SI 기업
- 건설/엔지니어링 기업
- 경영/기술 컨설팅 회사
- 제조업 B2G 영업팀

**User Personas**:
1. **김대리 (32세, IT 스타트업 BD)**
   - 일일 나라장터 모니터링 담당
   - 관련 프로젝트 필터링에 2시간/일 소요
   - 놓친 기회에 대한 부담감 높음
   
2. **박과장 (38세, 중견 SI업체)**
   - 연간 20개 이상 입찰 참여
   - 수주율 개선이 KPI
   - 데이터 기반 의사결정 선호
   
3. **이부장 (45세, 건설회사)**
   - 공공공사 입찰 10년 경력
   - 팀원 교육 및 프로세스 개선 관심
   - ROI 중심 도구 도입 결정권자

### 4. 핵심 기능 (Core Features)

#### 4.1 데이터 수집 및 처리
- **나라장터 실시간 크롤링**
  - 입찰공고, 사전규격, 수의계약, 긴급조달 정보
  - 10분 단위 실시간 업데이트
  - 중복 제거 및 데이터 정규화
  - 변경사항 추적 및 이력 관리

- **문서 처리 시스템**
  - HWP → PDF 자동 변환 (99% 성공률)
  - PDF 텍스트 추출 및 구조화
  - 테이블 데이터 자동 파싱
  - 첨부파일 분류 및 인덱싱

#### 4.2 AI 분석 시스템
- **RAG 기반 문서 이해**
  - RFP 문서 벡터 임베딩
  - 자연어 질의응답 (예: "이 프로젝트의 핵심 기술 요구사항은?")
  - 유사 과거 프로젝트 자동 매칭
  - 요구사항 충족도 자동 평가

- **수주 가능성 예측 모델**
  - 기업 프로필 vs 프로젝트 요구사항 매칭 스코어
  - 과거 10만건 입찰 데이터 학습
  - 경쟁 강도 및 예상 참여업체 분석
  - 수주 확률 및 신뢰구간 제시

- **입찰가 분석 시스템**
  - 예정가격 예측 모델
  - 업종별 낙찰률 패턴 분석
  - 최적 입찰가 구간 제안

- **프로젝트 히스토리 분석**
  - 발주처별 정기 프로젝트 패턴 분석
  - 반복/연간 계약 프로젝트 자동 탐지
  - 기존 수주업체 이력 추적 (최근 5년)
  - 업체 변경 주기 및 패턴 분석
  - 재입찰 가능성 예측 (계약 만료일 기준)

#### 4.3 기업 프로필 및 역량 관리
- **회원가입 시 수집 정보**
  - 회사 기본 정보 (업종, 규모, 설립연도, 직원수)
  - 전문 분야 키워드 (데이터분석, AI, 통계, 빅데이터 등)
  - 관심 입찰 분야 및 프로젝트 유형
  - 희망 프로젝트 규모 (예산 범위)
  - 보유 인증 및 자격증 관리 (ISO, CMMI, 기술등급 등)
  - 핵심 역량 키워드 설정 (최대 50개)
  
- **프로젝트 포트폴리오 관리**
  - 기존 수행 프로젝트 이력 등록
  - 프로젝트별 성과 및 실적 기록
  - 고객사 및 프로젝트 규모 정보
  - 프로젝트 카테고리별 분류 (SI, SM, 컨설팅, 구축 등)
  - 성공/실패 사례 분석 데이터

- **팀 역량 데이터베이스**
  - 개발자/엔지니어 기술 프로필
  - 팀원별 프로젝트 참여 이력
  - 가용 인력 현황 실시간 관리
  - 외주/파트너사 네트워크 정보

#### 4.4 지능형 매칭 및 알림 시스템
- **AI 기반 프로젝트 매칭**
  - 기업 역량 vs 입찰 요구사항 자동 매칭
  - 과거 유사 프로젝트 수행 경험 분석
  - 기술 스택 적합도 평가
  - 인증/자격 요구사항 충족도 체크
  - 매칭 스코어 및 상세 분석 리포트
  - **반복 프로젝트 우선 알림** (연간 계약 갱신 시점)

- **맞춤형 메일링 서비스**
  - 역량 기반 자동 프로젝트 추천
  - 매칭도 높은 프로젝트 우선 알림
  - 다단계 알림 설정 (매칭도 70%, 80%, 90% 이상)
  - **메일 발송 시간 설정**
    - MVP: 기본 오전 8시 (선택 가능: 6시, 7시, 8시, 9시, 12시, 14시, 17시, 19시)
    - 발송 빈도: 매일, 주 3회, 주 1회 선택
    - 추후: 사용자 맞춤 시간 설정, 요일별 설정
  - **특정 업체 독점 프로젝트 처리**
    - 동일 업체 3회 이상 연속 수주 시 경고 표시
    - 메일링 제외 옵션 또는 별도 섹션 분리
  - 알림 채널: 이메일 (MVP), 추후 SMS, 카카오톡, Slack 확장

- **스마트 필터링**
  - 최소 매칭도 설정 (예: 70% 이상만 알림)
  - 프로젝트 규모별 필터 (예산, 기간)
  - 지역별 필터링
  - 제외 키워드 설정 (관심 없는 분야 제외)
  - 선호 발주처 설정

#### 4.5 사용자 경험
- **맞춤형 대시보드**
  - 역량 매칭 기반 AI 추천 프로젝트 피드
  - 수주 가능성 시각화 (신호등 시스템)
  - **반복 프로젝트 전용 섹션** (연간/정기 입찰)
  - **경쟁업체 분석 대시보드** (기존 수주업체 정보)
  - 마감임박 알림 및 체크리스트
  - 팀 협업 기능 (코멘트, 태그)

- **상세 분석 리포트**
  - 1페이지 RFP 요약서 자동 생성
  - SWOT 분석 자동화
  - 필수 자격요건 체크리스트
  - **프로젝트 이력 리포트**
    - 과거 5년간 수주업체 변경 이력
    - 평균 계약 기간 및 갱신 주기
    - 업체별 재선정률 분석
    - 입찰 참여업체 트렌드
  - 제안서 작성 템플릿 제공

- **통합 알림 관리**
  - 실시간 푸시 알림 (웹/모바일)
  - 일일/주간 다이제스트 리포트
  - 중요도별 알림 우선순위 설정
  - 알림 히스토리 및 통계

#### 4.6 통계 및 인사이트
- **시장 분석**
  - 분야별 입찰 트렌드 대시보드
  - 발주기관별 선호도 분석
  - 계절성 및 예산 집행 패턴
  - 신규 발주처 발굴

- **성과 관리**
  - 개인/팀 수주율 추적
  - 업계 평균 대비 성과 비교
  - 실패 원인 분석 리포트
  - 개선 액션 아이템 제안

### 5. 기술 스택

#### 5.1 Backend
```yaml
Framework: FastAPI (Python 3.11+)
Database: 
  - PostgreSQL (메인 DB)
    - 사용자/기업 정보
    - 프로젝트 포트폴리오
    - 매칭 이력
  - Redis (캐싱/큐)
    - 실시간 알림 큐
    - 세션 관리
  - MongoDB (문서 저장)
    - 크롤링 데이터
    - RFP 문서
  - Vector DB (Pinecone/Weaviate)
    - 기업 역량 임베딩
    - 프로젝트 요구사항 임베딩
Queue: Celery + Redis
AI/ML: 
  - OpenAI GPT-4 Turbo
  - Claude 3 Opus (문서 분석)
  - LangChain (RAG 파이프라인)
  - XGBoost (매칭 스코어 예측)
  - Sentence Transformers (역량 임베딩)
```

#### 5.2 Document Processing
```yaml
HWP Processing: 
  - hwp5 라이브러리
  - LibreOffice headless 변환
  - Custom HWP parser
OCR: 
  - Tesseract 5.0
  - EasyOCR (한글 특화)
PDF Processing:
  - PyMuPDF (속도 우선)
  - pdfplumber (정확도 우선)
  - Camelot (테이블 추출)
```

#### 5.3 Frontend
```yaml
Framework: Next.js 14
UI Library: shadcn/ui
State: Zustand
Charts: Recharts
Real-time: Socket.io
```

#### 5.4 Infrastructure
```yaml
Hosting: AWS (Seoul Region)
Container: Docker + ECS
CDN: CloudFront
Storage: S3
Monitoring: 
  - Sentry (에러 트래킹)
  - Datadog (APM)
  - Grafana (메트릭)
CI/CD: GitHub Actions + AWS CodeDeploy
```

### 6. 데이터베이스 스키마 (주요 테이블)

#### 6.1 기업 정보 관리
```sql
-- 기업 프로필
companies (
  id, name, business_number, industry, 
  employee_count, established_date,
  certifications[], tech_stack[]
)

-- 프로젝트 포트폴리오
project_portfolio (
  id, company_id, project_name, client,
  budget, duration, category, outcome,
  tech_used[], team_size, success_rate
)

-- 팀 역량
team_capabilities (
  id, company_id, member_name, role,
  skills[], experience_years,
  availability_status
)
```

#### 6.2 프로젝트 히스토리
```sql
-- RFP 데이터베이스
rfp_database (
  id, rfp_title, rfp_number, agency_id,
  announcement_date, closing_date,
  budget_amount, project_type,
  hwp_content_parsed, key_requirements[],
  is_recurring, recurrence_pattern
)

-- 프로젝트 이력
project_history (
  id, rfp_id, project_name, agency_id, 
  winning_company, contract_amount,
  contract_start, contract_end,
  is_recurring, recurrence_pattern,
  previous_contractors[],
  monopoly_flag -- 특정업체 독점 여부
)

-- 반복 프로젝트 패턴
recurring_projects (
  id, agency_id, project_type,
  frequency, last_tender_date,
  next_expected_date, avg_contract_period,
  contractor_change_rate
)

-- 경쟁업체 분석
competitor_analysis (
  id, company_id, project_category,
  win_rate, avg_bid_amount,
  common_partners[], strengths[]
)
```

#### 6.3 매칭 및 알림
```sql
-- 매칭 규칙
matching_rules (
  id, company_id, min_match_score,
  preferred_categories[], excluded_keywords[],
  budget_range, location_preference,
  recurring_project_priority
)

-- 알림 설정
notification_settings (
  id, user_id, channels[], frequency,
  time_slots[], priority_threshold,
  recurring_alert_days_before
)

-- 매칭 이력
matching_history (
  id, company_id, project_id, match_score,
  matched_criteria[], notified_at,
  user_action, is_recurring_project
)
```

### 7. 비즈니스 모델

#### 7.1 구독 요금제

- **Starter** (월 9만원)
  - 일일 30개 프로젝트 알림
  - 기본 필터링 및 검색
  - 이메일 알림
  - 1개월 데이터 접근

- **Professional** (월 29만원)
  - 무제한 프로젝트 알림
  - AI 수주 가능성 분석
  - RAG 문서 검색
  - 카카오톡/Slack 연동
  - 6개월 데이터 접근
  - 5명 팀 계정

- **Enterprise** (월 99만원)
  - Professional 모든 기능
  - 무제한 팀원
  - API 접근 권한
  - 커스텀 AI 모델 학습
  - 전체 데이터 접근
  - 전담 고객 성공 매니저

- **Custom** (별도 협의)
  - 대기업/공공기관 맞춤형
  - On-premise 설치
  - 전용 인프라
  - SLA 보장

#### 7.2 부가 서비스
- RFP 작성 컨설팅 (건당 50만원)
- 맞춤형 시장 분석 리포트 (월 100만원)
- AI 모델 커스터마이징 (프로젝트별 견적)
- 제안서 검토 서비스 (건당 30만원)

### 8. 성공 지표 (KPIs)

#### 8.1 사용자 지표
- MAU: 500명 (6개월), 2,000명 (1년)
- DAU/MAU: 60% 이상
- 유료 전환율: 20%
- 월 이탈률(Churn): 5% 이하
- NPS Score: 50+ 

#### 8.2 기술 지표
- 크롤링 성공률: 99.9%
- 페이지 로드 시간: < 1초
- API 응답시간: < 500ms
- AI 예측 정확도: 75% (MVP), 85% (1년)
- 문서 처리 성공률: 95%+

#### 8.3 비즈니스 지표
- MRR: 5천만원 (6개월), 2억원 (1년)
- ARR: 25억원 (2년 목표)
- CAC: 30만원 이하
- LTV/CAC: 5 이상
- Gross Margin: 80%+

### 9. 개발 로드맵

#### Phase 1: Foundation (2개월)
- [x] 프로젝트 설정 및 인프라 구축
- [ ] 나라장터 크롤링 엔진 개발
- [ ] 기본 데이터베이스 스키마 설계
- [ ] 사용자 인증 시스템
- [ ] 관리자 대시보드

#### Phase 2: MVP (3개월)
- [ ] HWP/PDF 문서 처리 파이프라인
- [ ] 회원가입 및 기업 프로필 입력 시스템
- [ ] RFP-기업 자동 매칭 알고리즘
- [ ] 맞춤형 메일링 시스템 (시간대 선택 가능)
- [ ] 과거 수주업체 히스토리 DB 구축
- [ ] 주기성/일회성 프로젝트 패턴 분석
- [ ] 특정업체 독점 프로젝트 필터링
- [ ] 프로젝트 상세 페이지
- [ ] 결제 시스템 연동

#### Phase 3: AI Integration (3개월)
- [ ] RAG 시스템 구현
- [ ] 수주 가능성 예측 모델
- [ ] 자연어 검색
- [ ] RFP 자동 요약
- [ ] 맞춤 추천 알고리즘

#### Phase 4: Scale (4개월)
- [ ] 고급 분석 대시보드
- [ ] 팀 협업 기능
- [ ] 모바일 앱 (React Native)
- [ ] API 서비스
- [ ] 엔터프라이즈 기능

### 10. 리스크 및 완화 전략

#### 10.1 기술적 리스크
| 리스크 | 영향도 | 완화 전략 |
|--------|--------|-----------|
| 나라장터 크롤링 차단 | 높음 | IP 로테이션, User-Agent 다양화, 공식 API 협의 |
| HWP 파일 파싱 실패 | 중간 | 다중 변환 엔진, 폴백 메커니즘, 수동 처리 옵션 |
| AI 모델 정확도 부족 | 높음 | 지속적 학습, 사용자 피드백 루프, 하이브리드 모델 |
| 대용량 트래픽 처리 | 중간 | Auto-scaling, 캐싱 전략, CDN 활용 |

#### 10.2 법적/규제 리스크
| 리스크 | 영향도 | 완화 전략 |
|--------|--------|-----------|
| 공공데이터 저작권 | 낮음 | 공개 데이터만 활용, 법률 검토 완료 |
| 개인정보보호법 | 중간 | 최소 수집, 암호화, ISMS-P 인증 추진 |
| 불공정 경쟁 | 낮음 | 정보 제공 서비스로 한정, 입찰 대행 금지 |

#### 10.3 시장 리스크
| 리스크 | 영향도 | 완화 전략 |
|--------|--------|-----------|
| 경쟁사 출현 | 높음 | 빠른 시장 선점, 네트워크 효과 구축 |
| 시장 규모 제한 | 중간 | 해외 시장 확장 (동남아 정부조달) |
| 경기 침체 | 중간 | 프리미엄 기능 다양화, 비용 효율성 강조 |

### 11. 검증 계획

#### 11.1 Alpha Test (1개월)
- 내부 팀 10명 사용
- 핵심 기능 안정성 검증
- UX 개선사항 도출

#### 11.2 Beta Test (2개월)
- 30개 기업 파일럿 운영
- 무료 사용 대가 피드백 수집
- 실제 수주 성과 추적
- 제품-시장 적합성 검증

#### 11.3 Launch Strategy
- **Soft Launch**: IT 서비스 기업 100개사
- **확장 1단계**: 건설/엔지니어링 부문
- **확장 2단계**: 전 산업 분야
- **마케팅 채널**: 
  - SEO/SEM (나라장터 관련 키워드)
  - B2B 커뮤니티 (잡코리아, 사람인)
  - 파트너십 (회계법인, 컨설팅사)
  - 웨비나 및 교육 프로그램

### 12. 팀 구성 계획

#### 12.1 초기 팀 (MVP)
- Product Manager: 1명
- Backend Developer: 2명
- Frontend Developer: 1명
- AI/ML Engineer: 1명
- DevOps: 1명

#### 12.2 확장 팀 (1년 후)
- Engineering: 8명
- Product/Design: 3명
- Sales/CS: 4명
- Marketing: 2명
- Operations: 2명

### 13. 예산 계획

#### 13.1 초기 투자 (6개월)
- 인건비: 3억원
- 인프라: 3천만원
- AI API: 2천만원
- 마케팅: 5천만원
- 기타 운영비: 5천만원
- **총계**: 4.5억원

#### 13.2 연간 운영비 (정식 출시 후)
- 인건비: 10억원
- 인프라/클라우드: 1.2억원
- AI/API 비용: 1억원
- 마케팅/영업: 3억원
- 기타: 1.8억원
- **총계**: 17억원

### 14. 성공 요인

1. **차별화된 AI 기술**: 한국 공공조달 특화 모델
2. **빠른 실행력**: 6개월 내 MVP 출시
3. **고객 중심 개발**: 지속적인 피드백 반영
4. **네트워크 효과**: 데이터 축적을 통한 진입장벽
5. **전문성**: 공공조달 도메인 전문가 영입

### 15. Exit Strategy

- **3년 후 목표**:
  - ARR 50억원 달성
  - 시장 점유율 30%
  - Series B 투자 유치 (100억원)
  
- **5년 후 옵션**:
  - IPO (코스닥 상장)
  - M&A (대기업 인수)
  - 동남아 시장 진출