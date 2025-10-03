-- ============================================
-- ODIN-AI 관리자 웹 시스템 데이터베이스 스키마
-- ============================================
-- 작성일: 2025-10-02
-- 설명: 배치 모니터링, 시스템 메트릭, 관리자 활동 로그를 위한 테이블
-- ============================================

-- ============================================
-- 1. 배치 실행 로그 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS batch_execution_logs (
    id SERIAL PRIMARY KEY,

    -- 배치 정보
    batch_type VARCHAR(50) NOT NULL,           -- collector/downloader/processor/notification
    status VARCHAR(20) NOT NULL,                -- running/success/failed/cancelled

    -- 시간 정보
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds INTEGER,                   -- 종료 시 자동 계산

    -- 처리 통계
    total_items INTEGER DEFAULT 0,              -- 전체 처리 대상 항목 수
    success_items INTEGER DEFAULT 0,            -- 성공한 항목 수
    failed_items INTEGER DEFAULT 0,             -- 실패한 항목 수
    skipped_items INTEGER DEFAULT 0,            -- 스킵된 항목 수

    -- 에러 정보
    error_message TEXT,                         -- 주요 에러 메시지
    error_count INTEGER DEFAULT 0,              -- 총 에러 발생 횟수

    -- 메타데이터
    triggered_by VARCHAR(50) DEFAULT 'cron',   -- cron/manual/api
    triggered_by_user_id INTEGER REFERENCES users(id), -- 수동 실행 시

    -- 타임스탬프
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_batch_execution_batch_type ON batch_execution_logs(batch_type);
CREATE INDEX idx_batch_execution_status ON batch_execution_logs(status);
CREATE INDEX idx_batch_execution_start_time ON batch_execution_logs(start_time DESC);
CREATE INDEX idx_batch_execution_created_at ON batch_execution_logs(created_at DESC);

-- 코멘트
COMMENT ON TABLE batch_execution_logs IS '배치 프로그램 실행 이력 및 통계';
COMMENT ON COLUMN batch_execution_logs.batch_type IS '배치 타입: collector, downloader, processor, notification';
COMMENT ON COLUMN batch_execution_logs.status IS '실행 상태: running, success, failed, cancelled';
COMMENT ON COLUMN batch_execution_logs.triggered_by IS '실행 트리거: cron, manual, api';

-- ============================================
-- 2. 배치 처리 상세 로그 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS batch_detail_logs (
    id SERIAL PRIMARY KEY,

    -- 연관 관계
    execution_id INTEGER NOT NULL REFERENCES batch_execution_logs(id) ON DELETE CASCADE,

    -- 로그 정보
    log_level VARCHAR(20) NOT NULL,            -- DEBUG/INFO/WARNING/ERROR/CRITICAL
    message TEXT NOT NULL,                      -- 로그 메시지

    -- 컨텍스트 정보 (JSONB)
    context JSONB,                              -- 추가 컨텍스트 (파일명, 입찰ID 등)

    -- 타임스탬프
    created_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_batch_detail_execution_id ON batch_detail_logs(execution_id);
CREATE INDEX idx_batch_detail_log_level ON batch_detail_logs(log_level);
CREATE INDEX idx_batch_detail_created_at ON batch_detail_logs(created_at DESC);
CREATE INDEX idx_batch_detail_context ON batch_detail_logs USING GIN(context);

-- 코멘트
COMMENT ON TABLE batch_detail_logs IS '배치 실행 중 발생한 상세 로그';
COMMENT ON COLUMN batch_detail_logs.log_level IS '로그 레벨: DEBUG, INFO, WARNING, ERROR, CRITICAL';
COMMENT ON COLUMN batch_detail_logs.context IS 'JSON 형식의 추가 컨텍스트 정보';

-- ============================================
-- 3. 시스템 메트릭 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS system_metrics (
    id SERIAL PRIMARY KEY,

    -- 메트릭 정보
    metric_type VARCHAR(50) NOT NULL,          -- cpu/memory/disk/api_response_time/db_connections
    metric_value FLOAT NOT NULL,                -- 메트릭 값
    metric_unit VARCHAR(20),                    -- 단위: percent/mb/ms/count

    -- 추가 정보 (JSONB)
    metadata JSONB,                             -- 추가 메타데이터

    -- 타임스탬프
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_system_metrics_type ON system_metrics(metric_type);
CREATE INDEX idx_system_metrics_recorded_at ON system_metrics(recorded_at DESC);
CREATE INDEX idx_system_metrics_type_time ON system_metrics(metric_type, recorded_at DESC);

-- 코멘트
COMMENT ON TABLE system_metrics IS '시스템 리소스 및 성능 메트릭';
COMMENT ON COLUMN system_metrics.metric_type IS '메트릭 타입: cpu, memory, disk, api_response_time, db_connections';
COMMENT ON COLUMN system_metrics.metric_unit IS '메트릭 단위: percent, mb, ms, count';

-- ============================================
-- 4. 관리자 활동 로그 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS admin_activity_logs (
    id SERIAL PRIMARY KEY,

    -- 관리자 정보
    admin_user_id INTEGER NOT NULL REFERENCES users(id),

    -- 활동 정보
    action VARCHAR(100) NOT NULL,               -- batch_manual_run/user_deactivate/setting_change 등
    target_type VARCHAR(50),                    -- user/batch/system/database
    target_id INTEGER,                          -- 대상 ID (있을 경우)

    -- 상세 정보 (JSONB)
    details JSONB,                              -- 액션 상세 정보

    -- 요청 정보
    ip_address VARCHAR(50),                     -- 관리자 IP 주소
    user_agent TEXT,                            -- 브라우저 정보

    -- 결과
    result VARCHAR(20) DEFAULT 'success',       -- success/failed
    error_message TEXT,                         -- 실패 시 에러 메시지

    -- 타임스탬프
    created_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_admin_activity_admin_user_id ON admin_activity_logs(admin_user_id);
CREATE INDEX idx_admin_activity_action ON admin_activity_logs(action);
CREATE INDEX idx_admin_activity_created_at ON admin_activity_logs(created_at DESC);
CREATE INDEX idx_admin_activity_target ON admin_activity_logs(target_type, target_id);

-- 코멘트
COMMENT ON TABLE admin_activity_logs IS '관리자 활동 감사 로그';
COMMENT ON COLUMN admin_activity_logs.action IS '관리자 액션: batch_manual_run, user_deactivate, setting_change 등';
COMMENT ON COLUMN admin_activity_logs.target_type IS '대상 타입: user, batch, system, database';
COMMENT ON COLUMN admin_activity_logs.details IS 'JSON 형식의 액션 상세 정보';

-- ============================================
-- 5. API 성능 로그 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS api_performance_logs (
    id SERIAL PRIMARY KEY,

    -- API 정보
    endpoint VARCHAR(255) NOT NULL,             -- API 엔드포인트 경로
    http_method VARCHAR(10) NOT NULL,           -- GET/POST/PUT/DELETE

    -- 성능 정보
    response_time_ms INTEGER NOT NULL,          -- 응답 시간 (밀리초)
    status_code INTEGER NOT NULL,               -- HTTP 상태 코드

    -- 요청 정보
    user_id INTEGER REFERENCES users(id),       -- 요청한 사용자 (인증된 경우)
    ip_address VARCHAR(50),

    -- 에러 정보
    error_message TEXT,                         -- 에러 발생 시

    -- 타임스탬프
    created_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_api_perf_endpoint ON api_performance_logs(endpoint);
CREATE INDEX idx_api_perf_created_at ON api_performance_logs(created_at DESC);
CREATE INDEX idx_api_perf_endpoint_time ON api_performance_logs(endpoint, created_at DESC);
CREATE INDEX idx_api_perf_status_code ON api_performance_logs(status_code);

-- 코멘트
COMMENT ON TABLE api_performance_logs IS 'API 엔드포인트 성능 추적';
COMMENT ON COLUMN api_performance_logs.response_time_ms IS 'API 응답 시간 (밀리초)';

-- ============================================
-- 6. 알림 발송 로그 테이블 (기존 확장)
-- ============================================
CREATE TABLE IF NOT EXISTS notification_send_logs (
    id SERIAL PRIMARY KEY,

    -- 알림 정보
    notification_type VARCHAR(50) NOT NULL,     -- bid_match/deadline_alert/daily_digest/system
    user_id INTEGER REFERENCES users(id),

    -- 발송 정보
    email_to VARCHAR(255) NOT NULL,
    email_subject VARCHAR(500),

    -- 상태
    status VARCHAR(20) NOT NULL,                -- pending/sent/failed
    send_attempts INTEGER DEFAULT 0,            -- 발송 시도 횟수

    -- 결과
    sent_at TIMESTAMP,                          -- 실제 발송 시간
    error_message TEXT,                         -- 실패 시 에러 메시지

    -- 메타데이터
    metadata JSONB,                             -- 알림 관련 추가 정보 (입찰ID 등)

    -- 타임스탬프
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_notif_send_user_id ON notification_send_logs(user_id);
CREATE INDEX idx_notif_send_status ON notification_send_logs(status);
CREATE INDEX idx_notif_send_created_at ON notification_send_logs(created_at DESC);
CREATE INDEX idx_notif_send_type ON notification_send_logs(notification_type);

-- 코멘트
COMMENT ON TABLE notification_send_logs IS '이메일 알림 발송 로그';
COMMENT ON COLUMN notification_send_logs.notification_type IS '알림 타입: bid_match, deadline_alert, daily_digest, system';
COMMENT ON COLUMN notification_send_logs.status IS '발송 상태: pending, sent, failed';

-- ============================================
-- 7. 시스템 설정 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,

    -- 설정 정보
    setting_key VARCHAR(100) UNIQUE NOT NULL,   -- 설정 키 (예: batch_cron_collector)
    setting_value TEXT NOT NULL,                -- 설정 값
    setting_type VARCHAR(20) NOT NULL,          -- string/integer/boolean/json

    -- 설명
    description TEXT,                           -- 설정 설명
    category VARCHAR(50),                       -- batch/notification/api/system

    -- 변경 이력
    changed_by_user_id INTEGER REFERENCES users(id),
    changed_at TIMESTAMP,
    previous_value TEXT,                        -- 이전 값

    -- 타임스탬프
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 생성
CREATE UNIQUE INDEX idx_system_settings_key ON system_settings(setting_key);
CREATE INDEX idx_system_settings_category ON system_settings(category);

-- 코멘트
COMMENT ON TABLE system_settings IS '시스템 설정 관리';
COMMENT ON COLUMN system_settings.setting_key IS '설정 키 (고유값)';
COMMENT ON COLUMN system_settings.setting_type IS '설정 타입: string, integer, boolean, json';

-- ============================================
-- 8. 뷰 (View) 생성
-- ============================================

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

-- ============================================
-- 9. 함수 (Functions)
-- ============================================

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
    -- 시작 시간 조회
    SELECT start_time INTO v_start_time
    FROM batch_execution_logs
    WHERE id = p_execution_id;

    -- 배치 실행 로그 업데이트
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

    -- ERROR 레벨일 경우 에러 카운트 증가
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

-- ============================================
-- 10. 트리거 (Triggers)
-- ============================================

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

-- ============================================
-- 11. 초기 데이터 삽입
-- ============================================

-- 시스템 설정 초기값
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

-- ============================================
-- 12. 데이터 정리 작업 (선택사항)
-- ============================================

-- 90일 이전 시스템 메트릭 삭제 함수
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

-- 180일 이전 배치 상세 로그 삭제 함수
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

-- ============================================
-- 완료
-- ============================================
-- 스키마 생성 완료
-- 실행 방법:
-- psql -U blockmeta -d odin_db -f sql/admin_schema.sql
-- ============================================
