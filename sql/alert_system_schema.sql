-- 알림 시스템 데이터베이스 스키마

-- 1. 알림 규칙 메인 테이블
CREATE TABLE alert_rules (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rule_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- 조건 설정 (JSON으로 저장)
    conditions JSONB NOT NULL,
    match_type VARCHAR(10) DEFAULT 'ALL', -- 'ALL' or 'ANY'

    -- 알림 설정
    notification_channels TEXT[] DEFAULT ARRAY['email'], -- ['email', 'web', 'sms']
    notification_timing VARCHAR(20) DEFAULT 'immediate', -- 'immediate', 'daily', 'weekly'
    notification_time TIME DEFAULT '09:00:00',
    notification_day INTEGER DEFAULT 1, -- 1=월요일, 7=일요일

    -- 상태 관리
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_triggered TIMESTAMP,
    trigger_count INTEGER DEFAULT 0,

    -- 인덱스
    CONSTRAINT valid_match_type CHECK (match_type IN ('ALL', 'ANY')),
    CONSTRAINT valid_timing CHECK (notification_timing IN ('immediate', 'daily', 'weekly')),
    CONSTRAINT valid_day CHECK (notification_day BETWEEN 1 AND 7)
);

-- 2. 알림 발송 기록 테이블
CREATE TABLE alert_notifications (
    id SERIAL PRIMARY KEY,
    alert_rule_id INTEGER NOT NULL REFERENCES alert_rules(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bid_notice_no VARCHAR(50) NOT NULL, -- 해당 입찰 공고

    -- 발송 정보
    channel VARCHAR(20) NOT NULL, -- 'email', 'web', 'sms'
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'sent', 'failed', 'read'
    subject VARCHAR(500),
    content TEXT,

    -- 메타데이터
    sent_at TIMESTAMP,
    read_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 인덱스
    CONSTRAINT valid_channel CHECK (channel IN ('email', 'web', 'sms')),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'sent', 'failed', 'read'))
);

-- 3. 사용자 알림 기본 설정 테이블 (기존 강화)
CREATE TABLE user_notification_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,

    -- 글로벌 설정
    email_enabled BOOLEAN DEFAULT true,
    web_enabled BOOLEAN DEFAULT true,
    sms_enabled BOOLEAN DEFAULT false,

    -- 기본 알림 시간
    default_notification_time TIME DEFAULT '09:00:00',
    timezone VARCHAR(50) DEFAULT 'Asia/Seoul',

    -- 알림 빈도 제한
    max_daily_notifications INTEGER DEFAULT 50,
    quiet_hours_start TIME DEFAULT '22:00:00',
    quiet_hours_end TIME DEFAULT '08:00:00',

    -- 연락처 정보
    sms_phone_number VARCHAR(20),
    backup_email VARCHAR(255),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 알림 템플릿 테이블
CREATE TABLE notification_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(100) NOT NULL UNIQUE,
    channel VARCHAR(20) NOT NULL,

    -- 템플릿 내용
    subject_template TEXT,
    content_template TEXT NOT NULL,

    -- 메타데이터
    description TEXT,
    variables JSONB, -- 사용 가능한 변수 목록
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_template_channel CHECK (channel IN ('email', 'web', 'sms'))
);

-- 인덱스 생성
CREATE INDEX idx_alert_rules_user_id ON alert_rules(user_id);
CREATE INDEX idx_alert_rules_active ON alert_rules(is_active);
CREATE INDEX idx_alert_rules_timing ON alert_rules(notification_timing);

CREATE INDEX idx_alert_notifications_rule_id ON alert_notifications(alert_rule_id);
CREATE INDEX idx_alert_notifications_user_id ON alert_notifications(user_id);
CREATE INDEX idx_alert_notifications_status ON alert_notifications(status);
CREATE INDEX idx_alert_notifications_channel ON alert_notifications(channel);

-- 트리거: updated_at 자동 갱신
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_alert_rules_updated_at BEFORE UPDATE
    ON alert_rules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_notification_settings_updated_at BEFORE UPDATE
    ON user_notification_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_templates_updated_at BEFORE UPDATE
    ON notification_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 기본 템플릿 데이터 삽입
INSERT INTO notification_templates (template_name, channel, subject_template, content_template, description, variables) VALUES
('bid_match_email', 'email',
 '[ODIN-AI] 새로운 입찰 공고: {{title}}',
 '<h2>새로운 입찰 공고가 등록되었습니다</h2>
  <h3>{{title}}</h3>
  <p><strong>공고번호:</strong> {{bid_notice_no}}</p>
  <p><strong>발주기관:</strong> {{organization_name}}</p>
  <p><strong>예정가격:</strong> {{estimated_price}}</p>
  <p><strong>입찰마감:</strong> {{bid_end_date}}</p>
  <p><strong>상세보기:</strong> <a href="{{detail_url}}">공고 상세 페이지</a></p>',
 '새로운 입찰 공고 매칭 시 이메일 알림 템플릿',
 '{"title": "입찰 공고 제목", "bid_notice_no": "공고번호", "organization_name": "발주기관", "estimated_price": "예정가격", "bid_end_date": "입찰마감일", "detail_url": "상세 URL"}'::jsonb
),
('bid_match_web', 'web',
 '새로운 입찰 공고 매칭',
 '{{title}} - {{organization_name}} (마감: {{bid_end_date}})',
 '웹 푸시 알림 템플릿',
 '{"title": "입찰 공고 제목", "organization_name": "발주기관", "bid_end_date": "입찰마감일"}'::jsonb
),
('deadline_reminder_email', 'email',
 '[ODIN-AI] 입찰 마감 임박: {{title}}',
 '<h2>입찰 마감이 {{hours_remaining}}시간 남았습니다</h2>
  <h3>{{title}}</h3>
  <p><strong>공고번호:</strong> {{bid_notice_no}}</p>
  <p><strong>입찰마감:</strong> {{bid_end_date}}</p>
  <p><strong>상세보기:</strong> <a href="{{detail_url}}">공고 상세 페이지</a></p>',
 '입찰 마감 임박 알림 템플릿',
 '{"title": "입찰 공고 제목", "bid_notice_no": "공고번호", "bid_end_date": "입찰마감일", "hours_remaining": "남은 시간", "detail_url": "상세 URL"}'::jsonb
);