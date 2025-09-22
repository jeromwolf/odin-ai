"""
API 데이터 수집 모듈 (중복 방지 포함)
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import urllib.parse
from loguru import logger
import hashlib
import json

from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from src.database.models import (
    BidAnnouncement, BidDocument, BidAttachment
)
from src.shared.config import settings


class APICollector:
    """공공데이터포털 API 수집기"""

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.api_key = urllib.parse.unquote(settings.public_data_api_key)
        self.base_url = settings.public_data_base_url
        self.duplicate_count = 0
        self.new_count = 0
        self.updated_count = 0

    async def collect_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        page_size: int = 100
    ) -> Tuple[int, int, int]:
        """
        날짜 범위로 데이터 수집
        Returns: (신규, 중복, 업데이트) 건수
        """
        logger.info(f"수집 시작: {start_date.date()} ~ {end_date.date()}")

        self.duplicate_count = 0
        self.new_count = 0
        self.updated_count = 0

        # 날짜별로 수집 (API 제한 고려)
        current_date = start_date
        while current_date <= end_date:
            await self._collect_single_day(current_date, page_size)
            current_date += timedelta(days=1)

            # API 부하 방지
            await asyncio.sleep(1)

        logger.info(
            f"수집 완료 - 신규: {self.new_count}, "
            f"중복: {self.duplicate_count}, "
            f"업데이트: {self.updated_count}"
        )

        return self.new_count, self.duplicate_count, self.updated_count

    async def _collect_single_day(self, target_date: datetime, page_size: int):
        """단일 날짜 데이터 수집"""
        date_str = target_date.strftime('%Y%m%d')
        page_no = 1
        total_count = 0

        while True:
            items, total = await self._fetch_page(date_str, page_no, page_size)

            if not items:
                break

            # 각 항목 처리
            for item in items:
                await self._process_item(item)

            total_count += len(items)

            # 다음 페이지 확인
            if total_count >= total or len(items) < page_size:
                break

            page_no += 1
            await asyncio.sleep(0.5)  # API 부하 방지

        logger.info(f"{target_date.date()}: {total_count}건 처리")

    async def _fetch_page(
        self,
        date_str: str,
        page_no: int,
        page_size: int
    ) -> Tuple[List[Dict], int]:
        """API 페이지 단위 조회"""
        params = {
            'serviceKey': self.api_key,
            'pageNo': page_no,
            'numOfRows': page_size,
            'type': 'json',
            'inqryDiv': '1',
            'inqryBgnDt': f'{date_str}0000',
            'inqryEndDt': f'{date_str}2359',
        }

        url = f"{self.base_url}/getBidPblancListInfoCnstwk"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if 'response' in data and 'body' in data['response']:
                            body = data['response']['body']
                            items = body.get('items', [])
                            total_count = body.get('totalCount', 0)

                            return items, total_count
                    else:
                        logger.error(f"API 오류: HTTP {response.status}")
                        return [], 0

        except Exception as e:
            logger.error(f"API 호출 실패: {e}")
            return [], 0

    async def _process_item(self, item: Dict) -> bool:
        """
        개별 공고 처리 (중복 체크 포함)
        Returns: True if processed, False if duplicate
        """
        bid_notice_no = item.get('bidNtceNo')
        if not bid_notice_no:
            return False

        # 기존 공고 확인
        existing = self.db_session.query(BidAnnouncement).filter(
            BidAnnouncement.bid_notice_no == bid_notice_no
        ).first()

        if existing:
            # 이미 존재하는 경우, 업데이트 필요 여부 확인
            if self._needs_update(existing, item):
                self._update_announcement(existing, item)
                self.updated_count += 1
                logger.debug(f"업데이트: {bid_notice_no}")
            else:
                self.duplicate_count += 1
                logger.debug(f"중복 스킵: {bid_notice_no}")
            return False
        else:
            # 신규 공고 생성
            self._create_announcement(item)
            self.new_count += 1
            logger.info(f"신규 저장: {bid_notice_no} - {item.get('bidNtceNm', '')[:50]}")
            return True

    def _needs_update(self, existing: BidAnnouncement, new_data: Dict) -> bool:
        """
        업데이트 필요 여부 확인
        - 중요 필드가 변경된 경우만 업데이트
        """
        # 체크섬 비교 (주요 필드만)
        important_fields = [
            'bidNtceNm', 'bidBeginDt', 'bidClseDt',
            'presmptPrice', 'asignBdgtAmt', 'stdNtceDocUrl'
        ]

        existing_hash = self._calculate_hash(
            {k: getattr(existing, self._map_field_name(k), None)
             for k in important_fields}
        )
        new_hash = self._calculate_hash(
            {k: new_data.get(k) for k in important_fields}
        )

        return existing_hash != new_hash

    def _calculate_hash(self, data: Dict) -> str:
        """데이터 해시 계산"""
        # datetime 객체를 문자열로 변환
        def serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return str(obj)

        json_str = json.dumps(data, sort_keys=True, ensure_ascii=False, default=serialize)
        return hashlib.md5(json_str.encode()).hexdigest()

    def _create_announcement(self, item: Dict):
        """새 공고 생성"""
        announcement = BidAnnouncement(
            bid_notice_no=item.get('bidNtceNo'),
            bid_notice_ord=item.get('bidNtceOrd', '000'),
            title=item.get('bidNtceNm', ''),
            organization_code=item.get('ntceInsttCd'),
            organization_name=item.get('ntceInsttNm'),
            department_name=item.get('dminsttNm'),
            announcement_date=self._parse_datetime(item.get('bidNtceDt')),
            bid_start_date=self._parse_datetime(item.get('bidBeginDt')),
            bid_end_date=self._parse_datetime(item.get('bidClseDt')),
            opening_date=self._parse_datetime(item.get('opengDt')),
            estimated_price=self._parse_int(item.get('presmptPrice')),
            assigned_budget=self._parse_int(item.get('asignBdgtAmt')),
            bid_method=item.get('bidMethdNm'),
            contract_method=item.get('cntrctCnclsMthdNm'),
            officer_name=item.get('ntceInsttOfclNm'),
            officer_phone=self._mask_phone(item.get('ntceInsttOfclTelNo')),
            officer_email=self._mask_email(item.get('ntceInsttOfclEmailAdrs')),
            detail_page_url=item.get('bidNtceDtlUrl'),
            standard_doc_url=item.get('stdNtceDocUrl'),
            status='active',
            collection_status='collected',
            collected_at=datetime.now()
        )

        self.db_session.add(announcement)

        # 문서 정보 생성
        self._create_documents(item)

        # 첨부파일 정보 생성
        self._create_attachments(item)

        try:
            self.db_session.commit()
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"저장 실패: {e}")

    def _update_announcement(self, existing: BidAnnouncement, item: Dict):
        """기존 공고 업데이트"""
        # 주요 필드만 업데이트
        existing.title = item.get('bidNtceNm', existing.title)
        existing.bid_start_date = self._parse_datetime(item.get('bidBeginDt'))
        existing.bid_end_date = self._parse_datetime(item.get('bidClseDt'))
        existing.opening_date = self._parse_datetime(item.get('opengDt'))
        existing.estimated_price = self._parse_int(item.get('presmptPrice'))
        existing.assigned_budget = self._parse_int(item.get('asignBdgtAmt'))
        existing.standard_doc_url = item.get('stdNtceDocUrl', existing.standard_doc_url)
        existing.updated_at = datetime.now()

        # 새로운 첨부파일이 있는지 확인
        self._update_attachments(existing, item)

        try:
            self.db_session.commit()
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"업데이트 실패: {e}")

    def _create_documents(self, item: Dict):
        """문서 정보 생성"""
        bid_notice_no = item.get('bidNtceNo')

        # 표준 공고문서
        if item.get('stdNtceDocUrl'):
            # 중복 체크
            existing_doc = self.db_session.query(BidDocument).filter(
                and_(
                    BidDocument.bid_notice_no == bid_notice_no,
                    BidDocument.document_type == 'standard'
                )
            ).first()

            if not existing_doc:
                doc = BidDocument(
                    bid_notice_no=bid_notice_no,
                    document_type='standard',
                    download_url=item.get('stdNtceDocUrl'),
                    file_seq=self._extract_file_seq(item.get('stdNtceDocUrl')),
                    download_status='pending',
                    processing_status='pending'
                )
                self.db_session.add(doc)

    def _create_attachments(self, item: Dict):
        """첨부파일 정보 생성"""
        bid_notice_no = item.get('bidNtceNo')

        for i in range(1, 11):
            url_field = f'ntceSpecDocUrl{i}'
            name_field = f'ntceSpecFileNm{i}'

            url = item.get(url_field)
            name = item.get(name_field)

            if url and name:
                # 중복 체크
                existing_att = self.db_session.query(BidAttachment).filter(
                    and_(
                        BidAttachment.bid_notice_no == bid_notice_no,
                        BidAttachment.attachment_index == i
                    )
                ).first()

                if not existing_att:
                    file_ext = name.split('.')[-1].lower() if '.' in name else 'unknown'

                    # 다운로드 필요 여부 결정
                    should_download = self._should_download_file(name, file_ext)

                    attachment = BidAttachment(
                        bid_notice_no=bid_notice_no,
                        attachment_index=i,
                        file_name=name,
                        file_url=url,
                        file_type=file_ext,
                        document_category=self._categorize_document(name),
                        should_download=should_download,
                        is_downloaded=False
                    )
                    self.db_session.add(attachment)

    def _update_attachments(self, existing: BidAnnouncement, item: Dict):
        """첨부파일 업데이트 (새로운 파일만 추가)"""
        bid_notice_no = existing.bid_notice_no

        # 기존 첨부파일 인덱스 목록
        existing_indexes = {
            att.attachment_index
            for att in existing.attachments
        }

        # 새로운 첨부파일 확인
        for i in range(1, 11):
            if i not in existing_indexes:
                url = item.get(f'ntceSpecDocUrl{i}')
                name = item.get(f'ntceSpecFileNm{i}')

                if url and name:
                    self._create_single_attachment(bid_notice_no, i, url, name)

    def _should_download_file(self, file_name: str, file_ext: str) -> bool:
        """파일 다운로드 필요 여부 판단"""
        # 우선순위 높은 파일
        priority_keywords = ['공고', '시방서', '내역서', '과업']
        priority_extensions = ['hwp', 'pdf', 'docx', 'xlsx', 'xls']

        # 스킵할 파일
        skip_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp']

        if file_ext in skip_extensions:
            return False

        if file_ext in priority_extensions:
            return True

        for keyword in priority_keywords:
            if keyword in file_name:
                return True

        # ZIP 파일은 선택적
        if file_ext == 'zip':
            return any(keyword in file_name for keyword in priority_keywords)

        return False

    def _categorize_document(self, file_name: str) -> Optional[str]:
        """문서 카테고리 분류"""
        categories = {
            '공고': ['공고', '안내', '입찰'],
            '시방서': ['시방서', '시방'],
            '내역서': ['내역서', '내역', '산출'],
            '도면': ['도면', '설계도', 'CAD', 'DWG'],
            '과업': ['과업', '과업지시서', '제안요청서'],
        }

        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword.lower() in file_name.lower():
                    return category

        return '기타'

    def _extract_file_seq(self, url: str) -> Optional[int]:
        """URL에서 fileSeq 추출"""
        if not url or 'fileSeq=' not in url:
            return None

        try:
            seq_part = url.split('fileSeq=')[1]
            seq_value = seq_part.split('&')[0]
            return int(seq_value)
        except:
            return None

    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """날짜 문자열 파싱"""
        if not date_str:
            return None

        try:
            # 여러 형식 시도
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y-%m-%d',
                '%Y%m%d'
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue

            return None
        except:
            return None

    def _parse_int(self, value: Any) -> Optional[int]:
        """정수 파싱"""
        if value is None:
            return None

        try:
            if isinstance(value, str):
                value = value.replace(',', '')
            return int(float(value))
        except:
            return None

    def _mask_phone(self, phone: str) -> str:
        """전화번호 마스킹"""
        if not phone or len(phone) < 4:
            return phone

        # 뒤 4자리만 보이도록
        return '*' * (len(phone) - 4) + phone[-4:]

    def _mask_email(self, email: str) -> str:
        """이메일 마스킹"""
        if not email or '@' not in email:
            return email

        # 도메인만 보이도록
        parts = email.split('@')
        return '***@' + parts[1]

    def _map_field_name(self, api_field: str) -> str:
        """API 필드명을 DB 필드명으로 매핑"""
        mapping = {
            'bidNtceNo': 'bid_notice_no',
            'bidNtceNm': 'title',
            'bidBeginDt': 'bid_start_date',
            'bidClseDt': 'bid_end_date',
            'presmptPrice': 'estimated_price',
            'asignBdgtAmt': 'assigned_budget',
            'stdNtceDocUrl': 'standard_doc_url'
        }
        return mapping.get(api_field, api_field)

    def _create_single_attachment(
        self,
        bid_notice_no: str,
        index: int,
        url: str,
        name: str
    ):
        """단일 첨부파일 생성"""
        file_ext = name.split('.')[-1].lower() if '.' in name else 'unknown'

        attachment = BidAttachment(
            bid_notice_no=bid_notice_no,
            attachment_index=index,
            file_name=name,
            file_url=url,
            file_type=file_ext,
            document_category=self._categorize_document(name),
            should_download=self._should_download_file(name, file_ext),
            is_downloaded=False
        )
        self.db_session.add(attachment)