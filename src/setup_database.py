#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError, ProgrammingError
from database.models import Base
from shared.config import settings
from loguru import logger


def create_database_if_not_exists():
    """데이터베이스가 없으면 생성"""
    # 데이터베이스 이름 추출
    db_url = settings.database_url
    db_name = db_url.split('/')[-1]

    # 데이터베이스 없이 연결 (postgres 기본 DB 사용)
    base_url = db_url.rsplit('/', 1)[0]
    postgres_url = f"{base_url}/postgres"

    try:
        # postgres DB에 연결
        engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")

        with engine.connect() as conn:
            # 데이터베이스 존재 확인
            result = conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": db_name}
            )
            exists = result.scalar()

            if not exists:
                # 데이터베이스 생성
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                logger.info(f"데이터베이스 '{db_name}' 생성 완료")
            else:
                logger.info(f"데이터베이스 '{db_name}'가 이미 존재합니다")

    except OperationalError as e:
        logger.error(f"데이터베이스 연결 실패: {e}")
        return False
    except Exception as e:
        logger.error(f"데이터베이스 생성 실패: {e}")
        return False

    return True


def create_all_tables():
    """모든 테이블 생성"""
    try:
        logger.info("데이터베이스 테이블 생성 시작...")

        # 실제 데이터베이스에 연결
        engine = create_engine(settings.database_url)

        # 모든 테이블 생성
        Base.metadata.create_all(bind=engine)
        logger.info("모든 테이블 생성 완료!")

        # 생성된 테이블 확인
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        logger.info(f"생성된 테이블 목록:")
        for table in tables:
            logger.info(f"   - {table}")

        return True

    except Exception as e:
        logger.error(f"테이블 생성 실패: {e}")
        return False


def drop_all_tables():
    """모든 테이블 삭제 (주의!)"""
    try:
        logger.warning("모든 테이블 삭제 시작...")

        engine = create_engine(settings.database_url)
        Base.metadata.drop_all(bind=engine)

        logger.info("모든 테이블 삭제 완료")
        return True

    except Exception as e:
        logger.error(f"테이블 삭제 실패: {e}")
        return False


def verify_database():
    """데이터베이스 연결 및 테이블 확인"""
    try:
        engine = create_engine(settings.database_url)

        with engine.connect() as conn:
            # 연결 테스트
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"PostgreSQL 버전: {version}")

            # 테이블 수 확인
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM pg_tables "
                    "WHERE schemaname = 'public'"
                )
            )
            table_count = result.scalar()

            # 각 테이블의 레코드 수 확인
            tables_info = []
            result = conn.execute(
                text(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname = 'public' "
                    "ORDER BY tablename"
                )
            )

            for row in result:
                table_name = row[0]
                count_result = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                count = count_result.scalar()
                tables_info.append(f"{table_name}({count})")

            logger.info(f"테이블 수: {table_count}")
            if tables_info:
                logger.info(f"테이블 정보: {', '.join(tables_info)}")

            return True

    except Exception as e:
        logger.error(f"데이터베이스 검증 실패: {e}")
        return False


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="Odin-AI 데이터베이스 초기화")
    parser.add_argument('--create', action='store_true', help='데이터베이스 및 테이블 생성')
    parser.add_argument('--drop', action='store_true', help='모든 테이블 삭제')
    parser.add_argument('--verify', action='store_true', help='데이터베이스 상태 확인')

    args = parser.parse_args()

    # 기본 동작: verify
    if not any([args.create, args.drop, args.verify]):
        args.verify = True

    logger.info("=" * 50)
    logger.info("Odin-AI 데이터베이스 초기화 스크립트")
    logger.info("=" * 50)

    if args.drop:
        response = input("⚠️  모든 테이블을 삭제하시겠습니까? (yes/no): ")
        if response.lower() == 'yes':
            drop_all_tables()
        else:
            logger.info("삭제 취소")

    if args.create:
        # 데이터베이스 생성
        if create_database_if_not_exists():
            # 테이블 생성
            create_all_tables()

    if args.verify:
        verify_database()

    logger.info("=" * 50)
    logger.info("완료")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()