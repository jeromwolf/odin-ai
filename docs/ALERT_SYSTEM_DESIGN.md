# 🔔 ODIN-AI 알림 등록 시스템 설계서

> 작성일: 2025-09-25
> 작성자: ODIN-AI 개발팀

## 📋 개요

사용자가 관심있는 입찰 조건을 등록하면, 배치 프로그램 실행 후 매칭되는 입찰이 발견될 때 자동으로 알림을 발송하는 시스템

## 🎯 핵심 기능

1. **다양한 조건 등록**
   - 키워드 (복수 등록 가능)
   - 가격 범위
   - 기관/지역
   - 카테고리/업종
   - 마감일 임박 (D-day 설정)

2. **알림 채널**
   - 이메일
   - 웹 푸시
   - SMS (선택)
   - 인앱 알림
   - 카카오톡 (선택)

3. **알림 타이밍**
   - 즉시 알림
   - 일일 다이제스트
   - 주간 리포트
   - 맞춤 시간대

## 🗄️ 데이터베이스 설계

### 1. alert_rules (알림 규칙)
```sql
CREATE TABLE alert_rules (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    rule_name VARCHAR(100) NOT NULL,           -- "100억 이상 건설 프로젝트"
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 5,                 -- 1-10 우선순위

    -- 알림 조건
    keywords TEXT[],                           -- ['건설', '토목', '건축']
    exclude_keywords TEXT[],                    -- 제외 키워드
    min_price BIGINT,                          -- 최소 금액
    max_price BIGINT,                          -- 최대 금액
    organizations TEXT[],                       -- ['서울시', '경기도']
    categories TEXT[],                         -- ['공사', '용역', '물품']
    regions TEXT[],                            -- ['서울', '경기', '인천']

    -- 고급 조건
    deadline_days INTEGER,                     -- 마감 D-7 이내
    has_pre_announcement BOOLEAN,              -- 사전공고 있음
    subcontract_allowed BOOLEAN,               -- 하도급 가능
    joint_venture_allowed BOOLEAN,             -- 공동도급 가능

    -- 알림 설정
    notification_channels TEXT[],              -- ['email', 'push', 'sms']
    notification_timing VARCHAR(20),           -- 'immediate', 'daily', 'weekly'
    notification_time TIME,                     -- 09:00:00 (일일 알림 시간)
    notification_days INTEGER[],               -- [1,3,5] (주간: 월,수,금)

    -- 메타 정보
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_matched_at TIMESTAMP,
    match_count INTEGER DEFAULT 0,

    CONSTRAINT check_price CHECK (min_price IS NULL OR max_price IS NULL OR min_price <= max_price)
);

-- 인덱스
CREATE INDEX idx_alert_rules_user_id ON alert_rules(user_id);
CREATE INDEX idx_alert_rules_active ON alert_rules(is_active);
CREATE INDEX idx_alert_rules_keywords ON alert_rules USING GIN(keywords);
```

### 2. alert_matches (매칭 결과)
```sql
CREATE TABLE alert_matches (
    id SERIAL PRIMARY KEY,
    alert_rule_id INTEGER NOT NULL REFERENCES alert_rules(id) ON DELETE CASCADE,
    bid_id VARCHAR(50) NOT NULL REFERENCES bid_announcements(bid_notice_no),

    match_score FLOAT,                         -- 매칭 점수 (0-100)
    matched_keywords TEXT[],                   -- 매칭된 키워드
    match_reasons JSONB,                       -- 매칭 상세 이유

    is_notified BOOLEAN DEFAULT false,
    notified_at TIMESTAMP,
    notification_status VARCHAR(20),           -- 'pending', 'sent', 'failed'
    notification_error TEXT,

    user_action VARCHAR(20),                   -- 'viewed', 'bookmarked', 'ignored'
    user_action_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(alert_rule_id, bid_id)             -- 중복 방지
);

-- 인덱스
CREATE INDEX idx_alert_matches_rule_id ON alert_matches(alert_rule_id);
CREATE INDEX idx_alert_matches_bid_id ON alert_matches(bid_id);
CREATE INDEX idx_alert_matches_notified ON alert_matches(is_notified);
CREATE INDEX idx_alert_matches_created ON alert_matches(created_at);
```

