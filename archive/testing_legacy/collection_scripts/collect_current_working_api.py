#!/usr/bin/env python
"""
성공하는 HTTP API로 현재 데이터 수집
"""

import requests
import json
import urllib.parse
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path.cwd() / 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import BidAnnouncement, BidDocument

def collect_current_api_data():
    """현재 날짜로 API 데이터 수집"""

    print("🔄 성공하는 HTTP API로 현재 데이터 수집")
    print("=" * 60)

    # 올바른 API 키 (디코딩됨)
    api_key_encoded = "6h2l2VPWSfA2vG3xSFr7gf6iwaZT2dmzcoCOzklLnOIJY6sw17lrwHNQ3WxPdKMDIN%2FmMlv2vBTWTIzBDPKVdw%3D%3D"
    api_key = urllib.parse.unquote(api_key_encoded)

    # 현재 날짜 기준 검색 기간
    today = datetime.now()
    start_date = today - timedelta(days=7)  # 7일 전부터
    end_date = today + timedelta(days=30)   # 30일 후까지

    start_str = start_date.strftime('%Y%m%d0000')
    end_str = end_date.strftime('%Y%m%d2359')

    # HTTP URL (성공 확인됨)
    url = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwk"

    params = {
        'serviceKey': api_key,
        'pageNo': '1',
        'numOfRows': '50',  # 더 많이 수집
        'type': 'json',
        'inqryDiv': '1',
        'inqryBgnDt': start_str,
        'inqryEndDt': end_str
    }

    print(f"📅 검색 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    print(f"🔗 URL: {url}")
    print(f"📊 파라미터: numOfRows={params['numOfRows']}")
    print()

    try:
        print("🌐 API 호출 중...")
        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 200:
            text = response.text
            print(f"📊 응답 길이: {len(text)} 바이트")

            try:
                data = json.loads(text)
                print("✅ JSON 파싱 성공")

                if 'response' in data and 'body' in data['response']:
                    body = data['response']['body']

                    if 'items' in body:
                        items = body['items']
                        total_count = body.get('totalCount', 0)

                        print(f"🎉 API 성공: {total_count}개 중 {len(items)}개 수집")

                        if items:
                            # 첫 번째 공고 확인
                            first = items[0]
                            print(f"\n📋 첫 번째 공고:")
                            print(f"  공고번호: {first.get('bidNtceNo', 'N/A')}")
                            print(f"  공고명: {first.get('bidNtceNm', 'N/A')[:50]}...")
                            print(f"  공고일: {first.get('bidNtceDt', 'N/A')}")
                            print(f"  마감일: {first.get('bidClseDt', 'N/A')}")

                            # 날짜 검증
                            bid_date = first.get('bidNtceDt', '')
                            if bid_date:
                                year = bid_date[:4] if len(bid_date) >= 4 else ''
                                if year == '2025':
                                    print(f"✅ 올바른 연도: {year}")
                                else:
                                    print(f"❌ 잘못된 연도: {year}")

                            # 데이터베이스에 저장
                            save_result = save_to_database(items)
                            return save_result
                    else:
                        print("❌ items 없음")
                        print(f"body 내용: {body}")
                else:
                    print("❌ response/body 구조 오류")
                    print(f"응답 구조: {list(data.keys()) if data else 'None'}")

            except json.JSONDecodeError as e:
                print(f"❌ JSON 파싱 실패: {e}")
                print(f"응답 시작부분: {text[:200]}...")

        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            print(f"응답: {response.text[:300]}")

    except Exception as e:
        print(f"❌ 요청 실패: {e}")

    return False

def save_to_database(items):
    """데이터베이스에 저장"""
    print("\n💾 데이터베이스 저장 중...")

    DATABASE_URL = "postgresql://blockmeta@localhost:5432/odin_db"
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        saved_announcements = 0
        saved_documents = 0

        for item in items:
            bid_notice_no = item.get('bidNtceNo')
            if not bid_notice_no:
                continue

            # 공고 저장 (중복 체크)
            existing = session.query(BidAnnouncement).filter(
                BidAnnouncement.bid_notice_no == bid_notice_no
            ).first()

            if not existing:
                # 날짜 파싱 함수
                def parse_date_str(date_str):
                    if date_str and len(date_str) >= 8:
                        try:
                            return datetime.strptime(date_str[:8], '%Y%m%d')
                        except:
                            return None
                    return None

                announcement = BidAnnouncement(
                    bid_notice_no=bid_notice_no,
                    title=item.get('bidNtceNm'),
                    organization_name=item.get('ntceInsttNm'),
                    bid_method=item.get('bidMethdNm'),
                    estimated_price=item.get('presmptPrc'),
                    announcement_date=parse_date_str(item.get('bidNtceDt')),
                    bid_start_date=parse_date_str(item.get('bidBeginDt')),
                    bid_end_date=parse_date_str(item.get('bidClseDt')),
                    opening_date=parse_date_str(item.get('opengDt')),
                    collection_status='collected',
                    created_at=datetime.now()
                )
                session.add(announcement)
                saved_announcements += 1

                # 문서 정보 저장
                doc_urls = [
                    (item.get('stdNtceDocUrl'), item.get('stdNtceDocNm'), 'standard'),
                    (item.get('ntceSpecDocUrl1'), item.get('ntceSpecFileNm1'), 'specification')
                ]

                for doc_url, doc_name, doc_type in doc_urls:
                    if doc_url:
                        document = BidDocument(
                            bid_notice_no=bid_notice_no,
                            document_type=doc_type,
                            file_name=doc_name,
                            file_extension='hwp',
                            download_url=doc_url,
                            download_status='pending',
                            processing_status='pending'
                        )
                        session.add(document)
                        saved_documents += 1

        session.commit()

        print(f"✅ 저장 완료:")
        print(f"  - 새 공고: {saved_announcements}개")
        print(f"  - 새 문서: {saved_documents}개")

        # 전체 통계
        total_announcements = session.query(BidAnnouncement).count()
        total_documents = session.query(BidDocument).count()

        print(f"\n📊 전체 DB 현황:")
        print(f"  - 총 공고: {total_announcements}개")
        print(f"  - 총 문서: {total_documents}개")

        return True

    except Exception as e:
        print(f"❌ DB 저장 실패: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    success = collect_current_api_data()

    if success:
        print(f"\n🎯 성공: 현재 날짜 기준 API 데이터 수집 및 저장 완료")
    else:
        print(f"\n❌ 실패: API 데이터 수집 실패")