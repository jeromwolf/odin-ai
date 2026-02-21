"""
개선된 문서 처리기
Excel과 PDF 처리 로직 향상
"""

import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
from loguru import logger

# PDF 처리 라이브러리들
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from pdf2image import convert_from_path
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Excel 처리 라이브러리들
try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    import xlrd
except ImportError:
    xlrd = None


class ImprovedDocumentProcessor:
    """개선된 문서 처리기"""

    async def extract_excel_improved(self, file_path: Path) -> Tuple[Optional[str], str]:
        """개선된 Excel 파일 텍스트 추출"""
        try:
            # 파일 확장자에 따른 엔진 선택
            ext = file_path.suffix.lower()
            engine = 'openpyxl' if ext in ['.xlsx', '.xlsm'] else 'xlrd'

            # 병합된 셀, 숨겨진 시트 등 복잡한 구조 처리
            all_text = []
            errors = []

            try:
                # 모든 시트 읽기 (숨겨진 시트 포함)
                excel_file = pd.ExcelFile(file_path, engine=engine)

                for sheet_name in excel_file.sheet_names:
                    try:
                        # 다양한 옵션으로 시도
                        df = None

                        # 기본 읽기
                        try:
                            df = pd.read_excel(
                                file_path,
                                sheet_name=sheet_name,
                                engine=engine,
                                header=None  # 헤더를 자동 추정하지 않음
                            )
                        except:
                            # 헤더가 있는 경우
                            try:
                                df = pd.read_excel(
                                    file_path,
                                    sheet_name=sheet_name,
                                    engine=engine
                                )
                            except:
                                pass

                        if df is not None and not df.empty:
                            # 시트 제목
                            all_text.append(f"\n=== 시트: {sheet_name} ===\n")

                            # NaN 값 처리
                            df = df.fillna('')

                            # 데이터를 문자열로 변환
                            # 각 행을 탭으로 구분
                            for idx, row in df.iterrows():
                                row_text = '\t'.join([str(val) for val in row if str(val)])
                                if row_text.strip():
                                    all_text.append(row_text)

                            # 통계 정보 추가
                            all_text.append(f"\n[{len(df)}행 x {len(df.columns)}열]")

                    except Exception as sheet_error:
                        errors.append(f"시트 '{sheet_name}' 처리 오류: {sheet_error}")
                        continue

                # 수식이나 매크로가 있는 경우 openpyxl로 추가 처리
                if ext in ['.xlsx', '.xlsm'] and openpyxl:
                    try:
                        wb = openpyxl.load_workbook(file_path, data_only=True)
                        for sheet in wb.worksheets:
                            # 병합된 셀 정보 추출
                            if sheet.merged_cells:
                                all_text.append(f"\n[시트 {sheet.title}에 병합된 셀 {len(sheet.merged_cells)}개]")
                    except:
                        pass

                if all_text:
                    result_text = '\n'.join(all_text)
                    method = f"{engine} (개선된 처리)"

                    if errors:
                        logger.warning(f"Excel 처리 경고: {'; '.join(errors)}")

                    logger.info(f"Excel 처리 성공: {file_path.name} - {len(all_text)}줄 추출")
                    return result_text, method

            except Exception as e:
                logger.error(f"Excel 처리 실패: {e}")
                # CSV로 대체 시도
                try:
                    df = pd.read_csv(file_path, encoding='utf-8-sig', sep=None, engine='python')
                    text = df.to_string()
                    return text, "CSV 대체 처리"
                except:
                    pass

            return None, None

        except Exception as e:
            logger.error(f"Excel 처리 전체 오류: {e}")
            return None, None

    async def extract_pdf_improved(self, file_path: Path) -> Tuple[Optional[str], str]:
        """개선된 PDF 파일 텍스트 추출 (OCR 포함)"""
        all_text = []
        method = []

        # 1단계: pdfplumber 시도 (표 처리 우수)
        if pdfplumber:
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        # 텍스트 추출
                        text = page.extract_text()
                        if text:
                            all_text.append(text)

                        # 표 추출
                        tables = page.extract_tables()
                        for table in tables:
                            if table:
                                # 표를 마크다운 형식으로 변환
                                table_text = self._table_to_markdown(table)
                                all_text.append(table_text)

                if all_text:
                    method.append("pdfplumber")
                    logger.info(f"PDF 텍스트 추출 (pdfplumber): {len(all_text)}개 섹션")
            except Exception as e:
                logger.warning(f"pdfplumber 실패: {e}")

        # 2단계: PyPDF2 시도
        if not all_text and PyPDF2:
            try:
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text and text.strip():
                            all_text.append(text)

                if all_text:
                    method.append("PyPDF2")
                    logger.info(f"PDF 텍스트 추출 (PyPDF2): {len(all_text)}페이지")
            except Exception as e:
                logger.warning(f"PyPDF2 실패: {e}")

        # 3단계: OCR 시도 (텍스트가 없거나 부족한 경우)
        if OCR_AVAILABLE and len(''.join(all_text)) < 100:  # 텍스트가 100자 미만이면 OCR 시도
            try:
                logger.info(f"PDF OCR 처리 시작: {file_path.name}")

                # PDF를 이미지로 변환
                images = convert_from_path(file_path, dpi=200)
                ocr_texts = []

                for i, image in enumerate(images):
                    try:
                        # 이미지에서 텍스트 추출 (한국어 우선)
                        text = pytesseract.image_to_string(image, lang='kor+eng')
                        if text and text.strip():
                            ocr_texts.append(f"[페이지 {i+1}]\n{text}")
                    except Exception as page_error:
                        logger.warning(f"OCR 페이지 {i+1} 실패: {page_error}")

                if ocr_texts:
                    all_text = ocr_texts  # OCR 결과로 대체
                    method = ["OCR (Tesseract)"]
                    logger.info(f"PDF OCR 성공: {len(ocr_texts)}페이지")
            except Exception as e:
                logger.warning(f"PDF OCR 실패: {e}")

        # 결과 반환
        if all_text:
            result_text = '\n\n'.join(all_text)
            result_method = ' + '.join(method) if method else "알 수 없음"
            return result_text, result_method

        return None, None

    def _table_to_markdown(self, table):
        """표를 마크다운 형식으로 변환"""
        if not table or not table[0]:
            return ""

        markdown = []

        # 헤더
        header = table[0]
        markdown.append('| ' + ' | '.join([str(cell) if cell else '' for cell in header]) + ' |')
        markdown.append('| ' + ' | '.join(['---' for _ in header]) + ' |')

        # 데이터 행
        for row in table[1:]:
            if row:
                markdown.append('| ' + ' | '.join([str(cell) if cell else '' for cell in row]) + ' |')

        return '\n'.join(markdown)

    async def extract_with_temp_cleanup(self, file_path: Path, file_type: str) -> Tuple[Optional[str], str]:
        """임시 디렉토리를 사용한 안전한 파일 처리"""
        temp_dir = None
        try:
            # 임시 디렉토리 생성
            temp_dir = tempfile.mkdtemp(prefix=f"odin_{file_type}_", dir="/tmp")
            logger.debug(f"임시 디렉토리 생성: {temp_dir}")

            # 파일 처리 (HWPX 등 압축 해제가 필요한 경우)
            if file_type == 'hwpx':
                # HWPX 처리 로직
                result = await self._extract_hwpx_in_temp(file_path, Path(temp_dir))
            else:
                result = (None, None)

            return result

        finally:
            # 임시 디렉토리 정리
            if temp_dir and Path(temp_dir).exists():
                try:
                    shutil.rmtree(temp_dir)
                    logger.debug(f"임시 디렉토리 삭제: {temp_dir}")
                except Exception as e:
                    logger.warning(f"임시 디렉토리 삭제 실패: {e}")

    async def _extract_hwpx_in_temp(self, file_path: Path, temp_dir: Path) -> Tuple[Optional[str], str]:
        """HWPX 파일을 임시 디렉토리에서 처리"""
        import zipfile
        import xml.etree.ElementTree as ET

        try:
            # 임시 디렉토리에 압축 해제
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Contents 디렉토리에서 section*.xml 파일 찾기
            contents_dir = temp_dir / "Contents"
            if not contents_dir.exists():
                return None, None

            text_parts = []
            section_files = sorted(contents_dir.glob("section*.xml"))

            for section_file in section_files:
                try:
                    tree = ET.parse(section_file)
                    root = tree.getroot()

                    # 텍스트 추출 (네임스페이스 처리)
                    for elem in root.iter():
                        if elem.text and elem.text.strip():
                            text_parts.append(elem.text.strip())
                except:
                    continue

            if text_parts:
                return '\n'.join(text_parts), 'HWPX-XML'

            return None, None

        except Exception as e:
            logger.error(f"HWPX 처리 오류: {e}")
            return None, None