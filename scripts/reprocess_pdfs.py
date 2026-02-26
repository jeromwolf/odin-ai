"""
실패한 PDF 문서를 PyMuPDF(fitz)로 재처리하여 텍스트 추출 후 DB 업데이트.
임베딩 생성기가 이 문서들을 다시 처리할 수 있도록 processing_status를 'completed'로 변경.
"""

import os
import sys
import logging
import fitz  # PyMuPDF
import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_URL = os.getenv("DATABASE_URL", "postgresql://blockmeta@localhost:5432/odin_db")


def extract_text_pymupdf(pdf_path: str) -> str:
    """PyMuPDF로 PDF 텍스트 추출"""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()


def reprocess_failed_pdfs(limit: int = 0):
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()

    # 실패한 PDF 문서 조회
    query = """
        SELECT document_id, bid_notice_no, storage_path
        FROM bid_documents
        WHERE processing_status = 'failed'
          AND file_extension = 'pdf'
          AND storage_path IS NOT NULL
        ORDER BY document_id DESC
    """
    if limit > 0:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    rows = cursor.fetchall()
    total = len(rows)
    logger.info(f"재처리 대상 PDF: {total}건")

    stats = {'success': 0, 'no_file': 0, 'no_text': 0, 'error': 0}

    for i, (doc_id, bid_no, path) in enumerate(rows, 1):
        path = path.strip()

        if not os.path.exists(path):
            stats['no_file'] += 1
            continue

        try:
            text = extract_text_pymupdf(path)

            if not text or len(text) < 50:
                stats['no_text'] += 1
                continue

            # DB 업데이트: extracted_text, processing_status, extraction_method
            cursor.execute("""
                UPDATE bid_documents
                SET extracted_text = %s,
                    text_length = %s,
                    processing_status = 'completed',
                    extraction_method = 'pymupdf',
                    error_message = NULL,
                    processed_at = NOW()
                WHERE document_id = %s
            """, (text, len(text), doc_id))

            # has_embedding 플래그 리셋 (임베딩 생성기가 다시 처리하도록)
            cursor.execute("""
                UPDATE bid_announcements
                SET has_embedding = FALSE
                WHERE bid_notice_no = %s
                  AND (has_embedding IS NULL OR has_embedding = TRUE)
                  AND bid_notice_no NOT IN (
                      SELECT DISTINCT bid_notice_no FROM rfp_chunks WHERE embedding IS NOT NULL
                  )
            """, (bid_no,))

            stats['success'] += 1

            if i % 100 == 0 or i == total:
                conn.commit()
                logger.info(f"진행: {i}/{total} ({i/total*100:.1f}%) - 성공: {stats['success']}, 파일없음: {stats['no_file']}, 텍스트없음: {stats['no_text']}, 에러: {stats['error']}")

        except Exception as e:
            stats['error'] += 1
            if i % 500 == 0:
                logger.warning(f"에러 [{bid_no}]: {e}")

    conn.commit()
    conn.close()

    logger.info(f"PDF 재처리 완료: 총 {total}건")
    logger.info(f"  성공: {stats['success']}건")
    logger.info(f"  파일없음: {stats['no_file']}건")
    logger.info(f"  텍스트없음: {stats['no_text']}건 (이미지 PDF)")
    logger.info(f"  에러: {stats['error']}건")

    return stats


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    reprocess_failed_pdfs(limit=limit)
