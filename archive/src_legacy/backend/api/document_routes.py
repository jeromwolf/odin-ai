"""
문서 처리 관련 API 엔드포인트
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from typing import List, Optional
from pathlib import Path
import aiofiles
import hashlib
from datetime import datetime

from backend.services.integrated_document_processor import IntegratedDocumentProcessor

router = APIRouter(prefix="/api/documents", tags=["문서처리"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    bid_notice_no: Optional[str] = Query(None, description="입찰공고번호")
):
    """
    문서 업로드 및 처리

    - 지원 파일: HWP, PDF, DOC/DOCX
    - 자동으로 텍스트 추출 및 마크다운 변환
    """
    try:
        processor = IntegratedDocumentProcessor()

        # 파일 타입 확인
        file_type = processor.get_file_type(file.filename)
        if file_type == "unknown":
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 파일 형식입니다. (지원: HWP, PDF, DOC/DOCX)"
            )

        # 파일 저장
        save_path = Path(f"storage/downloads/{file_type}/{file.filename}")
        save_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(save_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # 파일 해시 생성
        file_hash = hashlib.sha256(content).hexdigest()

        # 문서 처리 (텍스트 추출 + 마크다운 변환)
        text = await processor.process_document(save_path)

        if text:
            # 마크다운 파일 생성
            markdown_content = processor._convert_text_to_markdown(text, file.filename)
            markdown_path = Path(f"storage/processed/{file_type}/{save_path.stem}.md")
            markdown_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(markdown_path, 'w', encoding='utf-8') as f:
                await f.write(markdown_content)

            return {
                "message": "문서 처리 성공",
                "filename": file.filename,
                "file_type": file_type,
                "file_hash": file_hash[:16],
                "text_length": len(text),
                "markdown_path": str(markdown_path),
                "bid_notice_no": bid_notice_no,
                "processed_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="텍스트 추출 실패"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"문서 처리 실패: {str(e)}"
        )


@router.post("/process-url")
async def process_document_from_url(
    url: str = Query(..., description="문서 URL"),
    bid_notice_no: Optional[str] = Query(None, description="입찰공고번호")
):
    """
    URL에서 문서 다운로드 및 처리

    - 나라장터 문서 URL 지원
    - 자동 다운로드 후 텍스트 추출
    """
    try:
        processor = IntegratedDocumentProcessor()

        # URL에서 문서 다운로드
        result = await processor.download_document(url)

        if result["success"]:
            return {
                "message": "문서 다운로드 및 처리 성공",
                "url": url,
                "filename": result["filename"],
                "file_type": result["file_type"],
                "text_length": result.get("text_length", 0),
                "save_path": result["save_path"],
                "bid_notice_no": bid_notice_no,
                "processed_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"문서 처리 실패: {result.get('error', '알 수 없는 오류')}"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"URL 처리 실패: {str(e)}"
        )


@router.get("/search")
async def search_documents(
    keyword: str = Query(..., description="검색어"),
    file_type: Optional[str] = Query(None, description="파일 타입 (hwp/pdf/doc)"),
    limit: int = Query(20, ge=1, le=100, description="결과 개수")
):
    """
    처리된 문서에서 텍스트 검색

    - 마크다운 파일에서 키워드 검색
    - 파일 타입별 필터링 가능
    """
    try:
        # 검색 대상 디렉토리
        if file_type:
            search_dirs = [Path(f"storage/processed/{file_type}")]
        else:
            search_dirs = [
                Path("storage/processed/hwp"),
                Path("storage/processed/pdf"),
                Path("storage/processed/doc")
            ]

        results = []
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            # 마크다운 파일 검색
            for md_file in search_dir.glob("*.md"):
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 키워드 검색
                    if keyword.lower() in content.lower():
                        # 매칭된 부분 추출
                        lines = content.split('\n')
                        matched_lines = []
                        for i, line in enumerate(lines):
                            if keyword.lower() in line.lower():
                                # 전후 문맥 포함
                                start = max(0, i - 1)
                                end = min(len(lines), i + 2)
                                matched_lines.extend(lines[start:end])

                        results.append({
                            "filename": md_file.name,
                            "file_type": search_dir.name,
                            "path": str(md_file),
                            "matched_text": "\n".join(matched_lines[:5]),  # 최대 5줄
                            "total_matches": content.lower().count(keyword.lower())
                        })

                        if len(results) >= limit:
                            break
                except Exception as e:
                    print(f"파일 읽기 실패 {md_file}: {e}")
                    continue

            if len(results) >= limit:
                break

        return {
            "keyword": keyword,
            "total_results": len(results),
            "results": results[:limit]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"검색 실패: {str(e)}"
        )


@router.get("/processed/{file_type}/{filename}")
async def download_processed_document(
    file_type: str,
    filename: str
):
    """
    처리된 마크다운 문서 다운로드

    - file_type: hwp/pdf/doc
    - filename: 파일명 (예: document.md)
    """
    try:
        file_path = Path(f"storage/processed/{file_type}/{filename}")

        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="파일을 찾을 수 없습니다."
            )

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="text/markdown"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"다운로드 실패: {str(e)}"
        )


@router.post("/batch-process")
async def batch_process_documents(
    urls: List[str],
    use_docker: bool = Query(True, description="Docker 서비스 사용 여부")
):
    """
    여러 문서 일괄 처리

    - 여러 URL을 동시에 처리
    - Docker 서비스 활용 가능
    """
    try:
        if use_docker:
            processor = IntegratedDocumentProcessor()
        else:
            processor = IntegratedDocumentProcessor()

        results = []
        for url in urls[:10]:  # 최대 10개 제한
            try:
                result = await processor.download_document(url)
                results.append({
                    "url": url,
                    "success": result.get("success", False),
                    "filename": result.get("filename"),
                    "file_type": result.get("file_type"),
                    "text_length": result.get("text_length", 0)
                })
            except Exception as e:
                results.append({
                    "url": url,
                    "success": False,
                    "error": str(e)
                })

        # 통계
        success_count = sum(1 for r in results if r["success"])

        return {
            "total": len(results),
            "success": success_count,
            "failed": len(results) - success_count,
            "results": results
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일괄 처리 실패: {str(e)}"
        )


@router.get("/status")
async def get_document_service_status():
    """
    문서 처리 서비스 상태 확인

    - Docker 서비스 상태
    - 처리된 문서 통계
    """
    try:
        processor = IntegratedDocumentProcessor()

        # Docker 서비스 상태
        health = await processor.health_check()

        # 처리된 문서 통계
        stats = {
            "hwp": len(list(Path("storage/processed/hwp").glob("*.md"))) if Path("storage/processed/hwp").exists() else 0,
            "pdf": len(list(Path("storage/processed/pdf").glob("*.md"))) if Path("storage/processed/pdf").exists() else 0,
            "doc": len(list(Path("storage/processed/doc").glob("*.md"))) if Path("storage/processed/doc").exists() else 0,
        }

        return {
            "service_health": health,
            "processed_documents": stats,
            "total_documents": sum(stats.values()),
            "storage_path": "storage/processed/"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"상태 확인 실패: {str(e)}"
        )