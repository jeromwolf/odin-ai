#!/usr/bin/env python
"""
현재 날짜 기준 올바른 데이터 수집
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from loguru import logger
import aiohttp

# 공공데이터포털 API 설정
API_KEY = "6h2l2VPWSfA2vG3xSFr7gf6iwaZT2dmzcoCOzklLnOIJY6sw17lrwHNQ3WxPdKMDIN%2FmMlv2vBTWTIzBDPKVdw%3D%3D"
BASE_URL = "http://apis.data.go.kr/1230000"


async def collect_current_bid_data():
    """현재 날짜 기준 입찰 공고 데이터 수집"""

    # 현재 날짜 기준으로 검색 기간 설정
    today = datetime.now()

    # 지난 7일부터 앞으로 30일까지 (실제 활성 입찰 기간)
    start_date = today - timedelta(days=7)
    end_date = today + timedelta(days=30)

    start_str = start_date.strftime("%Y%m%d0000")
    end_str = end_date.strftime("%Y%m%d2359")

    url = (
        f"{BASE_URL}/ad/BidPublicInfoService/getBidPblancListInfoCnstwk?"
        f"serviceKey={API_KEY}&"
        f"numOfRows=100&"
        f"pageNo=1&"
        f"inqryDiv=1&"
        f"inqryBgnDt={start_str}&"
        f"inqryEndDt={end_str}&"
        f"type=json"
    )

    logger.info("📅 현재 날짜 기준 API 데이터 수집 시작...")
    logger.info(f"🗓️ 검색 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    logger.info(f"🔗 URL: {url}")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    text = await response.text()

                    try:
                        import json
                        data = json.loads(text)
                    except json.JSONDecodeError:
                        logger.error("❌ JSON 파싱 실패")
                        logger.info(f"응답 샘플: {text[:200]}")
                        return False

                    if 'response' in data and 'body' in data['response']:
                        items = data['response']['body'].get('items', [])
                        total = data['response']['body'].get('totalCount', 0)

                        logger.info(f"✅ 총 {total}개 중 {len(items)}개 수집")

                        # 날짜 정보 확인
                        for i, item in enumerate(items[:5]):
                            notice_no = item.get('bidNtceNo')
                            notice_nm = item.get('bidNtceNm', '')[:30]
                            notice_dt = item.get('bidNtceDt', '')
                            close_dt = item.get('bidClseDt', '')

                            logger.info(f"  {i+1}. {notice_no}")
                            logger.info(f"     제목: {notice_nm}...")
                            logger.info(f"     공고일: {notice_dt}")
                            logger.info(f"     마감일: {close_dt}")
                            logger.info("")

                        # 데이터베이스에 저장
                        await save_to_database(items)
                        return True
                    else:
                        logger.error("❌ API 응답 형식 오류")
                        return False
                else:
                    logger.error(f"❌ API 오류: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"❌ 수집 실패: {e}")
            return False


async def save_to_database(items):
    """데이터베이스 저장"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).parent / 'src'))

    from src.database.models import BidAnnouncement, BidDocument

    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://blockmeta@localhost:5432/odin_db")

    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        saved = 0
        for item in items:
            # 중복 체크
            existing = session.query(BidAnnouncement).filter(
                BidAnnouncement.bid_notice_no == item.get('bidNtceNo')
            ).first()

            if not existing:
                # 날짜 필드 처리
                def parse_date(date_str):
                    if date_str and date_str.strip():
                        return date_str
                    return None

                announcement = BidAnnouncement(
                    bid_notice_no=item.get('bidNtceNo'),
                    title=item.get('bidNtceNm'),
                    organization_name=item.get('ntceInsttNm'),
                    bid_method=item.get('bidMethdNm'),
                    estimated_price=item.get('presmptPrc'),
                    announcement_date=parse_date(item.get('bidNtceDt')),
                    bid_start_date=parse_date(item.get('bidBeginDt')),
                    bid_end_date=parse_date(item.get('bidClseDt')),
                    opening_date=parse_date(item.get('opengDt')),
                    collection_status='pending',
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(announcement)

                # 문서 정보도 추가
                if item.get('ntceSpecDocUrl1'):
                    document = BidDocument(
                        bid_notice_no=item.get('bidNtceNo'),
                        document_type='specification',
                        file_name=item.get('ntceSpecFileNm1'),
                        file_extension='hwp',
                        download_url=item.get('ntceSpecDocUrl1'),
                        download_status='pending',
                        processing_status='pending'
                    )
                    session.add(document)

                saved += 1

        session.commit()
        logger.info(f"✅ {saved}개 새 공고 저장 완료")

        # 통계 출력
        total_announcements = session.query(BidAnnouncement).count()
        total_documents = session.query(BidDocument).count()

        logger.info(f"📊 DB 현황: 공고 {total_announcements}개, 문서 {total_documents}개")

    except Exception as e:
        logger.error(f"❌ DB 저장 실패: {e}")
        session.rollback()
    finally:
        session.close()


async def main():
    """메인 실행"""
    logger.info("=" * 60)
    logger.info("📅 올바른 날짜로 데이터 재수집")
    logger.info("=" * 60)

    success = await collect_current_bid_data()

    if success:
        logger.info("✅ 현재 날짜 기준 데이터 수집 완료!")
    else:
        logger.error("❌ 데이터 수집 실패")


if __name__ == "__main__":
    asyncio.run(main())