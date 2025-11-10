#!/usr/bin/env python
"""
알림 매칭 시스템 직접 테스트
기존 DB 데이터로 알림 매칭 테스트
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from batch.modules.notification_matcher import NotificationMatcher

# DB URL
db_url = os.getenv('DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db')

print("="*60)
print("🔔 알림 매칭 시스템 테스트")
print("="*60)

# NotificationMatcher 생성
matcher = NotificationMatcher(db_url)

# 최근 240시간(10일) 데이터로 테스트
print("\n📊 최근 10일 입찰 데이터로 알림 매칭 테스트...")
result = matcher.process_new_bids(since_hours=240)

print("\n" + "="*60)
print("✅ 테스트 완료")
print("="*60)
print(f"처리된 입찰: {result['processed_bids']}개")
print(f"생성된 알림: {result['notifications_created']}개")
print(f"발송된 이메일: {result['emails_sent']}개")
print("="*60)

if result['emails_sent'] > 0:
    print("\n📧 jeromwolf@gmail.com 메일함을 확인하세요!")
else:
    print("\n💡 매칭되는 입찰이 없거나 SMTP 설정이 필요합니다")
