#!/usr/bin/env python3
"""
전체 문서 재추출 스크립트
Phase 1 패턴 개선 후 모든 문서에 대해 정보 추출 재실행
"""
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 프로젝트 루트를 PYTHONPATH에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.database.models import BidDocument, BidExtractedInfo
from batch.modules.processor import DocumentProcessorModule

def main():
    print("=" * 80)
    print("📋 전체 문서 재추출 시작")
    print("=" * 80)
    print(f"⏰ 시작 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # DB 연결
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL 환경변수가 설정되지 않았습니다.")
        return

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    # 처리 대상 문서 조회
    docs = session.query(BidDocument).filter(
        BidDocument.processing_status == 'completed',
        BidDocument.extracted_text.isnot(None),
        BidDocument.extracted_text != ''
    ).all()

    total_docs = len(docs)
    print(f"📊 처리 대상: {total_docs}개 문서")
    print()

    # 기존 추출 정보 삭제
    print("🗑️  기존 추출 정보 삭제 중...")
    bid_notice_nos = [doc.bid_notice_no for doc in docs]
    deleted = session.query(BidExtractedInfo).filter(
        BidExtractedInfo.bid_notice_no.in_(bid_notice_nos)
    ).delete(synchronize_session=False)
    session.commit()
    print(f"   ✅ {deleted}개 항목 삭제 완료")
    print()

    # 문서 처리 모듈 초기화
    processor = DocumentProcessorModule()

    # 통계 변수
    total_extracted = 0
    success_count = 0
    fail_count = 0

    print("🔍 정보 추출 시작...")
    print("-" * 80)

    # 각 문서에 대해 정보 추출
    for idx, doc in enumerate(docs, 1):
        try:
            count = processor._extract_information(doc)
            processor.session.commit()
            total_extracted += count
            success_count += 1

            if idx % 50 == 0:
                print(f"   진행: {idx}/{total_docs} ({idx/total_docs*100:.1f}%) - "
                      f"추출: {total_extracted}개")

        except Exception as e:
            fail_count += 1
            print(f"   ❌ 오류 [{doc.bid_notice_no}]: {str(e)}")
            processor.session.rollback()

    print("-" * 80)
    print()

    # 최종 결과
    print("=" * 80)
    print("✅ 재추출 완료")
    print("=" * 80)
    print(f"⏰ 종료 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print(f"📊 처리 결과:")
    print(f"   • 총 문서: {total_docs}개")
    print(f"   • 성공: {success_count}개 ({success_count/total_docs*100:.1f}%)")
    print(f"   • 실패: {fail_count}개")
    print(f"   • 총 추출 항목: {total_extracted}개")
    print(f"   • 문서당 평균: {total_extracted/success_count:.1f}개")
    print()

    # 카테고리별 통계
    print("📈 카테고리별 통계:")
    categories = session.query(
        BidExtractedInfo.info_category,
        session.query(BidExtractedInfo).filter(
            BidExtractedInfo.info_category == BidExtractedInfo.info_category
        ).count().label('count')
    ).group_by(BidExtractedInfo.info_category).all()

    category_stats = {}
    for cat in categories:
        count = session.query(BidExtractedInfo).filter_by(
            info_category=cat[0]
        ).count()
        category_stats[cat[0]] = count

    for cat in sorted(category_stats.keys()):
        count = category_stats[cat]
        print(f"   • {cat}: {count}개 ({count/total_docs*100:.1f}% 커버리지)")

    session.close()
    print()
    print("🎉 모든 작업 완료!")

if __name__ == '__main__':
    main()
