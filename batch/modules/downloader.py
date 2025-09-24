#!/usr/bin/env python
"""
파일 다운로드 모듈
공고 문서 파일(HWP, PDF 등)을 다운로드하고 로컬에 저장
"""

import requests
import time
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.models import BidDocument


class DocumentDownloader:
    """문서 다운로드 관리자"""

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
        self.documents_path = self.storage_path / "documents"
        self.documents_path.mkdir(parents=True, exist_ok=True)

    def download_pending(self, limit=50):
        """대기 중인 문서 다운로드

        Args:
            limit: 최대 다운로드 개수

        Returns:
            dict: 다운로드 결과 통계
        """
        # 다운로드 대기 중인 문서 조회
        pending_docs = self.session.query(BidDocument).filter(
            BidDocument.download_status == 'pending'
        ).limit(limit).all()

        logger.info(f"📥 다운로드 대상: {len(pending_docs)}개 문서")

        stats = {
            'total': len(pending_docs),
            'success': 0,
            'failed': 0,
            'skipped': 0
        }

        for i, doc in enumerate(pending_docs, 1):
            try:
                logger.info(f"[{i}/{len(pending_docs)}] {doc.bid_notice_no} - {doc.file_name}")

                # 다운로드 실행
                if self._download_file(doc):
                    stats['success'] += 1
                    logger.info(f"  ✅ 다운로드 성공")
                else:
                    stats['failed'] += 1
                    logger.warning(f"  ❌ 다운로드 실패")

                # API 부하 방지
                time.sleep(0.5)

            except Exception as e:
                stats['failed'] += 1
                logger.error(f"  ❌ 오류: {e}")
                doc.download_status = 'failed'
                doc.error_message = str(e)
                self.session.commit()

        # 통계 출력
        if stats['total'] > 0:
            success_rate = (stats['success'] / stats['total']) * 100
            logger.info(f"📊 다운로드 완료: {stats['success']}/{stats['total']} 성공 ({success_rate:.1f}%)")

        self.session.close()
        return stats

    def _download_file(self, document):
        """파일 다운로드 실제 구현

        Args:
            document: BidDocument 객체

        Returns:
            bool: 다운로드 성공 여부
        """
        if not document.download_url:
            logger.warning(f"다운로드 URL 없음: {document.bid_notice_no}")
            document.download_status = 'failed'
            document.error_message = '다운로드 URL 없음'
            self.session.commit()
            return False

        try:
            # HTTP 요청
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(document.download_url, headers=headers, timeout=30)

            if response.status_code == 200:
                # 저장 디렉토리 생성
                doc_dir = self.documents_path / document.bid_notice_no
                doc_dir.mkdir(parents=True, exist_ok=True)

                # 파일명 결정
                if document.file_name:
                    file_name = document.file_name
                else:
                    # 기본 파일명
                    ext = document.file_extension or 'hwp'
                    file_name = f"document.{ext}"

                file_path = doc_dir / file_name

                # 파일 저장
                with open(file_path, 'wb') as f:
                    f.write(response.content)

                # DB 업데이트
                document.storage_path = str(file_path)
                document.download_status = 'completed'
                document.file_size = len(response.content)
                document.downloaded_at = datetime.now()

                # 파일 확장자 업데이트 (없으면)
                if not document.file_extension and '.' in file_name:
                    document.file_extension = file_name.split('.')[-1].lower()

                self.session.commit()

                logger.debug(f"  📁 저장: {file_path} ({len(response.content):,} bytes)")
                return True

            else:
                # HTTP 오류
                document.download_status = 'failed'
                document.error_message = f'HTTP {response.status_code}'
                self.session.commit()
                logger.warning(f"  HTTP 오류: {response.status_code}")
                return False

        except requests.exceptions.Timeout:
            document.download_status = 'failed'
            document.error_message = '다운로드 시간 초과'
            self.session.commit()
            logger.error("  타임아웃")
            return False

        except Exception as e:
            document.download_status = 'failed'
            document.error_message = str(e)[:500]  # 오류 메시지 길이 제한
            self.session.commit()
            logger.error(f"  다운로드 실패: {e}")
            return False

    def retry_failed(self, max_retries=3):
        """실패한 다운로드 재시도

        Args:
            max_retries: 최대 재시도 횟수

        Returns:
            dict: 재시도 결과 통계
        """
        # 실패한 문서 조회
        failed_docs = self.session.query(BidDocument).filter(
            BidDocument.download_status == 'failed'
        ).all()

        logger.info(f"🔄 재시도 대상: {len(failed_docs)}개 문서")

        stats = {
            'total': len(failed_docs),
            'success': 0,
            'still_failed': 0
        }

        for doc in failed_docs:
            # 재시도 카운터 초기화
            retry_count = 0
            success = False

            while retry_count < max_retries and not success:
                retry_count += 1
                logger.info(f"재시도 {retry_count}/{max_retries}: {doc.bid_notice_no}")

                # 상태 리셋
                doc.download_status = 'pending'
                doc.error_message = None
                self.session.commit()

                # 다운로드 시도
                if self._download_file(doc):
                    stats['success'] += 1
                    success = True
                else:
                    time.sleep(2)  # 재시도 전 대기

            if not success:
                stats['still_failed'] += 1

        logger.info(f"📊 재시도 결과: {stats['success']}개 성공, {stats['still_failed']}개 여전히 실패")

        self.session.close()
        return stats


# 독립 실행 가능
if __name__ == "__main__":
    downloader = DocumentDownloader()

    # 대기 중인 문서 다운로드
    result = downloader.download_pending(limit=5)
    print(f"다운로드 결과: {result}")

    # 실패한 문서 재시도
    if result['failed'] > 0:
        retry_result = downloader.retry_failed()
        print(f"재시도 결과: {retry_result}")