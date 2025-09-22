"""
데이터베이스 웹 뷰어
Odin-AI 데이터베이스 내용을 웹 브라우저에서 확인할 수 있는 간단한 인터페이스
"""

from flask import Flask, render_template_string, jsonify
import psycopg2
from shared.config import settings
import json
from datetime import datetime

app = Flask(__name__)

# HTML 템플릿
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Odin-AI 데이터베이스 뷰어</title>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
            padding: 10px;
            background: #ecf0f1;
            border-radius: 5px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
        }
        .stat-label {
            margin-top: 5px;
            opacity: 0.9;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #3498db;
            color: white;
            font-weight: bold;
        }
        tr:hover {
            background-color: #f8f9fa;
        }
        .status-completed {
            color: #27ae60;
            font-weight: bold;
        }
        .status-pending {
            color: #f39c12;
            font-weight: bold;
        }
        .status-failed {
            color: #e74c3c;
            font-weight: bold;
        }
        .refresh-btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        .refresh-btn:hover {
            background: #2980b9;
        }
        .timestamp {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .connection-info {
            background: #1abc9c;
            color: white;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🗄️ Odin-AI 데이터베이스 실시간 뷰어</h1>

        <div class="connection-info">
            <strong>📊 연결 정보:</strong> {{ db_info }} |
            <strong>🕐 최종 업데이트:</strong> {{ current_time }} |
            <button class="refresh-btn" onclick="location.reload()">🔄 새로고침</button>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ stats.bid_announcements }}</div>
                <div class="stat-label">📋 입찰공고</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.bid_documents }}</div>
                <div class="stat-label">📄 입찰문서</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.collection_logs }}</div>
                <div class="stat-label">📊 수집로그</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.total_records }}</div>
                <div class="stat-label">📈 전체 레코드</div>
            </div>
        </div>

        <h2>📋 입찰공고 (BID_ANNOUNCEMENTS)</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>공고번호</th>
                    <th>공고명</th>
                    <th>기관명</th>
                    <th>업종</th>
                    <th>생성일시</th>
                </tr>
            </thead>
            <tbody>
                {% for bid in bids %}
                <tr>
                    <td>{{ bid[0] }}</td>
                    <td><strong>{{ bid[1] }}</strong></td>
                    <td>{{ bid[2][:60] }}{% if bid[2]|length > 60 %}...{% endif %}</td>
                    <td>{{ bid[3] or '미지정' }}</td>
                    <td>{{ bid[4] or '미지정' }}</td>
                    <td class="timestamp">{{ bid[5] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <h2>📄 입찰문서 (BID_DOCUMENTS)</h2>
        <table>
            <thead>
                <tr>
                    <th>문서ID</th>
                    <th>공고번호</th>
                    <th>파일명</th>
                    <th>파일타입</th>
                    <th>다운로드 상태</th>
                    <th>처리 상태</th>
                    <th>생성일시</th>
                </tr>
            </thead>
            <tbody>
                {% for doc in docs %}
                <tr>
                    <td>{{ doc[0] }}</td>
                    <td>{{ doc[1] }}</td>
                    <td>{{ doc[2] }}</td>
                    <td><span style="background: #e8f4fd; padding: 2px 8px; border-radius: 15px;">{{ doc[3] }}</span></td>
                    <td><span class="status-{{ doc[4] }}">{{ doc[4] }}</span></td>
                    <td><span class="status-{{ doc[5] }}">{{ doc[5] }}</span></td>
                    <td class="timestamp">{{ doc[6] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <h2>📊 수집로그 (COLLECTION_LOGS)</h2>
        <table>
            <thead>
                <tr>
                    <th>로그ID</th>
                    <th>수집타입</th>
                    <th>상태</th>
                    <th>총 발견</th>
                    <th>신규 항목</th>
                    <th>실행시간</th>
                    <th>비고</th>
                </tr>
            </thead>
            <tbody>
                {% for log in logs %}
                <tr>
                    <td>{{ log[0] }}</td>
                    <td><strong>{{ log[1] }}</strong></td>
                    <td><span class="status-{{ log[2] }}">{{ log[2] }}</span></td>
                    <td>{{ log[3] or 0 }}건</td>
                    <td>{{ log[4] or 0 }}건</td>
                    <td class="timestamp">{{ log[5] }}</td>
                    <td>{{ log[6] or '없음' }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <h2>📈 전체 테이블 현황</h2>
        <table>
            <thead>
                <tr>
                    <th>테이블명</th>
                    <th>한글명</th>
                    <th>레코드 수</th>
                    <th>상태</th>
                </tr>
            </thead>
            <tbody>
                {% for table in all_tables %}
                <tr>
                    <td><code>{{ table[0] }}</code></td>
                    <td>{{ table[1] }}</td>
                    <td><strong>{{ table[2] }}건</strong></td>
                    <td>
                        {% if table[2] > 0 %}
                            <span style="color: #27ae60;">✅ 데이터 있음</span>
                        {% else %}
                            <span style="color: #95a5a6;">⚪ 빈 테이블</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <script>
        // 5초마다 자동 새로고침 (선택사항)
        // setInterval(function() { location.reload(); }, 5000);

        console.log('🗄️ Odin-AI 데이터베이스 뷰어 로드 완료');
        console.log('📊 실시간 데이터를 확인하고 있습니다.');
    </script>
</body>
</html>
"""

def format_datetime(dt):
    if dt is None:
        return 'NULL'
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def get_database_data():
    """데이터베이스에서 모든 데이터 조회"""
    try:
        conn = psycopg2.connect(settings.database_url)
        cur = conn.cursor()

        # 입찰공고 조회
        cur.execute('''
            SELECT id, bid_notice_no, bid_notice_name, notice_inst_name,
                   industry_type, created_at
            FROM bid_announcements
            ORDER BY created_at DESC
        ''')
        bids = cur.fetchall()
        bids = [(b[0], b[1], b[2], b[3], b[4], format_datetime(b[5])) for b in bids]

        # 입찰문서 조회
        cur.execute('''
            SELECT bd.id, ba.bid_notice_no, bd.file_name, bd.file_type,
                   bd.download_status, bd.processing_status, bd.created_at
            FROM bid_documents bd
            LEFT JOIN bid_announcements ba ON bd.bid_announcement_id = ba.id
            ORDER BY bd.created_at DESC
        ''')
        docs = cur.fetchall()
        docs = [(d[0], d[1], d[2], d[3], d[4], d[5], format_datetime(d[6])) for d in docs]

        # 수집로그 조회
        cur.execute('''
            SELECT id, collection_type, status, total_found, new_items,
                   collection_date, notes
            FROM collection_logs
            ORDER BY collection_date DESC
        ''')
        logs = cur.fetchall()
        logs = [(l[0], l[1], l[2], l[3], l[4], format_datetime(l[5]), l[6]) for l in logs]

        # 전체 테이블 통계
        tables_info = [
            ('bid_announcements', '입찰공고'),
            ('bid_documents', '입찰문서'),
            ('bid_participants', '입찰참가자'),
            ('bid_results', '입찰결과'),
            ('collection_logs', '수집로그'),
            ('contract_info', '계약정보'),
            ('document_chunks', '문서청크'),
            ('document_processing_queue', '문서처리큐'),
            ('document_search_histories', '문서검색이력'),
            ('documents', '일반문서'),
            ('user_api_keys', '사용자API키'),
            ('user_bid_bookmarks', '사용자북마크'),
            ('user_notifications', '사용자알림'),
            ('user_preferences', '사용자설정'),
            ('user_search_histories', '사용자검색이력'),
            ('users', '사용자')
        ]

        all_tables = []
        total_records = 0
        for table_name, korean_name in tables_info:
            cur.execute(f'SELECT COUNT(*) FROM {table_name}')
            count = cur.fetchone()[0]
            total_records += count
            all_tables.append((table_name, korean_name, count))

        # 통계 계산
        stats = {
            'bid_announcements': len(bids),
            'bid_documents': len(docs),
            'collection_logs': len(logs),
            'total_records': total_records
        }

        cur.close()
        conn.close()

        return {
            'bids': bids,
            'docs': docs,
            'logs': logs,
            'all_tables': all_tables,
            'stats': stats
        }

    except Exception as e:
        print(f"데이터베이스 오류: {e}")
        return {
            'bids': [],
            'docs': [],
            'logs': [],
            'all_tables': [],
            'stats': {'bid_announcements': 0, 'bid_documents': 0, 'collection_logs': 0, 'total_records': 0}
        }

@app.route('/')
def index():
    """메인 페이지 - 데이터베이스 전체 뷰"""
    data = get_database_data()

    db_info = settings.database_url.split('@')[1] if '@' in settings.database_url else 'localhost'
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return render_template_string(
        HTML_TEMPLATE,
        bids=data['bids'],
        docs=data['docs'],
        logs=data['logs'],
        all_tables=data['all_tables'],
        stats=data['stats'],
        db_info=db_info,
        current_time=current_time
    )

@app.route('/api/stats')
def api_stats():
    """API 엔드포인트 - 통계 데이터만 JSON으로 반환"""
    data = get_database_data()
    return jsonify(data['stats'])

@app.route('/api/tables/<table_name>')
def api_table(table_name):
    """API 엔드포인트 - 특정 테이블 데이터 JSON으로 반환"""
    try:
        conn = psycopg2.connect(settings.database_url)
        cur = conn.cursor()
        cur.execute(f'SELECT * FROM {table_name} LIMIT 100')
        rows = cur.fetchall()

        # 컬럼 정보 가져오기
        cur.execute(f'''
            SELECT column_name FROM information_schema.columns
            WHERE table_name = '{table_name}' ORDER BY ordinal_position
        ''')
        columns = [row[0] for row in cur.fetchall()]

        cur.close()
        conn.close()

        return jsonify({
            'table_name': table_name,
            'columns': columns,
            'rows': rows,
            'count': len(rows)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print('🌐 Odin-AI 데이터베이스 웹 뷰어 시작')
    print('📊 브라우저에서 확인: http://localhost:8002')
    print('🔄 실시간 데이터베이스 내용을 확인할 수 있습니다.')
    print('⏹️ 종료하려면 Ctrl+C를 누르세요.')

    app.run(host='0.0.0.0', port=8002, debug=True)