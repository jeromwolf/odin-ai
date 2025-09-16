#!/usr/bin/env python3
"""
PostgreSQL 간단한 연결 테스트
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from backend.core.config import settings


async def test_simple_connection():
    """PostgreSQL 연결 및 기본 기능 테스트"""
    print("🚀 PostgreSQL 연결 테스트")
    print("=" * 50)

    try:
        # 엔진 생성
        engine = create_engine(settings.DATABASE_URL, echo=True)

        # 연결 테스트
        with engine.connect() as conn:
            # PostgreSQL 버전 확인
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ 연결 성공: {version[:50]}...")

            # 데이터베이스 정보
            result = conn.execute(text("SELECT current_database(), current_user"))
            db_info = result.fetchone()
            print(f"🗄️ 데이터베이스: {db_info[0]}")
            print(f"👤 사용자: {db_info[1]}")

            # 테이블 확인
            result = conn.execute(text("""
                SELECT COUNT(*) as table_count
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name != 'alembic_version'
            """))
            table_count = result.fetchone()[0]
            print(f"📊 사용자 테이블: {table_count}개")

            # 확장 기능 확인
            result = conn.execute(text("""
                SELECT COUNT(*) as ext_count
                FROM pg_extension
                WHERE extname != 'plpgsql'
            """))
            ext_count = result.fetchone()[0]
            print(f"🔧 확장 기능: {ext_count}개")

            # 간단한 JSON 테스트
            result = conn.execute(text("""
                SELECT '{"test": "한글", "number": 123}'::jsonb->>'test' as json_test
            """))
            json_result = result.fetchone()[0]
            print(f"✅ JSON 지원: {json_result}")

        print("\n🎉 PostgreSQL 완전 준비 완료!")
        print("💡 모든 기능이 정상 작동합니다.")
        return True

    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_simple_connection())
    if result:
        print("\n✅ PostgreSQL 설정 성공 - 다음 단계로 진행 가능")
        sys.exit(0)
    else:
        print("\n❌ PostgreSQL 설정 실패")
        sys.exit(1)