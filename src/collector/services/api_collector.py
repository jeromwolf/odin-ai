"""
API 기반 데이터 수집기
공공데이터포털 API를 통한 입찰 데이터 수집
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger
import json

from shared.config import settings
from shared.database import get_db_context
from shared.models import BidAnnouncement, BidDocument, CollectionLog


class APICollector:
    """공공데이터포털 API 수집기"""
    
    def __init__(self):
        # URL 인코딩된 API 키를 디코딩
        import urllib.parse
        self.api_key = urllib.parse.unquote(settings.public_data_api_key)
        self.base_url = settings.public_data_base_url
        self.session: Optional[aiohttp.ClientSession] = None

        if not self.api_key:
            raise ValueError("공공데이터포털 API 키가 설정되지 않았습니다")
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60, connect=30)  # 타임아웃 증가
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def collect_latest_bids(self, days_back: int = 1) -> List[Dict[str, Any]]:
        """
        최근 입찰 공고 수집
        
        Args:
            days_back: 과거 며칠 까지 수집할지
            
        Returns:
            수집된 입찰 데이터 리스트
        """
        
        # 로그 시작
        with get_db_context() as db:
            log_entry = CollectionLog(
                collection_type="api",
                collection_date=datetime.utcnow(),
                status="running",
                start_time=datetime.utcnow()
            )
            db.add(log_entry)
            db.commit()
            log_id = log_entry.id
        
        try:
            async with self:
                # 날짜 범위 설정
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days_back)
                
                logger.info(f"API 수집 시작: {start_date.date()} ~ {end_date.date()}")
                
                collected_bids = []
                page = 1
                
                while True:
                    # API 호출
                    page_data = await self._fetch_bids_page(
                        start_date=start_date,
                        end_date=end_date,
                        page=page
                    )
                    
                    if not page_data or 'items' not in page_data:
                        break

                    items = page_data['items']
                    if not items:
                        break
                    
                    # 데이터 저장
                    saved_count = await self._save_bid_data(items)
                    collected_bids.extend(items)
                    
                    logger.info(
                        f"페이지 {page} 수집 완료: "
                        f"{len(items)}건 수집, {saved_count}건 저장"
                    )
                    
                    # 다음 페이지
                    page += 1
                    
                    # 요청 간격 (서버 부하 방지)
                    await asyncio.sleep(1)
                
                # 로그 업데이트 (성공)
                with get_db_context() as db:
                    log_entry = db.query(CollectionLog).filter(
                        CollectionLog.id == log_id
                    ).first()
                    
                    if log_entry:
                        log_entry.status = "completed"
                        log_entry.end_time = datetime.utcnow()
                        log_entry.total_found = len(collected_bids)
                        log_entry.new_items = len(collected_bids)  # 상세 계산은 _save_bid_data에서
                
                logger.info(f"API 수집 완료: 총 {len(collected_bids)}건")
                return collected_bids
                
        except Exception as e:
            # 로그 업데이트 (실패)
            with get_db_context() as db:
                log_entry = db.query(CollectionLog).filter(
                    CollectionLog.id == log_id
                ).first()
                
                if log_entry:
                    log_entry.status = "failed"
                    log_entry.end_time = datetime.utcnow()
                    log_entry.error_message = str(e)
            
            logger.error(f"API 수집 실패: {e}")
            raise

    async def collect_bids_by_date(
        self,
        target_date: datetime,
        announcement_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        특정 날짜의 입찰 공고 수집

        Args:
            target_date: 수집 대상 날짜
            announcement_types: 공고 유형 리스트 (예: ['입찰공고', '재공고'])

        Returns:
            수집된 입찰 데이터 리스트
        """
        logger.info(f"📅 {target_date.strftime('%Y-%m-%d')} 데이터 수집 시작")

        # 하루 전체를 대상으로 설정
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        try:
            # async context manager 사용으로 session 자동 초기화
            async with self:
                collected_bids = []
                page = 1

                while True:
                    page_data = await self._fetch_bids_page(start_date, end_date, page)

                    if not page_data or not page_data.get('items'):
                        break

                    # 공고 유형 필터링
                    if announcement_types:
                        filtered_data = [
                            bid for bid in page_data['items']
                            if any(ann_type in bid.get('bidNtceNm', '') for ann_type in announcement_types)
                        ]
                        collected_bids.extend(filtered_data)
                    else:
                        collected_bids.extend(page_data['items'])

                    # 마지막 페이지인지 확인
                    if len(page_data['items']) < settings.collection_batch_size:
                        break

                    page += 1
                    await asyncio.sleep(1)  # API 부하 방지

                # 데이터베이스에 저장
                if collected_bids:
                    await self._save_bid_data(collected_bids)

                logger.info(f"✅ {target_date.strftime('%Y-%m-%d')}: {len(collected_bids)}건 수집 완료")
                return collected_bids

        except Exception as e:
            logger.error(f"❌ {target_date.strftime('%Y-%m-%d')} 수집 실패: {e}")
            raise

    async def _fetch_bids_page(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        page: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        API에서 한 페이지의 데이터 가져오기
        """
        
        params = {
            'serviceKey': self.api_key,
            'pageNo': page,
            'numOfRows': settings.collection_batch_size,
            'type': 'json',
            'inqryDiv': '1',  # 입찰공고
            'inqryBgnDt': start_date.strftime('%Y%m%d0000'),
            'inqryEndDt': end_date.strftime('%Y%m%d2359'),
        }
        
        url = f"{self.base_url}/getBidPblancListInfoCnstwk"
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # API 응답 구조 처리
                    if 'response' in data and 'body' in data['response']:
                        return data['response']['body']
                    else:
                        logger.warning(f"비정상 API 응답 구조: {data}")
                        return None
                        
                else:
                    logger.error(f"API 요청 실패: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"API 호출 오류: {e}")
            return None
    
    async def _save_bid_data(self, bid_items: List[Dict[str, Any]]) -> int:
        """
        수집된 입찰 데이터를 데이터베이스에 저장
        
        Returns:
            저장된 아이템 수
        """
        
        saved_count = 0
        
        with get_db_context() as db:
            for item in bid_items:
                try:
                    # 중복 확인
                    bid_notice_no = item.get('bidNtceNo', '')
                    if not bid_notice_no:
                        continue
                    
                    existing = db.query(BidAnnouncement).filter(
                        BidAnnouncement.bid_notice_no == bid_notice_no
                    ).first()
                    
                    if existing:
                        # 기존 데이터 업데이트
                        self._update_bid_announcement(existing, item)
                    else:
                        # 신규 데이터 생성
                        bid_announcement = self._create_bid_announcement(item)
                        db.add(bid_announcement)
                        saved_count += 1
                    
                    # 첫부문서 정보 저장
                    if item.get('stdNtceDocUrl'):
                        self._save_document_info(db, bid_notice_no, item)
                        
                except Exception as e:
                    logger.error(f"데이터 저장 오류: {e}, 아이템: {item}")
                    continue
        
        return saved_count
    
    def _create_bid_announcement(self, item: Dict[str, Any]) -> BidAnnouncement:
        """입찰공고 모델 생성"""
        
        return BidAnnouncement(
            bid_notice_no=item.get('bidNtceNo', ''),
            title=item.get('bidNtceNm', ''),
            organization_name=item.get('ntceInsttNm', ''),
            contact_info=item.get('ntceInsttOfclNm', ''),
            
            # 날짜 변환
            announcement_date=self._parse_date(item.get('bidNtceDt')),
            document_submission_start=self._parse_date(item.get('bidClseDt')),
            document_submission_end=self._parse_date(item.get('bidClseDt')),
            opening_date=self._parse_date(item.get('opengDt')),
            
            # 금액 정보
            bid_amount=self._parse_amount(item.get('presmptPrce')),
            currency="KRW",
            
            # 분류 정보
            industry_type=item.get('indstrytyLctnm', ''),
            location=item.get('dcrmntNm', ''),
            
            # 추가 정보
            bid_method=item.get('bidMethdNm', ''),
            qualification=item.get('qlfctRgstNm', ''),
            
            # 링크 정보
            detail_url=item.get('bidNtceDtlUrl', ''),
            document_url=item.get('stdNtceDocUrl', ''),
            
            # 상태
            status="active",
            is_processed=False
        )
    
    def _update_bid_announcement(self, existing: BidAnnouncement, item: Dict[str, Any]):
        """기존 입찰공고 업데이트"""
        
        # 필요한 필드만 업데이트
        existing.title = item.get('bidNtceNm', existing.title)
        existing.organization_name = item.get('ntceInsttNm', existing.organization_name)
        existing.updated_at = datetime.utcnow()
    
    def _save_document_info(self, db, bid_notice_no: str, item: Dict[str, Any]):
        """첸부문서 정보 저장"""
        
        # 기존 문서 확인
        bid_announcement = db.query(BidAnnouncement).filter(
            BidAnnouncement.bid_notice_no == bid_notice_no
        ).first()
        
        if not bid_announcement:
            return
        
        existing_doc = db.query(BidDocument).filter(
            BidDocument.bid_announcement_id == bid_announcement.id
        ).first()
        
        if existing_doc:
            return  # 이미 존재
        
        # 새 문서 레코드 생성
        document = BidDocument(
            bid_announcement_id=bid_announcement.id,
            file_name=item.get('ntceSpecFileNm1', '문서.hwp'),
            download_url=item.get('stdNtceDocUrl', ''),
            file_type='hwp',
            download_status='pending',
            processing_status='pending'
        )
        
        db.add(document)
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """날짜 문자열 파싱"""
        
        if not date_str:
            return None
        
        try:
            # 여러 형식 시도
            formats = ['%Y%m%d %H%M', '%Y%m%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
                    
            # 모든 형식 실패 시 경고
            logger.warning(f"날짜 파싱 실패: {date_str}")
            return None
            
        except Exception as e:
            logger.error(f"날짜 파싱 오류: {e}")
            return None
    
    def _parse_amount(self, amount_str: Optional[str]) -> Optional[int]:
        """금액 문자열 파싱"""
        
        if not amount_str:
            return None
        
        try:
            # 숙자만 추출
            import re
            numbers = re.findall(r'\d+', str(amount_str))
            if numbers:
                return int(''.join(numbers))
            return None
            
        except Exception as e:
            logger.error(f"금액 파싱 오류: {e}")
            return None