### 3. alert_queue (알림 발송 큐)
```sql
CREATE TABLE alert_queue (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    alert_match_id INTEGER REFERENCES alert_matches(id),

    channel VARCHAR(20) NOT NULL,              -- 'email', 'push', 'sms'
    recipient VARCHAR(255) NOT NULL,           -- 이메일, 전화번호 등

    subject TEXT,
    content TEXT,
    template_id VARCHAR(50),
    template_data JSONB,

    priority INTEGER DEFAULT 5,
    scheduled_at TIMESTAMP,

    status VARCHAR(20) DEFAULT 'pending',      -- 'pending', 'processing', 'sent', 'failed'
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,

    sent_at TIMESTAMP,
    error_message TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_alert_queue_status ON alert_queue(status);
CREATE INDEX idx_alert_queue_scheduled ON alert_queue(scheduled_at);
CREATE INDEX idx_alert_queue_user_id ON alert_queue(user_id);
```

### 4. alert_templates (알림 템플릿)
```sql
CREATE TABLE alert_templates (
    id VARCHAR(50) PRIMARY KEY,                -- 'bid_match_email'
    name VARCHAR(100) NOT NULL,
    channel VARCHAR(20) NOT NULL,

    subject_template TEXT,                     -- "{{count}}개의 새로운 입찰이 발견되었습니다"
    body_template TEXT,                        -- HTML/텍스트 템플릿

    variables JSONB,                           -- 사용 가능한 변수 목록
    is_active BOOLEAN DEFAULT true,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🖥️ 알림 등록 화면 UI 설계

### 1. 알림 규칙 목록 페이지
```
┌─────────────────────────────────────────────────────┐
│  내 알림 설정                              + 새 알림 추가 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────────────────────────────────────┐  │
│  │ ⚡ 100억 이상 건설 프로젝트              ON │  │
│  │ 키워드: 건설, 토목 | 금액: 100억↑         │  │
│  │ 매칭: 152건 | 최근: 2시간 전              │  │
│  │ [수정] [복제] [삭제]                      │  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
│  ┌─────────────────────────────────────────────┐  │
│  │ 🏢 서울시 소프트웨어 용역              ON │  │
│  │ 키워드: SW, SI | 기관: 서울시              │  │
│  │ 매칭: 89건 | 최근: 어제                    │  │
│  │ [수정] [복제] [삭제]                      │  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 2. 알림 등록/수정 화면
```
┌─────────────────────────────────────────────────────┐
│  새 알림 규칙 만들기                                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  규칙 이름: [_________________________]            │
│                                                     │
│  ▼ 기본 조건                                       │
│  ┌───────────────────────────────────────────┐    │
│  │ 키워드:                                   │    │
│  │ [건설] [토목] [+추가]                     │    │
│  │                                           │    │
│  │ 제외 키워드:                              │    │
│  │ [폐기물] [+추가]                          │    │
│  │                                           │    │
│  │ 예정가격:                                 │    │
│  │ 최소 [100,000,000] ~ 최대 [___________]   │    │
│  │                                           │    │
│  │ 발주기관:                                 │    │
│  │ ☑ 서울특별시  ☑ 경기도  ☐ 인천광역시   │    │
│  │ ☐ 부산광역시  ☐ 대구광역시  [더보기]     │    │
│  └───────────────────────────────────────────┘    │
│                                                     │
│  ▼ 고급 조건                                       │
│  ┌───────────────────────────────────────────┐    │
│  │ 마감일:  [7] 일 이내                      │    │
│  │ ☑ 사전공고 있음                           │    │
│  │ ☑ 하도급 가능                             │    │
│  │ ☐ 공동도급 가능                           │    │
│  └───────────────────────────────────────────┘    │
│                                                     │
│  ▼ 알림 설정                                       │
│  ┌───────────────────────────────────────────┐    │
│  │ 알림 채널:                                │    │
│  │ ☑ 이메일  ☑ 웹 푸시  ☐ SMS              │    │
│  │                                           │    │
│  │ 알림 시점:                                │    │
│  │ ◉ 즉시 알림                               │    │
│  │ ○ 일일 다이제스트 [09:00]                │    │
│  │ ○ 주간 리포트 [월,수,금]                  │    │
│  └───────────────────────────────────────────┘    │
│                                                     │
│  [미리보기]  [테스트 실행]    [취소] [저장]        │
└─────────────────────────────────────────────────────┘
```

