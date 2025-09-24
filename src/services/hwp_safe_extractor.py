"""
HWP 파일 안전 추출 모듈 (subprocess를 사용하되 작업 디렉토리를 변경)
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from loguru import logger


def extract_hwp_subprocess(file_path: Path) -> Tuple[Optional[str], str]:
    """HWP 파일에서 텍스트를 안전하게 추출 (임시 디렉토리 사용)

    Args:
        file_path: HWP 파일 경로

    Returns:
        (추출된 텍스트, 추출 방법)
    """
    try:
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 원본 파일을 임시 디렉토리로 복사
            import shutil
            temp_hwp = temp_path / file_path.name
            shutil.copy2(file_path, temp_hwp)

            # hwp5txt 실행 (임시 디렉토리에서)
            result = subprocess.run(
                ['hwp5txt', str(temp_hwp)],
                capture_output=True,
                text=True,
                cwd=temp_dir,  # 작업 디렉토리를 임시 디렉토리로 설정
                timeout=30
            )

            if result.returncode == 0 and result.stdout:
                text = result.stdout.strip()
                if text and len(text) > 10:  # 최소 10자 이상이어야 유효한 텍스트로 간주
                    logger.info(f"HWP subprocess 추출 성공: {file_path.name} - {len(text)}자")
                    return text, "hwp5txt-subprocess"
                else:
                    logger.warning(f"HWP subprocess 추출했지만 텍스트가 너무 짧음: {len(text)}자")
                    return None, "text-too-short"
            else:
                error_msg = result.stderr if result.stderr else "No output"
                logger.warning(f"HWP subprocess 실패: {error_msg[:100]}")
                return None, f"subprocess-failed"

    except subprocess.TimeoutExpired:
        logger.error(f"HWP subprocess 타임아웃: {file_path.name}")
        return None, "timeout"
    except Exception as e:
        logger.error(f"HWP subprocess 오류: {e}")
        return None, f"error-{str(e)[:50]}"


def extract_hwp_safe(file_path: Path) -> Tuple[Optional[str], str]:
    """안전한 HWP 텍스트 추출 (루트 디렉토리 오염 방지)

    Args:
        file_path: HWP 파일 경로

    Returns:
        (추출된 텍스트, 추출 방법)
    """
    # subprocess로 안전하게 추출
    text, method = extract_hwp_subprocess(file_path)

    if text:
        return text, method

    # 실패 시 기본 정보만 반환
    file_size = file_path.stat().st_size
    fallback_text = f"""[HWP 문서]
파일명: {file_path.name}
크기: {file_size:,} bytes

(텍스트 추출 실패 - 방법: {method})
"""
    return fallback_text, f"fallback-{method}"