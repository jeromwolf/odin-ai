#!/usr/bin/env python3
"""
잘못된 태그 분류 수정 스크립트
건설공사에 잘못 붙은 "소프트웨어" 태그를 제거합니다.
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# DB 연결
db_url = os.getenv('DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db')
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

def analyze_wrong_tags():
    """잘못된 태그 분석"""
    print("=== 잘못된 소프트웨어 태그 분석 ===")

    # 건설공사에 소프트웨어 태그가 붙은 케이스 조회
    query = """
    SELECT
        ba.bid_notice_no,
        ba.title,
        COUNT(CASE WHEN bt.tag_name = '소프트웨어' THEN 1 END) as software_count,
        COUNT(CASE WHEN bt.tag_name IN ('건설', '공사', '시공', '토목') THEN 1 END) as construction_count,
        STRING_AGG(bt.tag_name, ', ' ORDER BY bt.tag_name) as all_tags
    FROM bid_announcements ba
    JOIN bid_tag_relations btr ON ba.bid_notice_no = btr.bid_notice_no
    JOIN bid_tags bt ON btr.tag_id = bt.tag_id
    WHERE ba.title LIKE '%공사%'
    GROUP BY ba.bid_notice_no, ba.title
    HAVING COUNT(CASE WHEN bt.tag_name = '소프트웨어' THEN 1 END) > 0
    ORDER BY ba.title
    LIMIT 10;
    """

    result = session.execute(text(query))
    rows = result.fetchall()

    print(f"발견된 문제 케이스: {len(rows)}개")
    for row in rows:
        print(f"- {row.title[:50]}...")
        print(f"  태그: {row.all_tags}")
        print()

    return len(rows)

def fix_wrong_software_tags():
    """건설공사에서 잘못된 소프트웨어 태그 제거"""
    print("=== 잘못된 소프트웨어 태그 제거 ===")

    # 1. 건설 관련 키워드가 있는 공고에서 소프트웨어 태그 조회
    construction_keywords = ['공사', '건축', '건설', '토목', '시공', '공원', '도로', '교량']

    wrong_tags_query = """
    DELETE FROM bid_tag_relations
    WHERE tag_id IN (SELECT tag_id FROM bid_tags WHERE tag_name = '소프트웨어')
    AND bid_notice_no IN (
        SELECT DISTINCT ba.bid_notice_no
        FROM bid_announcements ba
        WHERE ba.title ~* '(공사|건축|건설|토목|시공|공원|도로|교량|리모델링|보수|보강|정비|조성)'
        AND ba.title !~* '(시스템|소프트웨어|SW|프로그램|개발|정보화)'
    )
    """

    try:
        result = session.execute(text(wrong_tags_query))
        removed_count = result.rowcount
        session.commit()

        print(f"✅ 잘못된 소프트웨어 태그 {removed_count}개 제거 완료")
        return removed_count

    except Exception as e:
        session.rollback()
        print(f"❌ 태그 제거 실패: {e}")
        return 0

def verify_fix():
    """수정 결과 확인"""
    print("=== 수정 결과 확인 ===")

    query = """
    SELECT COUNT(*) as remaining_count
    FROM bid_announcements ba
    JOIN bid_tag_relations btr ON ba.bid_notice_no = btr.bid_notice_no
    JOIN bid_tags bt ON btr.tag_id = bt.tag_id
    WHERE ba.title LIKE '%공사%' AND bt.tag_name = '소프트웨어'
    """

    result = session.execute(text(query))
    remaining = result.fetchone()[0]

    print(f"남은 문제 케이스: {remaining}개")

    if remaining == 0:
        print("✅ 모든 잘못된 태그가 정리되었습니다!")
    else:
        print("⚠️ 일부 케이스가 남아있습니다. 수동 검토 필요")

def main():
    """메인 실행 함수"""
    print("🔧 태그 분류 오류 수정 도구")
    print("=" * 50)

    # 1. 문제 분석
    problem_count = analyze_wrong_tags()

    if problem_count == 0:
        print("✅ 문제가 발견되지 않았습니다.")
        return

    # 2. 자동 실행 (사용자 확인 생략)
    print(f"\n✅ {problem_count}개의 잘못된 태그를 자동으로 수정합니다...")

    # 3. 수정 실행
    removed_count = fix_wrong_software_tags()

    # 4. 결과 확인
    if removed_count > 0:
        verify_fix()

    session.close()
    print("\n🎉 작업 완료!")

if __name__ == "__main__":
    main()