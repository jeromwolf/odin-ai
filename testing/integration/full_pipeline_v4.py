#!/usr/bin/env python3
"""
Full Pipeline V4 - 완전 통합 테스트
MD 파일 정보 추출 → DB 저장 → 해시태그 생성까지 전체 파이프라인
"""

import os
import sys
import json
import time
import asyncio
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# 프로젝트 루트 추가
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

import aiohttp
import requests
from sqlalchemy import create_engine, text, Column, String, Integer, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

# 프로젝트 모듈
from src.database.models import Base, BidAnnouncement, BidDocument, BidExtractedInfo, BidTag, BidTagRelation
try:
    from src.services.document_downloader import DocumentDownloader
    from src.services.document_processor import DocumentProcessor
except ImportError:
    # 대체 경로 시도
    sys.path.insert(0, str(project_root / "backend"))
    from backend.services.file_downloader import FileDownloader as DocumentDownloader
    from backend.services.document_processor import DocumentProcessor

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pipeline_v4.log')
    ]
)
logger = logging.getLogger(__name__)


class HashtagGenerator:
    """해시태그 생성기"""

    def __init__(self, session: Session):
        self.session = session
        self.industry_keywords = {
            '건설': ['건설', '건축', '토목', '시공', '공사', '건물', '도로', '교량'],
            'IT': ['소프트웨어', 'SW', '시스템', '개발', 'IT', '정보', '전산', 'AI', '빅데이터'],
            '용역': ['용역', '서비스', '컨설팅', '연구', '조사', '분석', '평가'],
            '물품': ['물품', '구매', '납품', '장비', '자재', '소모품'],
            '전기': ['전기', '전력', '배전', '발전', '전기공사'],
            '통신': ['통신', '네트워크', '인터넷', '광케이블', '무선'],
        }

        self.region_keywords = {
            '서울': ['서울', '서울시', '서울특별시'],
            '경기': ['경기', '경기도', '수원', '성남', '용인', '고양'],
            '부산': ['부산', '부산시', '부산광역시'],
            '대구': ['대구', '대구시', '대구광역시'],
            '인천': ['인천', '인천시', '인천광역시'],
            '광주': ['광주', '광주시', '광주광역시'],
            '대전': ['대전', '대전시', '대전광역시'],
            '울산': ['울산', '울산시', '울산광역시'],
            '충북': ['충북', '충청북도', '청주', '충주'],
            '충남': ['충남', '충청남도', '천안', '아산'],
            '전북': ['전북', '전라북도', '전주', '익산'],
            '전남': ['전남', '전라남도', '목포', '여수'],
            '경북': ['경북', '경상북도', '포항', '구미'],
            '경남': ['경남', '경상남도', '창원', '김해'],
            '강원': ['강원', '강원도', '춘천', '원주'],
            '제주': ['제주', '제주도', '제주특별자치도'],
        }

        self.tech_keywords = {
            'AI': ['인공지능', 'AI', '머신러닝', '딥러닝', 'ML', 'DL'],
            '빅데이터': ['빅데이터', '데이터분석', '데이터마이닝', 'BI'],
            'IoT': ['IoT', '사물인터넷', '센서', 'M2M'],
            '클라우드': ['클라우드', 'Cloud', 'SaaS', 'PaaS', 'IaaS'],
            '블록체인': ['블록체인', 'Blockchain', '분산원장', 'DLT'],
            '보안': ['보안', 'Security', '정보보호', '사이버보안'],
        }

        self.qualification_keywords = {
            'ISO': ['ISO', 'ISO9001', 'ISO14001', 'ISO27001'],
            '중소기업': ['중소기업', '중기업', '소기업', '소상공인'],
            '여성기업': ['여성기업', '여성기업인'],
            '사회적기업': ['사회적기업', '사회적협동조합'],
            '장애인기업': ['장애인기업', '장애인고용'],
        }

    def generate_tags(self, announcement: BidAnnouncement, extracted_text: str = "") -> List[Dict]:
        """공고에 대한 태그 생성"""
        tags = []

        # 텍스트 결합
        full_text = f"{announcement.title} {announcement.organization_name} {extracted_text}".lower()

        # 산업 분류 태그
        for category, keywords in self.industry_keywords.items():
            if any(keyword.lower() in full_text for keyword in keywords):
                tags.append({
                    'name': category,
                    'category': 'industry',
                    'relevance': self._calculate_relevance(full_text, keywords)
                })

        # 지역 태그
        for region, keywords in self.region_keywords.items():
            if any(keyword.lower() in full_text for keyword in keywords):
                tags.append({
                    'name': region,
                    'category': 'region',
                    'relevance': self._calculate_relevance(full_text, keywords)
                })

        # 기술 태그
        for tech, keywords in self.tech_keywords.items():
            if any(keyword.lower() in full_text for keyword in keywords):
                tags.append({
                    'name': tech,
                    'category': 'technology',
                    'relevance': self._calculate_relevance(full_text, keywords)
                })

        # 자격 태그
        for qual, keywords in self.qualification_keywords.items():
            if any(keyword.lower() in full_text for keyword in keywords):
                tags.append({
                    'name': qual,
                    'category': 'qualification',
                    'relevance': self._calculate_relevance(full_text, keywords)
                })

        return tags

    def _calculate_relevance(self, text: str, keywords: List[str]) -> float:
        """관련성 점수 계산"""
        count = sum(1 for keyword in keywords if keyword.lower() in text)
        return min(1.0, count * 0.3)  # 최대 1.0

    def save_tags(self, bid_notice_no: str, tags: List[Dict]) -> int:
        """태그를 DB에 저장"""
        saved_count = 0

        for tag_info in tags:
            try:
                # 태그 마스터 확인/생성
                tag = self.session.query(BidTag).filter_by(
                    tag_name=tag_info['name']
                ).first()

                if not tag:
                    tag = BidTag(
                        tag_name=tag_info['name'],
                        tag_category=tag_info['category'],
                        usage_count=0
                    )
                    self.session.add(tag)
                    self.session.flush()

                # 사용 횟수 증가
                tag.usage_count += 1

                # 공고-태그 관계 생성
                relation = BidTagRelation(
                    bid_notice_no=bid_notice_no,
                    tag_id=tag.tag_id,
                    relevance_score=tag_info['relevance'],
                    source='auto'
                )
                self.session.add(relation)
                saved_count += 1

            except Exception as e:
                logger.error(f"태그 저장 실패 ({tag_info['name']}): {e}")
                continue

        self.session.commit()
        return saved_count


