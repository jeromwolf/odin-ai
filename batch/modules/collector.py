#!/usr/bin/env python
"""
API 수집 모듈
공공데이터포털 API에서 입찰공고 데이터를 수집하고 DB에 저장
"""

import requests
import urllib.parse
import time
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.models import BidAnnouncement, BidDocument


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
        api_key_encoded = os.getenv('BID_API_KEY', '6h2l2VPWSfA2vG3xSFr7gf6iwaZT2dmzcoCOzklLnOIJY6sw17lrwHNQ3WxPdKMDIN%2FmMlv2vBTWTIzBDPKVdw%3D%3D')
        self.api_key = urllib.parse.unquote(api_key_encoded)
        self.api_url = os.getenv('BID_API_URL', 'http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwk')

    def collect_by_date_range(self, start_date=None, end_date=None, num_of_rows=100, max_pages=None):
        """날짜 범위로 공고 수집 (페이지네이션 지원)

        Args:
            start_date: 시작일 (None이면 7일 전)
            end_date: 종료일 (None이면 오늘)
            num_of_rows: 페이지당 조회 건수
            max_pages: 최대 페이지 수 (None이면 모두)

        Returns:
            dict: 수집 결과 통계
        """
        # 날짜 설정
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=7)

        # API 날짜 형식
        start_str = start_date.strftime('%Y%m%d0000')
        end_str = end_date.strftime('%Y%m%d2359')

        logger.info(f"📅 API 수집 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

        total_fetched = 0
        total_saved = 0
        page_no = 1
        total_count = 0

        try:
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

                # API 호출
                logger.info(f"🌐 API 호출 중... (페이지 {page_no})")
                response = requests.get(self.api_url, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()

                # 응답 파싱
                if 'response' in data and 'body' in data['response']:
                    items = data['response']['body'].get('items', [])
                    total_count = data['response']['body'].get('totalCount', 0)

                    if not items:
                        logger.info(f"📋 페이지 {page_no}: 더 이상 데이터 없음")
                        break

                    logger.info(f"📊 페이지 {page_no}: {len(items)}개 조회 (전체 {total_count}개)")

                    # DB 저장
                    saved_count = self._save_to_database(items)
                    total_fetched += len(items)
                    total_saved += saved_count

                    # 다음 페이지 확인
                    if total_fetched >= total_count:
                        logger.info(f"✅ 모든 데이터 수집 완료")
                        break

                    # 최대 페이지 제한 확인
                    if max_pages and page_no >= max_pages:
                        logger.info(f"⚠️ 최대 페이지 수({max_pages}) 도달")
                        break

                    page_no += 1
                    time.sleep(0.5)  # API 부하 방지

                else:
                    logger.error(f"페이지 {page_no}: API 응답 형식 오류")
                    break

            logger.info(f"📊 수집 완료: 총 {total_count}개 중 {total_fetched}개 수집, {total_saved}개 저장")

            return {
                'total_api': total_count,
                'fetched': total_fetched,
                'saved': total_saved,
                'pages': page_no,
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"API 수집 실패: {e}")
            return {
                'total_api': total_count,
                'fetched': total_fetched,
                'saved': total_saved,
                'pages': page_no - 1,
                'status': 'error',
                'message': str(e)
            }
        finally:
            self.session.close()

    def _save_to_database(self, items):
        """데이터베이스에 저장

        Args:
            items: API 응답 아이템 리스트

        Returns:
            int: 저장된 건수
        """
        saved_count = 0

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
                        status='active',
                        collection_status='completed',
                        collected_at=datetime.now()
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
                    logger.debug(f"  ✅ 신규 저장: {bid_notice_no}")
                else:
                    logger.debug(f"  ⏭️ 이미 존재: {bid_notice_no}")

            except Exception as e:
                logger.error(f"저장 실패 {item.get('bidNtceNo')}: {e}")

        # 커밋
        self.session.commit()
        logger.info(f"💾 DB 저장 완료: {saved_count}건")

        return saved_count

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