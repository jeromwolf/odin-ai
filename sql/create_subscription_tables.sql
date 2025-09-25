-- 구독/결제 시스템 테이블 생성
-- 2025-09-25

-- 기존 테이블 삭제
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
    price_monthly INTEGER NOT NULL, -- 원화, 월 요금
    price_yearly INTEGER, -- 원화, 연 요금 (할인가)
    is_active BOOLEAN DEFAULT true,

    -- 기능 제한
    max_searches_per_day INTEGER DEFAULT NULL, -- NULL = 무제한
    max_downloads_per_month INTEGER DEFAULT NULL,
    max_bookmarks INTEGER DEFAULT NULL,
    max_alerts INTEGER DEFAULT NULL,
    api_rate_limit INTEGER DEFAULT NULL, -- 시간당 API 호출 제한

    -- 기능 플래그
    has_ai_recommendations BOOLEAN DEFAULT false,
    has_advanced_search BOOLEAN DEFAULT false,
    has_export_excel BOOLEAN DEFAULT false,
    has_api_access BOOLEAN DEFAULT false,
    has_priority_support BOOLEAN DEFAULT false,
    has_custom_alerts BOOLEAN DEFAULT false,
    has_team_collaboration BOOLEAN DEFAULT false,

    -- 추가 메타데이터
    badge_color VARCHAR(7), -- HEX 컬러 코드
    badge_text VARCHAR(20), -- 예: "BEST", "인기"
    sort_order INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 사용자 구독 정보
CREATE TABLE user_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id INTEGER NOT NULL REFERENCES subscription_plans(id),

    -- 구독 상태
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, cancelled, expired, paused
    billing_cycle VARCHAR(10) NOT NULL DEFAULT 'monthly', -- monthly, yearly

    -- 구독 기간
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    cancelled_at TIMESTAMP,

    -- 결제 정보
    next_billing_date TIMESTAMP,
    last_payment_date TIMESTAMP,
    last_payment_amount INTEGER,

    -- 자동 갱신
    auto_renew BOOLEAN DEFAULT true,

    -- 무료 체험
    is_trial BOOLEAN DEFAULT false,
    trial_ends_at TIMESTAMP,

    -- 프로모션
    promo_code VARCHAR(50),
    discount_percentage INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id) -- 사용자당 하나의 활성 구독만 허용
);

-- 결제 내역
CREATE TABLE payment_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id INTEGER REFERENCES user_subscriptions(id),

    -- 결제 정보
    amount INTEGER NOT NULL, -- 원화
    currency VARCHAR(3) DEFAULT 'KRW',
    payment_method VARCHAR(50), -- card, bank_transfer, etc

    -- 상태
    status VARCHAR(20) NOT NULL, -- pending, completed, failed, refunded

    -- 트랜잭션 정보
    transaction_id VARCHAR(100) UNIQUE,
    gateway VARCHAR(50), -- toss, iamport, etc
    gateway_response JSONB,

    -- 세부 정보
    description TEXT,
    invoice_number VARCHAR(50),

    -- 실패 정보
    failure_reason TEXT,
    failed_at TIMESTAMP,

    -- 환불 정보
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

    -- 카드 정보 (암호화 저장)
    type VARCHAR(20) NOT NULL, -- card, bank_account
    card_last4 VARCHAR(4),
    card_brand VARCHAR(20), -- visa, mastercard, etc
    bank_name VARCHAR(50),
    account_last4 VARCHAR(4),

    -- 빌링키 (PG사에서 발급)
    billing_key VARCHAR(200) UNIQUE,

    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,

    expires_at TIMESTAMP, -- 카드 만료일
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 청구지 주소
CREATE TABLE billing_addresses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    company_name VARCHAR(200),
    tax_id VARCHAR(20), -- 사업자등록번호

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

    -- 사용량 추적
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

    -- 금액 정보
    subtotal INTEGER NOT NULL,
    tax_amount INTEGER DEFAULT 0,
    discount_amount INTEGER DEFAULT 0,
    total_amount INTEGER NOT NULL,

    -- 청구 정보
    billing_period_start DATE,
    billing_period_end DATE,
    due_date DATE,

    -- 상태
    status VARCHAR(20) DEFAULT 'pending', -- pending, paid, overdue, cancelled

    -- PDF 경로
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
-- Free 플랜
('free', 'Free', '무료로 시작하세요',
 0, 0,
 10, 5, 20, 3,
 false, false, false, false,
 '#9CA3AF', NULL, 1),

-- Basic 플랜
('basic', 'Basic', '개인 사용자를 위한 기본 플랜',
 29900, 299000, -- 월 29,900원, 연 299,000원 (연간 약 17% 할인)
 50, 20, 100, 10,
 false, true, true, false,
 '#3B82F6', NULL, 2),

-- Professional 플랜
('professional', 'Professional', '전문가를 위한 프리미엄 기능',
 99000, 990000, -- 월 99,000원, 연 990,000원 (연간 약 17% 할인)
 NULL, 100, 500, 50, -- 검색 무제한
 true, true, true, true,
 '#8B5CF6', '인기', 3),

-- Enterprise 플랜
('enterprise', 'Enterprise', '기업용 맞춤형 솔루션',
 299000, 2990000, -- 월 299,000원, 연 2,990,000원
 NULL, NULL, NULL, NULL, -- 모두 무제한
 true, true, true, true,
 '#F59E0B', '기업용', 4);

-- 구독 플랜 특징 테이블 (UI 표시용)
CREATE TABLE subscription_features (
    id SERIAL PRIMARY KEY,
    plan_id INTEGER NOT NULL REFERENCES subscription_plans(id) ON DELETE CASCADE,
    feature_name VARCHAR(200) NOT NULL,
    feature_value VARCHAR(100), -- "무제한", "월 100회", "✓" 등
    feature_group VARCHAR(50), -- "검색", "분석", "지원" 등
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

-- 사용량 체크 함수
CREATE OR REPLACE FUNCTION check_subscription_limit(
    p_user_id INTEGER,
    p_limit_type VARCHAR(50) -- 'search', 'download', 'bookmark', 'alert', 'api'
) RETURNS JSON AS $
DECLARE
    v_plan subscription_plans;
    v_subscription user_subscriptions;
    v_usage subscription_usage;
    v_current_count INTEGER;
    v_limit INTEGER;
    v_is_allowed BOOLEAN;
BEGIN
    -- 현재 구독 정보 조회
    SELECT s.*, p.*
    INTO v_subscription, v_plan
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
            -- 월간 다운로드는 별도 계산
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
            -- 시간당 API 호출
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
$ LANGUAGE plpgsql;

-- 사용량 증가 함수
CREATE OR REPLACE FUNCTION increment_usage(
    p_user_id INTEGER,
    p_usage_type VARCHAR(50)
) RETURNS VOID AS $
BEGIN
    -- 사용량 증가
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
$ LANGUAGE plpgsql;

-- 트리거: 구독 업데이트 시 updated_at 갱신
CREATE OR REPLACE FUNCTION update_subscription_timestamp()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER update_subscription_plans_timestamp
BEFORE UPDATE ON subscription_plans
FOR EACH ROW EXECUTE FUNCTION update_subscription_timestamp();

CREATE TRIGGER update_user_subscriptions_timestamp
BEFORE UPDATE ON user_subscriptions
FOR EACH ROW EXECUTE FUNCTION update_subscription_timestamp();

GRANT ALL ON ALL TABLES IN SCHEMA public TO blockmeta;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO blockmeta;