class FullPipelineV4:
    """완전 통합 파이프라인 V4"""

    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db')
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.storage_path = Path("./storage")
        self.api_key = "1BoVC3SjQb3kb8M%2FdG5vXXt37P8I9OWBCY85W%2BHX3BqOqnFYSZhmxJLKdqGYlGRfiUOQ8k4T6LCMfT9Cs7vCPA%3D%3D"

        # 통계
        self.stats = {
            'start_time': None,
            'end_time': None,
            'announcements_collected': 0,
            'documents_downloaded': 0,
            'documents_processed': 0,
            'info_extracted': 0,
            'tags_generated': 0,
            'errors': []
        }

    def reset_database(self):
        """데이터베이스 초기화"""
        logger.info("📊 데이터베이스 초기화 시작...")

        with self.engine.connect() as conn:
            # 테이블 삭제 (순서 중요)
            tables = [
                'bid_tag_relations',
                'bid_tags',
                'bid_search_index',
                'bid_extracted_info',
                'bid_schedule',
                'bid_attachments',
                'bid_documents',
                'bid_announcements'
            ]

            for table in tables:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                    conn.commit()
                    logger.info(f"  ✅ {table} 테이블 삭제")
                except Exception as e:
                    logger.error(f"  ❌ {table} 삭제 실패: {e}")

        # 테이블 재생성
        Base.metadata.create_all(self.engine)
        logger.info("  ✅ 모든 테이블 재생성 완료")

    def reset_storage(self):
        """파일 시스템 초기화"""
        logger.info("📁 파일 시스템 초기화...")

        # storage 디렉토리 정리
        for subdir in ['documents', 'markdown']:
            dir_path = self.storage_path / subdir
            if dir_path.exists():
                import shutil
                shutil.rmtree(dir_path)
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"  ✅ {subdir} 디렉토리 초기화")

    async def collect_announcements(self, session: Session) -> int:
        """API에서 공고 수집"""
        logger.info("📥 공고 수집 시작...")

        # 현재 날짜 기준으로 조회
        today = datetime.now()
        start_date = today.strftime("%Y%m%d0000")
        end_date = today.strftime("%Y%m%d2359")

        logger.info(f"  🔍 조회 기간: {start_date} ~ {end_date}")

        url = (
            f"http://apis.data.go.kr/1230000/BidPublicInfoService/getBidPblancListInfoCnstwk?"
            f"serviceKey={self.api_key}&"
            f"numOfRows=100&pageNo=1&"
            f"inqryBgnDt={start_date}&"
            f"inqryEndDt={end_date}&"
            f"type=json"
        )

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            items = data.get('response', {}).get('body', {}).get('items', [])

            if not items:
                logger.warning("  ⚠️ 조회된 공고가 없습니다")
                return 0

            count = 0
            for item in items:
                try:
                    announcement = BidAnnouncement(
                        bid_notice_no=item.get('bidNtceNo', ''),
                        bid_notice_ord=item.get('bidNtceOrd', '000'),
                        title=item.get('bidNtceNm', ''),
                        organization_code=item.get('ntceInsttCd', ''),
                        organization_name=item.get('ntceInsttNm', ''),
                        department_name=item.get('dmndInsttNm', ''),
                        announcement_date=self._parse_date(item.get('bidNtceDt')),
                        bid_start_date=self._parse_date(item.get('bidBeginDt')),
                        bid_end_date=self._parse_date(item.get('bidClseDt')),
                        opening_date=self._parse_date(item.get('opengDt')),
                        estimated_price=self._parse_price(item.get('presmptPrce')),
                        bid_method=item.get('bidMethdNm', ''),
                        contract_method=item.get('cntrctCnclsMthdNm', ''),
                        detail_page_url=item.get('bidNtceDtlUrl', ''),
                        standard_doc_url=item.get('stdNtceDocUrl', ''),
                        status='active',
                        collection_status='completed',
                        collected_at=datetime.now()
                    )

                    session.merge(announcement)

                    # 문서 메타데이터 생성
                    if item.get('stdNtceDocUrl'):
                        doc = BidDocument(
                            bid_notice_no=item.get('bidNtceNo', ''),
                            document_type='standard',
                            file_name=item.get('ntceSpecFileNm1', 'standard.hwp'),
                            download_url=item.get('stdNtceDocUrl', ''),
                            download_status='pending',
                            processing_status='pending'
                        )
                        session.merge(doc)

                    count += 1

                except Exception as e:
                    logger.error(f"  ❌ 공고 저장 실패: {e}")
                    continue

            session.commit()
            logger.info(f"  ✅ {count}개 공고 수집 완료")
            return count

        except Exception as e:
            logger.error(f"  ❌ API 호출 실패: {e}")
            return 0

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """날짜 파싱"""
        if not date_str:
            return None
        try:
            # API 응답 형식: 'YYYY-MM-DD HH:mm:ss'
            if ' ' in date_str:
                return datetime.strptime(date_str.split(' ')[0], '%Y-%m-%d')
            elif '-' in date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')
            elif len(date_str) >= 8:
                return datetime.strptime(date_str[:8], '%Y%m%d')
        except:
            return None

    def _parse_price(self, price_str: str) -> Optional[int]:
        """가격 파싱"""
        if not price_str:
            return None
        try:
            # 숫자만 추출
            import re
            numbers = re.findall(r'\d+', str(price_str))
            if numbers:
                return int(''.join(numbers))
        except:
            return None

    async def download_documents(self, session: Session) -> int:
        """문서 다운로드"""
        logger.info("📥 문서 다운로드 시작...")

        downloader = DocumentDownloader(session, self.storage_path)

        # 다운로드 대기 문서 조회
        documents = session.query(BidDocument).filter(
            BidDocument.download_status == 'pending'
        ).limit(20).all()  # 테스트용으로 20개만

        logger.info(f"  📄 {len(documents)}개 문서 다운로드 대기")

        success_count = 0
        for doc in documents:
            try:
                result = await downloader._download_file(doc)
                if result:
                    success_count += 1
                    logger.info(f"  ✅ {doc.bid_notice_no}: {doc.file_name}")
            except Exception as e:
                logger.error(f"  ❌ {doc.bid_notice_no}: {e}")

        logger.info(f"  ✅ {success_count}/{len(documents)}개 다운로드 완료")
        return success_count

    async def process_documents(self, session: Session) -> int:
        """문서 처리 및 정보 추출"""
        logger.info("🔧 문서 처리 시작...")

        processor = DocumentProcessor(session, self.storage_path)

        # 처리 대기 문서 조회
        documents = session.query(BidDocument).filter(
            BidDocument.download_status == 'completed',
            BidDocument.processing_status == 'pending'
        ).all()

        logger.info(f"  📄 {len(documents)}개 문서 처리 대기")

        success_count = 0
        for doc in documents:
            try:
                result = await processor._process_document(doc)
                if doc.processing_status == 'completed':
                    success_count += 1

                    # 마크다운 파일에서 추가 정보 추출
                    if doc.markdown_path and Path(doc.markdown_path).exists():
                        self._extract_and_save_info(session, doc)

                    logger.info(f"  ✅ {doc.bid_notice_no}: 처리 완료")
            except Exception as e:
                logger.error(f"  ❌ {doc.bid_notice_no}: {e}")

        session.commit()
        logger.info(f"  ✅ {success_count}/{len(documents)}개 처리 완료")
        return success_count

    def _extract_and_save_info(self, session: Session, doc: BidDocument):
        """마크다운에서 정보 추출 후 DB 저장"""
        try:
            # 마크다운 파일 읽기
            with open(doc.markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # EnhancedTableParser 사용
            from testing.extraction_scripts.enhanced_table_parser import EnhancedTableParser
            parser = EnhancedTableParser()

            # 테이블 파싱
            tables = parser.extract_all_tables(content)

            # 정보 저장
            for category, items in tables.items():
                for item in items:
                    info = BidExtractedInfo(
                        bid_notice_no=doc.bid_notice_no,
                        document_id=doc.document_id,
                        info_category=category,
                        field_name=item.get('field', ''),
                        field_value=item.get('value', ''),
                        field_type=item.get('type', 'text'),
                        confidence_score=item.get('confidence', 0.8),
                        extraction_method='table_parsing',
                        extracted_at=datetime.now()
                    )
                    session.add(info)

            # 고도화된 정보 추출
            from testing.extraction_scripts.enhanced_info_extractor import EnhancedInfoExtractor
            extractor = EnhancedInfoExtractor()
            enhanced_info = extractor.extract_all_info(content)

            # 공고 테이블 업데이트
            announcement = session.query(BidAnnouncement).filter_by(
                bid_notice_no=doc.bid_notice_no
            ).first()

            if announcement:
                # 공사기간
                if enhanced_info.get('duration'):
                    announcement.duration_days = enhanced_info['duration'].get('days')
                    announcement.duration_text = enhanced_info['duration'].get('text')

                # 지역제한
                if enhanced_info.get('region'):
                    announcement.region_restriction = enhanced_info['region'].get('restriction')

                # 하도급
                if enhanced_info.get('subcontract'):
                    announcement.subcontract_allowed = enhanced_info['subcontract'].get('allowed')
                    announcement.subcontract_ratio = enhanced_info['subcontract'].get('ratio')

                # 자격요건
                if enhanced_info.get('qualification'):
                    announcement.qualification_summary = enhanced_info['qualification'].get('summary')

                # 특수조건
                if enhanced_info.get('special_conditions'):
                    announcement.special_conditions = ', '.join(enhanced_info['special_conditions'].get('conditions', []))

                session.merge(announcement)
                self.stats['info_extracted'] += len(tables.get('prices', [])) + len(tables.get('schedule', []))

        except Exception as e:
            logger.error(f"정보 추출 실패 ({doc.bid_notice_no}): {e}")

    def generate_hashtags(self, session: Session) -> int:
        """해시태그 생성 및 저장"""
        logger.info("🏷️ 해시태그 생성 시작...")

        generator = HashtagGenerator(session)

        # 모든 공고 조회
        announcements = session.query(BidAnnouncement).all()

        total_tags = 0
        for announcement in announcements:
            try:
                # 관련 문서의 텍스트 가져오기
                doc = session.query(BidDocument).filter_by(
                    bid_notice_no=announcement.bid_notice_no,
                    document_type='standard'
                ).first()

                extracted_text = ""
                if doc and doc.extracted_text:
                    extracted_text = doc.extracted_text[:1000]  # 처음 1000자만

                # 태그 생성
                tags = generator.generate_tags(announcement, extracted_text)

                # 태그 저장
                saved = generator.save_tags(announcement.bid_notice_no, tags)
                total_tags += saved

                if saved > 0:
                    logger.info(f"  ✅ {announcement.bid_notice_no}: {saved}개 태그 생성")

            except Exception as e:
                logger.error(f"  ❌ {announcement.bid_notice_no}: {e}")

        logger.info(f"  ✅ 총 {total_tags}개 태그 생성 완료")
        return total_tags

    def verify_results(self, session: Session):
        """결과 검증 및 통계"""
        logger.info("📊 결과 검증...")

        with self.engine.connect() as conn:
            # 공고 통계
            result = conn.execute(text("SELECT COUNT(*) FROM bid_announcements")).scalar()
            logger.info(f"  📋 수집된 공고: {result}개")

            # 문서 통계
            result = conn.execute(text("""
                SELECT download_status, COUNT(*)
                FROM bid_documents
                GROUP BY download_status
            """))
            for row in result:
                logger.info(f"  📄 문서 {row[0]}: {row[1]}개")

            # 추출 정보 통계
            result = conn.execute(text("""
                SELECT info_category, COUNT(*)
                FROM bid_extracted_info
                GROUP BY info_category
            """))
            logger.info("  📊 추출된 정보:")
            for row in result:
                logger.info(f"    - {row[0]}: {row[1]}개")

            # 태그 통계
            result = conn.execute(text("SELECT COUNT(*) FROM bid_tags")).scalar()
            logger.info(f"  🏷️ 생성된 태그 종류: {result}개")

            result = conn.execute(text("SELECT COUNT(*) FROM bid_tag_relations")).scalar()
            logger.info(f"  🔗 공고-태그 연결: {result}개")

            # 평균 태그 수
            result = conn.execute(text("""
                SELECT AVG(tag_count) FROM (
                    SELECT bid_notice_no, COUNT(*) as tag_count
                    FROM bid_tag_relations
                    GROUP BY bid_notice_no
                ) t
            """)).scalar()
            logger.info(f"  📈 공고당 평균 태그: {result:.1f}개")

    async def run(self):
        """전체 파이프라인 실행"""
        self.stats['start_time'] = time.time()

        logger.info("🚀 Full Pipeline V4 시작")
        logger.info("="*60)

        # Phase 1: 초기화
        self.reset_database()
        self.reset_storage()

        session = self.Session()

        try:
            # Phase 2: 공고 수집
            self.stats['announcements_collected'] = await self.collect_announcements(session)

            # Phase 3: 문서 다운로드
            self.stats['documents_downloaded'] = await self.download_documents(session)

            # Phase 4: 문서 처리 및 정보 추출
            self.stats['documents_processed'] = await self.process_documents(session)

            # Phase 5: 해시태그 생성
            self.stats['tags_generated'] = self.generate_hashtags(session)

            # Phase 6: 결과 검증
            self.verify_results(session)

        except Exception as e:
            logger.error(f"❌ 파이프라인 오류: {e}")
            self.stats['errors'].append(str(e))

        finally:
            session.close()

        self.stats['end_time'] = time.time()

        # 최종 보고서
        self.generate_report()

    def generate_report(self):
        """최종 보고서 생성"""
        elapsed = self.stats['end_time'] - self.stats['start_time']

        logger.info("="*60)
        logger.info("📊 FINAL REPORT - Pipeline V4")
        logger.info("="*60)
        logger.info(f"⏱️ 총 실행 시간: {elapsed:.1f}초")
        logger.info(f"📋 수집된 공고: {self.stats['announcements_collected']}개")
        logger.info(f"📥 다운로드된 문서: {self.stats['documents_downloaded']}개")
        logger.info(f"🔧 처리된 문서: {self.stats['documents_processed']}개")
        logger.info(f"📊 추출된 정보: {self.stats['info_extracted']}개")
        logger.info(f"🏷️ 생성된 태그: {self.stats['tags_generated']}개")

        if self.stats['errors']:
            logger.info(f"❌ 오류 발생: {len(self.stats['errors'])}건")
            for error in self.stats['errors'][:5]:  # 처음 5개만
                logger.info(f"  - {error}")

        # JSON 보고서 저장
        report_path = Path("testing/reports/pipeline_v4_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"📄 보고서 저장: {report_path}")
        logger.info("="*60)
        logger.info("✅ Pipeline V4 완료!")


async def main():
    """메인 실행"""
    pipeline = FullPipelineV4()
    await pipeline.run()


if __name__ == "__main__":
    asyncio.run(main())