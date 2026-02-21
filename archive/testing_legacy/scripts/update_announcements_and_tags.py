#!/usr/bin/env python3
"""
추출된 정보를 bid_announcements에 업데이트하고 태그 생성
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 프로젝트 루트 추가
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.database.models import BidAnnouncement, BidDocument, BidExtractedInfo, BidTag, BidTagRelation

def update_announcements(engine):
    """추출된 정보를 공고 테이블에 업데이트"""
    Session = sessionmaker(bind=engine)
    session = Session()

    print("🔄 공고 테이블 업데이트 시작...")

    # 모든 공고에 대해 추출된 정보 확인
    announcements = session.query(BidAnnouncement).all()

    updated_count = 0
    for announcement in announcements:
        try:
            # 해당 공고의 마크다운 파일 확인
            doc = session.query(BidDocument).filter_by(
                bid_notice_no=announcement.bid_notice_no,
                processing_status='completed'
            ).first()

            if doc and doc.markdown_path and Path(doc.markdown_path).exists():
                # 마크다운 파일 읽기
                with open(doc.markdown_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 간단한 정보 추출
                if '착공일로부터' in content:
                    import re
                    match = re.search(r'착공일로부터\s*(\d+)\s*일', content)
                    if match:
                        announcement.duration_days = int(match.group(1))
                        announcement.duration_text = f"착공일로부터 {match.group(1)}일"

                # 지역 제한
                regions = ['서울', '경기', '부산', '대구', '인천', '광주', '대전', '울산',
                          '충북', '충남', '전북', '전남', '경북', '경남', '강원', '제주']

                for region in regions:
                    if region in content:
                        announcement.region_restriction = region
                        break

                # 하도급
                if '하도급' in content:
                    announcement.subcontract_allowed = True
                    match = re.search(r'하도급.*?(\d+)\s*%', content)
                    if match:
                        announcement.subcontract_ratio = int(match.group(1))

                # 자격요건
                if '자격' in content:
                    # 자격 관련 문장 추출
                    lines = content.split('\n')
                    for line in lines:
                        if '자격' in line:
                            announcement.qualification_summary = line[:200]
                            break

                # 특수조건
                if 'PQ' in content or 'ISO' in content:
                    conditions = []
                    if 'PQ' in content:
                        conditions.append('PQ심사')
                    if 'ISO' in content:
                        conditions.append('ISO인증')
                    announcement.special_conditions = ', '.join(conditions)

                session.commit()
                updated_count += 1
                print(f"  ✅ {announcement.bid_notice_no} 업데이트")

        except Exception as e:
            print(f"  ❌ {announcement.bid_notice_no}: {e}")
            session.rollback()

    session.close()
    print(f"✅ {updated_count}개 공고 업데이트 완료")
    return updated_count

def generate_tags(engine):
    """태그 생성"""
    Session = sessionmaker(bind=engine)
    session = Session()

    print("\n🏷️ 태그 생성 시작...")

    # 태그 키워드
    industry_keywords = {
        '건설': ['건설', '건축', '토목', '시공', '공사'],
        'IT': ['소프트웨어', 'SW', '시스템', '개발', 'IT'],
        '용역': ['용역', '서비스', '컨설팅', '연구'],
        '전기': ['전기', '전력', '배전'],
        '통신': ['통신', '네트워크'],
    }

    region_keywords = {
        '서울': ['서울'],
        '경기': ['경기', '수원', '성남'],
        '부산': ['부산'],
        '강원': ['강원', '철원', '춘천'],
    }

    total_tags = 0
    announcements = session.query(BidAnnouncement).all()

    for announcement in announcements:
        try:
            # 문서 텍스트 가져오기
            doc = session.query(BidDocument).filter_by(
                bid_notice_no=announcement.bid_notice_no
            ).first()

            full_text = announcement.title or ""
            if doc and doc.extracted_text:
                full_text += " " + doc.extracted_text[:500]

            full_text = full_text.lower()

            # 산업 분류 태그
            for category, keywords in industry_keywords.items():
                if any(k.lower() in full_text for k in keywords):
                    # 태그 마스터
                    tag = session.query(BidTag).filter_by(tag_name=category).first()
                    if not tag:
                        tag = BidTag(
                            tag_name=category,
                            tag_category='industry',
                            usage_count=0
                        )
                        session.add(tag)
                        session.flush()

                    tag.usage_count += 1

                    # 관계 생성 (중복 체크)
                    existing = session.query(BidTagRelation).filter_by(
                        bid_notice_no=announcement.bid_notice_no,
                        tag_id=tag.tag_id
                    ).first()

                    if not existing:
                        relation = BidTagRelation(
                            bid_notice_no=announcement.bid_notice_no,
                            tag_id=tag.tag_id,
                            relevance_score=0.8,
                            source='auto'
                        )
                        session.add(relation)
                        total_tags += 1

            # 지역 태그
            for region, keywords in region_keywords.items():
                if any(k.lower() in full_text for k in keywords):
                    tag = session.query(BidTag).filter_by(tag_name=region).first()
                    if not tag:
                        tag = BidTag(
                            tag_name=region,
                            tag_category='region',
                            usage_count=0
                        )
                        session.add(tag)
                        session.flush()

                    tag.usage_count += 1

                    existing = session.query(BidTagRelation).filter_by(
                        bid_notice_no=announcement.bid_notice_no,
                        tag_id=tag.tag_id
                    ).first()

                    if not existing:
                        relation = BidTagRelation(
                            bid_notice_no=announcement.bid_notice_no,
                            tag_id=tag.tag_id,
                            relevance_score=0.7,
                            source='auto'
                        )
                        session.add(relation)
                        total_tags += 1

            session.commit()

        except Exception as e:
            print(f"  ❌ {announcement.bid_notice_no}: {e}")
            session.rollback()

    session.close()
    print(f"✅ {total_tags}개 태그 관계 생성 완료")
    return total_tags

def main():
    """메인 실행"""
    db_url = os.environ.get('DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db')
    engine = create_engine(db_url)

    print("="*60)
    print("📊 공고 정보 업데이트 및 태그 생성")
    print("="*60)

    # 1. 공고 테이블 업데이트
    updated = update_announcements(engine)

    # 2. 태그 생성
    tags = generate_tags(engine)

    # 3. 결과 확인
    with engine.connect() as conn:
        # 업데이트된 정보
        result = conn.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(duration_days) as duration,
                COUNT(region_restriction) as region,
                COUNT(subcontract_allowed) as subcontract
            FROM bid_announcements
        """)).first()

        print("\n📊 최종 결과:")
        print(f"  - 전체 공고: {result[0]}개")
        print(f"  - 공사기간 정보: {result[1]}개")
        print(f"  - 지역제한 정보: {result[2]}개")
        print(f"  - 하도급 정보: {result[3]}개")

        # 태그 통계
        result = conn.execute(text("SELECT COUNT(*) FROM bid_tags")).scalar()
        print(f"  - 태그 종류: {result}개")

        result = conn.execute(text("SELECT COUNT(*) FROM bid_tag_relations")).scalar()
        print(f"  - 태그 관계: {result}개")

    print("="*60)
    print("✅ 작업 완료!")

if __name__ == "__main__":
    main()