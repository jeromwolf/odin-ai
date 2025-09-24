#!/usr/bin/env python
"""
문서 처리 모듈
다운로드된 문서를 처리하여 마크다운 변환, 정보 추출, 태그 생성 등 수행
"""

import asyncio
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from loguru import logger
import os
import sys
import re
import zipfile

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.models import (
    BidDocument, BidExtractedInfo, BidSchedule,
    BidTag, BidTagRelation, BidAttachment
)
from src.services.document_processor import DocumentProcessor


class DocumentProcessorModule:
    """문서 처리 모듈"""

    def __init__(self, db_url=None, storage_path=None):
        """초기화

        Args:
            db_url: 데이터베이스 URL. None이면 환경변수에서 읽음
            storage_path: 파일 저장 경로. None이면 기본 경로 사용
        """
        # DB 설정
        self.db_url = db_url or os.getenv('DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db')
        self.engine = create_engine(self.db_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # 저장 경로 설정
        self.storage_path = Path(storage_path) if storage_path else Path("./storage")

        # DocumentProcessor 인스턴스
        self.processor = DocumentProcessor(self.session, self.storage_path)

    def process_downloaded(self, limit=50):
        """다운로드 완료된 문서 처리

        Args:
            limit: 최대 처리 개수

        Returns:
            dict: 처리 결과 통계
        """
        # 처리 대기 문서 조회
        pending_docs = self.session.query(BidDocument).filter(
            BidDocument.download_status == 'completed',
            BidDocument.processing_status == 'pending'
        ).limit(limit).all()

        logger.info(f"🔧 처리 대상: {len(pending_docs)}개 문서")

        stats = {
            'total': len(pending_docs),
            'success': 0,
            'failed': 0,
            'info_extracted': 0,
            'tags_created': 0,
            'attachments': 0
        }

        # 비동기 처리를 동기로 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        for i, doc in enumerate(pending_docs, 1):
            try:
                logger.info(f"[{i}/{len(pending_docs)}] {doc.bid_notice_no} - {doc.file_name}")

                # 문서 처리 (마크다운 변환)
                result = loop.run_until_complete(self.processor._process_document(doc))

                if doc.processing_status == 'completed':
                    stats['success'] += 1
                    logger.info(f"  ✅ 처리 성공")

                    # 추가 정보 추출
                    if doc.extracted_text:
                        # 정보 추출
                        extracted_count = self._extract_information(doc)
                        stats['info_extracted'] += extracted_count

                        # 태그 생성
                        tag_count = self._assign_tags(doc)
                        stats['tags_created'] += tag_count

                        # 일정 정보 추출
                        self._extract_schedules(doc)

                    # ZIP 파일인 경우 첨부파일 처리
                    if doc.file_extension == 'zip':
                        attachment_count = self._process_attachments(doc)
                        stats['attachments'] += attachment_count

                else:
                    stats['failed'] += 1
                    logger.warning(f"  ❌ 처리 실패: {doc.error_message}")

            except Exception as e:
                stats['failed'] += 1
                logger.error(f"  ❌ 오류: {e}")
                doc.processing_status = 'failed'
                doc.error_message = str(e)[:500]
                self.session.commit()

        loop.close()

        # 통계 출력
        if stats['total'] > 0:
            success_rate = (stats['success'] / stats['total']) * 100
            logger.info(f"📊 처리 완료: {stats['success']}/{stats['total']} 성공 ({success_rate:.1f}%)")
            logger.info(f"  📋 추출 정보: {stats['info_extracted']}개")
            logger.info(f"  🏷️ 생성 태그: {stats['tags_created']}개")
            logger.info(f"  📎 첨부파일: {stats['attachments']}개")

        # 카테고리별 추출 정보 집계
        extracted_by_category = {}
        if stats['info_extracted'] > 0:
            result = self.session.execute(text("""
                SELECT info_category, COUNT(*)
                FROM bid_extracted_info
                WHERE extracted_at::date = CURRENT_DATE
                GROUP BY info_category
            """))
            for row in result:
                extracted_by_category[row[0]] = row[1]

        stats['extracted_by_category'] = extracted_by_category

        self.session.close()
        return stats

    def _extract_information(self, document):
        """문서에서 정보 추출

        Args:
            document: BidDocument 객체

        Returns:
            int: 추출된 정보 개수
        """
        if not document.extracted_text:
            return 0

        text = document.extracted_text
        extracted_count = 0

        # 가격 정보 추출
        price_patterns = [
            (r'예정가격\s*[:：]\s*([\d,]+)\s*원', 'estimated_price'),
            (r'기초금액\s*[:：]\s*([\d,]+)\s*원', 'base_price'),
            (r'예산금액\s*[:：]\s*([\d,]+)\s*원', 'budget_amount'),
        ]

        for pattern, field_name in price_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                value = match.replace(',', '')
                info = BidExtractedInfo(
                    bid_notice_no=document.bid_notice_no,
                    info_category='prices',
                    field_name=field_name,
                    field_value=value,
                    confidence_score=0.9,
                    extraction_method='regex',
                    extracted_at=datetime.now()
                )
                self.session.add(info)
                extracted_count += 1

        # 계약 정보 추출
        contract_patterns = [
            (r'계약방법\s*[:：]\s*([^\n]+)', 'contract_method'),
            (r'낙찰자결정방법\s*[:：]\s*([^\n]+)', 'winner_decision'),
            (r'입찰방법\s*[:：]\s*([^\n]+)', 'bid_method'),
        ]

        for pattern, field_name in contract_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                info = BidExtractedInfo(
                    bid_notice_no=document.bid_notice_no,
                    info_category='contract_details',
                    field_name=field_name,
                    field_value=match.strip(),
                    confidence_score=0.85,
                    extraction_method='regex',
                    extracted_at=datetime.now()
                )
                self.session.add(info)
                extracted_count += 1

        # 자격요건 추출
        if '자격요건' in text or '참가자격' in text:
            qualification_start = text.find('자격요건') if '자격요건' in text else text.find('참가자격')
            qualification_text = text[qualification_start:qualification_start+500]

            info = BidExtractedInfo(
                bid_notice_no=document.bid_notice_no,
                info_category='requirements',
                field_name='qualification',
                field_value=qualification_text[:500],
                confidence_score=0.8,
                extraction_method='keyword_search',
                extracted_at=datetime.now()
            )
            self.session.add(info)
            extracted_count += 1

        self.session.commit()
        return extracted_count

    def _assign_tags(self, document):
        """문서에 태그 할당

        Args:
            document: BidDocument 객체

        Returns:
            int: 생성된 태그 관계 개수
        """
        if not document.extracted_text:
            return 0

        text = document.extracted_text.lower()
        tag_count = 0

        # 태그 후보 추출
        tag_keywords = {
            '건설': ['건설', '공사', '시공', '건축'],
            '토목': ['토목', '도로', '교량', '터널'],
            '전기': ['전기', '전력', '배전', '변압'],
            '통신': ['통신', '네트워크', 'IT', '정보시스템'],
            '용역': ['용역', '서비스', '컨설팅', '연구'],
            '물품': ['물품', '구매', '납품', '조달'],
            '긴급': ['긴급', '재난', '재해', '응급'],
            '소프트웨어': ['소프트웨어', 'SW', '프로그램', '시스템']
        }

        for tag_name, keywords in tag_keywords.items():
            # 키워드 존재 확인
            if any(keyword in text for keyword in keywords):
                # 태그 조회 또는 생성
                tag = self.session.query(BidTag).filter_by(tag_name=tag_name).first()
                if not tag:
                    tag = BidTag(tag_name=tag_name)
                    self.session.add(tag)
                    self.session.flush()

                # 관계 확인 (중복 방지)
                existing_relation = self.session.query(BidTagRelation).filter_by(
                    bid_notice_no=document.bid_notice_no,
                    tag_id=tag.tag_id
                ).first()

                if not existing_relation:
                    relation = BidTagRelation(
                        bid_notice_no=document.bid_notice_no,
                        tag_id=tag.tag_id
                    )
                    self.session.add(relation)
                    tag_count += 1

        self.session.commit()
        return tag_count

    def _extract_schedules(self, document):
        """일정 정보 추출

        Args:
            document: BidDocument 객체
        """
        if not document.extracted_text:
            return

        text = document.extracted_text

        # 날짜 패턴
        date_pattern = r'(\d{4})[년\.\-]?\s*(\d{1,2})[월\.\-]?\s*(\d{1,2})[일]?'

        # 일정 유형별 키워드
        schedule_keywords = {
            'bid_deadline': ['입찰마감', '제출마감', '접수마감'],
            'opening': ['개찰', '개봉'],
            'site_visit': ['현장설명', '현설'],
            'q&a': ['질의', '질문'],
        }

        for schedule_type, keywords in schedule_keywords.items():
            for keyword in keywords:
                pattern = f'{keyword}.*?{date_pattern}'
                matches = re.findall(pattern, text)

                for match in matches:
                    try:
                        year, month, day = match[-3:]
                        scheduled_date = datetime(int(year), int(month), int(day))

                        # 중복 체크
                        existing = self.session.query(BidSchedule).filter_by(
                            bid_notice_no=document.bid_notice_no,
                            schedule_type=schedule_type,
                            scheduled_date=scheduled_date
                        ).first()

                        if not existing:
                            schedule = BidSchedule(
                                bid_notice_no=document.bid_notice_no,
                                schedule_type=schedule_type,
                                scheduled_date=scheduled_date,
                                description=keyword
                            )
                            self.session.add(schedule)

                    except:
                        continue

        self.session.commit()

    def _process_attachments(self, document):
        """ZIP 파일 첨부파일 처리

        Args:
            document: BidDocument 객체

        Returns:
            int: 처리된 첨부파일 개수
        """
        if not document.storage_path or not Path(document.storage_path).exists():
            return 0

        attachment_count = 0

        try:
            with zipfile.ZipFile(document.storage_path, 'r') as zip_file:
                # ZIP 파일 내용 추출
                extract_dir = Path(document.storage_path).parent / 'extracted'
                extract_dir.mkdir(exist_ok=True)

                for file_info in zip_file.filelist:
                    if not file_info.is_dir():
                        # 파일 추출
                        extracted_path = zip_file.extract(file_info, extract_dir)

                        # 첨부파일 정보 저장
                        file_name = Path(file_info.filename).name
                        file_extension = file_name.split('.')[-1].lower() if '.' in file_name else ''

                        attachment = BidAttachment(
                            document_id=document.document_id,
                            bid_notice_no=document.bid_notice_no,
                            file_name=file_name,
                            file_path=str(extracted_path),
                            file_size=file_info.file_size,
                            file_extension=file_extension,
                            attachment_type='extracted_from_zip'
                        )
                        self.session.add(attachment)
                        attachment_count += 1

                self.session.commit()

        except Exception as e:
            logger.error(f"ZIP 파일 처리 실패: {e}")

        return attachment_count


# 독립 실행 가능
if __name__ == "__main__":
    processor = DocumentProcessorModule()

    # 다운로드 완료된 문서 처리
    result = processor.process_downloaded(limit=5)
    print(f"처리 결과: {result}")