### 3. 알림 히스토리 페이지
```
┌─────────────────────────────────────────────────────┐
│  알림 발송 내역                                     │
├─────────────────────────────────────────────────────┤
│  기간: [최근 7일 ▼]  상태: [전체 ▼]  [검색]       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  2025-09-25 09:00  📧 이메일                       │
│  "5개의 새로운 건설 프로젝트가 등록되었습니다"     │
│  규칙: 100억 이상 건설 프로젝트                    │
│  [상세보기]                                        │
│  ─────────────────────────────────────────────     │
│                                                     │
│  2025-09-24 18:30  🔔 푸시 알림                    │
│  "마감 임박: 서울시 전산장비 구매"                 │
│  규칙: 마감 D-3 알림                               │
│  [상세보기]                                        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 🔄 알림 처리 플로우

### 1. 배치 실행 시 알림 처리
```python
# batch/modules/alert_processor.py

class AlertProcessor:
    def process_new_bids(self, new_bids):
        """새로운 입찰에 대한 알림 처리"""

        # 1. 활성 알림 규칙 조회
        active_rules = self.get_active_rules()

        # 2. 각 규칙별로 매칭 확인
        for rule in active_rules:
            matches = self.match_bids_with_rule(new_bids, rule)

            if matches:
                # 3. 매칭 결과 저장
                self.save_matches(rule, matches)

                # 4. 알림 큐에 추가
                if rule.notification_timing == 'immediate':
                    self.queue_immediate_alert(rule, matches)
                else:
                    self.schedule_digest_alert(rule, matches)

    def match_bids_with_rule(self, bids, rule):
        """입찰과 규칙 매칭"""
        matched_bids = []

        for bid in bids:
            score = 0
            reasons = []

            # 키워드 매칭
            if rule.keywords:
                keyword_matches = self.match_keywords(
                    bid.title + bid.content,
                    rule.keywords
                )
                if keyword_matches:
                    score += 30
                    reasons.append(f"키워드 매칭: {keyword_matches}")

            # 가격 범위 확인
            if rule.min_price and bid.price >= rule.min_price:
                score += 20
                reasons.append(f"최소가격 충족: {bid.price:,}원")

            # 기관 확인
            if rule.organizations:
                if any(org in bid.organization for org in rule.organizations):
                    score += 20
                    reasons.append(f"기관 매칭: {bid.organization}")

            # 마감일 확인
            if rule.deadline_days:
                days_left = (bid.deadline - datetime.now()).days
                if days_left <= rule.deadline_days:
                    score += 15
                    reasons.append(f"마감 임박: D-{days_left}")

            if score >= 50:  # 임계값 이상이면 매칭
                matched_bids.append({
                    'bid': bid,
                    'score': score,
                    'reasons': reasons
                })

        return matched_bids
```

### 2. 알림 발송 워커
```python
# workers/alert_sender.py

