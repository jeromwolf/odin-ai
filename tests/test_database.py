#!/usr/bin/env python3
"""
데이터베이스 연결 및 기본 CRUD 테스트 스크립트
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# 프로젝트 루트를 경로에 추가
sys.path.append(str(Path(__file__).parent))

from sqlalchemy.orm import sessionmaker
from backend.models.database import engine, get_db, Base
from backend.models.bid_models import BidAnnouncement
from backend.models.user_models import User
from backend.models.document_models import Document


async def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("=" * 60)
    print("데이터베이스 연결 테스트")
    print("=" * 60)

    try:
        # 세션 생성
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # 기본 연결 테스트
        result = db.execute("SELECT 1 as test_col")
        row = result.fetchone()
        print(f"✅ 데이터베이스 연결 성공: {row.test_col}")

        # 테이블 존재 확인
        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        print(f"📊 생성된 테이블 수: {len(tables)}")
        for table in tables:
            print(f"   - {table.name}")

        db.close()
        return True

    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_crud_operations():
    """기본 CRUD 작업 테스트"""
    print("\n" + "=" * 60)
    print("CRUD 작업 테스트")
    print("=" * 60)

    try:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # 1. Create - 사용자 생성
        test_user = User(
            email="test@odin-ai.kr",
            password_hash="dummy_hash_for_testing",
            full_name="테스트 사용자",
            company_name="오딘 AI",
            is_active=True
        )

        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✅ 사용자 생성 성공: ID {test_user.id}")

        # 2. Create - 입찰공고 생성
        test_bid = BidAnnouncement(
            bid_notice_no="TEST-2025-001",
            bid_notice_name="테스트 입찰공고",
            bid_notice_date=datetime.now(timezone.utc),
            notice_inst_name="테스트 기관",
            bid_status="공고중"
        )

        db.add(test_bid)
        db.commit()
        db.refresh(test_bid)
        print(f"✅ 입찰공고 생성 성공: {test_bid.bid_notice_no}")

        # 3. Create - 문서 생성
        test_doc = Document(
            filename="test_document.hwp",
            file_type="hwp",
            file_size=1024,
            file_hash="abc123def456",
            document_type="spec",
            processing_status="pending"
        )

        db.add(test_doc)
        db.commit()
        db.refresh(test_doc)
        print(f"✅ 문서 생성 성공: ID {test_doc.id}")

        # 4. Read - 데이터 조회
        users = db.query(User).all()
        bids = db.query(BidAnnouncement).all()
        docs = db.query(Document).all()

        print(f"📊 조회된 데이터:")
        print(f"   - 사용자: {len(users)}명")
        print(f"   - 입찰공고: {len(bids)}건")
        print(f"   - 문서: {len(docs)}개")

        # 5. Update - 데이터 수정
        test_user.full_name = "업데이트된 사용자"
        db.commit()
        print("✅ 사용자 정보 업데이트 성공")

        # 6. Delete - 데이터 삭제
        db.delete(test_doc)
        db.delete(test_bid)
        db.delete(test_user)
        db.commit()
        print("✅ 테스트 데이터 정리 완료")

        db.close()
        return True

    except Exception as e:
        print(f"❌ CRUD 작업 실패: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        db.close()
        return False


async def test_model_relationships():
    """모델 관계 테스트"""
    print("\n" + "=" * 60)
    print("모델 관계 테스트")
    print("=" * 60)

    try:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # 사용자와 북마크 관계 테스트
        from backend.models.user_models import UserBidBookmark

        # 테스트 데이터 생성
        user = User(
            email="relationship_test@odin-ai.kr",
            password_hash="test_hash",
            full_name="관계 테스트 사용자"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        bid = BidAnnouncement(
            bid_notice_no="REL-TEST-001",
            bid_notice_name="관계 테스트 입찰공고",
            bid_status="공고중"
        )
        db.add(bid)
        db.commit()
        db.refresh(bid)

        # 북마크 생성 (관계 테스트)
        bookmark = UserBidBookmark(
            user_id=user.id,
            bid_notice_no=bid.bid_notice_no,
            memo="테스트 북마크"
        )
        db.add(bookmark)
        db.commit()

        # 관계를 통한 데이터 조회
        user_bookmarks = db.query(UserBidBookmark).filter_by(user_id=user.id).all()
        print(f"✅ 관계 테스트 성공: 사용자 {user.id}의 북마크 {len(user_bookmarks)}개")

        # 정리
        db.delete(bookmark)
        db.delete(bid)
        db.delete(user)
        db.commit()
        db.close()

        return True

    except Exception as e:
        print(f"❌ 관계 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        db.close()
        return False


async def test_database_schema():
    """데이터베이스 스키마 확인"""
    print("\n" + "=" * 60)
    print("데이터베이스 스키마 확인")
    print("=" * 60)

    try:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # 인덱스 정보 확인
        indexes = db.execute("""
            SELECT name, tbl_name, sql
            FROM sqlite_master
            WHERE type = 'index' AND name NOT LIKE 'sqlite_%'
            ORDER BY tbl_name, name
        """).fetchall()

        print(f"📊 생성된 인덱스: {len(indexes)}개")
        current_table = None
        for idx in indexes:
            if current_table != idx.tbl_name:
                current_table = idx.tbl_name
                print(f"\n테이블: {current_table}")
            print(f"  - {idx.name}")

        db.close()
        return True

    except Exception as e:
        print(f"❌ 스키마 확인 실패: {e}")
        return False


async def main():
    """메인 테스트 실행"""
    print("🧪 데이터베이스 종합 테스트 시작\n")

    tests = [
        ("데이터베이스 연결", test_database_connection),
        ("CRUD 작업", test_crud_operations),
        ("모델 관계", test_model_relationships),
        ("스키마 확인", test_database_schema),
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
    print("🏁 테스트 결과 요약")
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
        print("🎉 모든 데이터베이스 테스트 성공!")
        return 0
    else:
        print("⚠️ 일부 테스트 실패")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)