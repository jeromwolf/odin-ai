#!/usr/bin/env python
"""
알림 매칭 시스템 테스트 - 1개만
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env 파일 로드")
except:
    pass

from batch.modules.notification_matcher import NotificationMatcher

# 환경변수 확인
print("\n📧 SMTP 설정 확인:")
print(f"  EMAIL_HOST: {os.getenv('EMAIL_HOST')}")
print(f"  EMAIL_PORT: {os.getenv('EMAIL_PORT')}")
print(f"  EMAIL_USERNAME: {os.getenv('EMAIL_USERNAME')}")
print(f"  EMAIL_PASSWORD: {'*' * len(os.getenv('EMAIL_PASSWORD', ''))}")

# DB URL
db_url = os.getenv('DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db')

print("\n" + "="*60)
print("🔔 알림 매칭 시스템 테스트 - 최근 1시간 데이터만")
print("="*60)

# NotificationMatcher 생성
matcher = NotificationMatcher(db_url)

# 최근 1시간 데이터로 테스트 (1개만)
result = matcher.process_new_bids(since_hours=240)

print("\n" + "="*60)
print("✅ 테스트 완료")
print("="*60)
print(f"처리된 입찰: {result['processed_bids']}개")
print(f"생성된 알림: {result['notifications_created']}개")
print(f"발송된 이메일: {result['emails_sent']}개")
print("="*60)

if result['emails_sent'] > 0:
    print(f"\n📧 이메일이 {os.getenv('EMAIL_USERNAME')}로 발송되었습니다!")
    print("메일함을 확인해주세요.")
else:
    print("\n⚠️ 이메일 발송 실패 - 로그를 확인하세요")
