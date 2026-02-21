"""
재처리 메커니즘
실패한 문서를 다양한 방법으로 재처리
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from loguru import logger

from src.database.models import BidDocument
from src.services.improved_document_processor import ImprovedDocumentProcessor


class RetryProcessor:
    """실패한 문서 재처리기"""

    def __init__(self, db_session: Session, storage_path: Path):
        self.db_session = db_session
        self.storage_path = storage_path
        self.improved_processor = ImprovedDocumentProcessor()
        self.retry_strategies = {
            'hwp': self._retry_hwp,
            'hwpx': self._retry_hwpx,
            'pdf': self._retry_pdf,
            'xlsx': self._retry_excel,
            'xls': self._retry_excel,
            'xlsm': self._retry_excel,
            'docx': self._retry_docx,
            'doc': self._retry_doc
        }

    async def process_failed_documents(self, max_retries: int = 3) -> Dict[str, Any]:
        """실패한 문서들 재처리"""
        # 실패한 문서 조회
        failed_docs = self.db_session.query(BidDocument).filter(
            BidDocument.processing_status == 'failed',
            BidDocument.download_status == 'completed'
        ).all()

        logger.info(f"재처리 대상: {len(failed_docs)}개 문서")

        results = {
            'total': len(failed_docs),
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }

        # 세마포어로 동시 처리 제한
        semaphore = asyncio.Semaphore(5)

        async def process_with_retry(doc):
            async with semaphore:
                return await self._retry_document(doc, max_retries)

        # 병렬 처리
        tasks = [process_with_retry(doc) for doc in failed_docs]
        retry_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 집계
        for doc, result in zip(failed_docs, retry_results):
            if isinstance(result, Exception):
                results['failed'] += 1
                results['details'].append({
                    'bid_notice_no': doc.bid_notice_no,
                    'file_name': doc.file_name,
                    'status': 'error',
                    'error': str(result)
                })
            elif result['success']:
                results['success'] += 1
                results['details'].append({
                    'bid_notice_no': doc.bid_notice_no,
                    'file_name': doc.file_name,
                    'status': 'success',
                    'method': result.get('method'),
                    'text_length': result.get('text_length')
                })
            else:
                results['failed'] += 1
                results['details'].append({
                    'bid_notice_no': doc.bid_notice_no,
                    'file_name': doc.file_name,
                    'status': 'failed',
                    'error': result.get('error')
                })

        # 성공률 계산
        if results['total'] > 0:
            results['success_rate'] = (results['success'] / results['total']) * 100
        else:
            results['success_rate'] = 0

        logger.info(f"재처리 완료: 성공 {results['success']}개, 실패 {results['failed']}개 ({results['success_rate']:.1f}%)")

        return results

    async def _retry_document(self, document: BidDocument, max_retries: int) -> Dict[str, Any]:
        """단일 문서 재처리"""
        file_extension = document.file_extension.lower() if document.file_extension else ''

        # 파일 경로 확인
        file_path = self._get_file_path(document)
        if not file_path or not file_path.exists():
            logger.warning(f"파일 없음: {document.bid_notice_no}")
            return {'success': False, 'error': '파일 없음'}

        # 파일 타입별 재처리 전략
        retry_func = self.retry_strategies.get(file_extension)
        if not retry_func:
            logger.warning(f"지원하지 않는 형식: {file_extension}")
            document.processing_status = 'skipped'
            document.error_message = f"지원하지 않는 파일 형식: {file_extension}"
            self.db_session.commit()
            return {'success': False, 'error': '지원하지 않는 형식'}

        # 재처리 시도
        for attempt in range(max_retries):
            try:
                logger.info(f"재처리 시도 {attempt + 1}/{max_retries}: {document.bid_notice_no}")

                result = await retry_func(file_path, document, attempt)

                if result['success']:
                    # 성공 시 DB 업데이트
                    document.extracted_text = result['text'][:10000]  # 처음 10000자만
                    document.text_length = len(result['text'])
                    document.extraction_method = result['method']
                    document.processing_status = 'completed'
                    document.error_message = None
                    self.db_session.commit()

                    logger.success(f"재처리 성공: {document.bid_notice_no} - {result['method']}")
                    return result

            except Exception as e:
                logger.error(f"재처리 오류 (시도 {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    document.error_message = f"재처리 실패: {str(e)}"
                    self.db_session.commit()

        return {'success': False, 'error': '모든 재처리 시도 실패'}

    async def _retry_hwp(self, file_path: Path, document: BidDocument, attempt: int) -> Dict[str, Any]:
        """HWP 재처리"""
        strategies = [
            # 1차: hwp5txt 직접 실행
            lambda: self._try_hwp5txt(file_path),
            # 2차: LibreOffice 변환
            lambda: self._try_libreoffice_conversion(file_path, 'hwp'),
            # 3차: 파일 복구 후 재시도
            lambda: self._try_file_recovery_and_extract(file_path, 'hwp')
        ]

        if attempt < len(strategies):
            return await strategies[attempt]()

        return {'success': False, 'error': 'HWP 재처리 전략 소진'}

    async def _retry_hwpx(self, file_path: Path, document: BidDocument, attempt: int) -> Dict[str, Any]:
        """HWPX 재처리"""
        if attempt == 0:
            # 개선된 HWPX 처리기 사용
            text, method = await self.improved_processor.extract_with_temp_cleanup(file_path, 'hwpx')
            if text:
                return {'success': True, 'text': text, 'method': method}
        elif attempt == 1:
            # hwp5txt 직접 시도
            return await self._try_hwp5txt(file_path)

        return {'success': False, 'error': 'HWPX 재처리 실패'}

    async def _retry_pdf(self, file_path: Path, document: BidDocument, attempt: int) -> Dict[str, Any]:
        """PDF 재처리"""
        # 개선된 PDF 처리기 사용 (OCR 포함)
        text, method = await self.improved_processor.extract_pdf_improved(file_path)
        if text:
            return {'success': True, 'text': text, 'method': method, 'text_length': len(text)}

        return {'success': False, 'error': 'PDF 재처리 실패'}

    async def _retry_excel(self, file_path: Path, document: BidDocument, attempt: int) -> Dict[str, Any]:
        """Excel 재처리"""
        # 개선된 Excel 처리기 사용
        text, method = await self.improved_processor.extract_excel_improved(file_path)
        if text:
            return {'success': True, 'text': text, 'method': method, 'text_length': len(text)}

        return {'success': False, 'error': 'Excel 재처리 실패'}

    async def _retry_docx(self, file_path: Path, document: BidDocument, attempt: int) -> Dict[str, Any]:
        """DOCX 재처리"""
        # python-docx 또는 대체 방법 시도
        try:
            import docx
            doc = docx.Document(str(file_path))
            text_parts = []

            for para in doc.paragraphs:
                if para.text:
                    text_parts.append(para.text)

            if text_parts:
                text = '\n'.join(text_parts)
                return {'success': True, 'text': text, 'method': 'python-docx'}
        except:
            pass

        return {'success': False, 'error': 'DOCX 재처리 실패'}

    async def _retry_doc(self, file_path: Path, document: BidDocument, attempt: int) -> Dict[str, Any]:
        """DOC 재처리"""
        # LibreOffice를 통한 변환 시도
        return await self._try_libreoffice_conversion(file_path, 'doc')

    async def _try_hwp5txt(self, file_path: Path) -> Dict[str, Any]:
        """hwp5txt 직접 실행"""
        import subprocess

        try:
            result = subprocess.run(
                ['hwp5txt', str(file_path)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30
            )

            if result.returncode == 0 and result.stdout:
                return {
                    'success': True,
                    'text': result.stdout,
                    'method': 'hwp5txt-retry',
                    'text_length': len(result.stdout)
                }
        except Exception as e:
            logger.error(f"hwp5txt 재시도 실패: {e}")

        return {'success': False, 'error': 'hwp5txt 실패'}

    async def _try_libreoffice_conversion(self, file_path: Path, file_type: str) -> Dict[str, Any]:
        """LibreOffice를 통한 변환"""
        import subprocess
        import tempfile

        try:
            # 임시 디렉토리 생성
            with tempfile.TemporaryDirectory() as temp_dir:
                # LibreOffice로 텍스트 변환
                cmd = [
                    'soffice',
                    '--headless',
                    '--convert-to',
                    'txt:Text',
                    '--outdir',
                    temp_dir,
                    str(file_path)
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

                # 변환된 텍스트 파일 읽기
                txt_file = Path(temp_dir) / f"{file_path.stem}.txt"
                if txt_file.exists():
                    text = txt_file.read_text(encoding='utf-8')
                    if text:
                        return {
                            'success': True,
                            'text': text,
                            'method': f'LibreOffice-{file_type}',
                            'text_length': len(text)
                        }
        except Exception as e:
            logger.error(f"LibreOffice 변환 실패: {e}")

        return {'success': False, 'error': 'LibreOffice 변환 실패'}

    async def _try_file_recovery_and_extract(self, file_path: Path, file_type: str) -> Dict[str, Any]:
        """파일 복구 후 재추출 시도"""
        # 파일 헤더 체크 및 복구 로직
        # 실제 구현은 파일 타입별로 다름
        return {'success': False, 'error': '파일 복구 미구현'}

    def _get_file_path(self, document: BidDocument) -> Optional[Path]:
        """문서의 실제 파일 경로 반환"""
        if document.storage_path:
            path = Path(document.storage_path)
            if path.exists():
                return path

        # storage_path가 없으면 기본 경로에서 찾기
        possible_paths = [
            self.storage_path / "documents" / document.bid_notice_no / "standard.hwp",
            self.storage_path / "documents" / document.bid_notice_no / f"{document.file_name}",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        return None