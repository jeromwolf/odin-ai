"""
HWP 파일 직접 추출 모듈 (subprocess 없이 Python 라이브러리 직접 사용)
"""

import io
from pathlib import Path
from typing import Optional, Tuple
from loguru import logger

try:
    import hwp5
    import hwp5.xmlmodel
    import hwp5.binmodel
    import hwp5.dataio
    HWP5_AVAILABLE = True
except ImportError:
    HWP5_AVAILABLE = False
    logger.warning("hwp5 library not available")


def extract_hwp_direct(file_path: Path) -> Tuple[Optional[str], str]:
    """HWP 파일에서 텍스트를 직접 추출 (subprocess 없이)

    Args:
        file_path: HWP 파일 경로

    Returns:
        (추출된 텍스트, 추출 방법)
    """
    if not HWP5_AVAILABLE:
        return None, "hwp5-not-available"

    try:
        # HWP 파일 열기
        import olefile
        hwp_file = hwp5.HWPDocument(str(file_path))
        text_parts = []

        # 본문 텍스트 추출
        try:
            # BodyText 섹션들 읽기
            for section in hwp_file.bodytext.sections:
                try:
                    # 각 섹션의 텍스트 추출
                    for paragraph in section:
                        if hasattr(paragraph, 'text'):
                            text = str(paragraph.text())
                            if text.strip():
                                text_parts.append(text.strip())
                except Exception as e:
                    logger.debug(f"Section parsing error: {e}")
                    continue
        except AttributeError:
            # bodytext가 없는 경우 대체 방법
            logger.debug("No bodytext found, trying alternative method")

            # DocInfo에서 텍스트 추출 시도
            try:
                if hasattr(hwp_file, 'docinfo'):
                    docinfo_text = extract_from_docinfo(hwp_file.docinfo)
                    if docinfo_text:
                        text_parts.append(docinfo_text)
            except Exception as e:
                logger.debug(f"DocInfo extraction error: {e}")

        if text_parts:
            return '\n\n'.join(text_parts), 'hwp5-direct'
        else:
            return None, "no-text-extracted"

    except Exception as e:
        logger.error(f"HWP direct extraction error: {e}")
        return None, f"error-{str(e)[:50]}"


def extract_from_docinfo(docinfo) -> Optional[str]:
    """DocInfo에서 텍스트 추출

    Args:
        docinfo: HWP DocInfo 객체

    Returns:
        추출된 텍스트
    """
    text_parts = []

    try:
        # 문서 요약 정보
        if hasattr(docinfo, 'summary'):
            summary = docinfo.summary
            if hasattr(summary, 'title') and summary.title:
                text_parts.append(f"제목: {summary.title}")
            if hasattr(summary, 'subject') and summary.subject:
                text_parts.append(f"주제: {summary.subject}")
            if hasattr(summary, 'author') and summary.author:
                text_parts.append(f"작성자: {summary.author}")
            if hasattr(summary, 'keywords') and summary.keywords:
                text_parts.append(f"키워드: {summary.keywords}")
    except Exception as e:
        logger.debug(f"Summary extraction error: {e}")

    return '\n'.join(text_parts) if text_parts else None


def extract_hwp_as_xml(file_path: Path) -> Tuple[Optional[str], str]:
    """HWP 파일을 XML로 변환하여 텍스트 추출

    Args:
        file_path: HWP 파일 경로

    Returns:
        (추출된 텍스트, 추출 방법)
    """
    if not HWP5_AVAILABLE:
        return None, "hwp5-not-available"

    try:
        import xml.etree.ElementTree as ET

        # HWP를 XML로 변환
        output = io.StringIO()

        hwp_file = hwp5.HWPDocument(str(file_path))
        # XML 형식으로 내보내기
        hwp5.xmlmodel.Hwp5File(hwp_file).xmlevents().dump(output)

        # XML 파싱
        xml_content = output.getvalue()
        if not xml_content:
            return None, "no-xml-content"

        # 텍스트 추출
        root = ET.fromstring(xml_content)
        text_parts = []

        # 모든 텍스트 노드 찾기
        for elem in root.iter():
            if elem.text and elem.text.strip():
                text_parts.append(elem.text.strip())

        if text_parts:
            return '\n'.join(text_parts), 'hwp5-xml'
        else:
            return None, "no-text-in-xml"

    except Exception as e:
        logger.error(f"HWP XML extraction error: {e}")
        return None, f"xml-error-{str(e)[:50]}"


def extract_hwp_safe(file_path: Path) -> Tuple[Optional[str], str]:
    """안전한 HWP 텍스트 추출 (여러 방법 시도)

    Args:
        file_path: HWP 파일 경로

    Returns:
        (추출된 텍스트, 추출 방법)
    """
    # 방법 1: 직접 추출
    text, method = extract_hwp_direct(file_path)
    if text:
        return text, method

    # 방법 2: XML 변환 추출
    text, method = extract_hwp_as_xml(file_path)
    if text:
        return text, method

    return None, "all-methods-failed"