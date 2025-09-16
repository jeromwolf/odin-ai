"""
PDF Viewer API 서버
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse, PlainTextResponse
import tempfile
import os
import sys
from pathlib import Path

# PDF 뷰어 모듈 import
sys.path.append(str(Path(__file__).parent.parent))
from pdf_viewer import PDFParser
from pdf_viewer.markdown_formatter import PDFMarkdownFormatter

app = FastAPI(
    title="PDF Viewer API",
    description="PDF 파일 처리 및 텍스트 추출 API",
    version="0.1.0"
)


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "service": "PDF Viewer API"}


@app.post("/extract")
async def extract_text(
    file: UploadFile = File(...),
    method: str = Form(default="auto"),
    output_format: str = Form(default="text")
):
    """PDF에서 텍스트 추출"""

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다.")

    try:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # PDF 파싱
            parser = PDFParser(method=method)
            doc = parser.parse(tmp_path)

            if output_format == "markdown" or output_format == "md":
                # 마크다운 변환
                formatter = PDFMarkdownFormatter()

                metadata = {
                    "원본 파일": file.filename,
                    "파싱 방법": method
                }
                if doc.metadata.title:
                    metadata["제목"] = doc.metadata.title
                if doc.metadata.author:
                    metadata["작성자"] = doc.metadata.author
                if doc.metadata.pages:
                    metadata["총 페이지"] = f"{doc.metadata.pages}페이지"

                pages_info = []
                for page in doc.pages:
                    pages_info.append({
                        'page_num': page.page_num,
                        'text': page.text,
                        'tables': page.tables
                    })

                markdown_text = formatter.format_document(
                    title=Path(file.filename).stem,
                    content=doc.raw_text,
                    metadata=metadata,
                    pages=pages_info
                )

                return PlainTextResponse(markdown_text, media_type="text/markdown")
            else:
                # 일반 텍스트
                return {
                    "filename": file.filename,
                    "method": method,
                    "text": doc.raw_text,
                    "metadata": {
                        "title": doc.metadata.title,
                        "author": doc.metadata.author,
                        "pages": doc.metadata.pages,
                        "creation_date": doc.metadata.creation_date
                    },
                    "statistics": {
                        "pages": len(doc.pages),
                        "tables": sum(len(page.tables) for page in doc.pages),
                        "text_length": len(doc.raw_text)
                    }
                }

        finally:
            # 임시 파일 삭제
            os.unlink(tmp_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 처리 오류: {str(e)}")


@app.post("/info")
async def get_pdf_info(
    file: UploadFile = File(...),
    method: str = Form(default="auto")
):
    """PDF 파일 정보 조회"""

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다.")

    try:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # PDF 파싱
            parser = PDFParser(method=method)
            doc = parser.parse(tmp_path)

            return {
                "filename": file.filename,
                "metadata": {
                    "title": doc.metadata.title,
                    "author": doc.metadata.author,
                    "creator": doc.metadata.creator,
                    "producer": doc.metadata.producer,
                    "subject": doc.metadata.subject,
                    "keywords": doc.metadata.keywords,
                    "creation_date": doc.metadata.creation_date,
                    "modification_date": doc.metadata.modification_date,
                    "pages": doc.metadata.pages
                },
                "content": {
                    "pages": len(doc.pages),
                    "tables": sum(len(page.tables) for page in doc.pages),
                    "text_length": len(doc.raw_text)
                },
                "parsing": {
                    "method": method,
                    "success": True
                }
            }

        finally:
            # 임시 파일 삭제
            os.unlink(tmp_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 처리 오류: {str(e)}")


@app.post("/tables")
async def extract_tables(
    file: UploadFile = File(...),
    method: str = Form(default="auto")
):
    """PDF에서 테이블 추출"""

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다.")

    try:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # PDF 파싱
            parser = PDFParser(method=method)
            doc = parser.parse(tmp_path)

            tables = []
            for page in doc.pages:
                for i, table in enumerate(page.tables):
                    tables.append({
                        "page": page.page_num,
                        "table_index": i + 1,
                        "rows": table.rows,
                        "cols": table.cols,
                        "data": table.cells,
                        "bbox": table.bbox
                    })

            return {
                "filename": file.filename,
                "total_tables": len(tables),
                "tables": tables
            }

        finally:
            # 임시 파일 삭제
            os.unlink(tmp_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 처리 오류: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8124, reload=True)