"""
파일 다운로드 모듈 (중복 방지 및 재시도 포함)
"""

import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime
import hashlib
import zipfile
from loguru import logger

from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.database.models import (
    BidDocument, BidAttachment, BidAnnouncement
)


class FileDownloader:
    """파일 다운로드 관리자"""

    def __init__(self, db_session: Session, base_path: Path):
        self.db_session = db_session
        self.base_path = Path(base_path)
        self.download_path = self.base_path / "downloads"
        self.temp_path = self.base_path / "temp"

        # 디렉토리 생성
        self.download_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)

        # 동시 다운로드 제한
        self.semaphore = asyncio.Semaphore(5)

        # 통계
        self.stats = {
            'total': 0,
            'success': 0,
            'duplicate': 0,
            'failed': 0
        }

    async def download_pending_documents(self) -> dict:
        """
        대기 중인 문서 다운로드
        Returns: 다운로드 통계
        """
        # 표준문서 다운로드
        await self._download_standard_documents()

        # 첨부파일 다운로드
        await self._download_attachments()

        logger.info(
            f"다운로드 완료 - 총: {self.stats['total']}, "
            f"성공: {self.stats['success']}, "
            f"중복: {self.stats['duplicate']}, "
            f"실패: {self.stats['failed']}"
        )

        return self.stats

    async def _download_standard_documents(self):
        """표준문서 다운로드"""
        # pending 상태의 표준문서 조회
        pending_docs = self.db_session.query(BidDocument).filter(
            and_(
                BidDocument.document_type == 'standard',
                BidDocument.download_status == 'pending'
            )
        ).all()  # limit 제거 - 모든 pending 문서 처리

        if not pending_docs:
            logger.info("다운로드할 표준문서 없음")
            return

        logger.info(f"{len(pending_docs)}개 표준문서 다운로드 시작")

        # 비동기 다운로드
        tasks = []
        for doc in pending_docs:
            task = self._download_document(doc)
            tasks.append(task)

        await asyncio.gather(*tasks)

    async def _download_attachments(self):
        """첨부파일 다운로드"""
        # should_download=True이고 is_downloaded=False인 첨부파일 조회
        pending_attachments = self.db_session.query(BidAttachment).filter(
            and_(
                BidAttachment.should_download == True,
                BidAttachment.is_downloaded == False
            )
        ).all()  # limit 제거 - 모든 pending 첨부파일 처리

        if not pending_attachments:
            logger.info("다운로드할 첨부파일 없음")
            return

        logger.info(f"{len(pending_attachments)}개 첨부파일 다운로드 시작")

        # 비동기 다운로드
        tasks = []
        for attachment in pending_attachments:
            task = self._download_attachment(attachment)
            tasks.append(task)

        await asyncio.gather(*tasks)

    async def _download_document(self, document: BidDocument):
        """개별 문서 다운로드"""
        async with self.semaphore:
            try:
                self.stats['total'] += 1

                # 파일 경로 생성
                file_path = self._get_file_path(
                    document.bid_notice_no,
                    'standard',
                    document.download_url
                )

                # 이미 다운로드된 파일 확인
                if file_path.exists():
                    # 파일 해시로 중복 확인
                    existing_hash = self._calculate_file_hash(file_path)

                    # DB에 해시가 있으면 비교
                    if document.storage_path == str(file_path):
                        document.download_status = 'completed'
                        self.db_session.commit()
                        self.stats['duplicate'] += 1
                        logger.debug(f"이미 다운로드됨: {file_path.name}")
                        return

                # 다운로드 수행
                success, file_size = await self._download_file(
                    document.download_url,
                    file_path
                )

                if success:
                    # DB 업데이트
                    document.storage_path = str(file_path)
                    document.file_size = file_size
                    document.download_status = 'completed'
                    document.downloaded_at = datetime.now()
                    document.file_extension = file_path.suffix[1:]

                    self.db_session.commit()
                    self.stats['success'] += 1
                    logger.info(f"다운로드 성공: {file_path.name} ({file_size:,} bytes)")

                    # ZIP 파일인 경우 압축 해제
                    if file_path.suffix.lower() == '.zip':
                        await self._extract_zip(file_path, document)
                else:
                    document.download_status = 'failed'
                    document.error_message = "다운로드 실패"
                    self.db_session.commit()
                    self.stats['failed'] += 1

            except Exception as e:
                document.download_status = 'failed'
                document.error_message = str(e)
                self.db_session.commit()
                self.stats['failed'] += 1
                logger.error(f"다운로드 오류: {e}")

    async def _download_attachment(self, attachment: BidAttachment):
        """개별 첨부파일 다운로드"""
        async with self.semaphore:
            try:
                self.stats['total'] += 1

                # 파일 경로 생성
                file_path = self._get_file_path(
                    attachment.bid_notice_no,
                    f'attachment_{attachment.attachment_index}',
                    attachment.file_url,
                    attachment.file_name
                )

                # 이미 다운로드된 파일 확인
                if file_path.exists():
                    attachment.is_downloaded = True
                    self.db_session.commit()
                    self.stats['duplicate'] += 1
                    logger.debug(f"이미 다운로드됨: {file_path.name}")
                    return

                # 다운로드 수행
                success, file_size = await self._download_file(
                    attachment.file_url,
                    file_path
                )

                if success:
                    # BidDocument 레코드 생성
                    document = BidDocument(
                        bid_notice_no=attachment.bid_notice_no,
                        document_type=f'attachment{attachment.attachment_index}',
                        file_name=attachment.file_name,
                        file_extension=attachment.file_type,
                        file_size=file_size,
                        download_url=attachment.file_url,
                        storage_path=str(file_path),
                        download_status='completed',
                        downloaded_at=datetime.now()
                    )
                    self.db_session.add(document)

                    # 첨부파일 상태 업데이트
                    attachment.is_downloaded = True
                    self.db_session.commit()

                    self.stats['success'] += 1
                    logger.info(f"첨부파일 다운로드 성공: {file_path.name}")

                    # ZIP 파일인 경우 압축 해제
                    if file_path.suffix.lower() == '.zip':
                        await self._extract_zip(file_path, document)
                else:
                    self.stats['failed'] += 1

            except Exception as e:
                self.stats['failed'] += 1
                logger.error(f"첨부파일 다운로드 오류: {e}")

    async def _download_file(
        self,
        url: str,
        file_path: Path,
        max_retries: int = 3
    ) -> Tuple[bool, int]:
        """
        파일 다운로드 수행
        Returns: (성공 여부, 파일 크기)
        """
        for attempt in range(max_retries):
            try:
                # 임시 파일로 다운로드
                temp_file = self.temp_path / f"{file_path.stem}_{datetime.now().timestamp()}.tmp"

                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url,
                        timeout=aiohttp.ClientTimeout(total=30),
                        headers={'User-Agent': 'Odin-AI/1.0'}
                    ) as response:
                        if response.status == 200:
                            file_size = 0

                            async with aiofiles.open(temp_file, 'wb') as f:
                                async for chunk in response.content.iter_chunked(8192):
                                    await f.write(chunk)
                                    file_size += len(chunk)

                            # 임시 파일을 실제 위치로 이동
                            file_path.parent.mkdir(parents=True, exist_ok=True)
                            temp_file.rename(file_path)

                            return True, file_size
                        else:
                            logger.warning(f"HTTP {response.status}: {url}")

            except asyncio.TimeoutError:
                logger.warning(f"타임아웃 (시도 {attempt + 1}/{max_retries}): {url}")
            except Exception as e:
                logger.error(f"다운로드 오류 (시도 {attempt + 1}/{max_retries}): {e}")

            # 재시도 전 대기
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)

        return False, 0

    async def _extract_zip(self, zip_path: Path, document: BidDocument):
        """ZIP 파일 압축 해제"""
        try:
            extract_path = zip_path.parent / f"{zip_path.stem}_extracted"
            extract_path.mkdir(exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            logger.info(f"ZIP 압축 해제: {zip_path.name} → {extract_path.name}")

            # 추출된 파일 목록을 DB에 기록
            extracted_files = list(extract_path.rglob('*'))
            if extracted_files:
                document.error_message = f"압축 해제 완료: {len(extracted_files)}개 파일"
                self.db_session.commit()

        except Exception as e:
            logger.error(f"ZIP 압축 해제 실패: {e}")

    def _get_file_path(
        self,
        bid_notice_no: str,
        doc_type: str,
        url: str,
        file_name: Optional[str] = None
    ) -> Path:
        """파일 저장 경로 생성"""
        # 날짜별 디렉토리
        now = datetime.now()
        date_path = self.download_path / f"{now.year}/{now.month:02d}/{now.day:02d}"

        # 공고번호별 디렉토리
        bid_path = date_path / bid_notice_no

        # 파일명 결정
        if file_name:
            # 원본 파일명 사용
            safe_name = self._sanitize_filename(file_name)
        else:
            # URL에서 확장자 추론
            ext = self._guess_extension(url)
            safe_name = f"{doc_type}{ext}"

        return bid_path / safe_name

    def _sanitize_filename(self, filename: str) -> str:
        """파일명 정리 (한글 및 특수문자 안전 처리)"""
        import re
        import unicodedata

        # 1. 파일명이 너무 길면 해시 기반 안전명 사용
        if len(filename) > 100:
            import hashlib
            hash_part = hashlib.md5(filename.encode()).hexdigest()[:8]
            ext = ''
            if '.' in filename:
                ext = filename.rsplit('.', 1)[-1]
                if len(ext) <= 10:  # 정상적인 확장자만
                    ext = '.' + re.sub(r'[^a-zA-Z0-9]', '', ext)
            return f"doc_{hash_part}{ext}"

        # 2. 한글 및 특수문자 제거, 영문/숫자/하이픈/언더바만 허용
        safe = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

        # 3. 연속된 언더바 정리
        safe = re.sub(r'_+', '_', safe)
        safe = safe.strip('_')

        # 4. 빈 파일명 처리
        if not safe or safe == '_':
            import hashlib
            hash_part = hashlib.md5(filename.encode()).hexdigest()[:8]
            safe = f"doc_{hash_part}"

        # 5. 길이 제한
        if len(safe) > 50:
            name, ext = safe.rsplit('.', 1) if '.' in safe else (safe, '')
            safe = name[:45] + '.' + ext if ext else name[:50]

        return safe

    def _guess_extension(self, url: str) -> str:
        """URL에서 확장자 추론"""
        # URL 파라미터 제거
        url_path = url.split('?')[0].lower()

        # 일반적인 확장자 확인
        extensions = ['.hwp', '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.zip']
        for ext in extensions:
            if url_path.endswith(ext):
                return ext

        # 기본값
        return '.hwp'

    def _calculate_file_hash(self, file_path: Path) -> str:
        """파일 해시 계산"""
        hash_md5 = hashlib.md5()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)

        return hash_md5.hexdigest()

    async def verify_downloads(self) -> dict:
        """다운로드 검증 및 재시도"""
        failed_docs = self.db_session.query(BidDocument).filter(
            BidDocument.download_status == 'failed'
        ).limit(20).all()

        retry_stats = {
            'retry_count': len(failed_docs),
            'success': 0,
            'failed': 0
        }

        for doc in failed_docs:
            logger.info(f"재시도: {doc.bid_notice_no}")
            doc.download_status = 'pending'
            self.db_session.commit()

        if failed_docs:
            # 재다운로드 시도
            stats = await self.download_pending_documents()
            retry_stats['success'] = stats['success']
            retry_stats['failed'] = stats['failed']

        return retry_stats