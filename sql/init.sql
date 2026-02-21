-- ============================================================
-- ODIN-AI Database Initialization Script
-- Auto-generated master init file for Docker PostgreSQL
-- Combines all schema files in dependency order
-- ============================================================
-- Order:
--   1. create_user_tables.sql       (base: users, sessions, tokens)
--   2. create_alert_tables.sql      (references users implicitly)
--   3. create_bookmark_tables.sql   (references users implicitly)
--   4. create_subscription_tables.sql (references users)
--   5. create_subscription_functions.sql (uses subscription tables)
--   6. create_ai_recommendation_tables.sql (references users, bid_announcements)
--   7. admin_schema.sql             (references users)
--   8. create_ontology_tables.sql   (standalone domain tables)
--   9. seed_ontology_data.sql       (populates ontology tables)
--  10. create_rag_tables.sql        (references bid_announcements)
-- ============================================================


-- ============================================================
-- SECTION 1: User Tables
-- Source: sql/create_user_tables.sql
-- ============================================================

-- 사용자 테이블 생성
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    email_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    profile_image VARCHAR(500),
    phone_number VARCHAR(20),
    company VARCHAR(255),
    department VARCHAR(255),
    position VARCHAR(100)
);

-- 사용자 세션 테이블 (리프레시 토큰 관리)
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    refresh_token VARCHAR(500) UNIQUE NOT NULL,
    device_info VARCHAR(255),
    ip_address VARCHAR(45),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- 비밀번호 재설정 토큰 테이블
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 이메일 인증 토큰 테이블
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 사용자 권한/역할 테이블
CREATE TABLE IF NOT EXISTS user_roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 사용자-역할 관계 테이블
CREATE TABLE IF NOT EXISTS user_role_relations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES user_roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, role_id)
);

-- 기본 역할 추가
INSERT INTO user_roles (name, description) VALUES
    ('user', '일반 사용자'),
    ('premium', '프리미엄 사용자'),
    ('admin', '관리자')
ON CONFLICT (name) DO NOTHING;

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_refresh_token ON user_sessions(refresh_token);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_token ON email_verification_tokens(token);

COMMENT ON TABLE users IS '사용자 정보';
COMMENT ON TABLE user_sessions IS '사용자 세션 및 리프레시 토큰';
COMMENT ON TABLE password_reset_tokens IS '비밀번호 재설정 토큰';
COMMENT ON TABLE email_verification_tokens IS '이메일 인증 토큰';
COMMENT ON TABLE user_roles IS '사용자 권한/역할';
COMMENT ON TABLE user_role_relations IS '사용자-역할 관계';


-- ============================================================
-- SECTION 2: Alert Tables
-- Source: sql/create_alert_tables.sql
-- ============================================================

-- 1. 알림 규칙 테이블
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
    bid_close_days INTEGER,
    notification_channels TEXT[] DEFAULT ARRAY['email'],
    notification_timing VARCHAR(20) DEFAULT 'immediate',
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
    match_date DATE DEFAULT CURRENT_DATE,
    is_sent BOOLEAN DEFAULT false,
    sent_at TIMESTAMP,
    UNIQUE(rule_id, bid_id)
);

-- 3. 알림 발송 큐 테이블
CREATE TABLE IF NOT EXISTS alert_queue (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    bid_id VARCHAR(100),
    rule_id INTEGER REFERENCES alert_rules(id),
    match_id INTEGER REFERENCES alert_matches(id),
    channel VARCHAR(20) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    subject TEXT,
    content TEXT NOT NULL,
    priority INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    queue_date DATE DEFAULT CURRENT_DATE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0
);

-- 4. 알림 템플릿 테이블
CREATE TABLE IF NOT EXISTS alert_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(100) NOT NULL UNIQUE,
    channel VARCHAR(20) NOT NULL,
    subject_template TEXT,
    content_template TEXT NOT NULL,
    variables TEXT[],
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
    response_message TEXT
);

-- 6. 사용자 알림 설정 테이블
CREATE TABLE IF NOT EXISTS user_notification_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    email_enabled BOOLEAN DEFAULT true,
    sms_enabled BOOLEAN DEFAULT false,
    push_enabled BOOLEAN DEFAULT false,
    daily_digest_time TIME DEFAULT '09:00:00',
    weekly_digest_day INTEGER DEFAULT 1,
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
CREATE INDEX IF NOT EXISTS idx_alert_queue_status ON alert_queue(status);
CREATE INDEX IF NOT EXISTS idx_alert_queue_date ON alert_queue(queue_date);
CREATE INDEX IF NOT EXISTS idx_alert_queue_user_bid ON alert_queue(user_id, bid_id, channel, queue_date);
CREATE INDEX IF NOT EXISTS idx_alert_log_date ON alert_logs(sent_at);
CREATE INDEX IF NOT EXISTS idx_alert_log_user ON alert_logs(user_id);

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

COMMENT ON TABLE alert_rules IS '사용자 알림 규칙';
COMMENT ON TABLE alert_matches IS '알림 매칭 결과';
COMMENT ON TABLE alert_queue IS '알림 발송 대기 큐';
COMMENT ON TABLE alert_templates IS '알림 템플릿';
COMMENT ON TABLE alert_logs IS '알림 발송 로그';
COMMENT ON TABLE user_notification_settings IS '사용자 알림 설정';


-- ============================================================
-- SECTION 3: Bookmark Tables
-- Source: sql/create_bookmark_tables.sql
-- ============================================================

-- 1. 사용자 북마크 테이블
CREATE TABLE IF NOT EXISTS user_bookmarks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    bid_id VARCHAR(100) NOT NULL,
    title TEXT,
    organization_name VARCHAR(255),
    estimated_price BIGINT,
    bid_end_date TIMESTAMP,
    notes TEXT,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, bid_id)
);

-- 2. 북마크 폴더 (선택적 기능)
CREATE TABLE IF NOT EXISTS bookmark_folders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    folder_name VARCHAR(100) NOT NULL,
    description TEXT,
    color VARCHAR(7),
    icon VARCHAR(50),
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, folder_name)
);

-- 3. 북마크-폴더 관계
CREATE TABLE IF NOT EXISTS bookmark_folder_relations (
    id SERIAL PRIMARY KEY,
    bookmark_id INTEGER REFERENCES user_bookmarks(id) ON DELETE CASCADE,
    folder_id INTEGER REFERENCES bookmark_folders(id) ON DELETE CASCADE,
    UNIQUE(bookmark_id, folder_id)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_bookmarks_user ON user_bookmarks(user_id);
CREATE INDEX IF NOT EXISTS idx_bookmarks_bid ON user_bookmarks(bid_id);
CREATE INDEX IF NOT EXISTS idx_bookmarks_created ON user_bookmarks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bookmarks_end_date ON user_bookmarks(bid_end_date);

-- 뷰: 사용자별 북마크 통계
CREATE OR REPLACE VIEW v_user_bookmark_stats AS
SELECT
    user_id,
    COUNT(*) as total_bookmarks,
    COUNT(CASE WHEN bid_end_date > NOW() THEN 1 END) as active_bookmarks,
    COUNT(CASE WHEN bid_end_date <= NOW() THEN 1 END) as expired_bookmarks,
    MIN(created_at) as first_bookmark,
    MAX(created_at) as last_bookmark
FROM user_bookmarks
GROUP BY user_id;

-- 뷰: 인기 북마크 공고
CREATE OR REPLACE VIEW v_popular_bookmarks AS
SELECT
    bid_id,
    COUNT(DISTINCT user_id) as bookmark_count,
    MIN(title) as title,
    MIN(organization_name) as organization,
    MAX(bid_end_date) as bid_end_date
FROM user_bookmarks
GROUP BY bid_id
HAVING COUNT(DISTINCT user_id) > 1
ORDER BY bookmark_count DESC;

-- 함수: 북마크 토글 (추가/삭제)
CREATE OR REPLACE FUNCTION toggle_bookmark(
    p_user_id INTEGER,
    p_bid_id VARCHAR(100),
    p_title TEXT DEFAULT NULL,
    p_organization VARCHAR(255) DEFAULT NULL,
    p_price BIGINT DEFAULT NULL,
    p_end_date TIMESTAMP DEFAULT NULL
) RETURNS JSON AS $$
DECLARE
    v_bookmark_id INTEGER;
    v_action VARCHAR(10);
BEGIN
    -- 기존 북마크 확인
    SELECT id INTO v_bookmark_id
    FROM user_bookmarks
    WHERE user_id = p_user_id AND bid_id = p_bid_id;

    IF v_bookmark_id IS NOT NULL THEN
        -- 북마크 제거
        DELETE FROM user_bookmarks WHERE id = v_bookmark_id;
        v_action := 'removed';
    ELSE
        -- 북마크 추가
        INSERT INTO user_bookmarks (
            user_id, bid_id, title, organization_name,
            estimated_price, bid_end_date
        ) VALUES (
            p_user_id, p_bid_id, p_title, p_organization,
            p_price, p_end_date
        ) RETURNING id INTO v_bookmark_id;
        v_action := 'added';
    END IF;

    RETURN json_build_object(
        'success', true,
        'action', v_action,
        'bookmark_id', v_bookmark_id,
        'bid_id', p_bid_id
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE user_bookmarks IS '사용자 북마크';
COMMENT ON TABLE bookmark_folders IS '북마크 폴더';
COMMENT ON TABLE bookmark_folder_relations IS '북마크-폴더 관계';


-- ============================================================
-- SECTION 4: Subscription Tables
-- Source: sql/create_subscription_tables.sql
-- ============================================================

-- 기존 테이블 삭제 (초기화 시 재생성)
DROP TABLE IF EXISTS payment_history CASCADE;
DROP TABLE IF EXISTS user_subscriptions CASCADE;
DROP TABLE IF EXISTS subscription_features CASCADE;
DROP TABLE IF EXISTS subscription_plans CASCADE;
DROP TABLE IF EXISTS payment_methods CASCADE;
DROP TABLE IF EXISTS billing_addresses CASCADE;
DROP TABLE IF EXISTS subscription_usage CASCADE;
DROP TABLE IF EXISTS invoices CASCADE;

-- 구독 플랜 테이블
CREATE TABLE subscription_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    price_monthly INTEGER NOT NULL,
    price_yearly INTEGER,
    is_active BOOLEAN DEFAULT true,
    max_searches_per_day INTEGER DEFAULT NULL,
    max_downloads_per_month INTEGER DEFAULT NULL,
    max_bookmarks INTEGER DEFAULT NULL,
    max_alerts INTEGER DEFAULT NULL,
    api_rate_limit INTEGER DEFAULT NULL,
    has_ai_recommendations BOOLEAN DEFAULT false,
    has_advanced_search BOOLEAN DEFAULT false,
    has_export_excel BOOLEAN DEFAULT false,
    has_api_access BOOLEAN DEFAULT false,
    has_priority_support BOOLEAN DEFAULT false,
    has_custom_alerts BOOLEAN DEFAULT false,
    has_team_collaboration BOOLEAN DEFAULT false,
    badge_color VARCHAR(7),
    badge_text VARCHAR(20),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 사용자 구독 정보
CREATE TABLE user_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id INTEGER NOT NULL REFERENCES subscription_plans(id),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    billing_cycle VARCHAR(10) NOT NULL DEFAULT 'monthly',
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    cancelled_at TIMESTAMP,
    next_billing_date TIMESTAMP,
    last_payment_date TIMESTAMP,
    last_payment_amount INTEGER,
    auto_renew BOOLEAN DEFAULT true,
    is_trial BOOLEAN DEFAULT false,
    trial_ends_at TIMESTAMP,
    promo_code VARCHAR(50),
    discount_percentage INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id)
);

