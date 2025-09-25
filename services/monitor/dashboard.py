#!/usr/bin/env python3
"""
ODIN-AI 모니터링 대시보드
시스템 상태, 통계, 로그를 실시간으로 모니터링
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import redis
import psycopg2
from datetime import datetime, timedelta
import json
from collections import defaultdict

app = Flask(__name__)
CORS(app)

# 환경변수
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db')
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

# Redis 연결
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    redis_connected = redis_client.ping()
except:
    redis_connected = False
    redis_client = None


def get_db_connection():
    """데이터베이스 연결"""
    return psycopg2.connect(DATABASE_URL)


@app.route('/')
def index():
    """메인 대시보드 페이지"""
    return render_template('dashboard.html')


@app.route('/api/status')
def system_status():
    """시스템 상태 API"""
    status = {
        'timestamp': datetime.now().isoformat(),
        'services': {}
    }

    # PostgreSQL 상태
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        conn.close()
        status['services']['postgres'] = 'running'
    except:
        status['services']['postgres'] = 'down'

    # Redis 상태
    if redis_connected:
        status['services']['redis'] = 'running'
    else:
        status['services']['redis'] = 'down'

    # 배치 프로세스 상태
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT MAX(collected_at)
            FROM bid_announcements
            WHERE collected_at > NOW() - INTERVAL '1 day'
        """)
        last_batch = cur.fetchone()[0]
        conn.close()

        if last_batch:
            hours_ago = (datetime.now() - last_batch).total_seconds() / 3600
            if hours_ago < 12:
                status['services']['batch'] = 'active'
            else:
                status['services']['batch'] = 'idle'
        else:
            status['services']['batch'] = 'inactive'
    except:
        status['services']['batch'] = 'error'

    # 알림 서비스 상태
    if redis_client:
        try:
            queue_size = redis_client.llen('event_queue')
            status['services']['alert'] = 'active' if queue_size > 0 else 'idle'
        except:
            status['services']['alert'] = 'error'
    else:
        status['services']['alert'] = 'down'

    return jsonify(status)


@app.route('/api/stats/overview')
def stats_overview():
    """전체 통계 API"""
    stats = {}

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 오늘 통계
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN collected_at::date = CURRENT_DATE THEN 1 END) as today,
                COUNT(CASE WHEN collected_at > NOW() - INTERVAL '7 days' THEN 1 END) as week
            FROM bid_announcements
        """)
        row = cur.fetchone()
        stats['announcements'] = {
            'total': row[0],
            'today': row[1],
            'week': row[2]
        }

        # 문서 처리 통계
        cur.execute("""
            SELECT
                download_status,
                COUNT(*)
            FROM bid_documents
            GROUP BY download_status
        """)
        docs = dict(cur.fetchall())
        stats['documents'] = docs

        # 알림 통계
        cur.execute("""
            SELECT
                COUNT(*) as total_rules,
                COUNT(CASE WHEN is_active THEN 1 END) as active_rules
            FROM alert_rules
        """)
        row = cur.fetchone()
        stats['alerts'] = {
            'total_rules': row[0],
            'active_rules': row[1]
        }

        # 매칭 통계
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN is_sent THEN 1 END) as sent,
                COUNT(CASE WHEN match_date = CURRENT_DATE THEN 1 END) as today
            FROM alert_matches
        """)
        row = cur.fetchone()
        stats['matches'] = {
            'total': row[0],
            'sent': row[1],
            'today': row[2]
        }

        conn.close()

    except Exception as e:
        stats['error'] = str(e)

    return jsonify(stats)


@app.route('/api/stats/timeline')
def stats_timeline():
    """시계열 통계 API"""
    days = request.args.get('days', 7, type=int)

    timeline = []

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 날짜별 통계
        cur.execute("""
            SELECT
                date_trunc('day', collected_at) as day,
                COUNT(*) as announcements,
                COUNT(DISTINCT organization_code) as organizations
            FROM bid_announcements
            WHERE collected_at > NOW() - INTERVAL '%s days'
            GROUP BY day
            ORDER BY day
        """, (days,))

        for row in cur.fetchall():
            timeline.append({
                'date': row[0].strftime('%Y-%m-%d'),
                'announcements': row[1],
                'organizations': row[2]
            })

        conn.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify(timeline)


@app.route('/api/alerts/queue')
def alerts_queue():
    """알림 큐 상태 API"""
    queue_status = {}

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 큐 상태별 카운트
        cur.execute("""
            SELECT
                status,
                channel,
                COUNT(*) as count
            FROM alert_queue
            WHERE created_at > NOW() - INTERVAL '1 day'
            GROUP BY status, channel
        """)

        queue_status['by_status'] = defaultdict(lambda: defaultdict(int))
        for row in cur.fetchall():
            queue_status['by_status'][row[0]][row[1]] = row[2]

        # 최근 발송
        cur.execute("""
            SELECT
                id,
                user_id,
                channel,
                status,
                created_at,
                sent_at
            FROM alert_queue
            ORDER BY created_at DESC
            LIMIT 10
        """)

        queue_status['recent'] = []
        for row in cur.fetchall():
            queue_status['recent'].append({
                'id': row[0],
                'user_id': row[1],
                'channel': row[2],
                'status': row[3],
                'created_at': row[4].isoformat() if row[4] else None,
                'sent_at': row[5].isoformat() if row[5] else None
            })

        conn.close()

    except Exception as e:
        queue_status['error'] = str(e)

    return jsonify(queue_status)


@app.route('/api/batch/history')
def batch_history():
    """배치 실행 이력 API"""
    history = []

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 배치 실행 이력 (collected_at 기준으로 그룹)
        cur.execute("""
            SELECT
                DATE(collected_at) as batch_date,
                MIN(collected_at) as start_time,
                MAX(collected_at) as end_time,
                COUNT(*) as count
            FROM bid_announcements
            WHERE collected_at > NOW() - INTERVAL '30 days'
            GROUP BY batch_date
            ORDER BY batch_date DESC
            LIMIT 30
        """)

        for row in cur.fetchall():
            history.append({
                'date': row[0].strftime('%Y-%m-%d'),
                'start_time': row[1].isoformat() if row[1] else None,
                'end_time': row[2].isoformat() if row[2] else None,
                'count': row[3],
                'duration': (row[2] - row[1]).seconds if row[1] and row[2] else None
            })

        conn.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify(history)


@app.route('/api/logs/recent')
def recent_logs():
    """최근 로그 API"""
    log_type = request.args.get('type', 'all')
    limit = request.args.get('limit', 100, type=int)

    logs = []

    # Redis에서 이벤트 로그 가져오기
    if redis_client and log_type in ['all', 'events']:
        try:
            events = redis_client.lrange('event_queue', 0, limit - 1)
            for event in events:
                try:
                    event_data = json.loads(event)
                    logs.append({
                        'type': 'event',
                        'timestamp': event_data.get('timestamp'),
                        'data': event_data
                    })
                except:
                    pass
        except:
            pass

    # 정렬
    logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    return jsonify(logs[:limit])


@app.route('/api/health')
def health_check():
    """헬스체크 API"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)