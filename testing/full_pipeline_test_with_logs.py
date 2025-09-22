#!/usr/bin/env python3
"""
전체 파이프라인 테스트 (상세 로깅 포함)
1. API 호출 (요청/응답 로그)
2. HWP 파일 다운로드 (진행 로그)
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
import time
import hashlib

# Selenium 관련
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.shared.config import settings
from src.shared.database import get_db_context, engine
from src.shared.models import BidAnnouncement, BidDocument, Base
from loguru import logger

# HWP 처리를 위한 hwp-viewer 임포트
sys.path.insert(0, str(project_root / 'tools' / 'hwp-viewer'))
try:
    from hwp_viewer import HWPViewer
except ImportError:
    HWPViewer = None
    logger.warning("HWP Viewer를 사용할 수 없습니다. 기본 hwp5txt를 사용합니다.")


class FullPipelineTest:
    """전체 파이프라인 테스트 (상세 로깅)"""

    def __init__(self):
        self.test_id = f"FULL_PIPELINE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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
        self.log_file = self.log_dir / "pipeline_log.json"
        self.logs = []

        logger.info(f"테스트 ID: {self.test_id}")
        logger.info(f"다운로드 경로: {self.download_dir}")
        logger.info(f"마크다운 경로: {self.markdown_dir}")
        logger.info(f"로그 경로: {self.log_dir}")

    def add_log(self, phase: str, status: str, message: str, data: Any = None):
        """로그 추가"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "status": status,
            "message": message,
            "data": data
        }
        self.logs.append(log_entry)

        # 콘솔 출력
        icon = "✅" if status == "success" else "❌" if status == "error" else "⚠️" if status == "warning" else "ℹ️"
        logger.info(f"{icon} [{phase}] {message}")

        # 로그 파일 저장
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, indent=2, ensure_ascii=False, default=str)

    async def run_full_pipeline(self):
        """전체 파이프라인 실행"""
        logger.info("=" * 80)
        logger.info("🚀 전체 파이프라인 테스트 시작")
        logger.info("=" * 80)

        try:
            # Phase 1: API 데이터 수집
            api_data = await self.phase1_api_collection()

            if not api_data:
                self.add_log("Pipeline", "error", "API 데이터 수집 실패")
                return False

            # Phase 2: HWP 파일 다운로드
            downloaded_files = await self.phase2_download_files(api_data[:3])  # 3개만 테스트

            if not downloaded_files:
                self.add_log("Pipeline", "warning", "다운로드된 파일 없음")

            # Phase 3: 마크다운 변환
            markdown_files = await self.phase3_convert_to_markdown(downloaded_files)

            if not markdown_files:
                self.add_log("Pipeline", "warning", "변환된 마크다운 파일 없음")

            # Phase 4: 데이터베이스 업데이트
            saved_count = await self.phase4_update_database(api_data[:3], markdown_files)

            # 최종 요약
            self.generate_summary()

            return True

        except Exception as e:
            self.add_log("Pipeline", "error", f"파이프라인 실행 중 오류: {str(e)}")
            logger.error(f"파이프라인 오류: {e}", exc_info=True)
            return False

    async def phase1_api_collection(self) -> List[Dict]:
        """Phase 1: API 데이터 수집"""
        self.add_log("API", "info", "Phase 1: API 데이터 수집 시작")

        try:
            # API 요청 파라미터
            target_date = datetime.now()
            date_str = target_date.strftime('%Y%m%d')

            params = {
                'serviceKey': self.api_key,
                'pageNo': 1,
                'numOfRows': 10,  # 10개만 테스트
                'type': 'json',
                'inqryDiv': '1',
                'inqryBgnDt': f'{date_str}0000',
                'inqryEndDt': f'{date_str}2359',
            }

            # 요청 로그
            self.add_log("API", "info", "API 요청 시작", {
                "url": f"{self.base_url}/getBidPblancListInfoCnstwk",
                "params": params,
                "date": target_date.strftime('%Y-%m-%d')
            })

            url = f"{self.base_url}/getBidPblancListInfoCnstwk"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    response_data = {
                        "status": response.status,
                        "headers": dict(response.headers)
                    }

                    if response.status == 200:
                        data = await response.json()

                        if 'response' in data and 'body' in data['response']:
                            items = data['response']['body'].get('items', [])

                            # 응답 로그
                            self.add_log("API", "success", f"API 응답 성공: {len(items)}건", {
                                "total_count": len(items),
                                "sample": items[0] if items else None
                            })

                            # 중복 제거
                            unique = {}
                            for item in items:
                                bid_no = item.get('bidNtceNo')
                                if bid_no:
                                    # stdNtceDocUrl 필드 확인
                                    item['has_document_url'] = bool(item.get('stdNtceDocUrl'))
                                    unique[bid_no] = item

                            result = list(unique.values())
                            self.add_log("API", "success", f"중복 제거 완료: {len(result)}건")

                            return result
                        else:
                            self.add_log("API", "warning", "API 응답에 데이터 없음", response_data)
                            return []
                    else:
                        self.add_log("API", "error", f"API 오류: HTTP {response.status}", response_data)
                        return []

        except Exception as e:
            self.add_log("API", "error", f"API 수집 실패: {str(e)}")
            return []

    async def phase2_download_files(self, api_data: List[Dict]) -> List[Path]:
        """Phase 2: HWP 파일 다운로드"""
        self.add_log("Download", "info", "Phase 2: 파일 다운로드 시작")

        downloaded_files = []

        # Chrome 옵션 설정
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 헤드리스 모드
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option('prefs', {
            'download.default_directory': str(self.download_dir),
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': False
        })

        driver = None
        try:
            # ChromeDriver 경로 설정
            chromedriver_path = '/opt/homebrew/bin/chromedriver'
            if not Path(chromedriver_path).exists():
                chromedriver_path = 'chromedriver'  # PATH에서 찾기

            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)

            self.add_log("Download", "info", "Chrome 드라이버 초기화 성공")

            for idx, item in enumerate(api_data, 1):
                doc_url = item.get('stdNtceDocUrl')
                if not doc_url:
                    self.add_log("Download", "warning", f"문서 URL 없음: {item.get('bidNtceNm')}")
                    continue

                try:
                    # 다운로드 시작 로그
                    self.add_log("Download", "info", f"[{idx}/{len(api_data)}] 다운로드 시작", {
                        "title": item.get('bidNtceNm'),
                        "url": doc_url,
                        "bid_no": item.get('bidNtceNo')
                    })

                    # URL 접속
                    driver.get(doc_url)
                    time.sleep(3)  # 다운로드 대기

                    # 다운로드된 파일 확인
                    downloaded = list(self.download_dir.glob("*"))
                    if downloaded:
                        latest_file = max(downloaded, key=lambda x: x.stat().st_mtime)

                        # 파일명 변경 (bid_no 포함)
                        bid_no = item.get('bidNtceNo', 'unknown')
                        new_name = f"{bid_no}_{latest_file.name}"
                        new_path = self.download_dir / new_name

                        if not new_path.exists():
                            latest_file.rename(new_path)
                            downloaded_files.append(new_path)

                            self.add_log("Download", "success", f"다운로드 성공: {new_name}", {
                                "file_size": new_path.stat().st_size,
                                "file_path": str(new_path)
                            })
                        else:
                            self.add_log("Download", "info", f"파일 이미 존재: {new_name}")
                            downloaded_files.append(new_path)
                    else:
                        self.add_log("Download", "warning", f"파일 다운로드 실패: {item.get('bidNtceNm')}")

                except Exception as e:
                    self.add_log("Download", "error", f"다운로드 오류: {str(e)}", {
                        "title": item.get('bidNtceNm'),
                        "error": str(e)
                    })

        except Exception as e:
            self.add_log("Download", "error", f"Chrome 드라이버 오류: {str(e)}")
        finally:
            if driver:
                driver.quit()
                self.add_log("Download", "info", "Chrome 드라이버 종료")

        self.add_log("Download", "success", f"총 {len(downloaded_files)}개 파일 다운로드 완료")
        return downloaded_files

    async def phase3_convert_to_markdown(self, files: List[Path]) -> List[Path]:
        """Phase 3: 마크다운 변환"""
        self.add_log("Markdown", "info", "Phase 3: 마크다운 변환 시작")

        markdown_files = []

        for idx, file_path in enumerate(files, 1):
            try:
                self.add_log("Markdown", "info", f"[{idx}/{len(files)}] 변환 시작: {file_path.name}")

                # 파일 확장자 확인
                if file_path.suffix.lower() == '.hwp':
                    markdown_content = await self.convert_hwp_to_markdown(file_path)
                elif file_path.suffix.lower() == '.pdf':
                    markdown_content = await self.convert_pdf_to_markdown(file_path)
                else:
                    self.add_log("Markdown", "warning", f"지원하지 않는 파일 형식: {file_path.suffix}")
                    continue

                if markdown_content:
                    # 마크다운 파일 저장
                    md_filename = file_path.stem + '.md'
                    md_path = self.markdown_dir / md_filename

                    with open(md_path, 'w', encoding='utf-8') as f:
                        f.write(markdown_content)

                    markdown_files.append(md_path)

                    self.add_log("Markdown", "success", f"변환 성공: {md_filename}", {
                        "original_file": str(file_path),
                        "markdown_file": str(md_path),
                        "content_length": len(markdown_content),
                        "line_count": markdown_content.count('\n')
                    })
                else:
                    self.add_log("Markdown", "error", f"변환 실패: {file_path.name}")

            except Exception as e:
                self.add_log("Markdown", "error", f"변환 오류: {str(e)}", {
                    "file": str(file_path),
                    "error": str(e)
                })

        self.add_log("Markdown", "success", f"총 {len(markdown_files)}개 파일 변환 완료")
        return markdown_files

    async def convert_hwp_to_markdown(self, file_path: Path) -> Optional[str]:
        """HWP 파일을 마크다운으로 변환"""
        try:
            if HWPViewer:
                # HWP Viewer 사용
                viewer = HWPViewer()
                result = viewer.process_file(str(file_path))

                if result.get('success'):
                    content = result.get('markdown', '')
                    self.add_log("Markdown", "info", "HWP Viewer로 변환 성공", {
                        "method": "HWP Viewer",
                        "text_length": len(result.get('text', ''))
                    })
                    return content

            # 기본 hwp5txt 사용
            import subprocess
            result = subprocess.run(
                ['hwp5txt', str(file_path)],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                content = f"# {file_path.stem}\n\n{result.stdout}"
                self.add_log("Markdown", "info", "hwp5txt로 변환 성공", {
                    "method": "hwp5txt"
                })
                return content

        except Exception as e:
            self.add_log("Markdown", "error", f"HWP 변환 오류: {str(e)}")

        return None

    async def convert_pdf_to_markdown(self, file_path: Path) -> Optional[str]:
        """PDF 파일을 마크다운으로 변환"""
        try:
            import PyPDF2

            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text = ""

                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()

            content = f"# {file_path.stem}\n\n{text}"
            self.add_log("Markdown", "info", "PDF 변환 성공", {
                "method": "PyPDF2",
                "page_count": len(pdf_reader.pages)
            })
            return content

        except Exception as e:
            self.add_log("Markdown", "error", f"PDF 변환 오류: {str(e)}")
            return None

    async def phase4_update_database(self, api_data: List[Dict], markdown_files: List[Path]) -> int:
        """Phase 4: 데이터베이스 업데이트"""
        self.add_log("Database", "info", "Phase 4: 데이터베이스 업데이트 시작")

        saved_count = 0

        try:
            with get_db_context() as db:
                for item in api_data:
                    try:
                        bid_notice_no = item.get('bidNtceNo')

                        # 중복 체크
                        existing = db.query(BidAnnouncement).filter(
                            BidAnnouncement.bid_notice_no == bid_notice_no
                        ).first()

                        if existing:
                            self.add_log("Database", "info", f"이미 존재하는 공고: {bid_notice_no}")

                            # 문서 정보 업데이트
                            md_file = next((f for f in markdown_files if bid_notice_no in f.name), None)
                            if md_file and not existing.markdown_file_path:
                                existing.markdown_file_path = str(md_file)
                                existing.extracted_text_length = md_file.stat().st_size
                                existing.updated_at = datetime.now()
                                db.commit()

                                self.add_log("Database", "success", f"문서 정보 업데이트: {bid_notice_no}")
                            continue

                        # 새 데이터 저장
                        announcement = BidAnnouncement(
                            bid_notice_no=bid_notice_no,
                            title=item.get('bidNtceNm', ''),
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
                        md_file = next((f for f in markdown_files if bid_notice_no in f.name), None)
                        if md_file:
                            announcement.markdown_file_path = str(md_file)
                            announcement.extracted_text_length = md_file.stat().st_size

                        db.add(announcement)
                        db.commit()
                        saved_count += 1

                        self.add_log("Database", "success", f"저장 성공: {bid_notice_no}", {
                            "title": item.get('bidNtceNm'),
                            "markdown_file": str(md_file) if md_file else None
                        })

                    except Exception as e:
                        db.rollback()
                        self.add_log("Database", "error", f"저장 오류: {str(e)}", {
                            "bid_no": item.get('bidNtceNo'),
                            "error": str(e)
                        })

                self.add_log("Database", "success", f"총 {saved_count}개 레코드 저장 완료")

        except Exception as e:
            self.add_log("Database", "error", f"데이터베이스 오류: {str(e)}")

        return saved_count

    def generate_summary(self):
        """테스트 요약 생성"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 파이프라인 테스트 요약")
        logger.info("=" * 80)

        # 단계별 집계
        phase_summary = {}
        for log in self.logs:
            phase = log['phase']
            status = log['status']

            if phase not in phase_summary:
                phase_summary[phase] = {'success': 0, 'error': 0, 'warning': 0, 'info': 0}

            if status in phase_summary[phase]:
                phase_summary[phase][status] += 1

        # 요약 출력
        for phase, counts in phase_summary.items():
            total = sum(counts.values())
            success = counts.get('success', 0)
            error = counts.get('error', 0)

            logger.info(f"\n📌 {phase}:")
            logger.info(f"  - 총 로그: {total}개")
            logger.info(f"  - 성공: {success}개")
            logger.info(f"  - 오류: {error}개")
            logger.info(f"  - 경고: {counts.get('warning', 0)}개")

        # 최종 결과
        logger.info(f"\n📁 저장 위치:")
        logger.info(f"  - HWP 파일: {self.download_dir}")
        logger.info(f"  - 마크다운: {self.markdown_dir}")
        logger.info(f"  - 로그 파일: {self.log_file}")

        # 요약 보고서 생성
        report_file = self.log_dir / "summary_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# 파이프라인 테스트 보고서\n\n")
            f.write(f"**테스트 ID**: {self.test_id}\n")
            f.write(f"**실행 시간**: {datetime.now()}\n\n")

            f.write("## 단계별 요약\n\n")
            for phase, counts in phase_summary.items():
                f.write(f"### {phase}\n")
                f.write(f"- 성공: {counts.get('success', 0)}개\n")
                f.write(f"- 오류: {counts.get('error', 0)}개\n")
                f.write(f"- 경고: {counts.get('warning', 0)}개\n\n")

            f.write("## 상세 로그\n\n")
            f.write(f"상세 로그는 다음 파일을 참조하세요:\n")
            f.write(f"- {self.log_file}\n")

        logger.info(f"\n✅ 보고서 생성 완료: {report_file}")


async def main():
    """메인 실행 함수"""
    tester = FullPipelineTest()
    success = await tester.run_full_pipeline()

    if success:
        logger.info("\n🎉 전체 파이프라인 테스트 완료!")
    else:
        logger.error("\n❌ 파이프라인 테스트 실패")

    return success


if __name__ == "__main__":
    asyncio.run(main())