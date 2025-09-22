#!/usr/bin/env python
"""
FULL_TEST_TASKS_V3 완전한 파이프라인 실행
현재 날짜(2025-09-23) 기준 정확한 데이터 수집 및 처리
"""

import sys
from pathlib import Path
import time
import requests
import json
import urllib.parse
from datetime import datetime, timedelta
import asyncio

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path.cwd() / 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.database.models import BidAnnouncement, BidDocument, BidExtractedInfo
from src.services.document_processor import DocumentProcessor
from realistic_table_extractor import RealisticTableExtractor

class CompletePipelineV3:
    """완전한 파이프라인 V3 - 정확한 날짜와 데이터"""

    def __init__(self):
        self.DATABASE_URL = "postgresql://blockmeta@localhost:5432/odin_db"
        self.engine = create_engine(self.DATABASE_URL)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # API 정보 (확인된 정확한 URL과 키)
        api_key_encoded = "6h2l2VPWSfA2vG3xSFr7gf6iwaZT2dmzcoCOzklLnOIJY6sw17lrwHNQ3WxPdKMDIN%2FmMlv2vBTWTIzBDPKVdw%3D%3D"
        self.api_key = urllib.parse.unquote(api_key_encoded)
        self.api_url = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwk"

        # 표 추출기
        self.table_extractor = RealisticTableExtractor()

        # 현재 날짜 확인
        self.current_date = datetime.now()
        print(f"⏰ 현재 시스템 날짜: {self.current_date.strftime('%Y-%m-%d %H:%M:%S')}")

    def phase0_initialize(self):
        """Phase 0: 시스템 초기화"""
        print("\n" + "="*80)
        print("🔄 Phase 0: 시스템 완전 초기화")
        print("="*80)

        # storage 디렉토리 생성
        storage_paths = [
            Path("./storage/documents"),
            Path("./storage/markdown/2025/09/23"),  # 오늘 날짜로!
        ]

        for path in storage_paths:
            path.mkdir(parents=True, exist_ok=True)
            print(f"✅ 디렉토리 생성: {path}")

        # 데이터베이스 상태 확인
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM bid_announcements")).scalar()
            print(f"📊 기존 공고 수: {result}개")

        return True

    def phase1_collect_api_data(self):
        """Phase 1: 현재 날짜 기준 API 데이터 수집"""
        print("\n" + "="*80)
        print("📥 Phase 1: 현재 날짜 기준 API 데이터 수집")
        print("="*80)

        # 정확한 날짜 범위 설정 (최근 7일)
        end_date = self.current_date
        start_date = end_date - timedelta(days=7)

        # API 날짜 형식 (YYYYMMDDHHmm)
        start_str = start_date.strftime('%Y%m%d0000')  # 202509160000
        end_str = end_date.strftime('%Y%m%d2359')      # 202509232359

        params = {
            'serviceKey': self.api_key,
            'pageNo': '1',
            'numOfRows': '100',  # 100개 수집
            'type': 'json',
            'inqryDiv': '1',
            'inqryBgnDt': start_str,
            'inqryEndDt': end_str
        }

        print(f"📅 API 검색 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        print(f"📍 API URL: {self.api_url}")
        print(f"🔑 파라미터: inqryBgnDt={start_str}, inqryEndDt={end_str}")

        try:
            print("\n🌐 API 호출 중...")
            response = requests.get(self.api_url, params=params, timeout=30)

            if response.status_code == 200:
                data = json.loads(response.text)

                if 'response' in data and 'body' in data['response']:
                    body = data['response']['body']

                    if 'items' in body:
                        items = body['items']
                        total_count = body.get('totalCount', 0)

                        print(f"✅ API 호출 성공: 총 {total_count}개 중 {len(items)}개 수집")

                        # 첫 번째 항목 날짜 검증
                        if items:
                            first_item = items[0]
                            bid_date_str = first_item.get('bidNtceDt', '')
                            if bid_date_str:
                                year = bid_date_str[:4]
                                month = bid_date_str[4:6]
                                print(f"\n🔍 첫 번째 공고 날짜 검증:")
                                print(f"  공고일: {year}-{month} ({'✅ 올바른 날짜' if year == '2025' and month == '09' else '❌ 잘못된 날짜'})")

                        # DB에 저장
                        saved_count = self._save_to_database(items)
                        print(f"💾 DB 저장 완료: {saved_count}개 공고")

                        return len(items), saved_count

            print(f"❌ API 호출 실패: {response.status_code}")
            return 0, 0

        except Exception as e:
            print(f"❌ API 오류: {e}")
            return 0, 0

    def _save_to_database(self, items):
        """API 데이터를 DB에 저장"""
        saved_count = 0

        for item in items:
            bid_notice_no = item.get('bidNtceNo')
            if not bid_notice_no:
                continue

            # 중복 체크
            existing = self.session.query(BidAnnouncement).filter(
                BidAnnouncement.bid_notice_no == bid_notice_no
            ).first()

            if not existing:
                # 날짜 파싱 (API는 'YYYY-MM-DD HH:mm:ss' 형식으로 반환)
                def parse_date_str(date_str):
                    if date_str:
                        try:
                            # 'YYYY-MM-DD HH:mm:ss' 형식 처리
                            if ' ' in date_str:
                                return datetime.strptime(date_str.split(' ')[0], '%Y-%m-%d')
                            # 'YYYY-MM-DD' 형식 처리
                            elif '-' in date_str:
                                return datetime.strptime(date_str, '%Y-%m-%d')
                            # 'YYYYMMDDHHmm' 형식 처리 (기존 방식)
                            elif len(date_str) >= 8:
                                return datetime.strptime(date_str[:8], '%Y%m%d')
                        except:
                            return None
                    return None

                # 금액 정보 파싱 (API 필드명 수정: presmptPrc → presmptPrce)
                # presmptPrce 또는 mainCnsttyPresmptPrce 사용
                estimated_price = None
                if item.get('presmptPrce'):
                    try:
                        estimated_price = int(item.get('presmptPrce'))
                    except:
                        pass
                elif item.get('mainCnsttyPresmptPrce'):
                    try:
                        estimated_price = int(item.get('mainCnsttyPresmptPrce'))
                    except:
                        pass

                announcement = BidAnnouncement(
                    bid_notice_no=bid_notice_no,
                    title=item.get('bidNtceNm'),
                    organization_name=item.get('ntceInsttNm'),
                    bid_method=item.get('bidMethdNm'),
                    estimated_price=estimated_price,  # 수정된 금액 필드
                    announcement_date=parse_date_str(item.get('bidNtceDt')),
                    bid_start_date=parse_date_str(item.get('bidBeginDt')),
                    bid_end_date=parse_date_str(item.get('bidClseDt')),
                    opening_date=parse_date_str(item.get('opengDt')),
                    collection_status='collected',
                    created_at=datetime.now()
                )
                self.session.add(announcement)

                # HWP 문서 정보 저장
                if item.get('stdNtceDocUrl'):
                    document = BidDocument(
                        bid_notice_no=bid_notice_no,
                        document_type='standard',
                        file_name=item.get('stdNtceDocNm'),
                        file_extension='hwp',
                        download_url=item.get('stdNtceDocUrl'),
                        download_status='pending',
                        processing_status='pending'
                    )
                    self.session.add(document)

                saved_count += 1

        self.session.commit()
        return saved_count

    def phase2_download_files(self, limit=20):
        """Phase 2: HWP 파일 다운로드"""
        print("\n" + "="*80)
        print("📄 Phase 2: HWP 파일 다운로드")
        print("="*80)

        # 다운로드 대기 중인 문서
        pending_docs = self.session.query(BidDocument).filter(
            BidDocument.download_status == 'pending'
        ).limit(limit).all()

        print(f"📥 다운로드 대상: {len(pending_docs)}개 문서")

        downloaded_count = 0
        for i, doc in enumerate(pending_docs, 1):
            try:
                print(f"\n[{i}/{len(pending_docs)}] {doc.bid_notice_no}")

                if self._download_file(doc):
                    downloaded_count += 1
                    print(f"  ✅ 다운로드 성공")
                else:
                    print(f"  ❌ 다운로드 실패")

                # 너무 빠른 요청 방지
                time.sleep(0.5)

            except Exception as e:
                print(f"  ❌ 오류: {e}")

        success_rate = (downloaded_count / len(pending_docs) * 100) if pending_docs else 0
        print(f"\n📊 다운로드 결과: {downloaded_count}/{len(pending_docs)} 성공 ({success_rate:.1f}%)")

        return downloaded_count, len(pending_docs)

    def _download_file(self, document):
        """파일 다운로드"""
        if not document.download_url:
            return False

        try:
            response = requests.get(document.download_url, timeout=30)

            if response.status_code == 200:
                # 저장 경로 생성
                storage_dir = Path(f"storage/documents/{document.bid_notice_no}")
                storage_dir.mkdir(parents=True, exist_ok=True)

                file_path = storage_dir / "standard.hwp"

                # 파일 저장
                with open(file_path, 'wb') as f:
                    f.write(response.content)

                # DB 업데이트
                document.storage_path = str(file_path)
                document.download_status = 'completed'
                document.file_size = len(response.content)
                document.downloaded_at = datetime.now()
                self.session.commit()

                return True

        except Exception as e:
            document.download_status = 'failed'
            document.error_message = str(e)
            self.session.commit()

        return False

    def phase3_convert_to_markdown(self):
        """Phase 3: HWP → 마크다운 변환"""
        print("\n" + "="*80)
        print("📝 Phase 3: HWP → 마크다운 변환")
        print("="*80)

        # 다운로드 완료된 문서
        completed_docs = self.session.query(BidDocument).filter(
            BidDocument.download_status == 'completed',
            BidDocument.processing_status == 'pending'
        ).all()

        print(f"📄 변환 대상: {len(completed_docs)}개 문서")

        # DocumentProcessor 초기화
        storage_path = Path('./storage')
        processor = DocumentProcessor(self.session, storage_path)

        converted_count = 0
        for i, doc in enumerate(completed_docs, 1):
            try:
                print(f"\n[{i}/{len(completed_docs)}] {doc.bid_notice_no}")

                # 비동기 처리를 동기로 실행
                result = asyncio.run(processor._process_document(doc))
                self.session.refresh(doc)

                if doc.processing_status == 'completed':
                    converted_count += 1
                    print(f"  ✅ 변환 성공: {len(doc.extracted_text) if doc.extracted_text else 0}자")

                    # 마크다운 파일 날짜 확인
                    if doc.markdown_path:
                        self._verify_markdown_date(doc.markdown_path, doc.bid_notice_no)
                else:
                    print(f"  ❌ 변환 실패: {doc.error_message}")

            except Exception as e:
                print(f"  ❌ 오류: {e}")

        success_rate = (converted_count / len(completed_docs) * 100) if completed_docs else 0
        print(f"\n📊 변환 결과: {converted_count}/{len(completed_docs)} 성공 ({success_rate:.1f}%)")

        return converted_count, len(completed_docs)

    def _verify_markdown_date(self, markdown_path, bid_notice_no):
        """마크다운 파일 날짜 검증"""
        try:
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()

                # 공고일 찾기
                import re
                date_pattern = r'공고일[:\s]*(\d{4})-(\d{2})'
                match = re.search(date_pattern, content)

                if match:
                    year, month = match.groups()
                    if year == '2025' and month == '09':
                        print(f"    📅 날짜 검증: ✅ {year}-{month} (올바른 날짜)")
                    else:
                        print(f"    📅 날짜 검증: ❌ {year}-{month} (잘못된 날짜)")

        except Exception as e:
            print(f"    📅 날짜 검증 실패: {e}")

    def phase4_table_parsing(self):
        """Phase 4: 표 파싱 및 구조화"""
        print("\n" + "="*80)
        print("📊 Phase 4: 표 파싱 및 구조화")
        print("="*80)

        # 처리 완료된 문서
        processed_docs = self.session.query(BidDocument).filter(
            BidDocument.processing_status == 'completed'
        ).all()

        print(f"📋 파싱 대상: {len(processed_docs)}개 문서")

        parsed_count = 0
        for i, doc in enumerate(processed_docs, 1):
            try:
                print(f"\n[{i}/{len(processed_docs)}] {doc.bid_notice_no}")

                if doc.storage_path and Path(doc.storage_path).exists():
                    # 표 데이터 추출
                    extracted_data = self.table_extractor.extract_structured_data(
                        Path(doc.storage_path), doc.bid_notice_no
                    )

                    if extracted_data:
                        # DB에 저장
                        self._save_extracted_info(doc.bid_notice_no, extracted_data)
                        parsed_count += 1

                        # 추출 결과 표시
                        prices = len(extracted_data.get('prices', {}))
                        dates = len(extracted_data.get('dates', {}))
                        contracts = len(extracted_data.get('contract_details', {}))

                        print(f"  ✅ 파싱 성공: 가격({prices}), 날짜({dates}), 계약({contracts})")

            except Exception as e:
                print(f"  ❌ 오류: {e}")

        success_rate = (parsed_count / len(processed_docs) * 100) if processed_docs else 0
        print(f"\n📊 파싱 결과: {parsed_count}/{len(processed_docs)} 성공 ({success_rate:.1f}%)")

        return parsed_count, len(processed_docs)

    def _save_extracted_info(self, bid_notice_no, extracted_data):
        """추출된 정보를 DB에 저장"""
        for category, data in extracted_data.items():
            if category == 'bid_notice_no' or not data:
                continue

            if isinstance(data, dict):
                for field_name, field_value in data.items():
                    if field_value:
                        extracted_info = BidExtractedInfo(
                            bid_notice_no=bid_notice_no,
                            info_category=category,
                            field_name=field_name,
                            field_value=str(field_value),
                            field_type='text',
                            confidence_score=0.8,
                            extraction_method='table_parsing'
                        )
                        self.session.add(extracted_info)

        self.session.commit()

    def phase5_verify_results(self):
        """Phase 5: 결과 검증"""
        print("\n" + "="*80)
        print("🎯 Phase 5: 최종 결과 검증")
        print("="*80)

        # 1. 날짜 검증
        print("\n📅 날짜 검증:")
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN EXTRACT(MONTH FROM announcement_date) = 9 THEN 1 END) as sept_count,
                    COUNT(CASE WHEN EXTRACT(MONTH FROM announcement_date) != 9 THEN 1 END) as other_count
                FROM bid_announcements
                WHERE announcement_date IS NOT NULL
            """)).first()

            if result:
                print(f"  전체: {result[0]}개")
                print(f"  9월 데이터: {result[1]}개 ✅" if result[1] > 0 else f"  9월 데이터: {result[1]}개 ❌")
                print(f"  기타 월: {result[2]}개" + (" ⚠️" if result[2] > 0 else ""))

        # 2. 마크다운 파일 검증
        print("\n📝 마크다운 파일 검증:")
        markdown_path = Path("./storage/markdown/2025/09/23")
        if markdown_path.exists():
            md_files = list(markdown_path.glob("*.md"))
            print(f"  생성된 파일: {len(md_files)}개")
            print(f"  경로: {markdown_path}")
        else:
            print(f"  ❌ 마크다운 경로 없음")

        # 3. 추출 데이터 통계
        print("\n📊 추출 데이터 통계:")
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT
                    info_category,
                    COUNT(*) as count
                FROM bid_extracted_info
                GROUP BY info_category
                ORDER BY count DESC
            """))

            for row in result:
                print(f"  {row[0]}: {row[1]}개")

        return True

    def run_complete_pipeline(self):
        """전체 파이프라인 실행"""
        print("🚀 FULL_TEST_TASKS_V3 완전한 파이프라인 시작")
        print(f"📅 실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

        start_time = time.time()

        # Phase 0: 초기화
        self.phase0_initialize()

        # Phase 1: API 데이터 수집
        collected, saved = self.phase1_collect_api_data()

        # Phase 2: HWP 다운로드
        downloaded, total_download = self.phase2_download_files(20)

        # Phase 3: 마크다운 변환
        converted, total_convert = self.phase3_convert_to_markdown()

        # Phase 4: 표 파싱
        parsed, total_parse = self.phase4_table_parsing()

        # Phase 5: 결과 검증
        self.phase5_verify_results()

        # 최종 결과 요약
        total_time = time.time() - start_time

        print("\n" + "="*80)
        print("🏆 최종 결과 요약")
        print("="*80)
        print(f"⏱️ 총 실행 시간: {total_time:.1f}초")
        print(f"📥 API 수집: {collected}개 수집, {saved}개 저장")
        print(f"📄 다운로드: {downloaded}/{total_download} 성공 ({downloaded/total_download*100:.1f}%)")
        print(f"📝 마크다운 변환: {converted}/{total_convert} 성공 ({converted/total_convert*100:.1f}%)")
        print(f"📊 표 파싱: {parsed}/{total_parse} 성공 ({parsed/total_parse*100:.1f}%)")

        # 성공 기준 평가
        overall_success = (
            collected > 0 and
            (downloaded/total_download if total_download > 0 else 0) >= 0.8 and
            (converted/total_convert if total_convert > 0 else 0) >= 0.9 and
            (parsed/total_parse if total_parse > 0 else 0) >= 0.8
        )

        print(f"\n{'🎉 전체 테스트 성공!' if overall_success else '⚠️ 일부 기준 미달'}")

        self.session.close()
        return overall_success


if __name__ == "__main__":
    pipeline = CompletePipelineV3()
    success = pipeline.run_complete_pipeline()

    if success:
        print("\n✅ FULL_TEST_TASKS_V3 완료: 현재 날짜 기준 완벽한 파이프라인 구축 성공!")
    else:
        print("\n❌ 일부 문제 발생: 로그를 확인하세요")