-- batch_schedules: 배치 스케줄 관리 (알람 스타일)
-- 관리자 웹에서 배치 실행 시간을 추가/수정/삭제/ON·OFF 제어

CREATE TABLE IF NOT EXISTS batch_schedules (
    id SERIAL PRIMARY KEY,
    label VARCHAR(100) NOT NULL,
    schedule_hour INTEGER NOT NULL CHECK (schedule_hour >= 0 AND schedule_hour <= 23),
    schedule_minute INTEGER NOT NULL CHECK (schedule_minute >= 0 AND schedule_minute <= 59),
    days_of_week VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT true,
    options JSONB NOT NULL DEFAULT '{
        "enable_notification": true,
        "enable_embedding": false,
        "enable_graph_sync": false,
        "enable_graphrag": false,
        "enable_award_collection": false,
        "enable_daily_digest": false
    }'::jsonb,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_batch_schedules_active ON batch_schedules(is_active);
