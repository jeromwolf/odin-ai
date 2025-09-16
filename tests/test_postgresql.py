#!/usr/bin/env python3
"""
PostgreSQL 연결 및 성능 테스트 스크립트
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# 프로젝트 루트를 경로에 추가
sys.path.append(str(Path(__file__).parent))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from backend.models.database import engine, get_db
from backend.models.bid_models import BidAnnouncement
from backend.models.user_models import User


async def test_postgresql_connection():
    """PostgreSQL 연결 테스트"""
    print("=" * 60)
    print("PostgreSQL 연결 테스트")
    print("=" * 60)

    try:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # PostgreSQL 버전 확인
        result = db.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"✅ PostgreSQL 연결 성공")
        print(f"📊 버전: {version[:50]}...")

        # 데이터베이스 정보
        result = db.execute(text("SELECT current_database(), current_user"))
        db_info = result.fetchone()
        print(f"🗄️ 데이터베이스: {db_info[0]}")
        print(f"👤 사용자: {db_info[1]}")

        # 테이블 목록 확인
        result = db.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = result.fetchall()
        print(f"📋 생성된 테이블: {len(tables)}개")
        for table in tables:
            print(f"   - {table[0]}")

        db.close()
        return True

    except Exception as e:
        print(f"❌ PostgreSQL 연결 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_postgresql_performance():
    """PostgreSQL 성능 테스트"""
    print("\n" + "=" * 60)
    print("PostgreSQL 성능 테스트")
    print("=" * 60)

    try:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # 대량 데이터 삽입 테스트
        start_time = datetime.now()

        # 100건의 테스트 입찰공고 생성
        test_bids = []
        for i in range(100):
            bid = BidAnnouncement(
                bid_notice_no=f"PERF-TEST-{i:03d}",
                bid_notice_name=f"성능 테스트 입찰공고 {i+1}",
                bid_notice_date=datetime.now(timezone.utc),
                notice_inst_name="성능테스트기관",
                bid_status="공고중",
                presumpt_price=10000000 + (i * 100000)
            )
            test_bids.append(bid)

        db.add_all(test_bids)
        db.commit()

        insert_time = (datetime.now() - start_time).total_seconds()
        print(f"✅ 대량 삽입 (100건): {insert_time:.2f}초")

        # 인덱스 성능 테스트
        start_time = datetime.now()
        result = db.query(BidAnnouncement).filter(
            BidAnnouncement.bid_status == "공고중"
        ).count()

        index_time = (datetime.now() - start_time).total_seconds()
        print(f"✅ 인덱스 검색 ({result}건): {index_time:.3f}초")

        # 범위 검색 테스트 (예산 범위)
        start_time = datetime.now()
        result = db.query(BidAnnouncement).filter(
            BidAnnouncement.presumpt_price.between(10000000, 15000000)
        ).count()

        range_time = (datetime.now() - start_time).total_seconds()
        print(f"✅ 범위 검색 ({result}건): {range_time:.3f}초")

        # 텍스트 검색 테스트
        start_time = datetime.now()
        result = db.query(BidAnnouncement).filter(
            BidAnnouncement.bid_notice_name.like("%성능 테스트%")
        ).count()

        text_search_time = (datetime.now() - start_time).total_seconds()
        print(f"✅ 텍스트 검색 ({result}건): {text_search_time:.3f}초")

        # 정리
        db.query(BidAnnouncement).filter(
            BidAnnouncement.bid_notice_no.like("PERF-TEST-%")
        ).delete(synchronize_session=False)
        db.commit()
        print("🧹 테스트 데이터 정리 완료")

        db.close()
        return True

    except Exception as e:
        print(f"❌ 성능 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        db.close()
        return False


async def test_postgresql_extensions():
    """PostgreSQL 확장 기능 테스트"""
    print("\n" + "=" * 60)
    print("PostgreSQL 확장 기능 테스트")
    print("=" * 60)

    try:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # 설치된 확장 확인
        result = db.execute(text("""
            SELECT extname, extversion
            FROM pg_extension
            WHERE extname != 'plpgsql'
            ORDER BY extname
        """))
        extensions = result.fetchall()
        print(f"🔧 설치된 확장: {len(extensions)}개")
        for ext in extensions:
            print(f"   - {ext[0]} v{ext[1]}")

        # JSON 기능 테스트
        db.execute(text("""
            CREATE TEMPORARY TABLE test_json (
                id SERIAL PRIMARY KEY,
                data JSONB
            )
        """))

        db.execute(text("""
            INSERT INTO test_json (data) VALUES
            ('{"name": "테스트", "type": "공사", "budget": 1000000}'),
            ('{"name": "프로젝트", "type": "용역", "budget": 500000}')
        """))

        result = db.execute(text("""
            SELECT data->>'name' as name, data->>'budget' as budget
            FROM test_json
            WHERE data->>'type' = '공사'
        """))

        json_result = result.fetchone()
        print(f"✅ JSON 검색 테스트: {json_result[0]}, 예산: {json_result[1]}")

        # 전문 검색 기능 테스트
        result = db.execute(text("""
            SELECT to_tsvector('korean', '입찰공고 시스템 개발 프로젝트') @@
                   to_tsquery('korean', '시스템 & 개발') as match_result
        """))

        search_result = result.fetchone()[0]
        print(f"✅ 전문 검색 테스트: {'성공' if search_result else '실패'}")

        db.close()
        return True

    except Exception as e:
        print(f"❌ 확장 기능 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        db.close()
        return False


async def main():
    """메인 테스트 실행"""
    print("🚀 PostgreSQL 종합 테스트 시작\n")

    tests = [
        ("PostgreSQL 연결", test_postgresql_connection),
        ("성능 테스트", test_postgresql_performance),
        ("확장 기능", test_postgresql_extensions),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} 테스트 실행 중 오류: {e}")
            results.append((name, False))

    # 결과 요약
    print("\n" + "=" * 60)
    print("🏁 PostgreSQL 테스트 결과 요약")
    print("=" * 60)

    success_count = 0
    for name, result in results:
        if result:
            print(f"✅ {name}: 성공")
            success_count += 1
        else:
            print(f"❌ {name}: 실패")

    print(f"\n📊 총 {len(results)}개 테스트 중 {success_count}개 성공")

    if success_count == len(results):
        print("🎉 PostgreSQL 완전 준비 완료!")
        print("💡 다음 단계: 나라장터 크롤러 구현")
        return 0
    else:
        print("⚠️ 일부 테스트 실패")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)