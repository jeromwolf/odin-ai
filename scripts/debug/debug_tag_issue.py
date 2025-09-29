#!/usr/bin/env python3
"""
태그 분류 문제 디버그 스크립트
"""
import sys
sys.path.append('/Users/blockmeta/Desktop/blockmeta/project/odin-ai')

from src.services.tag_generator import TagGenerator
from src.database.models import BidAnnouncement
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# DB 연결
db_url = os.getenv('DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db')
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

# TagGenerator 초기화
tag_gen = TagGenerator(session)

# 테스트용 건설공사 공고 생성
test_announcement = BidAnnouncement()
test_announcement.bid_notice_no = "TEST123"
test_announcement.title = "대전무궁공원 제2지연장지 2차 화층공사"
test_announcement.organization_name = "대전광역시 시설관리공단"

print("=== 태그 생성 테스트 ===")
print(f"제목: {test_announcement.title}")
print(f"기관명: {test_announcement.organization_name}")

# 태그 생성
tags = tag_gen.generate_tags(test_announcement)

print(f"\n생성된 태그:")
for tag in sorted(tags):
    print(f"  - {tag}")

# 세부 분석
print("\n=== 세부 분석 ===")

# 산업 분야 태그 분석
industry_tags = tag_gen._extract_industry_tags(test_announcement.title)
print(f"산업 분야 태그: {industry_tags}")

# 키워드 매칭 분석
print("\n키워드 매칭:")
for industry, keywords in tag_gen.industry_keywords.items():
    for keyword in keywords:
        if keyword.lower() in test_announcement.title.lower():
            print(f"  {industry}: '{keyword}' 매칭됨")

# 자동 태그 분석
auto_tags = tag_gen._extract_auto_tags(test_announcement.title)
print(f"\n자동 추출 태그: {auto_tags}")

session.close()