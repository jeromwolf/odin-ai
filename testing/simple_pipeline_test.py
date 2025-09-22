#!/usr/bin/env python3
"""
간단한 파이프라인 테스트 (curl 사용)
1. API 호출 (요청/응답 로그)
2. HWP 파일 다운로드 (curl 사용)
3. 마크다운 변환 (변환 과정 로그)
4. 데이터베이스 업데이트 (저장 로그)
"""

import asyncio
import aiohttp
import sys
import os
from datetime import datetime
from pathlib import Path
import json
import urllib.parse
from typing import Dict, Any, List, Optional
import subprocess

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.shared.config import settings
from src.shared.database import get_db_context, engine
from src.shared.models import BidAnnouncement, BidDocument, Base
from loguru import logger


class SimplePipelineTest:
    """간단한 파이프라인 테스트"""

    def __init__(self):
        self.test_id = f"SIMPLE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.api_key = urllib.parse.unquote(settings.public_data_api_key)
        self.base_url = settings.public_data_base_url

        # 저장 경로 설정
        self.download_dir = project_root / "data" / "downloads" / self.test_id
        self.markdown_dir = project_root / "data" / "markdown" / self.test_id
        self.log_dir = project_root / "testing" / "logs" / self.test_id

        # 디렉토리 생성
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.markdown_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 로그 파일 설정
        self.log_file = self.log_dir / "pipeline_log.txt"

        logger.info(f"📋 테스트 ID: {self.test_id}")
        logger.info(f"📂 다운로드: {self.download_dir}")
        logger.info(f"📝 마크다운: {self.markdown_dir}")
        logger.info(f"📊 로그: {self.log_dir}")

    def write_log(self, message: str):
        """로그 파일에 기록"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"

        # 콘솔 출력
        print(log_message)

        # 파일 기록
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + "\n")

    async def run_pipeline(self):
        """파이프라인 실행"""
        self.write_log("=" * 70)
        self.write_log("🚀 파이프라인 테스트 시작")
        self.write_log("=" * 70)

        # Phase 1: API 데이터 수집
        self.write_log("\n📡 Phase 1: API 데이터 수집")
        api_data = await self.collect_api_data()

        if not api_data:
            self.write_log("❌ API 데이터 수집 실패")
            return False

        # Phase 2: HWP 파일 다운로드
        self.write_log(f"\n📥 Phase 2: HWP 파일 다운로드 ({len(api_data[:3])}개)")
        downloaded_files = await self.download_files(api_data[:3])

        # Phase 3: 마크다운 변환
        self.write_log(f"\n📝 Phase 3: 마크다운 변환 ({len(downloaded_files)}개 파일)")
        markdown_files = await self.convert_to_markdown(downloaded_files)

        # Phase 4: 데이터베이스 업데이트
        self.write_log("\n💾 Phase 4: 데이터베이스 업데이트")
        saved_count = await self.update_database(api_data[:3], markdown_files)

        # 요약
        self.write_log("\n" + "=" * 70)
        self.write_log("📊 테스트 요약")
        self.write_log(f"  - API 수집: {len(api_data)}건")
        self.write_log(f"  - 다운로드: {len(downloaded_files)}개 파일")
        self.write_log(f"  - 마크다운 변환: {len(markdown_files)}개")
        self.write_log(f"  - DB 저장: {saved_count}건")
        self.write_log("=" * 70)

        return True

    async def collect_api_data(self) -> List[Dict]:
        """API 데이터 수집"""
        try:
            target_date = datetime.now()
            date_str = target_date.strftime('%Y%m%d')

            params = {
                'serviceKey': self.api_key,
                'pageNo': 1,
                'numOfRows': 10,
                'type': 'json',
                'inqryDiv': '1',
                'inqryBgnDt': f'{date_str}0000',
                'inqryEndDt': f'{date_str}2359',
            }

            # 요청 로그
            self.write_log(f"  요청 URL: {self.base_url}/getBidPblancListInfoCnstwk")
            self.write_log(f"  요청 날짜: {target_date.strftime('%Y-%m-%d')}")
            self.write_log(f"  요청 파라미터: pageNo=1, numOfRows=10")

            url = f"{self.base_url}/getBidPblancListInfoCnstwk"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    self.write_log(f"  응답 상태: HTTP {response.status}")

                    if response.status == 200:
                        data = await response.json()

                        if 'response' in data and 'body' in data['response']:
                            items = data['response']['body'].get('items', [])
                            self.write_log(f"  ✅ 수집 성공: {len(items)}건")

                            # 샘플 출력
                            if items:
                                sample = items[0]
                                self.write_log(f"\n  [샘플 데이터]")
                                self.write_log(f"    공고명: {sample.get('bidNtceNm', 'N/A')}")
                                self.write_log(f"    공고번호: {sample.get('bidNtceNo', 'N/A')}")
                                self.write_log(f"    문서URL: {sample.get('stdNtceDocUrl', 'N/A')[:50]}...")

                            return items
                        else:
                            self.write_log("  ⚠️ 응답에 데이터 없음")
                            return []
                    else:
                        self.write_log(f"  ❌ HTTP 오류: {response.status}")
                        return []

        except Exception as e:
            self.write_log(f"  ❌ 오류: {str(e)}")
            return []

    async def download_files(self, api_data: List[Dict]) -> List[Path]:
        """파일 다운로드 (curl 사용)"""
        downloaded_files = []

        for idx, item in enumerate(api_data, 1):
            doc_url = item.get('stdNtceDocUrl')
            bid_no = item.get('bidNtceNo', 'unknown')
            title = item.get('bidNtceNm', 'unknown')

            if not doc_url:
                self.write_log(f"  [{idx}] ⚠️ URL 없음: {title}")
                continue

            try:
                # 파일명 생성
                file_ext = '.hwp'  # 기본값
                if 'pdf' in doc_url.lower():
                    file_ext = '.pdf'

                filename = f"{bid_no}_{idx}{file_ext}"
                filepath = self.download_dir / filename

                self.write_log(f"\n  [{idx}] 다운로드 시작")
                self.write_log(f"    제목: {title}")
                self.write_log(f"    URL: {doc_url[:80]}...")
                self.write_log(f"    저장: {filename}")

                # curl로 다운로드
                cmd = ['curl', '-L', '-o', str(filepath), doc_url]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0 and filepath.exists():
                    file_size = filepath.stat().st_size
                    self.write_log(f"    ✅ 성공: {file_size:,} bytes")
                    downloaded_files.append(filepath)
                else:
                    self.write_log(f"    ❌ 실패: {result.stderr}")

            except Exception as e:
                self.write_log(f"    ❌ 오류: {str(e)}")

        return downloaded_files

    async def convert_to_markdown(self, files: List[Path]) -> List[Path]:
        """마크다운 변환"""
        markdown_files = []

        for idx, filepath in enumerate(files, 1):
            try:
                self.write_log(f"\n  [{idx}] 변환 시작: {filepath.name}")

                # HWP 파일인 경우
                if filepath.suffix.lower() == '.hwp':
                    # hwp5txt 사용
                    cmd = ['hwp5txt', str(filepath)]
                    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

                    if result.returncode == 0:
                        content = result.stdout
                        self.write_log(f"    텍스트 추출: {len(content):,}자")

                        # 마크다운 생성
                        md_content = f"# {filepath.stem}\n\n"
                        md_content += f"**파일명**: {filepath.name}\n"
                        md_content += f"**변환일시**: {datetime.now()}\n\n"
                        md_content += "---\n\n"
                        md_content += content

                        # 저장
                        md_path = self.markdown_dir / f"{filepath.stem}.md"
                        with open(md_path, 'w', encoding='utf-8') as f:
                            f.write(md_content)

                        self.write_log(f"    ✅ 저장: {md_path.name} ({len(md_content):,}자)")
                        markdown_files.append(md_path)
                    else:
                        self.write_log(f"    ❌ hwp5txt 실패: {result.stderr}")

                # PDF 파일인 경우
                elif filepath.suffix.lower() == '.pdf':
                    self.write_log(f"    ⚠️ PDF 변환은 지원하지 않습니다")

                else:
                    self.write_log(f"    ⚠️ 알 수 없는 형식: {filepath.suffix}")

            except Exception as e:
                self.write_log(f"    ❌ 오류: {str(e)}")

        return markdown_files

    async def update_database(self, api_data: List[Dict], markdown_files: List[Path]) -> int:
        """데이터베이스 업데이트"""
        saved_count = 0

        try:
            with get_db_context() as db:
                for item in api_data:
                    try:
                        bid_no = item.get('bidNtceNo')
                        title = item.get('bidNtceNm', '')

                        self.write_log(f"\n  DB 저장: {bid_no}")
                        self.write_log(f"    제목: {title}")

                        # 중복 체크
                        existing = db.query(BidAnnouncement).filter(
                            BidAnnouncement.bid_notice_no == bid_no
                        ).first()

                        if existing:
                            self.write_log(f"    ℹ️ 이미 존재")

                            # 마크다운 파일 경로 업데이트
                            md_file = next((f for f in markdown_files if bid_no in f.name), None)
                            if md_file and not existing.markdown_file_path:
                                existing.markdown_file_path = str(md_file)
                                existing.extracted_text_length = md_file.stat().st_size
                                existing.updated_at = datetime.now()
                                db.commit()
                                self.write_log(f"    ✅ 마크다운 경로 업데이트")
                            continue

                        # 새 레코드 생성
                        announcement = BidAnnouncement(
                            bid_notice_no=bid_no,
                            title=title,
                            organization_name=item.get('ntceInsttNm', ''),
                            contact_info=item.get('ntceInsttOfclTelNo', ''),
                            announcement_date=datetime.strptime(
                                item.get('bidNtceDate', datetime.now().strftime('%Y-%m-%d')),
                                '%Y-%m-%d'
                            ) if item.get('bidNtceDate') else datetime.now(),
                            bid_amount=int(float(item.get('asignBdgtAmt', 0))) if item.get('asignBdgtAmt') else None,
                            detail_url=item.get('bidNtceDtlUrl', ''),
                            document_url=item.get('stdNtceDocUrl', ''),
                            status='active',
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )

                        # 마크다운 파일 경로 추가
                        md_file = next((f for f in markdown_files if bid_no in f.name), None)
                        if md_file:
                            announcement.markdown_file_path = str(md_file)
                            announcement.extracted_text_length = md_file.stat().st_size

                        db.add(announcement)
                        db.commit()
                        saved_count += 1
                        self.write_log(f"    ✅ 저장 성공")

                    except Exception as e:
                        db.rollback()
                        self.write_log(f"    ❌ 오류: {str(e)}")

                self.write_log(f"\n  총 {saved_count}개 저장 완료")

        except Exception as e:
            self.write_log(f"  ❌ DB 오류: {str(e)}")

        return saved_count


async def main():
    """메인 실행"""
    tester = SimplePipelineTest()
    success = await tester.run_pipeline()

    if success:
        logger.info("\n✅ 파이프라인 테스트 완료!")
        logger.info(f"📋 로그 파일: {tester.log_file}")
    else:
        logger.error("\n❌ 파이프라인 테스트 실패")

    return success


if __name__ == "__main__":
    asyncio.run(main())