"""
개선된 HWP 파일 파서 - pyhwp를 활용한 한글 처리 최적화
"""

import os
import sys
from pathlib import Path
import logging
import tempfile
import subprocess
from typing import List, Optional

from .models import HWPDocument, HWPMetadata, HWPParagraph, HWPTable

logger = logging.getLogger(__name__)


class ImprovedHWPParser:
    """개선된 HWP 파서 - 한글 깨짐 문제 해결"""

    def __init__(self):
        self.document = None

    def parse(self, file_path: str) -> HWPDocument:
        """HWP 파일을 파싱하여 구조화된 문서 객체 반환"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        # 순차적으로 여러 방법 시도
        methods = [
            self._parse_with_hwp5txt,
            self._parse_with_pyhwp_cli,
            self._parse_with_system_command,
            self._parse_with_basic_extraction
        ]

        for method in methods:
            try:
                logger.info(f"파싱 시도: {method.__name__}")
                return method(file_path)
            except Exception as e:
                logger.warning(f"{method.__name__} 실패: {e}")
                continue

        # 모든 방법 실패 시 빈 문서 반환
        logger.error("모든 파싱 방법 실패")
        return HWPDocument(
            metadata=HWPMetadata(),
            paragraphs=[],
            tables=[],
            raw_text=""
        )

    def _parse_with_hwp5txt(self, file_path: str) -> HWPDocument:
        """hwp5txt 명령어를 사용한 파싱 (pyhwp 설치 시)"""
        try:
            # hwp5txt 명령어 실행
            result = subprocess.run(
                ['hwp5txt', file_path],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30
            )

            if result.returncode == 0:
                text = result.stdout

                # 문단 분리
                paragraphs = [
                    HWPParagraph(text=p.strip())
                    for p in text.split('\n\n')
                    if p.strip()
                ]

                return HWPDocument(
                    metadata=HWPMetadata(),
                    paragraphs=paragraphs,
                    tables=[],
                    raw_text=text
                )

        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            raise Exception(f"hwp5txt 실행 실패: {e}")

    def _parse_with_pyhwp_cli(self, file_path: str) -> HWPDocument:
        """pyhwp CLI를 사용한 파싱"""
        try:
            # pyhwp를 Python 모듈로 실행
            result = subprocess.run(
                [sys.executable, '-m', 'hwp5', 'txt', file_path],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30
            )

            if result.returncode == 0:
                text = result.stdout

                # 문단 분리
                paragraphs = [
                    HWPParagraph(text=p.strip())
                    for p in text.split('\n\n')
                    if p.strip()
                ]

                return HWPDocument(
                    metadata=HWPMetadata(),
                    paragraphs=paragraphs,
                    tables=[],
                    raw_text=text
                )

        except Exception as e:
            raise Exception(f"pyhwp CLI 실행 실패: {e}")

    def _parse_with_system_command(self, file_path: str) -> HWPDocument:
        """시스템의 변환 도구를 사용한 파싱"""
        try:
            # strings 명령어로 텍스트 추출 (macOS/Linux)
            result = subprocess.run(
                ['strings', file_path],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=30
            )

            if result.returncode == 0:
                lines = result.stdout.split('\n')

                # 한글이 포함된 라인만 필터링
                korean_lines = []
                for line in lines:
                    if any('\uac00' <= char <= '\ud7af' for char in line):
                        korean_lines.append(line.strip())

                text = '\n'.join(korean_lines)

                paragraphs = [
                    HWPParagraph(text=p.strip())
                    for p in korean_lines
                    if p.strip()
                ]

                return HWPDocument(
                    metadata=HWPMetadata(),
                    paragraphs=paragraphs,
                    tables=[],
                    raw_text=text
                )

        except Exception as e:
            raise Exception(f"시스템 명령어 실행 실패: {e}")

    def _parse_with_basic_extraction(self, file_path: str) -> HWPDocument:
        """기본 바이너리 추출"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()

            # 한글 텍스트 패턴 찾기
            texts = []
            i = 0
            while i < len(data) - 1:
                # UTF-16 LE 한글 범위 체크
                if i < len(data) - 3:
                    # 2바이트씩 읽어서 UTF-16 LE로 디코딩 시도
                    chunk = data[i:i+2]
                    try:
                        char = chunk.decode('utf-16-le', errors='ignore')
                        if '\uac00' <= char <= '\ud7af' or char in ' \n\r\t':
                            # 한글 또는 공백 문자면 계속 읽기
                            text_chunk = chunk
                            j = i + 2
                            while j < len(data) - 1:
                                next_chunk = data[j:j+2]
                                try:
                                    next_char = next_chunk.decode('utf-16-le', errors='ignore')
                                    if '\uac00' <= next_char <= '\ud7af' or next_char in ' \n\r\t.,!?':
                                        text_chunk += next_chunk
                                        j += 2
                                    else:
                                        break
                                except:
                                    break

                            if len(text_chunk) > 4:  # 최소 2글자 이상
                                decoded = text_chunk.decode('utf-16-le', errors='ignore').strip()
                                if decoded and len(decoded) > 1:
                                    texts.append(decoded)
                            i = j
                            continue
                    except:
                        pass

                i += 1

            # 중복 제거 및 정리
            unique_texts = []
            seen = set()
            for text in texts:
                if text not in seen and len(text) > 2:
                    seen.add(text)
                    unique_texts.append(text)

            paragraphs = [HWPParagraph(text=t) for t in unique_texts]
            raw_text = '\n'.join(unique_texts)

            return HWPDocument(
                metadata=HWPMetadata(),
                paragraphs=paragraphs,
                tables=[],
                raw_text=raw_text
            )

        except Exception as e:
            raise Exception(f"기본 추출 실패: {e}")

    def extract_text(self, file_path: str) -> str:
        """텍스트만 빠르게 추출"""
        doc = self.parse(file_path)
        return doc.raw_text