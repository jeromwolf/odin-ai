#!/usr/bin/env python
"""
API 수집 모듈
공공데이터포털 API에서 입찰공고 데이터를 수집하고 DB에 저장
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

from src.database.models import BidAnnouncement, BidDocument


# 공공데이터포털 입찰공고 API 엔드포인트 (4개 카테고리)
CATEGORY_ENDPOINTS = {
    "공사": "getBidPblancListInfoCnstwk",
    "용역": "getBidPblancListInfoServc",
    "물품": "getBidPblancListInfoThng",
    "외자": "getBidPblancListInfoFrgcpt",
}


class APICollector:
    """API 데이터 수집기"""

    def __init__(self, db_url=None):
        """초기화

        Args:
            db_url: 데이터베이스 URL. None이면 환경변수에서 읽음
        """
        # DB 설정
        self.db_url = db_url or os.getenv('DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db')
        self.engine = create_engine(self.db_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # API 설정
        api_key_encoded = os.getenv('BID_API_KEY')
        if not api_key_encoded:
            raise ValueError("BID_API_KEY 환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
        self.api_key = urllib.parse.unquote(api_key_encoded)
        self.base_url = os.getenv('BID_API_BASE_URL', 'http://apis.data.go.kr/1230000/ad/BidPublicInfoService')

    def collect_by_date_range(self, start_date=None, end_date=None, num_of_rows=100, max_pages=None, categories=None):
        """날짜 범위로 공고 수집 - 4개 카테고리 모두 수집 (페이지네이션 지원)

        Args:
            start_date: 시작일 (None이면 7일 전)
            end_date: 종료일 (None이면 오늘)
            num_of_rows: 페이지당 조회 건수
            max_pages: 최대 페이지 수 (None이면 모두)
            categories: 수집할 카테고리 리스트 (None이면 전체 4개)

        Returns:
            dict: 수집 결과 통계
        """
        # 날짜 설정
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        if start_date is None:
            start_date = end_date - timedelta(days=7)

        # API 날짜 형식
        start_str = start_date.strftime('%Y%m%d0000')
        end_str = end_date.strftime('%Y%m%d2359')

        logger.info(f"📅 API 수집 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

        # 카테고리 필터 (None이면 전체)
        target_categories = categories or list(CATEGORY_ENDPOINTS.keys())

        total_fetched = 0
        total_saved = 0
        total_count_all = 0
        new_bid_ids = []

        try:
            for category, endpoint_name in CATEGORY_ENDPOINTS.items():
                if category not in target_categories:
                    continue

                api_url = f"{self.base_url}/{endpoint_name}"
                logger.info(f"📂 [{category}] 카테고리 수집 시작...")

                page_no = 1
                cat_fetched = 0
                cat_total = 0

                while True:
                    # API 파라미터
                    params = {
                        'serviceKey': self.api_key,
                        'pageNo': str(page_no),
                        'numOfRows': str(num_of_rows),
                        'type': 'json',
                        'inqryDiv': '1',
                        'inqryBgnDt': start_str,
                        'inqryEndDt': end_str
                    }

                    logger.info(f"🌐 [{category}] API 호출 중... (페이지 {page_no})")
                    response = requests.get(api_url, params=params, timeout=30)
                    response.raise_for_status()
                    data = response.json()

                    if 'response' in data and 'body' in data['response']:
                        items = data['response']['body'].get('items', [])
                        cat_total = data['response']['body'].get('totalCount', 0)

                        if not items:
                            logger.info(f"📋 [{category}] 페이지 {page_no}: 더 이상 데이터 없음")
                            break

                        logger.info(f"📊 [{category}] 페이지 {page_no}: {len(items)}개 조회 (전체 {cat_total}개)")

                        saved_count, saved_ids = self._save_to_database(items, category=category)
                        cat_fetched += len(items)
                        total_saved += saved_count
                        new_bid_ids.extend(saved_ids)

                        if cat_fetched >= cat_total:
                            logger.info(f"✅ [{category}] 모든 데이터 수집 완료")
                            break

                        if max_pages and page_no >= max_pages:
                            logger.info(f"⚠️ [{category}] 최대 페이지 수({max_pages}) 도달")
                            break

                        page_no += 1
                        time.sleep(0.5)  # API 부하 방지

                    else:
                        logger.error(f"[{category}] 페이지 {page_no}: API 응답 형식 오류")
                        break

                total_fetched += cat_fetched
                total_count_all += cat_total
                logger.info(f"✅ [{category}] 수집 완료: {cat_total}개 중 {cat_fetched}개 수집, 신규 저장됨")

            logger.info(f"📊 전체 수집 완료: 총 {total_count_all}개, {total_fetched}개 수집, {total_saved}개 저장")

            return {
                'total_api': total_count_all,
                'fetched': total_fetched,
                'saved': total_saved,
                'status': 'success',
                'new_bid_ids': new_bid_ids
            }

        except Exception as e:
            logger.error(f"API 수집 실패: {e}")
            return {
                'total_api': total_count_all,
                'fetched': total_fetched,
                'saved': total_saved,
                'status': 'error',
                'message': str(e),
                'new_bid_ids': new_bid_ids
            }
        finally:
            self.session.close()

    def _save_to_database(self, items, category='공사'):
        """데이터베이스에 저장

        Args:
            items: API 응답 아이템 리스트
            category: 입찰 카테고리 (공사/용역/물품/외자)

        Returns:
            tuple: (저장된 건수, 새로 저장된 공고 ID 리스트)
        """
        saved_count = 0
        saved_ids = []

        for item in items:
            try:
                bid_notice_no = item.get('bidNtceNo')

                # 중복 체크
                existing = self.session.query(BidAnnouncement).filter_by(
                    bid_notice_no=bid_notice_no
                ).first()

                if not existing:
                    # 공고 정보 저장
                    announcement = BidAnnouncement(
                        bid_notice_no=bid_notice_no,
                        bid_notice_ord=item.get('bidNtceOrd', '000'),
                        title=item.get('bidNtceNm'),
                        organization_code=item.get('ntceInsttCd'),
                        organization_name=item.get('ntceInsttNm'),
                        department_name=item.get('dmndInsttNm'),
                        announcement_date=self._parse_date(item.get('bidNtceDt')),
                        bid_start_date=self._parse_date(item.get('bidBeginDt')),
                        bid_end_date=self._parse_date(item.get('bidClseDt')),
                        opening_date=self._parse_date(item.get('opengDt')),
                        estimated_price=self._parse_price(item.get('presmptPrce')),
                        bid_method=item.get('bidMethdNm'),
                        contract_method=item.get('cntrctCnclsMthdNm'),
                        detail_page_url=item.get('bidNtceDtlUrl'),
                        standard_doc_url=item.get('stdNtceDocUrl'),
                        category=category,
                        status='active',
                        collection_status='completed',
                        collected_at=datetime.now(timezone.utc)
                    )
                    self.session.add(announcement)

                    # 문서 정보 저장
                    if item.get('stdNtceDocUrl'):
                        # 파일명과 확장자 추출
                        file_name = item.get('ntceSpecFileNm1', 'standard.hwp')
                        file_extension = ''
                        if '.' in file_name:
                            file_extension = file_name.split('.')[-1].lower()

                        document = BidDocument(
                            bid_notice_no=bid_notice_no,
                            document_type='standard',
                            file_name=file_name,
                            file_extension=file_extension,
                            download_url=item.get('stdNtceDocUrl'),
                            download_status='pending',
                            processing_status='pending'
                        )
                        self.session.add(document)

                    saved_count += 1
                    saved_ids.append(bid_notice_no)  # 새로 저장된 ID 추가
                    logger.debug(f"  ✅ 신규 저장: {bid_notice_no}")
                else:
                    logger.debug(f"  ⏭️ 이미 존재: {bid_notice_no}")

            except Exception as e:
                logger.error(f"저장 실패 {item.get('bidNtceNo')}: {e}")

        # 커밋
        self.session.commit()
        logger.info(f"💾 DB 저장 완료: {saved_count}건")

        return saved_count, saved_ids

    def _parse_date(self, date_str):
        """날짜 문자열 파싱

        Args:
            date_str: 날짜 문자열 (YYYY-MM-DD HH:mm:ss 형식)

        Returns:
            datetime: 파싱된 날짜
        """
        if not date_str:
            return None

        try:
            # 'YYYY-MM-DD HH:mm:ss' 형식 처리
            if ' ' in date_str:
                return datetime.strptime(date_str.split(' ')[0], '%Y-%m-%d')
            # 'YYYY-MM-DD' 형식 처리
            elif '-' in date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            logger.debug(f"날짜 파싱 실패: {date_str}")

        return None

    def _parse_price(self, price_str):
        """가격 문자열 파싱

        Args:
            price_str: 가격 문자열

        Returns:
            int: 파싱된 가격
        """
        if not price_str:
            return None

        try:
            # 숫자만 추출
            numbers = ''.join(c for c in str(price_str) if c.isdigit())
            if numbers:
                return int(numbers)
        except:
            pass

        return None


# 독립 실행 가능
if __name__ == "__main__":
    collector = APICollector()
    result = collector.collect_by_date_range(num_of_rows=10)
    print(f"수집 결과: {result}")