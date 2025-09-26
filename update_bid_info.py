#!/usr/bin/env python3
"""
입찰 정보 업데이트 스크립트
문서에서 카테고리와 지역제한 정보를 추출하여 DB 업데이트
"""
import os
import re
import psycopg2
from datetime import datetime

# DB 연결
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db')
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

def extract_bid_category(text):
    """입찰 카테고리 추출"""
    # 전문공사 패턴
    if re.search(r'전문공사업|석공사업|도장.*습식.*방수|전기공사업|정보통신공사업|전기통신공사업', text):
        return '전문공사'
    # 일반공사 패턴 (조경공사업 추가)
    elif re.search(r'일반건설업|종합건설업|건축공사업|토목건축공사업|조경공사업|토목공사업', text):
        return '일반공사'
    # 용역/서비스 패턴 (단, 공사업이 명시된 경우 제외)
    elif re.search(r'용역|서비스|설계|감리|연구|조사', text) and not re.search(r'공사업|건설업', text):
        return '용역'
    # 물품 패턴
    elif re.search(r'물품|구매|납품|제조', text):
        return '물품'
    # 공사 관련 키워드가 있으면 일반공사
    elif re.search(r'공사|건설|시공|건축|토목', text):
        return '일반공사'
    else:
        # 기본값은 일반공사로 설정
        return '일반공사'

def extract_region_restriction(text):
    """지역 제한 정보 추출"""
    # 홍천군 패턴
    if re.search(r'홍천군에 소재한 업체', text):
        return '홍천군'
    # 의성군 패턴
    elif re.search(r'의성군.{0,10}소재', text):
        return '의성군'
    # 이천시 패턴
    elif re.search(r'이천시.{0,10}소재', text):
        return '이천시'
    # 광주광역시 패턴 (추가)
    elif re.search(r'광주광역시.{0,20}(소재|주된.{0,5}영업소)', text):
        return '광주광역시'
    # 전라남도/보성 패턴
    elif re.search(r'전라남도.{0,10}소재|보성.{0,10}소재', text):
        return '전라남도'
    # 전라북도 패턴
    elif re.search(r'전라북도.{0,10}소재|전주.{0,10}소재', text):
        return '전라북도'
    # 경기도 패턴
    elif re.search(r'경기도.{0,10}소재', text):
        return '경기도'
    # 지역제한 키워드가 있지만 없음으로 명시된 경우
    elif re.search(r'지역제한.{0,5}없음|전국', text):
        return '전국'
    # 지역제한이라는 단어가 있으면서 특정 지역이 언급된 경우
    elif re.search(r'지역제한', text):
        # 지역제한이 있지만 구체적 지역을 못 찾은 경우
        return '지역제한(상세확인필요)'
    else:
        # 기본값
        return '전국'

def extract_qualification(text):
    """참가자격 정보 추출"""
    # 자격 요건 패턴 찾기
    patterns = [
        r'견적참가자격.{0,300}',
        r'입찰참가자격.{0,300}',
        r'참가자격.{0,300}',
        r'자격요건.{0,300}'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            qualification = match.group(0)
            # 첫 300자만 저장 (너무 길지 않게)
            qualification = qualification[:300].replace('\n', ' ').strip()
            return qualification

    return '입찰참가 등록업체'

def update_bid_info():
    """각 입찰공고의 정보 업데이트"""

    # 모든 입찰공고 조회
    cursor.execute("""
        SELECT ba.bid_notice_no, ba.title, ba.organization_name,
               bd.extracted_text
        FROM bid_announcements ba
        LEFT JOIN bid_documents bd ON ba.bid_notice_no = bd.bid_notice_no
        WHERE bd.extracted_text IS NOT NULL
    """)

    rows = cursor.fetchall()
    print(f"총 {len(rows)}개 공고 분석 중...")

    for row in rows:
        bid_no = row[0]
        title = row[1]
        org = row[2]
        text = row[3] or ''

        # 정보 추출
        category = extract_bid_category(text)
        region = extract_region_restriction(text)
        qualification = extract_qualification(text)

        # DB 업데이트
        cursor.execute("""
            UPDATE bid_announcements
            SET bid_category = %s,
                region_restriction = %s,
                qualification_summary = %s,
                updated_at = NOW()
            WHERE bid_notice_no = %s
        """, (category, region, qualification, bid_no))

        print(f"✅ {bid_no}: {category}, {region}, {qualification[:50]}...")

    conn.commit()
    print(f"\n✅ 총 {len(rows)}개 공고 정보 업데이트 완료!")

if __name__ == "__main__":
    try:
        update_bid_info()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()