-- 결제 내역
CREATE TABLE payment_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id INTEGER REFERENCES user_subscriptions(id),
    amount INTEGER NOT NULL,
    currency VARCHAR(3) DEFAULT 'KRW',
    payment_method VARCHAR(50),
    status VARCHAR(20) NOT NULL,
    transaction_id VARCHAR(100) UNIQUE,
    gateway VARCHAR(50),
    gateway_response JSONB,
    description TEXT,
    invoice_number VARCHAR(50),
    failure_reason TEXT,
    failed_at TIMESTAMP,
    refund_amount INTEGER,
    refund_reason TEXT,
    refunded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);

-- 결제 수단
CREATE TABLE payment_methods (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL,
    card_last4 VARCHAR(4),
    card_brand VARCHAR(20),
    bank_name VARCHAR(50),
    account_last4 VARCHAR(4),
    billing_key VARCHAR(200) UNIQUE,
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 청구지 주소
CREATE TABLE billing_addresses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_name VARCHAR(200),
    tax_id VARCHAR(20),
    address_line1 VARCHAR(200) NOT NULL,
    address_line2 VARCHAR(200),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100),
    postal_code VARCHAR(20) NOT NULL,
    country VARCHAR(2) DEFAULT 'KR',
    phone VARCHAR(20),
    email VARCHAR(255),
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 구독 사용량 추적
CREATE TABLE subscription_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id INTEGER REFERENCES user_subscriptions(id),
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    searches_count INTEGER DEFAULT 0,
    downloads_count INTEGER DEFAULT 0,
    api_calls_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- 인보이스
CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    subscription_id INTEGER REFERENCES user_subscriptions(id),
    payment_id INTEGER REFERENCES payment_history(id),
    subtotal INTEGER NOT NULL,
    tax_amount INTEGER DEFAULT 0,
    discount_amount INTEGER DEFAULT 0,
    total_amount INTEGER NOT NULL,
    billing_period_start DATE,
    billing_period_end DATE,
    due_date DATE,
    status VARCHAR(20) DEFAULT 'pending',
    pdf_path VARCHAR(500),
    issued_at TIMESTAMP DEFAULT NOW(),
    paid_at TIMESTAMP,
    sent_at TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX idx_user_subscriptions_status ON user_subscriptions(status);
CREATE INDEX idx_user_subscriptions_expires_at ON user_subscriptions(expires_at);
CREATE INDEX idx_payment_history_user_id ON payment_history(user_id);
CREATE INDEX idx_payment_history_status ON payment_history(status);
CREATE INDEX idx_payment_history_created_at ON payment_history(created_at);
CREATE INDEX idx_subscription_usage_user_date ON subscription_usage(user_id, date);
CREATE INDEX idx_invoices_user_id ON invoices(user_id);
CREATE INDEX idx_invoices_status ON invoices(status);

-- 기본 구독 플랜 데이터 입력
INSERT INTO subscription_plans (
    name, display_name, description,
    price_monthly, price_yearly,
    max_searches_per_day, max_downloads_per_month, max_bookmarks, max_alerts,
    has_ai_recommendations, has_advanced_search, has_export_excel, has_api_access,
    badge_color, badge_text, sort_order
) VALUES
('free', 'Free', '무료로 시작하세요',
 0, 0,
 10, 5, 20, 3,
 false, false, false, false,
 '#9CA3AF', NULL, 1),

('basic', 'Basic', '개인 사용자를 위한 기본 플랜',
 29900, 299000,
 50, 20, 100, 10,
 false, true, true, false,
 '#3B82F6', NULL, 2),

('professional', 'Professional', '전문가를 위한 프리미엄 기능',
 99000, 990000,
 NULL, 100, 500, 50,
 true, true, true, true,
 '#8B5CF6', '인기', 3),

('enterprise', 'Enterprise', '기업용 맞춤형 솔루션',
 299000, 2990000,
 NULL, NULL, NULL, NULL,
 true, true, true, true,
 '#F59E0B', '기업용', 4);

-- 구독 플랜 특징 테이블 (UI 표시용)
CREATE TABLE subscription_features (
    id SERIAL PRIMARY KEY,
    plan_id INTEGER NOT NULL REFERENCES subscription_plans(id) ON DELETE CASCADE,
    feature_name VARCHAR(200) NOT NULL,
    feature_value VARCHAR(100),
    feature_group VARCHAR(50),
    sort_order INTEGER DEFAULT 0
);

-- 각 플랜의 주요 기능 설명
INSERT INTO subscription_features (plan_id, feature_name, feature_value, feature_group, sort_order)
SELECT
    p.id,
    f.feature_name,
    CASE
        WHEN p.name = 'free' THEN f.free_value
        WHEN p.name = 'basic' THEN f.basic_value
        WHEN p.name = 'professional' THEN f.professional_value
        WHEN p.name = 'enterprise' THEN f.enterprise_value
    END as feature_value,
    f.feature_group,
    f.sort_order
FROM subscription_plans p
CROSS JOIN (
    VALUES
    ('일일 검색 횟수', '10회', '50회', '무제한', '무제한', '검색', 1),
    ('월간 다운로드', '5건', '20건', '100건', '무제한', '검색', 2),
    ('북마크 저장', '20개', '100개', '500개', '무제한', '저장', 3),
    ('맞춤 알림', '3개', '10개', '50개', '무제한', '알림', 4),
    ('AI 추천', '✗', '✗', '✓', '✓', '분석', 5),
    ('고급 필터링', '✗', '✓', '✓', '✓', '검색', 6),
    ('엑셀 내보내기', '✗', '✓', '✓', '✓', '내보내기', 7),
    ('API 접근', '✗', '✗', '✓', '✓', 'API', 8),
    ('이메일 지원', '✗', '✓', '✓', '✓', '지원', 9),
    ('전담 매니저', '✗', '✗', '✗', '✓', '지원', 10),
    ('팀 협업', '✗', '✗', '✗', '✓', '협업', 11),
    ('맞춤 교육', '✗', '✗', '✗', '✓', '지원', 12)
) AS f(feature_name, free_value, basic_value, professional_value, enterprise_value, feature_group, sort_order)
WHERE f.feature_name IS NOT NULL;

-- 트리거: 구독 업데이트 시 updated_at 갱신
CREATE OR REPLACE FUNCTION update_subscription_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_subscription_plans_timestamp
BEFORE UPDATE ON subscription_plans
FOR EACH ROW EXECUTE FUNCTION update_subscription_timestamp();

CREATE TRIGGER update_user_subscriptions_timestamp
BEFORE UPDATE ON user_subscriptions
FOR EACH ROW EXECUTE FUNCTION update_subscription_timestamp();

GRANT ALL ON ALL TABLES IN SCHEMA public TO blockmeta;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO blockmeta;


-- ============================================================
-- SECTION 5: Subscription Functions
-- Source: sql/create_subscription_functions.sql
-- ============================================================

-- 사용량 체크 함수
CREATE OR REPLACE FUNCTION check_subscription_limit(
    p_user_id INTEGER,
    p_limit_type VARCHAR(50)
) RETURNS JSON AS $$
DECLARE
    v_plan subscription_plans;
    v_usage subscription_usage;
    v_current_count INTEGER;
    v_limit INTEGER;
    v_is_allowed BOOLEAN;
BEGIN
    -- 현재 구독 정보 조회
    SELECT p.*
    INTO v_plan
    FROM user_subscriptions s
    JOIN subscription_plans p ON s.plan_id = p.id
    WHERE s.user_id = p_user_id
        AND s.status = 'active'
        AND s.expires_at > NOW()
    LIMIT 1;

    -- 구독이 없으면 Free 플랜 적용
    IF v_plan.id IS NULL THEN
        SELECT * INTO v_plan
        FROM subscription_plans
        WHERE name = 'free';
    END IF;

    -- 오늘 사용량 조회
    SELECT * INTO v_usage
    FROM subscription_usage
    WHERE user_id = p_user_id
        AND date = CURRENT_DATE;

    -- 사용량이 없으면 초기화
    IF v_usage.id IS NULL THEN
        INSERT INTO subscription_usage (user_id, date)
        VALUES (p_user_id, CURRENT_DATE)
        RETURNING * INTO v_usage;
    END IF;

    -- 타입별 제한 체크
    CASE p_limit_type
        WHEN 'search' THEN
            v_current_count := v_usage.searches_count;
            v_limit := v_plan.max_searches_per_day;
        WHEN 'download' THEN
            SELECT COALESCE(SUM(downloads_count), 0) INTO v_current_count
            FROM subscription_usage
            WHERE user_id = p_user_id
                AND date >= DATE_TRUNC('month', CURRENT_DATE);
            v_limit := v_plan.max_downloads_per_month;
        WHEN 'bookmark' THEN
            SELECT COUNT(*) INTO v_current_count
            FROM user_bookmarks
            WHERE user_id = p_user_id;
            v_limit := v_plan.max_bookmarks;
        WHEN 'api' THEN
            SELECT COALESCE(SUM(api_calls_count), 0) INTO v_current_count
            FROM subscription_usage
            WHERE user_id = p_user_id
                AND created_at >= NOW() - INTERVAL '1 hour';
            v_limit := v_plan.api_rate_limit;
        ELSE
            RETURN json_build_object(
                'allowed', false,
                'error', 'Invalid limit type'
            );
    END CASE;

    -- 무제한인 경우
    IF v_limit IS NULL THEN
        v_is_allowed := true;
    ELSE
        v_is_allowed := v_current_count < v_limit;
    END IF;

    RETURN json_build_object(
        'allowed', v_is_allowed,
        'current_count', v_current_count,
        'limit', v_limit,
        'plan_name', v_plan.name,
        'limit_type', p_limit_type
    );
