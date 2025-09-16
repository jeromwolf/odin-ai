"""
HWP 파일 변환 모듈
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)


class HWPConverter:
    """HWP 파일을 다른 형식으로 변환하는 클래스"""

    def __init__(self):
        self.libreoffice_path = self._find_libreoffice()

    def _find_libreoffice(self) -> Optional[str]:
        """LibreOffice 실행 파일 찾기"""
        possible_paths = [
            # macOS
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            # Linux
            "/usr/bin/libreoffice",
            "/usr/bin/soffice",
            # Windows
            "C:\\Program Files\\LibreOffice\\program\\soffice.exe",
            "C:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe",
        ]

        for path in possible_paths:
            if Path(path).exists():
                return path

        # PATH에서 찾기
        try:
            result = subprocess.run(['which', 'libreoffice'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        return None

    def convert_to_pdf(self, hwp_file: str, output_dir: Optional[str] = None) -> Optional[str]:
        """HWP를 PDF로 변환

        Args:
            hwp_file: HWP 파일 경로
            output_dir: 출력 디렉토리 (None이면 임시 디렉토리)

        Returns:
            변환된 PDF 파일 경로 또는 None
        """
        if not self.libreoffice_path:
            logger.error("LibreOffice를 찾을 수 없습니다. 변환 불가능")
            return None

        try:
            hwp_path = Path(hwp_file)
            if not hwp_path.exists():
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {hwp_file}")

            # 출력 디렉토리 설정
            if output_dir is None:
                output_dir = tempfile.mkdtemp()
            else:
                Path(output_dir).mkdir(parents=True, exist_ok=True)

            # LibreOffice 명령 실행
            cmd = [
                self.libreoffice_path,
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', output_dir,
                str(hwp_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                # 변환된 파일 경로 생성
                pdf_name = hwp_path.stem + '.pdf'
                pdf_path = Path(output_dir) / pdf_name

                if pdf_path.exists():
                    logger.info(f"PDF 변환 성공: {pdf_path}")
                    return str(pdf_path)
                else:
                    logger.error("PDF 파일이 생성되지 않았습니다")
                    return None
            else:
                logger.error(f"LibreOffice 변환 실패: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.error("변환 시간 초과")
            return None
        except Exception as e:
            logger.error(f"변환 중 오류 발생: {e}")
            return None

    def convert_to_html(self, hwp_file: str, output_dir: Optional[str] = None) -> Optional[str]:
        """HWP를 HTML로 변환

        Args:
            hwp_file: HWP 파일 경로
            output_dir: 출력 디렉토리 (None이면 임시 디렉토리)

        Returns:
            변환된 HTML 파일 경로 또는 None
        """
        if not self.libreoffice_path:
            logger.error("LibreOffice를 찾을 수 없습니다. 변환 불가능")
            return None

        try:
            hwp_path = Path(hwp_file)
            if not hwp_path.exists():
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {hwp_file}")

            # 출력 디렉토리 설정
            if output_dir is None:
                output_dir = tempfile.mkdtemp()
            else:
                Path(output_dir).mkdir(parents=True, exist_ok=True)

            # LibreOffice 명령 실행
            cmd = [
                self.libreoffice_path,
                '--headless',
                '--convert-to', 'html',
                '--outdir', output_dir,
                str(hwp_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                # 변환된 파일 경로 생성
                html_name = hwp_path.stem + '.html'
                html_path = Path(output_dir) / html_name

                if html_path.exists():
                    logger.info(f"HTML 변환 성공: {html_path}")
                    return str(html_path)
                else:
                    logger.error("HTML 파일이 생성되지 않았습니다")
                    return None
            else:
                logger.error(f"LibreOffice 변환 실패: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.error("변환 시간 초과")
            return None
        except Exception as e:
            logger.error(f"변환 중 오류 발생: {e}")
            return None

    def convert_to_txt(self, hwp_file: str, output_file: Optional[str] = None) -> Optional[str]:
        """HWP를 텍스트로 변환

        Args:
            hwp_file: HWP 파일 경로
            output_file: 출력 파일 경로 (None이면 임시 파일)

        Returns:
            텍스트 파일 경로 또는 None
        """
        try:
            # HWPParser를 사용하여 텍스트 추출
            from .parser import HWPParser

            parser = HWPParser()
            text = parser.extract_text(hwp_file)

            if not text:
                logger.warning("추출된 텍스트가 없습니다")
                return None

            # 출력 파일 설정
            if output_file is None:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                    f.write(text)
                    output_file = f.name
            else:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text)

            logger.info(f"텍스트 변환 성공: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"텍스트 변환 실패: {e}")
            return None

    def is_libreoffice_available(self) -> bool:
        """LibreOffice 사용 가능 여부 확인"""
        return self.libreoffice_path is not None