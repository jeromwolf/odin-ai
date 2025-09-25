-- 알림 시스템 테이블 생성 스크립트
-- 실행: psql -U blockmeta -d odin_db -f sql/create_alert_tables.sql

-- 1. 알림 규칙 테이블 (이미 설계됨)
CREATE TABLE IF NOT EXISTS alert_rules (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    rule_name VARCHAR(100) NOT NULL,
    keywords TEXT[],
    exclude_keywords TEXT[],
    min_price BIGINT,
    max_price BIGINT,
    organizations TEXT[],
    regions TEXT[],
    categories TEXT[],
    bid_close_days INTEGER, -- 마감 D-day
    notification_channels TEXT[] DEFAULT ARRAY['email'],
    notification_timing VARCHAR(20) DEFAULT 'immediate', -- immediate, daily, weekly
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 알림 매칭 결과 테이블
CREATE TABLE IF NOT EXISTS alert_matches (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES alert_rules(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL,
    bid_id VARCHAR(100) NOT NULL,
    match_score DECIMAL(3, 2) DEFAULT 0.00,
    matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    match_date DATE DEFAULT CURRENT_DATE, -- 매칭 날짜 (중복 체크용)
    is_sent BOOLEAN DEFAULT false,
    sent_at TIMESTAMP,
    UNIQUE(rule_id, bid_id) -- 같은 규칙, 같은 공고는 한 번만
);

-- 3. 알림 발송 큐 테이블
CREATE TABLE IF NOT EXISTS alert_queue (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    bid_id VARCHAR(100),
    rule_id INTEGER REFERENCES alert_rules(id),
    match_id INTEGER REFERENCES alert_matches(id),
    channel VARCHAR(20) NOT NULL, -- email, sms, push
    recipient VARCHAR(255) NOT NULL, -- 이메일 주소, 전화번호 등
    subject TEXT,
    content TEXT NOT NULL,
    priority INTEGER DEFAULT 1, -- 1(낮음), 2(중간), 3(높음)
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, sent, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    queue_date DATE DEFAULT CURRENT_DATE, -- 큐 생성 날짜 (중복 체크용)
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    INDEX idx_queue_status (status),
    INDEX idx_queue_date (queue_date),
    INDEX idx_user_bid (user_id, bid_id, channel, queue_date) -- 중복 체크용 복합 인덱스
);

-- 4. 알림 템플릿 테이블
CREATE TABLE IF NOT EXISTS alert_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(100) NOT NULL UNIQUE,
    channel VARCHAR(20) NOT NULL,
    subject_template TEXT,
    content_template TEXT NOT NULL,
    variables TEXT[], -- 사용 가능한 변수 목록
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. 알림 발송 로그 테이블 (분석용)
CREATE TABLE IF NOT EXISTS alert_logs (
    id SERIAL PRIMARY KEY,
    queue_id INTEGER REFERENCES alert_queue(id),
    user_id INTEGER NOT NULL,
    bid_id VARCHAR(100),
    rule_id INTEGER,
    channel VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_code VARCHAR(10),
    response_message TEXT,
    INDEX idx_log_date (sent_at),
    INDEX idx_log_user (user_id)
);

-- 6. 사용자 알림 설정 테이블
CREATE TABLE IF NOT EXISTS user_notification_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    email_enabled BOOLEAN DEFAULT true,
    sms_enabled BOOLEAN DEFAULT false,
    push_enabled BOOLEAN DEFAULT false,
    daily_digest_time TIME DEFAULT '09:00:00',
    weekly_digest_day INTEGER DEFAULT 1, -- 1=월요일
    max_alerts_per_day INTEGER DEFAULT 50,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_alert_rules_user ON alert_rules(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_matches_date ON alert_matches(match_date);
CREATE INDEX IF NOT EXISTS idx_alert_matches_sent ON alert_matches(is_sent);
CREATE INDEX IF NOT EXISTS idx_alert_queue_processing ON alert_queue(status, scheduled_at);

-- 기본 템플릿 데이터 삽입
INSERT INTO alert_templates (template_name, channel, subject_template, content_template, variables)
VALUES
('immediate_email', 'email',
 '[ODIN-AI] 새로운 입찰 공고: {{ bid_title }}',
 '안녕하세요 {{ user_name }}님, 알림 규칙 "{{ rule_name }}"에 매칭되는 새로운 입찰 공고가 등록되었습니다.',
 ARRAY['user_name', 'rule_name', 'bid_title', 'bid_id', 'match_score']),

('daily_digest_email', 'email',
 '[ODIN-AI] 일일 입찰 공고 다이제스트',
 '오늘 등록된 {{ total_count }}개의 매칭 공고가 있습니다.',
 ARRAY['user_name', 'total_count', 'bids_list']),

('immediate_sms', 'sms',
 NULL,
 '[ODIN-AI] 새 공고: {{ bid_title_short }} 매칭률 {{ match_score }}%',
 ARRAY['bid_title_short', 'match_score', 'bid_id'])
ON CONFLICT (template_name) DO NOTHING;

-- 뷰 생성: 오늘의 알림 현황
CREATE OR REPLACE VIEW v_today_alerts AS
SELECT
    am.user_id,
    COUNT(DISTINCT am.bid_id) as matched_bids,
    COUNT(DISTINCT CASE WHEN am.is_sent THEN am.bid_id END) as sent_alerts,
    COUNT(DISTINCT CASE WHEN NOT am.is_sent THEN am.bid_id END) as pending_alerts,
    MAX(am.matched_at) as last_match_time
FROM alert_matches am
WHERE am.match_date = CURRENT_DATE
GROUP BY am.user_id;

-- 뷰 생성: 큐 상태 모니터링
CREATE OR REPLACE VIEW v_queue_status AS
SELECT
    status,
    channel,
    COUNT(*) as count,
    MIN(created_at) as oldest,
    MAX(created_at) as newest
FROM alert_queue
WHERE queue_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY status, channel;

-- 권한 설정
GRANT ALL ON ALL TABLES IN SCHEMA public TO blockmeta;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO blockmeta;

COMMENT ON TABLE alert_rules IS '사용자 알림 규칙';
COMMENT ON TABLE alert_matches IS '알림 매칭 결과';
COMMENT ON TABLE alert_queue IS '알림 발송 대기 큐';
COMMENT ON TABLE alert_templates IS '알림 템플릿';
COMMENT ON TABLE alert_logs IS '알림 발송 로그';
COMMENT ON TABLE user_notification_settings IS '사용자 알림 설정';