END;
$$ LANGUAGE plpgsql;

-- 사용량 증가 함수
CREATE OR REPLACE FUNCTION increment_usage(
    p_user_id INTEGER,
    p_usage_type VARCHAR(50)
) RETURNS VOID AS $$
BEGIN
    INSERT INTO subscription_usage (user_id, date)
    VALUES (p_user_id, CURRENT_DATE)
    ON CONFLICT (user_id, date) DO UPDATE
    SET
        searches_count = CASE
            WHEN p_usage_type = 'search' THEN subscription_usage.searches_count + 1
            ELSE subscription_usage.searches_count
        END,
        downloads_count = CASE
            WHEN p_usage_type = 'download' THEN subscription_usage.downloads_count + 1
            ELSE subscription_usage.downloads_count
        END,
        api_calls_count = CASE
            WHEN p_usage_type = 'api' THEN subscription_usage.api_calls_count + 1
            ELSE subscription_usage.api_calls_count
        END;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- SECTION 6: AI Recommendation Tables
-- Source: sql/create_ai_recommendation_tables.sql
-- Note: user_bid_interactions and bid_similarities reference
--       bid_announcements which is created by the batch system.
--       Using IF NOT EXISTS and deferring FK constraints where needed.
-- ============================================================

DROP TABLE IF EXISTS user_preferences CASCADE;
DROP TABLE IF EXISTS user_bid_interactions CASCADE;
DROP TABLE IF EXISTS bid_similarities CASCADE;
DROP TABLE IF EXISTS recommendation_history CASCADE;
DROP TABLE IF EXISTS recommendation_feedback CASCADE;

-- 사용자 선호도 테이블
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preferred_categories JSONB DEFAULT '{}',
    preferred_organizations JSONB DEFAULT '[]',
    preferred_regions JSONB DEFAULT '[]',
    preferred_price_min BIGINT,
    preferred_price_max BIGINT,
    preferred_keywords JSONB DEFAULT '{}',
    excluded_keywords JSONB DEFAULT '[]',
    total_interactions INTEGER DEFAULT 0,
    total_bookmarks INTEGER DEFAULT 0,
    total_views INTEGER DEFAULT 0,
    last_calculated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id)
);

-- 사용자 입찰 상호작용 기록
-- Note: FK to bid_announcements added after that table exists via batch
CREATE TABLE user_bid_interactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bid_notice_no VARCHAR(20) NOT NULL,
    interaction_type VARCHAR(20) NOT NULL,
    interaction_score FLOAT DEFAULT 1.0,
    duration_seconds INTEGER,
    source VARCHAR(50),
    search_query TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, bid_notice_no, interaction_type, created_at)
);

-- 입찰 간 유사도 테이블 (사전 계산)
-- Note: FK to bid_announcements added after that table exists via batch
CREATE TABLE bid_similarities (
    id SERIAL PRIMARY KEY,
    bid_notice_no_1 VARCHAR(20) NOT NULL,
    bid_notice_no_2 VARCHAR(20) NOT NULL,
    title_similarity FLOAT,
    category_similarity FLOAT,
    organization_similarity FLOAT,
    price_similarity FLOAT,
    keyword_similarity FLOAT,
    overall_similarity FLOAT NOT NULL,
    calculated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(bid_notice_no_1, bid_notice_no_2),
    CHECK (bid_notice_no_1 < bid_notice_no_2)
);

-- 추천 이력
-- Note: FK to bid_announcements added after that table exists via batch
CREATE TABLE recommendation_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bid_notice_no VARCHAR(20) NOT NULL,
    recommendation_type VARCHAR(50) NOT NULL,
    recommendation_score FLOAT NOT NULL,
    recommendation_reasons JSONB,
    context VARCHAR(50),
    was_clicked BOOLEAN DEFAULT false,
    was_bookmarked BOOLEAN DEFAULT false,
    click_position INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 추천 피드백
