-- 구독 시스템 함수들
-- 2025-09-25

-- 사용량 체크 함수
CREATE OR REPLACE FUNCTION check_subscription_limit(
    p_user_id INTEGER,
    p_limit_type VARCHAR(50)
) RETURNS JSON AS $$
DECLARE
    v_plan subscription_plans;
    v_subscription user_subscriptions;
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
$$ LANGUAGE plpgsql;

-- 사용량 증가 함수
CREATE OR REPLACE FUNCTION increment_usage(
    p_user_id INTEGER,
    p_usage_type VARCHAR(50)
) RETURNS VOID AS $$
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
$$ LANGUAGE plpgsql;

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