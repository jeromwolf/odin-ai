#!/usr/bin/env python
"""
낙찰정보 수집 모듈
조달청 나라장터 낙찰정보서비스 API에서 낙찰 데이터를 수집하고
기존 bid_announcements 레코드를 UPDATE
"""

import requests
import urllib.parse
import time
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.models import BidAnnouncement


# 낙찰정보서비스 API 엔드포인트 (4개 카테고리)
AWARD_ENDPOINTS = {
    "공사": "getScsbidListSttusCnstwk",
    "물품": "getScsbidListSttusThngPPSSrch",
    "용역": "getScsbidListSttusServcPPSSrch",
    "외자": "getScsbidListSttusFrgcpt",
}

AWARD_BASE_URL = "https://apis.data.go.kr/1230000/as/ScsbidInfoService"


class AwardCollector:
    """낙찰정보 수집기"""

    def __init__(self, db_url=None):
        """초기화

        Args:
            db_url: 데이터베이스 URL. None이면 환경변수에서 읽음
        """
        self.db_url = db_url or os.getenv('DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db')
        self.engine = create_engine(self.db_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # API 설정 (공고 수집과 동일한 API 키 사용)
        api_key_encoded = os.getenv('BID_API_KEY')
        if not api_key_encoded:
            raise ValueError("BID_API_KEY 환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
        self.api_key = urllib.parse.unquote(api_key_encoded)

    def collect_awards(self, start_date=None, end_date=None, num_of_rows=100, max_pages=None, categories=None):
        """날짜 범위로 낙찰정보 수집 - 4개 카테고리

        Args:
            start_date: 시작일 (None이면 30일 전)
            end_date: 종료일 (None이면 오늘)
            num_of_rows: 페이지당 조회 건수
            max_pages: 최대 페이지 수 (None이면 모두)
            categories: 수집할 카테고리 리스트 (None이면 전체 4개)

        Returns:
            dict: 수집 결과 통계
        """
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        start_str = start_date.strftime('%Y%m%d0000')
        end_str = end_date.strftime('%Y%m%d2359')

        logger.info(f"🏆 낙찰정보 수집 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

        target_categories = categories or list(AWARD_ENDPOINTS.keys())

        total_fetched = 0
        total_updated = 0
        total_skipped = 0
        total_count_all = 0

        try:
            for category, endpoint_name in AWARD_ENDPOINTS.items():
                if category not in target_categories:
                    continue

                api_url = f"{AWARD_BASE_URL}/{endpoint_name}"
                logger.info(f"📂 [{category}] 낙찰정보 수집 시작...")

                page_no = 1
                cat_fetched = 0
                cat_total = 0

                while True:
                    params = {
                        'serviceKey': self.api_key,
                        'pageNo': str(page_no),
                        'numOfRows': str(num_of_rows),
                        'type': 'json',
                        'inqryDiv': '1',
                        'inqryBgnDt': start_str,
                        'inqryEndDt': end_str
                    }

                    logger.info(f"🌐 [{category}] 낙찰정보 API 호출 중... (페이지 {page_no})")

                    try:
                        response = requests.get(api_url, params=params, timeout=30)
                        response.raise_for_status()
                        data = response.json()
                    except requests.exceptions.RequestException as e:
                        logger.error(f"[{category}] 페이지 {page_no}: API 호출 실패 - {e}")
                        break

                    if 'response' in data and 'body' in data['response']:
                        items = data['response']['body'].get('items', [])
                        cat_total = data['response']['body'].get('totalCount', 0)

                        if not items:
                            logger.info(f"📋 [{category}] 페이지 {page_no}: 더 이상 데이터 없음")
                            break

                        logger.info(f"📊 [{category}] 페이지 {page_no}: {len(items)}개 조회 (전체 {cat_total}개)")

                        updated, skipped = self._update_award_info(items, category)
                        cat_fetched += len(items)
                        total_updated += updated
                        total_skipped += skipped

                        if cat_fetched >= cat_total:
                            logger.info(f"✅ [{category}] 모든 낙찰정보 수집 완료")
                            break

                        if max_pages and page_no >= max_pages:
                            logger.info(f"⚠️ [{category}] 최대 페이지 수({max_pages}) 도달")
                            break

                        page_no += 1
                        time.sleep(0.5)

                    else:
                        logger.error(f"[{category}] 페이지 {page_no}: API 응답 형식 오류")
                        break

                total_fetched += cat_fetched
                total_count_all += cat_total
                logger.info(f"✅ [{category}] 완료: {cat_total}개 중 {cat_fetched}개 수집")

            logger.info(f"🏆 전체 낙찰정보 수집 완료: {total_fetched}개 수집, {total_updated}개 업데이트, {total_skipped}개 스킵(미매칭)")

            return {
                'total_api': total_count_all,
                'fetched': total_fetched,
                'updated': total_updated,
                'skipped': total_skipped,
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"낙찰정보 수집 실패: {e}")
            return {
                'total_api': total_count_all,
                'fetched': total_fetched,
                'updated': total_updated,
                'skipped': total_skipped,
                'status': 'error',
                'message': str(e)
            }
        finally:
            self.session.close()

    def _update_award_info(self, items, category):
        """기존 bid_announcements 레코드에 낙찰정보 UPDATE

        Args:
            items: API 응답 아이템 리스트
            category: 입찰 카테고리

        Returns:
            tuple: (업데이트 건수, 스킵 건수)
        """
        updated_count = 0
        skipped_count = 0

        for item in items:
            try:
                bid_notice_no = item.get('bidNtceNo')
                if not bid_notice_no:
                    continue

                existing = self.session.query(BidAnnouncement).filter_by(
                    bid_notice_no=bid_notice_no
                ).first()

                if existing:
                    existing.winning_company = item.get('bidwinnrNm')
                    existing.winning_bizno = item.get('bidwinnrBizno')
                    existing.winning_price = self._parse_price(item.get('sucsfbidAmt'))
                    existing.winning_rate = self._parse_float(item.get('sucsfbidRate'))
                    existing.bid_participant_count = self._parse_int(item.get('prtcptCnum'))
                    existing.award_date = self._parse_date(item.get('fnlSucsfDate'))
                    existing.award_status = 'awarded'
                    updated_count += 1
                    logger.debug(f"  ✅ 낙찰정보 업데이트: {bid_notice_no} → {item.get('bidwinnrNm')}")
                else:
                    skipped_count += 1
                    logger.debug(f"  ⏭️ 미매칭 (공고 없음): {bid_notice_no}")

            except Exception as e:
                logger.error(f"낙찰정보 업데이트 실패 {item.get('bidNtceNo')}: {e}")

        self.session.commit()
        logger.info(f"💾 낙찰정보 DB 업데이트: {updated_count}건, 스킵: {skipped_count}건")

        return updated_count, skipped_count

    def _parse_date(self, date_str):
        """날짜 문자열 파싱"""
        if not date_str:
            return None
        try:
            if ' ' in date_str:
                return datetime.strptime(date_str.split(' ')[0], '%Y-%m-%d')
            elif '-' in date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            logger.debug(f"날짜 파싱 실패: {date_str}")
        return None

    def _parse_price(self, price_str):
        """가격 문자열 파싱"""
        if not price_str:
            return None
        try:
            return int(float(str(price_str).replace(',', '')))
        except (ValueError, TypeError):
            return None

    def _parse_float(self, value):
        """실수 파싱"""
        if not value:
            return None
        try:
            return float(str(value).replace(',', ''))
        except (ValueError, TypeError):
            return None

    def _parse_int(self, value):
        """정수 파싱"""
        if not value:
            return None
        try:
            return int(float(str(value).replace(',', '')))
        except (ValueError, TypeError):
            return None


if __name__ == '__main__':
    """독립 실행 시 테스트"""
    from dotenv import load_dotenv
    load_dotenv()

    collector = AwardCollector()
    result = collector.collect_awards()
    print(f"\n결과: {result}")
