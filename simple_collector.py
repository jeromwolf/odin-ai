#!/usr/bin/env python3
"""
간단한 API 데이터 수집 스크립트
오늘 날짜의 입찰 공고를 수집하여 DB에 저장
"""
import os
import sys
import requests
import psycopg2
from datetime import datetime, timedelta
import urllib.parse
from xml.etree import ElementTree

# DB 연결
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db')
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# API 설정
API_KEY = "IuRNRNzuwSydSl2igB5vz6BgZqyM5sKRqhBWRrbiqYjdQIBjL1aNL0PmIH6aQRJo4CJ5hs7vsOGG1egqHpEFCA=="
BASE_URL = "https://apis.data.go.kr/1230000/BidPublicInfoService04"

def fetch_data():
    """API에서 오늘 날짜 데이터 수집"""
    today = datetime.now()
    start_date = today.strftime("%Y%m%d0000")
    end_date = (today + timedelta(days=7)).strftime("%Y%m%d2359")

    print(f"수집 기간: {start_date} ~ {end_date}")

    url = f"{BASE_URL}/getBidPblancListEvaluationIndstrytyMaterial"
    params = {
        'serviceKey': API_KEY,
        'numOfRows': 100,
        'pageNo': 1,
        'inqryDiv': '1',
        'inqryBgnDt': start_date,
        'inqryEndDt': end_date,
        'type': 'json'
    }

    try:
        # SSL 검증 비활성화 (개발 환경용)
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        response = requests.get(url, params=params, timeout=30, verify=False)
        response.raise_for_status()

        data = response.json()
        items = data.get('response', {}).get('body', {}).get('items', [])

        if not items:
            print("수집된 데이터가 없습니다.")
            return 0

        count = 0
        for item in items:
            # DB에 저장
            cursor.execute("""
                INSERT INTO bid_announcements (
                    bid_notice_no,
                    bid_notice_ord,
                    title,
                    organization_code,
                    organization_name,
                    department_name,
                    announcement_date,
                    bid_start_date,
                    bid_end_date,
                    opening_date,
                    estimated_price,
                    assigned_budget,
                    bid_method,
                    contract_method,
                    officer_name,
                    officer_phone,
                    officer_email,
                    detail_page_url,
                    status,
                    created_at,
                    updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) ON CONFLICT (bid_notice_no) DO UPDATE SET
                    title = EXCLUDED.title,
                    bid_end_date = EXCLUDED.bid_end_date,
                    detail_page_url = EXCLUDED.detail_page_url,
                    updated_at = NOW()
            """, (
                item.get('bidNtceNo'),
                item.get('bidNtceOrd', '00'),
                item.get('bidNtceNm', ''),
                item.get('ntceInsttCd'),
                item.get('ntceInsttNm', ''),
                item.get('dminsttNm', ''),
                datetime.strptime(item.get('bidNtceDt', '2025-01-01'), '%Y-%m-%d') if item.get('bidNtceDt') else None,
                datetime.strptime(item.get('bidBeginDt', '2025-01-01'), '%Y-%m-%d %H:%M:%S') if item.get('bidBeginDt') else None,
                datetime.strptime(item.get('bidClseDt', '2025-01-01'), '%Y-%m-%d %H:%M:%S') if item.get('bidClseDt') else None,
                datetime.strptime(item.get('opengDt', '2025-01-01'), '%Y-%m-%d %H:%M:%S') if item.get('opengDt') else None,
                int(item.get('presmptPrce', 0)) if item.get('presmptPrce') else None,
                int(item.get('asignBdgtAmt', 0)) if item.get('asignBdgtAmt') else None,
                item.get('bidMethdNm'),
                item.get('cntrctCnclsMthdNm'),
                item.get('ntceInsttOfclNm'),
                item.get('ntceInsttOfclTelNo'),
                item.get('ntceInsttOfclEmailAdrs'),
                item.get('bidNtceDtlUrl', ''),
                'active' if datetime.strptime(item.get('bidClseDt', '2025-01-01'), '%Y-%m-%d %H:%M:%S') >= datetime.now() else 'closed' if item.get('bidClseDt') else 'active',
                datetime.now(),
                datetime.now()
            ))
            count += 1
            print(f"저장: {item.get('bidNtceNm', 'Unknown')[:50]}...")

        conn.commit()
        print(f"\n총 {count}개 공고 저장 완료!")
        return count

    except Exception as e:
        print(f"오류 발생: {e}")
        conn.rollback()
        return 0

if __name__ == "__main__":
    try:
        count = fetch_data()
        print(f"\n✅ 데이터 수집 완료: {count}개")
    except Exception as e:
        print(f"❌ 실행 실패: {e}")
    finally:
        cursor.close()
        conn.close()