class AlertSender:
    def process_queue(self):
        """알림 큐 처리"""
        pending_alerts = self.get_pending_alerts()

        for alert in pending_alerts:
            try:
                if alert.channel == 'email':
                    self.send_email(alert)
                elif alert.channel == 'push':
                    self.send_push(alert)
                elif alert.channel == 'sms':
                    self.send_sms(alert)

                self.mark_as_sent(alert)
            except Exception as e:
                self.handle_failure(alert, e)

    def send_email(self, alert):
        """이메일 발송"""
        template = self.get_template('bid_match_email')

        html_content = self.render_template(
            template,
            alert.template_data
        )

        # 실제 이메일 발송
        send_mail(
            to=alert.recipient,
            subject=alert.subject,
            html=html_content
        )
```

## 📊 알림 통계 대시보드

```sql
-- 알림 규칙별 성과 분석
CREATE VIEW alert_performance AS
SELECT
    ar.id,
    ar.rule_name,
    ar.user_id,
    COUNT(DISTINCT am.bid_id) as total_matches,
    COUNT(DISTINCT CASE WHEN am.user_action = 'viewed' THEN am.bid_id END) as viewed_count,
    COUNT(DISTINCT CASE WHEN am.user_action = 'bookmarked' THEN am.bid_id END) as bookmarked_count,
    AVG(am.match_score) as avg_match_score,
    MAX(am.created_at) as last_match_at
FROM alert_rules ar
LEFT JOIN alert_matches am ON ar.id = am.alert_rule_id
GROUP BY ar.id, ar.rule_name, ar.user_id;
```

## 🚀 구현 태스크

### Phase 1: 기초 구현 (1주)
- [ ] DB 테이블 생성
- [ ] 알림 규칙 CRUD API
- [ ] 알림 등록 화면 UI
- [ ] 기본 매칭 엔진

### Phase 2: 알림 발송 (1주)
- [ ] 이메일 발송 시스템
- [ ] 알림 큐 처리 워커
- [ ] 템플릿 시스템
- [ ] 발송 히스토리

### Phase 3: 고급 기능 (2주)
- [ ] 웹 푸시 알림
- [ ] SMS 연동
- [ ] 일일/주간 다이제스트
- [ ] 알림 성과 분석

### Phase 4: 최적화 (1주)
- [ ] 매칭 알고리즘 개선
- [ ] 중복 알림 방지
- [ ] 사용자별 선호도 학습
- [ ] A/B 테스트

## 📝 API 엔드포인트

```yaml
# 알림 규칙 관리
POST   /api/alerts/rules              # 규칙 생성
GET    /api/alerts/rules              # 규칙 목록
GET    /api/alerts/rules/{id}         # 규칙 상세
PUT    /api/alerts/rules/{id}         # 규칙 수정
DELETE /api/alerts/rules/{id}         # 규칙 삭제
POST   /api/alerts/rules/{id}/test    # 규칙 테스트

# 알림 히스토리
GET    /api/alerts/history            # 발송 내역
GET    /api/alerts/matches            # 매칭 결과
POST   /api/alerts/matches/{id}/action # 사용자 액션

# 알림 설정
GET    /api/alerts/settings           # 알림 설정
PUT    /api/alerts/settings           # 설정 변경
POST   /api/alerts/unsubscribe        # 수신 거부
```

## 🔒 보안 고려사항

1. **개인정보 보호**
   - 알림 내용 암호화
   - 수신 거부 링크 제공
   - GDPR 준수

2. **스팸 방지**
   - 일일 발송 제한
   - 중복 알림 방지
   - 사용자별 rate limiting

3. **권한 관리**
   - 본인 규칙만 수정 가능
   - 구독 플랜별 규칙 수 제한
   - 관리자 승인 필요 항목

## 💡 차별화 포인트

1. **스마트 매칭**
   - AI 기반 연관 입찰 추천
   - 과거 관심사 학습
   - 경쟁사 동향 알림

2. **맞춤형 리포트**
   - 주간 시장 동향
   - 카테고리별 분석
   - 낙찰 예측 정보

3. **협업 기능**
   - 팀 공유 알림
   - 담당자 지정
   - 코멘트/메모 기능