#!/usr/bin/env python3
"""실패한 xlsx 파일 재처리"""

import sys
import asyncio
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.services.document_processor import DocumentProcessor
from loguru import logger

# DB 연결
db_url = "postgresql://blockmeta@localhost:5432/odin_db"
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

# DocumentProcessor 인스턴스 생성
processor = DocumentProcessor(session, Path("./storage"))

async def main():
    logger.info("=" * 80)
    logger.info("실패한 xlsx 파일 재처리 시작")
    logger.info("=" * 80)
    
    # pending 상태의 문서 처리
    stats = await processor.process_pending_documents()
    
    logger.info("=" * 80)
    logger.info(f"재처리 완료: 성공 {stats['success']}/{stats['total']}, 실패 {stats['failed']}/{stats['total']}")
    logger.info("=" * 80)
    
    session.close()

if __name__ == "__main__":
    asyncio.run(main())
