#!/usr/bin/env python
"""
RAG 임베딩 생성 모듈
문서를 청크로 분할하고 벡터 임베딩을 생성하여 rfp_chunks 테이블에 저장
"""

import os
import sys
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# backend/services 경로 추가
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# 임베딩/청킹 서비스 임포트 (optional)
try:
    from services.embedding_service import get_embedding_provider
    from services.chunker import get_chunker
    EMBEDDING_AVAILABLE = True
except ImportError as e:
    EMBEDDING_AVAILABLE = False
    logger.warning(f"임베딩 서비스 로드 실패: {e}")


class EmbeddingGenerator:
    """문서 임베딩 생성기"""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.stats = {
            'total_documents': 0,
            'documents_processed': 0,
            'documents_skipped': 0,
            'documents_failed': 0,
            'chunks_created': 0,
            'embeddings_generated': 0,
        }

    def generate_embeddings(self, limit: int = None, force: bool = False) -> dict:
        """
        미처리 문서에 대해 임베딩 생성

        Args:
            limit: 처리할 최대 문서 수 (None = 전체)
            force: True면 이미 임베딩된 문서도 재처리

        Returns:
            처리 통계 dict
        """
        if not EMBEDDING_AVAILABLE:
            logger.warning("임베딩 서비스 사용 불가 - 건너뜀")
            return self.stats

        embedder = get_embedding_provider()
        if not embedder:
            logger.warning("OPENAI_API_KEY 미설정 - 임베딩 생성 건너뜀")
            return self.stats

        chunker = get_chunker()

        import psycopg2
        conn = psycopg2.connect(self.db_url)

        try:
            cursor = conn.cursor()

            # 1. 임베딩이 필요한 문서 조회
            if force:
                query = """
                    SELECT bd.document_id, bd.bid_notice_no, bd.extracted_text
                    FROM bid_documents bd
                    JOIN bid_announcements ba ON bd.bid_notice_no = ba.bid_notice_no
                    WHERE bd.processing_status = 'completed'
                    AND bd.extracted_text IS NOT NULL
                    AND LENGTH(bd.extracted_text) > 100
                    ORDER BY bd.document_id DESC
                """
            else:
                query = """
                    SELECT bd.document_id, bd.bid_notice_no, bd.extracted_text
                    FROM bid_documents bd
                    JOIN bid_announcements ba ON bd.bid_notice_no = ba.bid_notice_no
                    WHERE bd.processing_status = 'completed'
                    AND bd.extracted_text IS NOT NULL
                    AND LENGTH(bd.extracted_text) > 100
                    AND (ba.has_embedding IS NULL OR ba.has_embedding = FALSE)
                    ORDER BY bd.document_id DESC
                """

            params = []
            if limit:
                query += " LIMIT %s"
                params.append(int(limit))

            cursor.execute(query, params if params else None)
            documents = cursor.fetchall()
            self.stats['total_documents'] = len(documents)

            if not documents:
                logger.info("임베딩 대상 문서 없음")
                return self.stats

            logger.info(f"임베딩 대상 문서: {len(documents)}건")

            # 2. 각 문서를 청킹하고 임베딩 생성
            for doc_idx, (document_id, bid_notice_no, extracted_text) in enumerate(documents):
                try:
                    # 2a. Try to read full text from markdown file first
                    full_text = self._read_markdown_file(bid_notice_no)
                    if not full_text:
                        full_text = extracted_text  # Fallback to DB text (may be truncated)

                    if not full_text or len(full_text.strip()) < 100:
                        self.stats['documents_skipped'] += 1
                        continue

                    # 2b. Chunk the document
                    chunks = chunker.chunk_document(
                        markdown_text=full_text,
                        bid_notice_no=bid_notice_no,
                        document_id=document_id,
                    )

                    if not chunks:
                        self.stats['documents_skipped'] += 1
                        continue

                    # 2c. Generate embeddings for all chunks at once (batched API call)
                    chunk_texts = [c.text for c in chunks]
                    embeddings = embedder.embed_texts(chunk_texts)

                    # 2d. Store chunks + embeddings in rfp_chunks table
                    # First, delete existing chunks for this document (idempotent)
                    cursor.execute(
                        "DELETE FROM rfp_chunks WHERE bid_notice_no = %s",
                        (bid_notice_no,)
                    )

                    for chunk, embedding in zip(chunks, embeddings):
                        if embedding is None:
                            continue  # Skip failed embeddings

                        cursor.execute("""
                            INSERT INTO rfp_chunks (
                                bid_notice_no, document_id, chunk_index,
                                chunk_text, embedding, embedding_model,
                                section_type, token_count
                            ) VALUES (%s, %s, %s, %s, %s::vector, %s, %s, %s)
                        """, (
                            bid_notice_no,
                            document_id,
                            chunk.chunk_index,
                            chunk.text,
                            str(embedding),  # Convert list to string for pgvector
                            embedder.model_name,
                            chunk.section_type,
                            chunk.token_count,
                        ))
                        self.stats['embeddings_generated'] += 1

                    self.stats['chunks_created'] += len(chunks)

                    # 2e. Mark document as embedded
                    cursor.execute(
                        "UPDATE bid_announcements SET has_embedding = TRUE WHERE bid_notice_no = %s",
                        (bid_notice_no,)
                    )

                    conn.commit()
                    self.stats['documents_processed'] += 1

                    # Progress logging every 10 documents
                    if (doc_idx + 1) % 10 == 0:
                        logger.info(
                            f"임베딩 진행: {doc_idx + 1}/{len(documents)} "
                            f"(청크: {self.stats['chunks_created']}, "
                            f"임베딩: {self.stats['embeddings_generated']})"
                        )

                except Exception as e:
                    logger.error(f"문서 임베딩 실패 (bid={bid_notice_no}): {e}")
                    conn.rollback()
                    self.stats['documents_failed'] += 1
                    continue

            logger.info(
                f"임베딩 생성 완료: "
                f"처리={self.stats['documents_processed']}, "
                f"스킵={self.stats['documents_skipped']}, "
                f"실패={self.stats['documents_failed']}, "
                f"청크={self.stats['chunks_created']}, "
                f"임베딩={self.stats['embeddings_generated']}"
            )

        finally:
            conn.close()

        return self.stats

    def _read_markdown_file(self, bid_notice_no: str) -> str:
        """마크다운 파일에서 전체 텍스트 읽기 (truncation 없는 원본)"""
        # Try multiple path patterns
        storage_base = Path("storage/markdown")

        # Pattern 1: storage/markdown/{YYYY}/{MM}/{DD}/{bid_notice_no}_standard.md
        # Pattern 2: storage/markdown/{bid_notice_no}.md
        # Pattern 3: search recursively

        # Quick search in storage/markdown/
        if storage_base.exists():
            # Search for any markdown file matching this bid_notice_no
            for md_file in storage_base.rglob(f"*{bid_notice_no}*.md"):
                try:
                    text = md_file.read_text(encoding='utf-8')
                    if len(text) > 100:
                        return text
                except Exception:
                    continue

        return None


# Standalone execution for testing
if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description='ODIN-AI 임베딩 생성기')
    parser.add_argument('--limit', type=int, default=None, help='처리할 최대 문서 수')
    parser.add_argument('--force', action='store_true', help='이미 임베딩된 문서도 재처리')
    args = parser.parse_args()

    db_url = os.getenv('DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db')

    generator = EmbeddingGenerator(db_url)
    stats = generator.generate_embeddings(limit=args.limit, force=args.force)

    print(f"\n{'='*40}")
    print(f"임베딩 생성 결과:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print(f"{'='*40}")
