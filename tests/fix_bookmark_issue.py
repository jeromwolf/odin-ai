#!/usr/bin/env python3
"""북마크 문제 해결 방안"""

import psycopg2
from psycopg2 import sql

def option1_add_test_data():
    """옵션 1: 테스트용 공고 데이터 추가"""
    conn = psycopg2.connect("postgresql://blockmeta@localhost:5432/odin_db")
    cur = conn.cursor()

    # 테스트용 공고 추가
    cur.execute("""
        INSERT INTO bid_announcements (bid_notice_no, title, organization, announcement_date)
        VALUES ('TEST-BOOKMARK-001', '테스트 공고', '테스트 기관', CURRENT_TIMESTAMP)
        ON CONFLICT (bid_notice_no) DO NOTHING;
    """)

    conn.commit()
    print("✅ 테스트용 공고 추가 완료")
    cur.close()
    conn.close()

def option2_use_real_data():
    """옵션 2: 실제 공고 번호 사용"""
    print("""
    tests/execute_350_tests.py 수정:

    변경 전:
    "bid_notice_no": "20250925-00001"

    변경 후:
    "bid_notice_no": "R25BK01070736"  # 실제 DB에 있는 공고
    """)

def option3_simplify_bookmark():
    """옵션 3: 북마크 테이블 간소화 (FK 제거)"""
    print("""
    ⚠️ 비추천: FK 제약은 데이터 무결성 보장

    만약 정말 필요하다면:
    ALTER TABLE user_bookmarks
    DROP CONSTRAINT IF EXISTS user_bookmarks_bid_notice_no_fkey;

    하지만 이렇게 하면:
    - 존재하지 않는 공고도 북마크 가능 (데이터 오염)
    - 공고 삭제시 북마크 정리 안됨
    """)

print("=" * 50)
print("북마크 기능 해결 방안")
print("=" * 50)
print("\n🔧 3가지 옵션:\n")
print("1. 테스트용 데이터 추가 (추천)")
print("2. 실제 공고 번호 사용 (간단)")
print("3. FK 제약 제거 (비추천)")
print("\n어떤 방법을 선택하시겠습니까?")
print("\n실행: python3 tests/fix_bookmark_issue.py")

# 옵션 1 실행 (가장 안전)
if input("\n테스트 데이터를 추가하시겠습니까? (y/n): ").lower() == 'y':
    option1_add_test_data()
else:
    option2_use_real_data()