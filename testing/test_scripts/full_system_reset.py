#!/usr/bin/env python
"""
시스템 완전 초기화 스크립트
데이터베이스와 파일 시스템을 완전히 초기화
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, text
from loguru import logger

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.database.models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://blockmeta@localhost:5432/odin_db")


def reset_database():
    """데이터베이스 완전 초기화"""
    logger.info("📊 데이터베이스 초기화 시작...")

    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conn:
            # 모든 테이블 DROP
            logger.info("🗑️ 기존 테이블 삭제 중...")
            tables = ['bid_attachments', 'bid_documents', 'bid_announcements']
            for table in tables:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                    conn.commit()
                    logger.info(f"  ✅ {table} 테이블 삭제")
                except Exception as e:
                    logger.warning(f"  ⚠️ {table} 삭제 실패: {e}")

            # 추가로 남은 테이블 확인 및 삭제
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
            """))
            remaining_tables = [row[0] for row in result]

            if remaining_tables:
                logger.warning(f"남은 테이블 발견: {remaining_tables}")
                for table in remaining_tables:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                    conn.commit()
                    logger.info(f"  ✅ {table} 추가 삭제")

        # ORM을 사용한 테이블 재생성
        logger.info("🔨 새 테이블 생성 중...")
        Base.metadata.create_all(engine)

        # 생성된 테이블 확인
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """))

            created_tables = [row[0] for row in result]
            logger.info(f"✅ 생성된 테이블: {created_tables}")

            # 인덱스 생성
            logger.info("📑 인덱스 생성 중...")
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_bid_announcements_bid_notice_no ON bid_announcements(bid_notice_no)",
                "CREATE INDEX IF NOT EXISTS idx_bid_documents_bid_notice_no ON bid_documents(bid_notice_no)",
                "CREATE INDEX IF NOT EXISTS idx_bid_documents_status ON bid_documents(download_status, processing_status)",
                "CREATE INDEX IF NOT EXISTS idx_bid_documents_extension ON bid_documents(file_extension)"
            ]

            for idx_sql in indexes:
                try:
                    conn.execute(text(idx_sql))
                    conn.commit()
                    logger.info(f"  ✅ 인덱스 생성")
                except Exception as e:
                    logger.warning(f"  ⚠️ 인덱스 생성 실패: {e}")

        logger.info("✅ 데이터베이스 초기화 완료!")
        return True

    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 실패: {e}")
        return False


def reset_filesystem():
    """파일 시스템 초기화"""
    logger.info("📁 파일 시스템 초기화 시작...")

    try:
        # storage 디렉토리 완전 삭제 및 재생성
        storage_path = Path("./storage")
        if storage_path.exists():
            logger.info(f"🗑️ {storage_path} 삭제 중...")
            shutil.rmtree(storage_path)

        # 디렉토리 재생성
        directories = [
            storage_path / "documents",
            storage_path / "markdown" / "2025" / "09" / "22",
            storage_path / "temp",
            storage_path / "logs"
        ]

        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"  ✅ {dir_path} 생성")

        # 루트의 임시 디렉토리 정리
        logger.info("🧹 루트 임시 디렉토리 정리 중...")
        root_path = Path(".")
        patterns_to_remove = []

        # 언더스코어로 끝나는 디렉토리
        for item in root_path.glob("*_"):
            if item.is_dir():
                patterns_to_remove.append(item)

        # standard 디렉토리
        if (root_path / "standard").exists():
            patterns_to_remove.append(root_path / "standard")

        # 숫자로 시작하는 디렉토리
        for item in root_path.iterdir():
            if item.is_dir() and item.name[0].isdigit() and "_" in item.name:
                patterns_to_remove.append(item)

        removed_count = 0
        for item in patterns_to_remove:
            try:
                shutil.rmtree(item)
                logger.info(f"  ✅ {item.name} 삭제")
                removed_count += 1
            except Exception as e:
                logger.warning(f"  ⚠️ {item.name} 삭제 실패: {e}")

        logger.info(f"🧹 {removed_count}개 임시 디렉토리 정리 완료")

        # 로그 파일 백업 및 초기화
        logger.info("📝 로그 파일 초기화 중...")
        logs_path = Path("./logs")
        if logs_path.exists():
            # 백업
            backup_name = f"logs_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = Path(f"./{backup_name}")
            shutil.copytree(logs_path, backup_path)
            logger.info(f"  ✅ 로그 백업: {backup_path}")

            # 로그 파일 초기화
            for log_file in logs_path.glob("*.log"):
                log_file.unlink()
            logger.info("  ✅ 로그 파일 초기화")

        logger.info("✅ 파일 시스템 초기화 완료!")
        return True

    except Exception as e:
        logger.error(f"❌ 파일 시스템 초기화 실패: {e}")
        return False


def verify_reset():
    """초기화 확인"""
    logger.info("🔍 초기화 상태 확인 중...")

    checks = {
        "database": False,
        "filesystem": False,
        "temp_dirs": False
    }

    # 데이터베이스 확인
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM bid_announcements
                UNION ALL SELECT COUNT(*) FROM bid_documents
                UNION ALL SELECT COUNT(*) FROM bid_attachments
            """))
            counts = [row[0] for row in result]

            if all(count == 0 for count in counts):
                checks["database"] = True
                logger.info("  ✅ 데이터베이스: 비어있음")
            else:
                logger.warning(f"  ⚠️ 데이터베이스: 레코드 존재 {counts}")
    except Exception as e:
        logger.error(f"  ❌ 데이터베이스 확인 실패: {e}")

    # 파일시스템 확인
    storage_path = Path("./storage")
    if storage_path.exists():
        doc_count = len(list((storage_path / "documents").glob("**/*")))
        if doc_count == 0:
            checks["filesystem"] = True
            logger.info("  ✅ 파일시스템: 비어있음")
        else:
            logger.warning(f"  ⚠️ 파일시스템: {doc_count}개 파일 존재")
    else:
        logger.warning("  ⚠️ storage 디렉토리 없음")

    # 임시 디렉토리 확인
    root_path = Path(".")
    temp_dirs = [d for d in root_path.glob("*_") if d.is_dir()]
    if len(temp_dirs) == 0:
        checks["temp_dirs"] = True
        logger.info("  ✅ 임시 디렉토리: 정리됨")
    else:
        logger.warning(f"  ⚠️ 임시 디렉토리: {len(temp_dirs)}개 존재")

    # 전체 결과
    if all(checks.values()):
        logger.info("✅ 모든 초기화 확인 완료!")
        return True
    else:
        logger.warning("⚠️ 일부 초기화 미완료")
        return False


def main():
    """메인 실행 함수"""
    logger.info("=" * 60)
    logger.info("🔄 시스템 완전 초기화 시작")
    logger.info(f"📅 시작 시간: {datetime.now()}")
    logger.info("=" * 60)

    # 초기화 수행
    steps = [
        ("데이터베이스 초기화", reset_database),
        ("파일시스템 초기화", reset_filesystem),
        ("초기화 확인", verify_reset)
    ]

    success = True
    for step_name, step_func in steps:
        logger.info(f"\n{'=' * 40}")
        logger.info(f"🔄 {step_name}")
        logger.info(f"{'=' * 40}")

        if not step_func():
            logger.error(f"❌ {step_name} 실패!")
            success = False
            break

    # 최종 결과
    logger.info("\n" + "=" * 60)
    if success:
        logger.info("✅ 시스템 초기화 완료!")
    else:
        logger.error("❌ 시스템 초기화 실패!")
    logger.info(f"📅 완료 시간: {datetime.now()}")
    logger.info("=" * 60)

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)