"""
이메일 템플릿 모음
HTML 이메일 템플릿을 관리
"""

# 기본 레이아웃 템플릿
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject }}</title>
    <style>
        body {
            font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 0;
        }
        .wrapper {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: bold;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        .content {
            padding: 30px 20px;
        }
        .section {
            margin-bottom: 30px;
        }
        .section-title {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #667eea;
        }
        .bid-card {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 4px;
        }
        .bid-title {
            font-size: 16px;
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
        }
        .bid-info {
            font-size: 14px;
            color: #666;
            margin: 5px 0;
        }
        .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 5px;
        }
        .badge-urgent {
            background: #dc3545;
            color: white;
        }
        .badge-new {
            background: #28a745;
            color: white;
        }
        .badge-hot {
            background: #ffc107;
            color: #333;
        }
        .btn {
            display: inline-block;
            padding: 12px 24px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: bold;
            margin: 10px 5px;
        }
        .btn:hover {
            background: #5a67d8;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin: 20px 0;
        }
        .stat-box {
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .stat-number {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #666;
        }
        .footer a {
            color: #667eea;
            text-decoration: none;
        }
        .unsubscribe {
            margin-top: 15px;
            font-size: 11px;
        }
        @media only screen and (max-width: 600px) {
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="wrapper">
        {{ content }}
    </div>
</body>
</html>
"""

# 일일 요약 템플릿
DAILY_SUMMARY_TEMPLATE = """
<div class="header">
    <h1>📊 Odin-AI 일일 요약</h1>
    <p>{{ user_name }}님을 위한 {{ date }} 입찰 정보</p>
</div>

<div class="content">
    <div class="section">
        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-number">{{ new_bids }}</div>
                <div class="stat-label">신규 공고</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{{ deadline_soon }}</div>
                <div class="stat-label">마감 임박</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{{ matched_count }}</div>
                <div class="stat-label">키워드 매칭</div>
            </div>
        </div>
    </div>

    {% if keyword_bids %}
    <div class="section">
        <h2 class="section-title">🎯 키워드 매칭 입찰</h2>
        {% for item in keyword_bids %}
        <div class="bid-card">
            <span class="badge badge-hot">{{ item.keyword }}</span>
            <div class="bid-title">{{ item.title }}</div>
            <div class="bid-info">🏢 {{ item.organization }}</div>
            <div class="bid-info">⏰ 마감: {{ item.deadline }}</div>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    {% if recommended_bids %}
    <div class="section">
        <h2 class="section-title">⭐ 추천 입찰</h2>
        {% for bid in recommended_bids %}
        <div class="bid-card">
            {% if bid.is_urgent %}<span class="badge badge-urgent">긴급</span>{% endif %}
            <div class="bid-title">{{ bid.title }}</div>
            <div class="bid-info">🏢 {{ bid.organization }}</div>
            <div class="bid-info">💰 예정가격: {{ bid.price }}원</div>
            <div class="bid-info">⏰ 마감: {{ bid.deadline }}</div>
            <div class="bid-info">🎯 예상 성공률: {{ bid.success_rate }}%</div>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <div style="text-align: center; margin: 30px 0;">
        <a href="{{ dashboard_url }}" class="btn">대시보드에서 더 보기</a>
    </div>
</div>

<div class="footer">
    <p>이 이메일은 Odin-AI에서 발송되었습니다.</p>
    <p><a href="{{ settings_url }}">알림 설정 변경</a></p>
    <div class="unsubscribe">
        <a href="{{ unsubscribe_url }}">구독 취소</a>
    </div>
</div>
"""

# 실시간 알림 템플릿
REALTIME_ALERT_TEMPLATE = """
<div class="header">
    <h1>🔔 실시간 입찰 알림</h1>
    <p>{{ user_name }}님의 키워드와 일치하는 새로운 입찰이 등록되었습니다</p>
</div>

<div class="content">
    <div class="section">
        <h2 class="section-title">🆕 방금 등록된 입찰</h2>
        {% for bid in bids %}
        <div class="bid-card">
            <span class="badge badge-new">NEW</span>
            <div class="bid-title">{{ bid.title }}</div>
            <div class="bid-info">🏢 {{ bid.organization }}</div>
            <div class="bid-info">💰 예정가격: {{ bid.amount }}원</div>
            <div class="bid-info">⏰ 마감: {{ bid.deadline }}</div>
            <div style="margin-top: 10px;">
                <a href="{{ bid.url }}" class="btn" style="padding: 8px 16px; font-size: 14px;">
                    상세보기
                </a>
            </div>
        </div>
        {% endfor %}
    </div>

    <div style="text-align: center; margin: 30px 0;">
        <a href="{{ dashboard_url }}" class="btn">대시보드로 이동</a>
    </div>
</div>

<div class="footer">
    <p>실시간 알림을 받지 않으시려면 <a href="{{ settings_url }}">알림 설정</a>을 변경해주세요.</p>
</div>
"""

# 마감 임박 알림 템플릿
DEADLINE_ALERT_TEMPLATE = """
<div class="header">
    <h1>⏰ 마감 임박 알림</h1>
    <p>{{ user_name }}님이 관심있어 하시는 입찰이 곧 마감됩니다</p>
</div>

<div class="content">
    <div class="section">
        <h2 class="section-title">🚨 24시간 내 마감</h2>
        {% for bid in bids %}
        <div class="bid-card">
            <span class="badge badge-urgent">{{ bid.remaining_hours }}시간 남음</span>
            <div class="bid-title">{{ bid.title }}</div>
            <div class="bid-info">🏢 {{ bid.organization }}</div>
            <div class="bid-info">⏰ 마감: {{ bid.deadline }}</div>
            <div style="margin-top: 10px;">
                <a href="{{ bid.url }}" class="btn" style="background: #dc3545;">
                    지금 확인하기
                </a>
            </div>
        </div>
        {% endfor %}
    </div>

    <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
        <strong>⚠️ 주의사항</strong><br>
        입찰 마감 시간을 꼭 확인하시고, 여유있게 제출하시기 바랍니다.
    </div>
</div>

<div class="footer">
    <p>마감 알림 설정은 <a href="{{ settings_url }}">여기</a>에서 변경할 수 있습니다.</p>
</div>
"""

# 주간 보고서 템플릿
WEEKLY_REPORT_TEMPLATE = """
<div class="header">
    <h1>📈 주간 입찰 보고서</h1>
    <p>{{ user_name }}님의 {{ start_date }} ~ {{ end_date }} 입찰 시장 분석</p>
</div>

<div class="content">
    <div class="section">
        <h2 class="section-title">📊 주간 통계</h2>
        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-number">{{ total_bids }}</div>
                <div class="stat-label">전체 공고</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{{ matched_bids }}</div>
                <div class="stat-label">매칭 공고</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{{ avg_competition }}:1</div>
                <div class="stat-label">평균 경쟁률</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2 class="section-title">💰 금액대별 분포</h2>
        <table style="width: 100%; border-collapse: collapse;">
            {% for range, count in price_ranges.items() %}
            <tr style="border-bottom: 1px solid #dee2e6;">
                <td style="padding: 10px;">{{ range }}</td>
                <td style="padding: 10px; text-align: right; font-weight: bold;">{{ count }}건</td>
            </tr>
            {% endfor %}
        </table>
    </div>

    {% if top_organizations %}
    <div class="section">
        <h2 class="section-title">🏢 주요 발주기관</h2>
        <ol>
            {% for org in top_organizations %}
            <li style="margin: 10px 0;">
                <strong>{{ org.name }}</strong> - {{ org.count }}건
            </li>
            {% endfor %}
        </ol>
    </div>
    {% endif %}

    {% if insights %}
    <div class="section">
        <h2 class="section-title">💡 인사이트</h2>
        <ul>
            {% for insight in insights %}
            <li style="margin: 10px 0;">{{ insight }}</li>
            {% endfor %}
        </ul>
    </div>
    {% endif %}

    <div style="text-align: center; margin: 30px 0;">
        <a href="{{ report_url }}" class="btn">상세 보고서 보기</a>
    </div>
</div>

<div class="footer">
    <p>주간 보고서는 매주 월요일 오전에 발송됩니다.</p>
    <p><a href="{{ settings_url }}">보고서 설정 변경</a></p>
</div>
"""

# 회원가입 환영 이메일
WELCOME_EMAIL_TEMPLATE = """
<div class="header">
    <h1>🎉 Odin-AI에 오신 것을 환영합니다!</h1>
    <p>{{ user_name }}님, 가입을 축하드립니다</p>
</div>

<div class="content">
    <div class="section">
        <p>안녕하세요 {{ user_name }}님,</p>
        <p>Odin-AI 가입을 진심으로 환영합니다! 이제 한국 공공조달 시장의 모든 기회를 놓치지 마세요.</p>
    </div>

    <div class="section">
        <h2 class="section-title">🚀 시작하기</h2>
        <ol style="line-height: 2;">
            <li><strong>키워드 설정</strong>: 관심있는 분야의 키워드를 등록하세요</li>
            <li><strong>알림 설정</strong>: 원하는 시간에 알림을 받도록 설정하세요</li>
            <li><strong>대시보드 확인</strong>: 매칭된 입찰을 실시간으로 확인하세요</li>
            <li><strong>AI 분석 활용</strong>: 성공 확률과 추천을 참고하세요</li>
        </ol>
    </div>

    <div style="text-align: center; margin: 30px 0;">
        <a href="{{ getting_started_url }}" class="btn">지금 시작하기</a>
    </div>

    <div class="section">
        <h2 class="section-title">💡 도움이 필요하신가요?</h2>
        <p>궁금한 점이 있으시면 언제든지 문의해주세요:</p>
        <ul>
            <li>📧 이메일: support@odin-ai.kr</li>
            <li>📱 전화: 02-1234-5678</li>
            <li>📖 <a href="{{ help_url }}">도움말 센터</a></li>
        </ul>
    </div>
</div>

<div class="footer">
    <p>Odin-AI와 함께 성공적인 입찰을 기원합니다!</p>
</div>
"""