CREATE TABLE recommendation_feedback (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recommendation_id INTEGER REFERENCES recommendation_history(id),
    feedback_type VARCHAR(20) NOT NULL,
    feedback_score INTEGER,
    feedback_text TEXT,
    feedback_reasons JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX idx_user_bid_interactions_user_id ON user_bid_interactions(user_id);
CREATE INDEX idx_user_bid_interactions_bid_notice_no ON user_bid_interactions(bid_notice_no);
CREATE INDEX idx_user_bid_interactions_created_at ON user_bid_interactions(created_at);
CREATE INDEX idx_bid_similarities_bid1 ON bid_similarities(bid_notice_no_1);
CREATE INDEX idx_bid_similarities_bid2 ON bid_similarities(bid_notice_no_2);
CREATE INDEX idx_bid_similarities_overall ON bid_similarities(overall_similarity DESC);
CREATE INDEX idx_recommendation_history_user_id ON recommendation_history(user_id);
CREATE INDEX idx_recommendation_history_created_at ON recommendation_history(created_at);
CREATE INDEX idx_recommendation_feedback_user_id ON recommendation_feedback(user_id);

-- 사용자 선호도 업데이트 함수
CREATE OR REPLACE FUNCTION update_user_preferences(
    p_user_id INTEGER
) RETURNS VOID AS $$
DECLARE
    v_category_prefs JSONB;
    v_org_prefs JSONB;
    v_keyword_prefs JSONB;
BEGIN
    -- 북마크 기반 카테고리 선호도 계산
    WITH bookmark_categories AS (
        SELECT
            t.tag_name,
            COUNT(*) as count
        FROM user_bookmarks ub
        JOIN bid_tag_relations btr ON ub.bid_id = btr.bid_notice_no
        JOIN bid_tags t ON btr.tag_id = t.tag_id
        WHERE ub.user_id = p_user_id
        GROUP BY t.tag_name
    )
    SELECT jsonb_object_agg(
        tag_name,
        ROUND(count::numeric / total_count, 2)
    ) INTO v_category_prefs
    FROM bookmark_categories, (SELECT SUM(count) as total_count FROM bookmark_categories) t;

    -- 북마크 기반 기관 선호도
    WITH bookmark_orgs AS (
        SELECT
            b.organization_name,
            COUNT(*) as count
        FROM user_bookmarks ub
        JOIN bid_announcements b ON ub.bid_id = b.bid_notice_no
        WHERE ub.user_id = p_user_id
            AND b.organization_name IS NOT NULL
        GROUP BY b.organization_name
        ORDER BY count DESC
        LIMIT 10
    )
    SELECT jsonb_agg(organization_name) INTO v_org_prefs
    FROM bookmark_orgs;

    v_keyword_prefs := '{}';

    INSERT INTO user_preferences (
        user_id,
        preferred_categories,
        preferred_organizations,
        preferred_keywords,
        last_calculated_at
    ) VALUES (
        p_user_id,
        COALESCE(v_category_prefs, '{}'),
        COALESCE(v_org_prefs, '[]'),
        v_keyword_prefs,
        NOW()
    )
    ON CONFLICT (user_id) DO UPDATE SET
        preferred_categories = COALESCE(v_category_prefs, '{}'),
        preferred_organizations = COALESCE(v_org_prefs, '[]'),
        preferred_keywords = v_keyword_prefs,
        last_calculated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- 추천 점수 계산 함수
CREATE OR REPLACE FUNCTION calculate_recommendation_score(
    p_user_id INTEGER,
    p_bid_notice_no VARCHAR(20)
) RETURNS FLOAT AS $$
DECLARE
    v_score FLOAT := 0;
    v_preferences RECORD;
    v_bid RECORD;
    v_category_match FLOAT := 0;
    v_org_match FLOAT := 0;
    v_similar_bookmarks INTEGER := 0;
BEGIN
    SELECT * INTO v_preferences
    FROM user_preferences
    WHERE user_id = p_user_id;

    IF v_preferences IS NULL THEN
        RETURN 50;
    END IF;

    SELECT * INTO v_bid
    FROM bid_announcements
    WHERE bid_notice_no = p_bid_notice_no;

    IF v_bid IS NULL THEN
        RETURN 0;
    END IF;

    IF v_preferences.preferred_categories IS NOT NULL THEN
        SELECT COALESCE(SUM(
            (v_preferences.preferred_categories->>(t.tag_name))::float
        ), 0) * 30 INTO v_category_match
        FROM bid_tag_relations btr
        JOIN bid_tags t ON btr.tag_id = t.tag_id
        WHERE btr.bid_notice_no = p_bid_notice_no;

        v_score := v_score + LEAST(v_category_match, 30);
    END IF;

    IF v_preferences.preferred_organizations ? v_bid.organization_name THEN
        v_score := v_score + 20;
    END IF;

    SELECT COUNT(*) INTO v_similar_bookmarks
    FROM bid_similarities bs
    JOIN user_bookmarks ub ON (
        ub.bid_id = bs.bid_notice_no_1 OR
        ub.bid_id = bs.bid_notice_no_2
    )
    WHERE ub.user_id = p_user_id
        AND (bs.bid_notice_no_1 = p_bid_notice_no OR
             bs.bid_notice_no_2 = p_bid_notice_no)
        AND bs.overall_similarity > 0.7;

    v_score := v_score + LEAST(v_similar_bookmarks * 10, 30);

    IF v_bid.created_at > NOW() - INTERVAL '7 days' THEN
        v_score := v_score + 10;
    ELSIF v_bid.created_at > NOW() - INTERVAL '14 days' THEN
        v_score := v_score + 5;
    END IF;

    IF v_bid.bid_end_date BETWEEN NOW() AND NOW() + INTERVAL '7 days' THEN
        v_score := v_score + 10;
    END IF;

    RETURN LEAST(v_score, 100);
END;
$$ LANGUAGE plpgsql;

-- 협업 필터링 추천 함수
CREATE OR REPLACE FUNCTION get_collaborative_recommendations(
    p_user_id INTEGER,
    p_limit INTEGER DEFAULT 10
) RETURNS TABLE (
    bid_notice_no VARCHAR(20),
    score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH user_bookmarks_set AS (
        SELECT bid_id
        FROM user_bookmarks
        WHERE user_id = p_user_id
    ),
    similar_users AS (
        SELECT
            ub2.user_id,
            COUNT(*) as common_bookmarks
        FROM user_bookmarks ub1
        JOIN user_bookmarks ub2 ON ub1.bid_id = ub2.bid_id
        WHERE ub1.user_id = p_user_id
            AND ub2.user_id != p_user_id
        GROUP BY ub2.user_id
        HAVING COUNT(*) >= 2
        ORDER BY common_bookmarks DESC
        LIMIT 20
    )
    SELECT
        ub.bid_id,
        COUNT(*)::float / (SELECT MAX(common_bookmarks) FROM similar_users) * 100 as rec_score
    FROM user_bookmarks ub
    JOIN similar_users su ON ub.user_id = su.user_id
    WHERE ub.bid_id NOT IN (SELECT bid_id FROM user_bookmarks_set)
        AND EXISTS (
            SELECT 1 FROM bid_announcements ba
            WHERE ba.bid_notice_no = ub.bid_id
                AND ba.bid_end_date > NOW()
        )
    GROUP BY ub.bid_id
    ORDER BY rec_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 트리거: 상호작용 시 선호도 업데이트
CREATE OR REPLACE FUNCTION trigger_update_preferences()
RETURNS TRIGGER AS $$
BEGIN
    IF (SELECT COUNT(*) FROM user_bid_interactions
        WHERE user_id = NEW.user_id) % 10 = 0 THEN
        PERFORM update_user_preferences(NEW.user_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_preferences_on_interaction
AFTER INSERT ON user_bid_interactions
FOR EACH ROW EXECUTE FUNCTION trigger_update_preferences();

GRANT ALL ON ALL TABLES IN SCHEMA public TO blockmeta;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO blockmeta;


-- ============================================================
-- SECTION 7: Admin Schema
-- Source: sql/admin_schema.sql
-- ============================================================

-- 1. 배치 실행 로그 테이블
CREATE TABLE IF NOT EXISTS batch_execution_logs (
    id SERIAL PRIMARY KEY,
    batch_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    total_items INTEGER DEFAULT 0,
    success_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    skipped_items INTEGER DEFAULT 0,
    error_message TEXT,
    error_count INTEGER DEFAULT 0,
    triggered_by VARCHAR(50) DEFAULT 'cron',
    triggered_by_user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_batch_execution_batch_type ON batch_execution_logs(batch_type);
CREATE INDEX idx_batch_execution_status ON batch_execution_logs(status);
CREATE INDEX idx_batch_execution_start_time ON batch_execution_logs(start_time DESC);
CREATE INDEX idx_batch_execution_created_at ON batch_execution_logs(created_at DESC);

COMMENT ON TABLE batch_execution_logs IS '배치 프로그램 실행 이력 및 통계';
COMMENT ON COLUMN batch_execution_logs.batch_type IS '배치 타입: collector, downloader, processor, notification';
COMMENT ON COLUMN batch_execution_logs.status IS '실행 상태: running, success, failed, cancelled';
COMMENT ON COLUMN batch_execution_logs.triggered_by IS '실행 트리거: cron, manual, api';

-- 2. 배치 처리 상세 로그 테이블
CREATE TABLE IF NOT EXISTS batch_detail_logs (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER NOT NULL REFERENCES batch_execution_logs(id) ON DELETE CASCADE,
    log_level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    context JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_batch_detail_execution_id ON batch_detail_logs(execution_id);
CREATE INDEX idx_batch_detail_log_level ON batch_detail_logs(log_level);
CREATE INDEX idx_batch_detail_created_at ON batch_detail_logs(created_at DESC);
CREATE INDEX idx_batch_detail_context ON batch_detail_logs USING GIN(context);

COMMENT ON TABLE batch_detail_logs IS '배치 실행 중 발생한 상세 로그';

-- 3. 시스템 메트릭 테이블
CREATE TABLE IF NOT EXISTS system_metrics (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(20),
    metadata JSONB,
    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_system_metrics_type ON system_metrics(metric_type);
CREATE INDEX idx_system_metrics_recorded_at ON system_metrics(recorded_at DESC);
CREATE INDEX idx_system_metrics_type_time ON system_metrics(metric_type, recorded_at DESC);

COMMENT ON TABLE system_metrics IS '시스템 리소스 및 성능 메트릭';

-- 4. 관리자 활동 로그 테이블
CREATE TABLE IF NOT EXISTS admin_activity_logs (
    id SERIAL PRIMARY KEY,
    admin_user_id INTEGER NOT NULL REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50),
    target_id INTEGER,
    details JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    result VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_admin_activity_admin_user_id ON admin_activity_logs(admin_user_id);
CREATE INDEX idx_admin_activity_action ON admin_activity_logs(action);
CREATE INDEX idx_admin_activity_created_at ON admin_activity_logs(created_at DESC);
CREATE INDEX idx_admin_activity_target ON admin_activity_logs(target_type, target_id);

COMMENT ON TABLE admin_activity_logs IS '관리자 활동 감사 로그';

-- 5. API 성능 로그 테이블
CREATE TABLE IF NOT EXISTS api_performance_logs (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    response_time_ms INTEGER NOT NULL,
    status_code INTEGER NOT NULL,
    user_id INTEGER REFERENCES users(id),
    ip_address VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_api_perf_endpoint ON api_performance_logs(endpoint);
CREATE INDEX idx_api_perf_created_at ON api_performance_logs(created_at DESC);
CREATE INDEX idx_api_perf_endpoint_time ON api_performance_logs(endpoint, created_at DESC);
CREATE INDEX idx_api_perf_status_code ON api_performance_logs(status_code);

COMMENT ON TABLE api_performance_logs IS 'API 엔드포인트 성능 추적';

-- 6. 알림 발송 로그 테이블
CREATE TABLE IF NOT EXISTS notification_send_logs (
    id SERIAL PRIMARY KEY,
    notification_type VARCHAR(50) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    email_to VARCHAR(255) NOT NULL,
    email_subject VARCHAR(500),
    status VARCHAR(20) NOT NULL,
    send_attempts INTEGER DEFAULT 0,
    sent_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notif_send_user_id ON notification_send_logs(user_id);
CREATE INDEX idx_notif_send_status ON notification_send_logs(status);
CREATE INDEX idx_notif_send_created_at ON notification_send_logs(created_at DESC);
CREATE INDEX idx_notif_send_type ON notification_send_logs(notification_type);

COMMENT ON TABLE notification_send_logs IS '이메일 알림 발송 로그';

-- 7. 시스템 설정 테이블
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    setting_type VARCHAR(20) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    changed_by_user_id INTEGER REFERENCES users(id),
    changed_at TIMESTAMP,
    previous_value TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_system_settings_key ON system_settings(setting_key);
CREATE INDEX idx_system_settings_category ON system_settings(category);

COMMENT ON TABLE system_settings IS '시스템 설정 관리';

-- 8. 뷰 (View) 생성

-- 8.1 배치 실행 통계 뷰
CREATE OR REPLACE VIEW v_batch_execution_stats AS
SELECT
    batch_type,
    DATE(start_time) as execution_date,
    COUNT(*) as total_executions,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
    AVG(duration_seconds) as avg_duration_seconds,
    MAX(duration_seconds) as max_duration_seconds,
    MIN(duration_seconds) as min_duration_seconds,
    SUM(total_items) as total_items_processed,
    SUM(success_items) as total_success_items,
    SUM(failed_items) as total_failed_items
FROM batch_execution_logs
WHERE status IN ('success', 'failed')
GROUP BY batch_type, DATE(start_time);

COMMENT ON VIEW v_batch_execution_stats IS '배치 실행 통계 (일별, 배치 타입별)';

-- 8.2 시스템 메트릭 최근 1시간 평균 뷰
CREATE OR REPLACE VIEW v_system_metrics_recent AS
SELECT
    metric_type,
    AVG(metric_value) as avg_value,
    MAX(metric_value) as max_value,
    MIN(metric_value) as min_value,
    COUNT(*) as sample_count,
    MAX(recorded_at) as last_recorded_at
FROM system_metrics
WHERE recorded_at >= NOW() - INTERVAL '1 hour'
GROUP BY metric_type;

COMMENT ON VIEW v_system_metrics_recent IS '시스템 메트릭 최근 1시간 통계';

-- 8.3 관리자 활동 요약 뷰
CREATE OR REPLACE VIEW v_admin_activity_summary AS
SELECT
    a.admin_user_id,
    u.username as admin_username,
    u.email as admin_email,
    COUNT(*) as total_activities,
    COUNT(CASE WHEN a.result = 'success' THEN 1 END) as success_count,
    COUNT(CASE WHEN a.result = 'failed' THEN 1 END) as failed_count,
    MAX(a.created_at) as last_activity_at
FROM admin_activity_logs a
LEFT JOIN users u ON a.admin_user_id = u.id
GROUP BY a.admin_user_id, u.username, u.email;

COMMENT ON VIEW v_admin_activity_summary IS '관리자별 활동 요약';

-- 9. 함수 (Functions)

-- 9.1 배치 실행 시작 함수
CREATE OR REPLACE FUNCTION fn_batch_start(
    p_batch_type VARCHAR,
    p_triggered_by VARCHAR DEFAULT 'cron',
    p_triggered_by_user_id INTEGER DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    v_execution_id INTEGER;
BEGIN
    INSERT INTO batch_execution_logs (
        batch_type,
        status,
        start_time,
        triggered_by,
        triggered_by_user_id
    ) VALUES (
        p_batch_type,
        'running',
        NOW(),
        p_triggered_by,
        p_triggered_by_user_id
    ) RETURNING id INTO v_execution_id;

    RETURN v_execution_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_batch_start IS '배치 실행 시작 로그 생성';

-- 9.2 배치 실행 완료 함수
CREATE OR REPLACE FUNCTION fn_batch_finish(
    p_execution_id INTEGER,
    p_status VARCHAR,
    p_total_items INTEGER DEFAULT 0,
    p_success_items INTEGER DEFAULT 0,
    p_failed_items INTEGER DEFAULT 0,
    p_error_message TEXT DEFAULT NULL
) RETURNS VOID AS $$
DECLARE
    v_start_time TIMESTAMP;
BEGIN
    SELECT start_time INTO v_start_time
    FROM batch_execution_logs
    WHERE id = p_execution_id;

    UPDATE batch_execution_logs SET
        status = p_status,
        end_time = NOW(),
        duration_seconds = EXTRACT(EPOCH FROM (NOW() - v_start_time)),
        total_items = p_total_items,
        success_items = p_success_items,
        failed_items = p_failed_items,
        error_message = p_error_message,
        updated_at = NOW()
    WHERE id = p_execution_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_batch_finish IS '배치 실행 완료 로그 업데이트';

-- 9.3 배치 상세 로그 추가 함수
CREATE OR REPLACE FUNCTION fn_batch_log(
    p_execution_id INTEGER,
    p_log_level VARCHAR,
    p_message TEXT,
    p_context JSONB DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO batch_detail_logs (
        execution_id,
        log_level,
        message,
        context
    ) VALUES (
        p_execution_id,
        p_log_level,
        p_message,
        p_context
    );

    IF p_log_level = 'ERROR' THEN
        UPDATE batch_execution_logs
        SET error_count = error_count + 1
        WHERE id = p_execution_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_batch_log IS '배치 상세 로그 추가 (에러 카운트 자동 증가)';

-- 9.4 시스템 메트릭 기록 함수
CREATE OR REPLACE FUNCTION fn_record_metric(
    p_metric_type VARCHAR,
    p_metric_value FLOAT,
    p_metric_unit VARCHAR DEFAULT 'percent',
    p_metadata JSONB DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO system_metrics (
        metric_type,
        metric_value,
        metric_unit,
        metadata
    ) VALUES (
        p_metric_type,
        p_metric_value,
        p_metric_unit,
        p_metadata
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_record_metric IS '시스템 메트릭 기록';

-- 10. 트리거 (Triggers)

-- 10.1 batch_execution_logs updated_at 자동 업데이트
CREATE OR REPLACE FUNCTION trg_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_batch_execution_updated_at
BEFORE UPDATE ON batch_execution_logs
FOR EACH ROW
EXECUTE FUNCTION trg_update_timestamp();

-- 10.2 system_settings updated_at 자동 업데이트
CREATE TRIGGER trg_system_settings_updated_at
BEFORE UPDATE ON system_settings
FOR EACH ROW
EXECUTE FUNCTION trg_update_timestamp();

-- 11. 초기 데이터 삽입

INSERT INTO system_settings (setting_key, setting_value, setting_type, description, category) VALUES
('batch_cron_collector', '0 7,12,18 * * *', 'string', 'Collector 배치 실행 크론 표현식', 'batch'),
('batch_cron_downloader', '30 7,12,18 * * *', 'string', 'Downloader 배치 실행 크론 표현식', 'batch'),
('batch_cron_processor', '0 8,13,19 * * *', 'string', 'Processor 배치 실행 크론 표현식', 'batch'),
('batch_cron_notification', '0 9,14,20 * * *', 'string', 'Notification 배치 실행 크론 표현식', 'batch'),
('notification_daily_digest_time', '08:00', 'string', '일일 다이제스트 발송 시간', 'notification'),
('api_rate_limit_per_minute', '100', 'integer', '분당 API 요청 제한', 'api'),
('log_level', 'INFO', 'string', '로그 레벨 (DEBUG/INFO/WARNING/ERROR)', 'system'),
('metric_collection_interval_seconds', '60', 'integer', '메트릭 수집 주기 (초)', 'system'),
('alert_cpu_threshold', '90', 'integer', 'CPU 사용률 알림 임계값 (%)', 'system'),
('alert_memory_threshold', '85', 'integer', '메모리 사용률 알림 임계값 (%)', 'system'),
('alert_disk_threshold', '80', 'integer', '디스크 사용률 알림 임계값 (%)', 'system')
ON CONFLICT (setting_key) DO NOTHING;

-- 12. 데이터 정리 함수

CREATE OR REPLACE FUNCTION fn_cleanup_old_metrics()
RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM system_metrics
    WHERE recorded_at < NOW() - INTERVAL '90 days';

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_cleanup_old_metrics IS '90일 이전 시스템 메트릭 삭제';

CREATE OR REPLACE FUNCTION fn_cleanup_old_batch_detail_logs()
RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM batch_detail_logs
    WHERE created_at < NOW() - INTERVAL '180 days';

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_cleanup_old_batch_detail_logs IS '180일 이전 배치 상세 로그 삭제';


-- ============================================================
-- SECTION 8: Ontology Tables
-- Source: sql/create_ontology_tables.sql
-- ============================================================

-- 1. 온톨로지 개념 계층 테이블
CREATE TABLE IF NOT EXISTS ontology_concepts (
    id SERIAL PRIMARY KEY,
    concept_name VARCHAR(100) NOT NULL,
    concept_name_en VARCHAR(100),
    parent_id INTEGER REFERENCES ontology_concepts(id) ON DELETE SET NULL,
    level INTEGER DEFAULT 0,
    description TEXT,
    keywords TEXT[] DEFAULT '{}',
    synonyms TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ontology_concepts_parent_id
    ON ontology_concepts(parent_id);

CREATE INDEX IF NOT EXISTS idx_ontology_concepts_concept_name
    ON ontology_concepts(concept_name);

CREATE INDEX IF NOT EXISTS idx_ontology_concepts_level
    ON ontology_concepts(level);

CREATE INDEX IF NOT EXISTS idx_ontology_concepts_keywords
    ON ontology_concepts USING GIN(keywords);

CREATE INDEX IF NOT EXISTS idx_ontology_concepts_synonyms
    ON ontology_concepts USING GIN(synonyms);

-- 2. 개념 간 관계 테이블
CREATE TABLE IF NOT EXISTS ontology_relations (
    id SERIAL PRIMARY KEY,
    source_concept_id INTEGER NOT NULL REFERENCES ontology_concepts(id) ON DELETE CASCADE,
    target_concept_id INTEGER NOT NULL REFERENCES ontology_concepts(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL,
    weight FLOAT DEFAULT 1.0,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_concept_id, target_concept_id, relation_type)
);

CREATE INDEX IF NOT EXISTS idx_ontology_relations_source_concept_id
    ON ontology_relations(source_concept_id);

CREATE INDEX IF NOT EXISTS idx_ontology_relations_target_concept_id
    ON ontology_relations(target_concept_id);

CREATE INDEX IF NOT EXISTS idx_ontology_relations_relation_type
    ON ontology_relations(relation_type);

-- 3. 입찰공고-온톨로지 매핑 테이블
CREATE TABLE IF NOT EXISTS bid_ontology_mappings (
    id SERIAL PRIMARY KEY,
    bid_notice_no VARCHAR(100) NOT NULL,
    concept_id INTEGER NOT NULL REFERENCES ontology_concepts(id) ON DELETE CASCADE,
    confidence FLOAT DEFAULT 0.0,
    source VARCHAR(50) DEFAULT 'auto',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(bid_notice_no, concept_id)
);

CREATE INDEX IF NOT EXISTS idx_bid_ontology_mappings_bid_notice_no
    ON bid_ontology_mappings(bid_notice_no);

CREATE INDEX IF NOT EXISTS idx_bid_ontology_mappings_concept_id
    ON bid_ontology_mappings(concept_id);

CREATE INDEX IF NOT EXISTS idx_bid_ontology_mappings_confidence
    ON bid_ontology_mappings(confidence);

-- 헬퍼 함수

CREATE OR REPLACE FUNCTION fn_get_descendant_concepts(root_id INTEGER)
RETURNS TABLE(concept_id INTEGER, concept_name VARCHAR, level INTEGER, path TEXT) AS $$
WITH RECURSIVE concept_tree AS (
    SELECT id, concept_name, level, concept_name::TEXT as path
    FROM ontology_concepts
    WHERE id = root_id AND is_active = true

    UNION ALL

    SELECT oc.id, oc.concept_name, oc.level, ct.path || ' > ' || oc.concept_name
    FROM ontology_concepts oc
    JOIN concept_tree ct ON oc.parent_id = ct.id
    WHERE oc.is_active = true
)
SELECT id, concept_name, level, path FROM concept_tree;
$$ LANGUAGE SQL STABLE;

CREATE OR REPLACE FUNCTION fn_get_expanded_keywords(root_id INTEGER)
RETURNS TEXT[] AS $$
SELECT ARRAY(
    SELECT DISTINCT unnest(oc.keywords || oc.synonyms)
    FROM ontology_concepts oc
    WHERE oc.id IN (
        SELECT concept_id FROM fn_get_descendant_concepts(root_id)
    )
    AND oc.is_active = true
);
$$ LANGUAGE SQL STABLE;


-- ============================================================
-- SECTION 9: Ontology Seed Data
-- Source: sql/seed_ontology_data.sql
-- ============================================================

BEGIN;

DELETE FROM ontology_relations;
DELETE FROM bid_ontology_mappings;
DELETE FROM ontology_concepts;

ALTER SEQUENCE ontology_concepts_id_seq RESTART WITH 1;
ALTER SEQUENCE ontology_relations_id_seq RESTART WITH 1;

-- LEVEL 0: ROOT
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES (
    '입찰공고', 'bid_announcement', NULL, 0,
    '공공입찰 도메인 최상위 개념. 모든 공사/용역/물품 입찰공고의 루트 노드.',
    ARRAY['입찰', '공고', '조달', '발주', '나라장터'],
    ARRAY['입찰공고', '조달공고', '발주공고', '공공입찰'],
    0
);

-- LEVEL 1: 대분류
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES
(
    '공사', 'construction',
    (SELECT id FROM ontology_concepts WHERE concept_name = '입찰공고'),
    1,
    '건설, 토목, 전기, 기계 등 물리적 시설물의 시공 및 설치를 포함하는 대분류.',
    ARRAY['공사', '시공', '건설', '설치', '축조'],
    ARRAY['건설공사', '시공공사', '설치공사'],
    1
),
(
    '용역', 'service',
    (SELECT id FROM ontology_concepts WHERE concept_name = '입찰공고'),
    1,
    'IT 개발, 컨설팅, 연구, 설계, 감리 등 전문 서비스 제공을 포함하는 대분류.',
    ARRAY['용역', '서비스', '컨설팅', '연구'],
    ARRAY['용역사업', '서비스사업', '전문용역'],
    2
),
(
    '물품', 'goods',
    (SELECT id FROM ontology_concepts WHERE concept_name = '입찰공고'),
    1,
    'IT 장비, 사무용품, 의료기기, 차량 등 유형 재화의 구매/납품을 포함하는 대분류.',
    ARRAY['물품', '구매', '납품', '조달', '공급'],
    ARRAY['물품구매', '물품조달', '물자'],
    3
);

-- LEVEL 2: 중분류 - 공사 하위
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES
(
    '건축공사', 'building_construction',
    (SELECT id FROM ontology_concepts WHERE concept_name = '공사'),
    2,
    '건물의 신축, 증축, 리모델링, 실내건축, 철거 등을 포함하는 건축 분야 공사.',
    ARRAY['건축', '건물', '빌딩', '아파트', '주택'],
    ARRAY['건축시공', '건물공사', '건물시공'],
    1
),
(
    '토목공사', 'civil_engineering',
    (SELECT id FROM ontology_concepts WHERE concept_name = '공사'),
    2,
    '도로, 교량, 터널, 하천, 상하수도 등 사회기반시설 건설을 포함하는 토목 분야 공사.',
    ARRAY['토목', '토공', '지반'],
    ARRAY['토목시공', '토목건설', '기반시설공사'],
    2
),
(
    '조경공사', 'landscaping',
    (SELECT id FROM ontology_concepts WHERE concept_name = '공사'),
    2,
    '공원, 녹지, 식재, 정원 조성 등 조경 분야 공사.',
    ARRAY['조경', '녹지', '공원', '식재', '잔디', '수목', '정원'],
    ARRAY['조경시공', '녹화공사', '공원조성'],
    3
),
(
    '전기공사', 'electrical_construction',
    (SELECT id FROM ontology_concepts WHERE concept_name = '공사'),
    2,
    '전력설비, 조명, 태양광 등 전기 분야 공사.',
    ARRAY['전기', '전력', '배전', '수전', '변전', '조명', '발전'],
    ARRAY['전기시공', '전기설비공사', '전력공사'],
    4
),
(
    '통신공사', 'telecommunications',
    (SELECT id FROM ontology_concepts WHERE concept_name = '공사'),
    2,
    '정보통신, 네트워크, 광케이블, CCTV 등 통신 분야 공사.',
    ARRAY['통신', '정보통신', 'ICT', '네트워크', '광케이블', 'CCTV'],
    ARRAY['통신시공', '정보통신공사', 'ICT공사'],
    5
),
(
    '기계설비공사', 'mechanical_construction',
    (SELECT id FROM ontology_concepts WHERE concept_name = '공사'),
    2,
    '냉난방, 소방, 승강기, 배관 등 기계설비 분야 공사.',
    ARRAY['기계', '설비', '냉난방', 'HVAC', '배관', '펌프', '공조'],
    ARRAY['기계시공', '설비공사', '기계설비시공'],
    6
),
(
    '포장공사', 'paving_construction',
    (SELECT id FROM ontology_concepts WHERE concept_name = '공사'),
    2,
    '아스콘, 콘크리트 포장 등 도로/보도 포장 분야 공사.',
    ARRAY['포장', '아스콘', '콘크리트포장', '보차도'],
    ARRAY['포장시공', '도로포장공사', '노면포장'],
    7
);

-- LEVEL 2: 중분류 - 용역 하위
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES
(
    'IT/SW개발', 'it_sw_development',
    (SELECT id FROM ontology_concepts WHERE concept_name = '용역'),
    2,
    '소프트웨어 개발, 시스템 구축, 웹/앱 개발, AI/빅데이터, 클라우드 인프라 등 IT 분야 용역.',
    ARRAY['소프트웨어', 'SW', 'IT', '개발', '프로그램', '시스템'],
    ARRAY['IT개발', 'SW개발', '소프트웨어개발', '정보시스템개발', 'SI'],
    1
),
(
    '컨설팅', 'consulting',
    (SELECT id FROM ontology_concepts WHERE concept_name = '용역'),
    2,
    '경영, 기술, 정책 등 전문 분야 자문 및 진단 용역.',
    ARRAY['컨설팅', '자문', '진단', '평가', '분석'],
    ARRAY['자문용역', '진단용역', '평가용역', '전문상담'],
    2
),
(
    '연구용역', 'research',
    (SELECT id FROM ontology_concepts WHERE concept_name = '용역'),
    2,
    '학술 연구, 정책 연구, 기초 조사 등 연구 분야 용역.',
    ARRAY['연구', '조사', '분석', '학술', '기획'],
    ARRAY['연구사업', '학술용역', '조사연구', '기초연구'],
    3
),
(
    '유지보수', 'maintenance',
    (SELECT id FROM ontology_concepts WHERE concept_name = '용역'),
    2,
    '시설, 소프트웨어, 장비의 유지관리, 운영, 점검 등 유지보수 분야 용역.',
    ARRAY['유지보수', '유지관리', '운영', '점검', '보전'],
    ARRAY['유지보수용역', '운영관리', '관리용역'],
    4
),
(
    '설계용역', 'design_service',
    (SELECT id FROM ontology_concepts WHERE concept_name = '용역'),
    2,
    '건축설계, 토목설계, 기본설계, 실시설계, 타당성조사 등 설계 분야 용역.',
    ARRAY['설계', '기본설계', '실시설계', '타당성'],
    ARRAY['설계사업', '설계업무', '기본계획'],
    5
),
(
    '감리용역', 'supervision',
    (SELECT id FROM ontology_concepts WHERE concept_name = '용역'),
    2,
    '시공감리, 책임감리, 건설사업관리 등 감리/감독 분야 용역.',
    ARRAY['감리', '감독', '시공감리', '책임감리'],
    ARRAY['감리업무', '건설사업관리', 'CM', '감독업무'],
    6
),
(
    '교육/훈련', 'education_training',
    (SELECT id FROM ontology_concepts WHERE concept_name = '용역'),
    2,
    '직원 교육, 기술 훈련, 연수, 워크숍, 세미나 등 교육 분야 용역.',
    ARRAY['교육', '훈련', '연수', '워크샵', '세미나'],
    ARRAY['교육사업', '훈련용역', '연수사업', '역량강화'],
    7
);

-- LEVEL 2: 중분류 - 물품 하위
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES
(
    'IT장비', 'it_equipment',
    (SELECT id FROM ontology_concepts WHERE concept_name = '물품'),
    2,
    '컴퓨터, 서버, 네트워크 장비, 모니터, 프린터 등 IT 분야 물품.',
    ARRAY['컴퓨터', 'PC', '서버', '네트워크장비', '모니터', '프린터'],
    ARRAY['IT장비구매', '전산장비', '정보화장비'],
    1
),
(
    '사무용품', 'office_supplies',
    (SELECT id FROM ontology_concepts WHERE concept_name = '물품'),
    2,
    '가구, 비품, 문구, 소모품 등 사무용 물품.',
    ARRAY['사무', '가구', '비품', '문구', '소모품'],
    ARRAY['사무용품구매', '사무가구', '사무비품'],
    2
),
(
    '의료기기', 'medical_equipment',
    (SELECT id FROM ontology_concepts WHERE concept_name = '물품'),
    2,
    '의료장비, 의약품, 진단기기, 치료기기 등 의료 분야 물품.',
    ARRAY['의료', '의약', '의료기기', '진단', '치료'],
    ARRAY['의료장비구매', '의약품조달', '의료물품'],
    3
),
(
    '차량/운송', 'vehicles_transport',
    (SELECT id FROM ontology_concepts WHERE concept_name = '물품'),
    2,
    '차량, 트럭, 버스, 특수차량 등 운송 관련 물품.',
    ARRAY['차량', '자동차', '트럭', '버스', '운송'],
    ARRAY['차량구매', '차량조달', '운송장비'],
    4
),
(
    '식품/급식', 'food_catering',
    (SELECT id FROM ontology_concepts WHERE concept_name = '물품'),
    2,
    '식품, 식자재, 급식 등 식품 관련 물품.',
    ARRAY['식품', '급식', '식자재', '식재료', '음식'],
    ARRAY['식품구매', '급식재료', '식자재조달'],
    5
),
(
    '보안장비', 'security_equipment',
    (SELECT id FROM ontology_concepts WHERE concept_name = '물품'),
    2,
    'CCTV, 출입통제, 방범, 경비 장비 등 보안 관련 물품.',
    ARRAY['보안', 'CCTV', '출입통제', '방범', '경비'],
    ARRAY['보안장비구매', '방범장비', '보안시스템물품'],
    6
);

-- LEVEL 3: 소분류 - 건축공사 하위
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES
(
    '신축공사', 'new_building',
    (SELECT id FROM ontology_concepts WHERE concept_name = '건축공사'),
    3,
    '새 건물의 신설 공사.',
    ARRAY['신축', '신설', '새건물'],
    ARRAY['건물신축', '신축시공', '건물신설'],
    1
),
(
    '증축공사', 'building_extension',
    (SELECT id FROM ontology_concepts WHERE concept_name = '건축공사'),
    3,
    '기존 건물의 확장 또는 증설 공사.',
    ARRAY['증축', '확장', '증설'],
    ARRAY['건물증축', '시설확장', '증축시공'],
    2
),
(
    '리모델링', 'remodeling',
    (SELECT id FROM ontology_concepts WHERE concept_name = '건축공사'),
    3,
    '기존 건물의 개보수, 수선, 개선 공사.',
    ARRAY['리모델링', '개보수', '보수', '수선', '개선'],
    ARRAY['건물리모델링', '시설개보수', '건물보수', '수리공사'],
    3
),
(
    '실내건축', 'interior_construction',
    (SELECT id FROM ontology_concepts WHERE concept_name = '건축공사'),
    3,
    '실내 인테리어, 내장, 내부 마감 공사.',
    ARRAY['실내', '인테리어', '내장', '내부'],
    ARRAY['실내건축공사', '인테리어공사', '내장공사', '실내마감'],
    4
),
(
    '철거공사', 'demolition',
    (SELECT id FROM ontology_concepts WHERE concept_name = '건축공사'),
    3,
    '기존 건물의 철거, 해체, 멸실 공사.',
    ARRAY['철거', '해체', '멸실'],
    ARRAY['건물철거', '해체공사', '구조물철거'],
    5
);

-- LEVEL 3: 소분류 - 토목공사 하위
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES
(
    '도로공사', 'road_construction',
    (SELECT id FROM ontology_concepts WHERE concept_name = '토목공사'),
    3,
    '도로 신설, 확장, 포장, 노면 보수 등 도로 관련 공사.',
    ARRAY['도로', '포장', '아스팔트', '노면', '차도', '보도'],
    ARRAY['도로건설', '도로시공', '노면공사', '도로개설'],
    1
),
(
    '교량공사', 'bridge_construction',
    (SELECT id FROM ontology_concepts WHERE concept_name = '토목공사'),
    3,
    '교량, 육교, 고가도로 등 교량 관련 공사.',
    ARRAY['교량', '다리', '육교', '고가'],
    ARRAY['교량건설', '교량시공', '다리공사', '고가도로공사'],
    2
),
(
    '터널공사', 'tunnel_construction',
    (SELECT id FROM ontology_concepts WHERE concept_name = '토목공사'),
    3,
    '터널, 지하도, 갱도 등 지하 구조물 공사.',
    ARRAY['터널', '지하도', '갱도'],
    ARRAY['터널건설', '터널시공', '지하도공사', '굴착공사'],
    3
),
(
    '하천공사', 'river_construction',
    (SELECT id FROM ontology_concepts WHERE concept_name = '토목공사'),
    3,
    '하천 정비, 배수, 수로, 제방, 호안 등 하천 관련 공사.',
    ARRAY['하천', '하수', '배수', '수로', '제방', '호안'],
    ARRAY['하천정비', '하천시공', '배수공사', '제방공사'],
    4
),
(
    '상수도공사', 'water_supply',
    (SELECT id FROM ontology_concepts WHERE concept_name = '토목공사'),
    3,
    '상수도, 급수, 취수, 정수, 배수지 등 상수 관련 공사.',
    ARRAY['상수도', '급수', '취수', '정수', '배수지'],
    ARRAY['상수도시공', '급수공사', '정수시설공사'],
    5
),
(
    '하수도공사', 'sewerage',
    (SELECT id FROM ontology_concepts WHERE concept_name = '토목공사'),
    3,
    '하수도, 오수, 우수, 맨홀, 관로 등 하수 관련 공사.',
    ARRAY['하수도', '오수', '우수', '맨홀', '관로'],
    ARRAY['하수도시공', '하수관로공사', '오수처리공사'],
    6
);

-- LEVEL 3: 소분류 - 전기공사 하위
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES
(
    '전력설비', 'power_facilities',
    (SELECT id FROM ontology_concepts WHERE concept_name = '전기공사'),
    3,
    '고압/저압 전력설비, 변압기, 차단기 등 전력 인프라 공사.',
    ARRAY['전력', '고압', '저압', '변압기', '차단기'],
    ARRAY['전력설비공사', '수변전설비', '전력인프라'],
    1
),
(
    '조명공사', 'lighting',
    (SELECT id FROM ontology_concepts WHERE concept_name = '전기공사'),
    3,
    '가로등, LED 조명, 등기구 설치 등 조명 관련 공사.',
    ARRAY['조명', '가로등', 'LED', '등기구'],
    ARRAY['조명설비공사', 'LED공사', '가로등공사', '조명시공'],
    2
),
(
    '태양광', 'solar_power',
    (SELECT id FROM ontology_concepts WHERE concept_name = '전기공사'),
    3,
    '태양광, 태양열, 신재생에너지 설비 공사.',
    ARRAY['태양광', '태양열', '신재생', '솔라'],
    ARRAY['태양광발전', '태양광설비', '신재생에너지공사', '솔라패널'],
    3
);

-- LEVEL 3: 소분류 - 기계설비공사 하위
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES
(
    '냉난방설비', 'hvac',
    (SELECT id FROM ontology_concepts WHERE concept_name = '기계설비공사'),
    3,
    '냉방, 난방, 보일러, 에어컨, 히트펌프 등 냉난방 설비 공사.',
    ARRAY['냉방', '난방', '보일러', '에어컨', '히트펌프'],
    ARRAY['냉난방공사', 'HVAC공사', '공조설비', '냉난방시공'],
    1
),
(
    '소방설비', 'fire_protection',
    (SELECT id FROM ontology_concepts WHERE concept_name = '기계설비공사'),
    3,
    '소방, 소화, 스프링클러, 화재경보 등 소방 설비 공사.',
    ARRAY['소방', '소화', '스프링클러', '화재', '경보'],
    ARRAY['소방설비공사', '소화설비', '화재경보공사', '소방시공'],
    2
),
(
    '승강기', 'elevator',
    (SELECT id FROM ontology_concepts WHERE concept_name = '기계설비공사'),
    3,
    '엘리베이터, 에스컬레이터, 리프트 등 승강 설비 공사.',
    ARRAY['승강기', '엘리베이터', '에스컬레이터', '리프트'],
    ARRAY['승강기공사', '엘리베이터설치', '승강설비'],
    3
);

-- LEVEL 3: 소분류 - IT/SW개발 하위
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES
(
    '웹개발', 'web_development',
    (SELECT id FROM ontology_concepts WHERE concept_name = 'IT/SW개발'),
    3,
    '웹사이트, 홈페이지, 포털 시스템 구축 용역.',
    ARRAY['웹', '홈페이지', '포털', '웹사이트'],
    ARRAY['웹개발용역', '홈페이지구축', '포털개발', '웹시스템'],
    1
),
(
    '앱개발', 'app_development',
    (SELECT id FROM ontology_concepts WHERE concept_name = 'IT/SW개발'),
    3,
    '모바일 앱, 어플리케이션 개발 용역.',
    ARRAY['앱', '모바일', '어플', '애플리케이션'],
    ARRAY['앱개발용역', '모바일개발', '어플개발', '모바일앱'],
    2
),
(
    'AI/빅데이터', 'ai_bigdata',
    (SELECT id FROM ontology_concepts WHERE concept_name = 'IT/SW개발'),
    3,
    '인공지능, 빅데이터, 머신러닝, 딥러닝 관련 개발 용역.',
    ARRAY['AI', '인공지능', '빅데이터', '머신러닝', '딥러닝'],
    ARRAY['AI개발', '인공지능개발', '빅데이터분석', '데이터사이언스'],
    3
),
(
    '클라우드/인프라', 'cloud_infrastructure',
    (SELECT id FROM ontology_concepts WHERE concept_name = 'IT/SW개발'),
    3,
    '클라우드 서비스, 서버 인프라, IDC, 데이터센터 구축 용역.',
    ARRAY['클라우드', '서버', '인프라', 'IDC', '데이터센터'],
    ARRAY['클라우드구축', '인프라구축', 'IaaS', 'PaaS', 'SaaS'],
    4
);

-- LEVEL 3: 소분류 - 유지보수 하위
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES
(
    '시설유지보수', 'facility_maintenance',
    (SELECT id FROM ontology_concepts WHERE concept_name = '유지보수'),
    3,
    '건물관리, 청소, 경비 등 시설 유지관리 용역.',
    ARRAY['시설', '건물관리', '청소', '경비'],
    ARRAY['시설관리', '건물유지보수', '시설운영', 'FM'],
    1
),
(
    'SW유지보수', 'sw_maintenance',
    (SELECT id FROM ontology_concepts WHERE concept_name = '유지보수'),
    3,
    '소프트웨어 유지보수, 시스템 운영, SM 등 IT 유지관리 용역.',
    ARRAY['SW유지보수', '시스템운영', 'SM', '운영관리'],
    ARRAY['소프트웨어유지보수', '시스템유지보수', 'IT운영', '정보시스템운영'],
    2
),
(
    '장비유지보수', 'equipment_maintenance',
    (SELECT id FROM ontology_concepts WHERE concept_name = '유지보수'),
    3,
    '장비, 기기 수리, 정비 등 장비 유지관리 용역.',
    ARRAY['장비', '기기', '수리', '정비'],
    ARRAY['장비수리', '기기정비', '장비관리', '설비정비'],
    3
);

-- LEVEL 3: 소분류 - 설계용역 하위
INSERT INTO ontology_concepts (concept_name, concept_name_en, parent_id, level, description, keywords, synonyms, display_order)
VALUES
(
    '건축설계', 'architectural_design',
    (SELECT id FROM ontology_concepts WHERE concept_name = '설계용역'),
    3,
    '건축물 설계, 건축사 설계, 설계도면 작성 용역.',
    ARRAY['건축설계', '건축사', '설계도'],
    ARRAY['건축설계용역', '건물설계', '건축도면'],
    1
),
(
    '토목설계', 'civil_design',
    (SELECT id FROM ontology_concepts WHERE concept_name = '설계용역'),
    3,
    '토목 설계, 측량, 지질조사 등 토목 분야 설계 용역.',
    ARRAY['토목설계', '측량', '지질조사'],
    ARRAY['토목설계용역', '측량설계', '지질조사용역', '기반시설설계'],
    2
);

-- CROSS-CATEGORY RELATIONS
INSERT INTO ontology_relations (source_concept_id, target_concept_id, relation_type, weight, description)
VALUES
(
    (SELECT id FROM ontology_concepts WHERE concept_name = '건축공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '건축설계'),
    'relatedTo', 0.8,
    '건축공사는 건축설계를 기반으로 수행됨. 건축설계 완료 후 건축공사 발주가 일반적.'
),
(
    (SELECT id FROM ontology_concepts WHERE concept_name = '토목공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '토목설계'),
    'relatedTo', 0.8,
    '토목공사는 토목설계를 기반으로 수행됨. 설계-시공 연계가 밀접함.'
),
(
    (SELECT id FROM ontology_concepts WHERE concept_name = '전기공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '조명공사'),
    'relatedTo', 0.7,
    '조명공사는 전기공사의 하위 분야이며, 전기 인프라를 전제로 함.'
),
(
    (SELECT id FROM ontology_concepts WHERE concept_name = '통신공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = 'IT/SW개발'),
    'relatedTo', 0.6,
    '통신 인프라 구축 후 IT/SW 시스템이 운영됨. 네트워크-소프트웨어 연계.'
),
(
    (SELECT id FROM ontology_concepts WHERE concept_name = 'IT/SW개발'),
    (SELECT id FROM ontology_concepts WHERE concept_name = 'SW유지보수'),
    'relatedTo', 0.8,
    'SW개발 완료 후 SW유지보수로 전환됨. 개발-운영 생명주기 연계.'
),
(
    (SELECT id FROM ontology_concepts WHERE concept_name = '건축공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '감리용역'),
    'requires', 0.7,
    '일정 규모 이상 건축공사는 법적으로 감리 의무. 건설기술진흥법 시행령 기준.'
),
(
    (SELECT id FROM ontology_concepts WHERE concept_name = '토목공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '감리용역'),
    'requires', 0.7,
    '일정 규모 이상 토목공사는 법적으로 감리 의무. 건설기술진흥법 시행령 기준.'
),
(
    (SELECT id FROM ontology_concepts WHERE concept_name = '도로공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '포장공사'),
    'relatedTo', 0.9,
    '도로공사는 대부분 포장공사를 포함함. 아스팔트/콘크리트 포장이 핵심 공정.'
),
(
    (SELECT id FROM ontology_concepts WHERE concept_name = '도로공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '교량공사'),
    'relatedTo', 0.7,
    '도로 노선에 교량이 포함되는 경우가 많음. 도로-교량 복합 공사 빈번.'
),
(
    (SELECT id FROM ontology_concepts WHERE concept_name = '도로공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '터널공사'),
    'relatedTo', 0.6,
    '산악 지형 도로에 터널이 포함됨. 도로-터널 복합 공사.'
),
(
    (SELECT id FROM ontology_concepts WHERE concept_name = '하천공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '하수도공사'),
    'relatedTo', 0.7,
    '하천 정비와 하수도 정비가 연계되는 경우가 많음. 배수 체계 통합 관리.'
),
(
    (SELECT id FROM ontology_concepts WHERE concept_name = '상수도공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '하수도공사'),
    'relatedTo', 0.6,
    '상수도와 하수도는 물 순환 체계의 양면. 동시 발주되는 경우 있음.'
),
(
    (SELECT id FROM ontology_concepts WHERE concept_name = '냉난방설비'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '기계설비공사'),
    'relatedTo', 0.9,
    '냉난방설비는 기계설비공사의 핵심 구성 요소. 배관/펌프/공조와 밀접.'
),
(
    (SELECT id FROM ontology_concepts WHERE concept_name = '소방설비'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '전기공사'),
    'relatedTo', 0.6,
    '소방설비(화재경보, 비상전원)는 전기 인프라에 의존함. 전기-소방 연계 시공.'
),
(
    (SELECT id FROM ontology_concepts WHERE concept_name = '통신공사'),
    (SELECT id FROM ontology_concepts WHERE concept_name = '보안장비'),
    'similarTo', 0.7,
    'CCTV는 통신공사(설치)와 보안장비(물품 구매) 양쪽에 걸침. 공사-물품 경계 개념.'
);

COMMIT;


-- ============================================================
-- SECTION 10: RAG Tables
-- Source: sql/create_rag_tables.sql
-- Note: Requires pgvector extension and bid_announcements table
--       (bid_announcements is created by the batch system at runtime)
-- ============================================================

BEGIN;

-- 확장 모듈 설치
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- rfp_chunks 테이블: RFP 문서의 청크 단위 저장
CREATE TABLE IF NOT EXISTS rfp_chunks (
    chunk_id        BIGSERIAL PRIMARY KEY,
    bid_notice_no   VARCHAR(100) NOT NULL,
    document_id     INTEGER,
    chunk_index     INTEGER NOT NULL,
    chunk_text      TEXT NOT NULL,
    chunk_text_tsv  TSVECTOR GENERATED ALWAYS AS
                        (to_tsvector('simple', chunk_text)) STORED,
    embedding       vector(1536),
    embedding_model VARCHAR(50) DEFAULT 'text-embedding-3-small',
    section_type    VARCHAR(50),
    page_number     INTEGER,
    token_count     INTEGER,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE rfp_chunks IS 'RFP 문서를 청크 단위로 분할하여 벡터 임베딩과 함께 저장하는 RAG 핵심 테이블';
COMMENT ON COLUMN rfp_chunks.chunk_index    IS '문서 내 청크 순서 (0부터 시작)';
COMMENT ON COLUMN rfp_chunks.chunk_text_tsv IS 'simple 딕셔너리 기반 전문 검색용 tsvector (자동 생성 컬럼)';
COMMENT ON COLUMN rfp_chunks.embedding      IS 'text-embedding-3-small 모델 기준 1536차원 벡터';
COMMENT ON COLUMN rfp_chunks.section_type   IS '청크가 속한 문서 섹션 유형 (자격요건, 예정가격, 제출서류 등)';

-- rfp_chunks 인덱스
CREATE INDEX IF NOT EXISTS idx_rfp_chunks_embedding_hnsw
    ON rfp_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 128);

CREATE INDEX IF NOT EXISTS idx_rfp_chunks_tsv_gin
    ON rfp_chunks USING GIN (chunk_text_tsv);

CREATE INDEX IF NOT EXISTS idx_rfp_chunks_trgm
    ON rfp_chunks USING GIN (chunk_text gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_rfp_chunks_bid_notice_no
    ON rfp_chunks(bid_notice_no);

CREATE INDEX IF NOT EXISTS idx_rfp_chunks_section_type
    ON rfp_chunks(section_type);

CREATE INDEX IF NOT EXISTS idx_rfp_chunks_bid_chunk
    ON rfp_chunks(bid_notice_no, chunk_index);

-- has_embedding 컬럼: bid_announcements가 이미 존재하는 경우에만 추가
-- (배치 시스템이 bid_announcements를 먼저 생성한 후 이 파일이 적용됨)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'bid_announcements') THEN
        ALTER TABLE bid_announcements
            ADD COLUMN IF NOT EXISTS has_embedding BOOLEAN DEFAULT FALSE;

        COMMENT ON COLUMN bid_announcements.has_embedding IS '해당 공고의 RFP 문서가 벡터 임베딩 처리 완료되었는지 여부';

        CREATE INDEX IF NOT EXISTS idx_bid_has_embedding
            ON bid_announcements(has_embedding);
    END IF;
END $$;

-- fn_hybrid_search 함수: RRF 기반 하이브리드 검색
CREATE OR REPLACE FUNCTION fn_hybrid_search(
    query_embedding     vector(1536),
    query_text          TEXT,
    match_count         INT     DEFAULT 10,
    candidate_count     INT     DEFAULT 40,
    rrf_k               INT     DEFAULT 60,
    filter_bid_notice_no VARCHAR DEFAULT NULL,
    filter_section_type  VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    chunk_id     BIGINT,
    chunk_text   TEXT,
    bid_notice_no VARCHAR,
    section_type  VARCHAR,
    chunk_index   INTEGER,
    rrf_score     DOUBLE PRECISION,
    match_sources TEXT[]
)
LANGUAGE SQL
STABLE
AS $$
    WITH vector_results AS (
        SELECT
            c.chunk_id,
            ROW_NUMBER() OVER (ORDER BY c.embedding <=> query_embedding) AS rank
        FROM rfp_chunks c
        WHERE
            c.embedding IS NOT NULL
            AND (filter_bid_notice_no IS NULL OR c.bid_notice_no = filter_bid_notice_no)
            AND (filter_section_type  IS NULL OR c.section_type  = filter_section_type)
        ORDER BY c.embedding <=> query_embedding
        LIMIT candidate_count
    ),
    fts_results AS (
        SELECT
            c.chunk_id,
            ROW_NUMBER() OVER (
                ORDER BY ts_rank_cd(c.chunk_text_tsv, plainto_tsquery('simple', query_text)) DESC
            ) AS rank
        FROM rfp_chunks c
        WHERE
            c.chunk_text_tsv @@ plainto_tsquery('simple', query_text)
            AND (filter_bid_notice_no IS NULL OR c.bid_notice_no = filter_bid_notice_no)
            AND (filter_section_type  IS NULL OR c.section_type  = filter_section_type)
        ORDER BY ts_rank_cd(c.chunk_text_tsv, plainto_tsquery('simple', query_text)) DESC
        LIMIT candidate_count
    ),
    combined AS (
        SELECT chunk_id, 1.0 / (rrf_k + rank) AS rrf_score, 'vector' AS source
        FROM vector_results

        UNION ALL

        SELECT chunk_id, 1.0 / (rrf_k + rank) AS rrf_score, 'fts' AS source
        FROM fts_results
    ),
    fused AS (
        SELECT
            chunk_id,
            SUM(rrf_score)         AS total_rrf_score,
            ARRAY_AGG(DISTINCT source ORDER BY source) AS sources
        FROM combined
        GROUP BY chunk_id
    )
    SELECT
        rc.chunk_id,
        rc.chunk_text,
        rc.bid_notice_no,
        rc.section_type,
        rc.chunk_index,
        f.total_rrf_score  AS rrf_score,
        f.sources          AS match_sources
    FROM fused f
    JOIN rfp_chunks rc ON rc.chunk_id = f.chunk_id
    ORDER BY f.total_rrf_score DESC
    LIMIT match_count;
$$;

COMMENT ON FUNCTION fn_hybrid_search IS
    'RRF(Reciprocal Rank Fusion) 알고리즘으로 벡터 검색(코사인 유사도)과 '
    '전문 검색(FTS)을 융합하는 하이브리드 검색 함수.';

COMMIT;

-- ============================================================
-- SECTION 11: User Settings Table
-- Source: backend/api/settings.py (auto-created by API)
-- ============================================================

CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);

-- ============================================================
-- END OF INITIALIZATION SCRIPT
-- ============================================================
