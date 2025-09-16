#!/usr/bin/env python3
"""
Selenium 크롤러 테스트
"""

import asyncio
import sys
from datetime import datetime, timedelta

from backend.services.g2b_selenium_crawler import G2BSeleniumCrawler


def test_selenium_crawler():
    """
    Selenium 크롤러 테스트
    """
    print("=" * 60)
    print("Selenium 나라장터 크롤러 테스트")
    print("=" * 60)
    
    crawler = G2BSeleniumCrawler()
    
    try:
        # Chrome 드라이버 설정 (헤드리스 모드 사용)
        print("\n1. Chrome 드라이버 설정 중...")
        crawler.setup_driver(headless=True)
        print("✅ 드라이버 설정 완료")
        
        # 입찰공고 검색
        print("\n2. 입찰공고 검색 중...")
        
        # 최근 7일간의 공고 검색
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        results = crawler.search_bids(
            keyword="시스템",  # 검색 키워드
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d")
        )
        
        if results:
            print(f"✅ {len(results)}건의 입찰공고 검색 성공")
            
            # 검색 결과 출력
            for i, result in enumerate(results[:3], 1):
                print(f"\n  [{i}] 공고번호: {result.get('공고번호', 'N/A')}")
                print(f"      공고명: {result.get('공고명', 'N/A')}")
                print(f"      기관: {result.get('공고기관', 'N/A')}")
                print(f"      마감: {result.get('마감일시', 'N/A')}")
                
            # 첫 번째 공고의 첨부파일 다운로드 시도
            if results and results[0].get('상세링크'):
                print("\n3. 첨부파일 다운로드 테스트...")
                downloaded = crawler.download_bid_documents(results[0]['상세링크'])
                
                if downloaded:
                    print(f"✅ {len(downloaded)}개 파일 다운로드 성공")
                    for file_path in downloaded:
                        print(f"   - {file_path}")
                else:
                    print("⚠️  첨부파일을 찾을 수 없거나 다운로드가 제한되어 있습니다")
            
            # 엑셀 파일로 저장
            print("\n4. 엑셀 파일로 저장 중...")
            crawler.export_to_excel(results)
            print("✅ 엑셀 파일 저장 완료")
            
        else:
            print("❌ 검색 결과가 없습니다")
            print("   현재 나라장터가 2025년 차세대 시스템으로 변경되어")
            print("   URL 구조가 변경되었을 수 있습니다")
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 드라이버 종료
        crawler.close()
        print("\n" + "=" * 60)
        print("테스트 종료")
        print("=" * 60)


if __name__ == "__main__":
    test_selenium_crawler()