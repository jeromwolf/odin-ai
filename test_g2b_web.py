#!/usr/bin/env python3
"""
나라장터 웹사이트 실제 크롤링 테스트
로그인 없이 접근 가능한 공개 정보 수집
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json

class G2BWebCrawler:
    """나라장터 웹 크롤러 (공개 정보)"""

    def __init__(self):
        self.base_url = "https://www.g2b.go.kr"
        self.search_url = "https://www.g2b.go.kr:8081/ep/preparation/prestd/preStdSearch.do"
        self.session = None

    async def setup(self):
        """세션 설정"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)

    async def close(self):
        """세션 종료"""
        if self.session:
            await self.session.close()

    async def search_bids_public(self):
        """공개 입찰정보 검색 (로그인 불필요)"""

        # 나라장터 입찰정보 검색 페이지 (공개)
        search_url = "https://www.g2b.go.kr:8081/ep/preparation/prestd/preStdSearch.do"

        # 검색 파라미터 (공개 검색)
        params = {
            'preStdRegNo': '',  # 사전규격등록번호
            'referNo': '',      # 참조번호
            'title': '',        # 품명
            'swbizObjectYn': 'N',
            'taskClCds': '',
            'taskClCd': '',
            'dataType': 'ANNOUNCEMENT',  # 공고 데이터
            'orderType': '1',   # 정렬: 최신순
            'currentPageNo': '1',
            'countPerPage': '10',
            'type': 'list'
        }

        print("나라장터 공개 입찰정보 검색 중...")

        try:
            async with self.session.get(search_url, params=params) as response:
                if response.status == 200:
                    html = await response.text()
                    return self.parse_search_results(html)
                else:
                    print(f"HTTP {response.status} 응답")
                    return None
        except Exception as e:
            print(f"검색 실패: {e}")
            return None

    def parse_search_results(self, html):
        """검색 결과 파싱"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []

        # 테이블 찾기 (나라장터 리스트 구조)
        table = soup.find('table', class_='table_list')
        if not table:
            # 다른 형식 시도
            table = soup.find('table', class_='list_table')

        if table:
            rows = table.find_all('tr')[1:]  # 헤더 제외

            for row in rows:
                cells = row.find_all('td')
                if len(cells) > 3:
                    result = {
                        '순번': cells[0].get_text(strip=True),
                        '공고명': cells[1].get_text(strip=True) if len(cells) > 1 else '',
                        '기관명': cells[2].get_text(strip=True) if len(cells) > 2 else '',
                        '공고일': cells[3].get_text(strip=True) if len(cells) > 3 else '',
                    }

                    # 상세 링크 추출
                    link = cells[1].find('a') if len(cells) > 1 else None
                    if link and link.get('href'):
                        result['상세링크'] = link['href']

                    results.append(result)

        return results

    async def get_bid_detail_public(self, detail_url):
        """입찰 상세정보 조회 (공개 정보)"""

        if not detail_url.startswith('http'):
            detail_url = self.base_url + detail_url

        print(f"상세정보 조회: {detail_url[:50]}...")

        try:
            async with self.session.get(detail_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self.parse_detail(html)
                else:
                    print(f"HTTP {response.status} 응답")
                    return None
        except Exception as e:
            print(f"상세 조회 실패: {e}")
            return None

    def parse_detail(self, html):
        """상세정보 파싱"""
        soup = BeautifulSoup(html, 'html.parser')
        detail = {}

        # 상세정보 테이블 파싱
        info_tables = soup.find_all('table', class_='table_info')

        for table in info_tables:
            rows = table.find_all('tr')
            for row in rows:
                th = row.find('th')
                td = row.find('td')

                if th and td:
                    key = th.get_text(strip=True).replace(':', '')
                    value = td.get_text(strip=True)
                    detail[key] = value

        # 첨부파일 정보
        file_area = soup.find('div', class_='file_area')
        if file_area:
            files = []
            links = file_area.find_all('a')
            for link in links:
                if link.get('href'):
                    files.append({
                        'name': link.get_text(strip=True),
                        'url': link['href']
                    })
            detail['첨부파일'] = files

        return detail


async def test_narajangteo():
    """나라장터 실제 테스트"""

    print("=" * 60)
    print("나라장터 공개정보 크롤링 테스트")
    print("=" * 60)

    crawler = G2BWebCrawler()
    await crawler.setup()

    try:
        # 1. 공개 입찰정보 검색
        print("\n1. 공개 입찰정보 검색")
        results = await crawler.search_bids_public()

        if results:
            print(f"✅ {len(results)}건 검색 성공")
            for i, result in enumerate(results[:3], 1):
                print(f"\n[{i}] {result.get('공고명', 'N/A')}")
                print(f"    기관: {result.get('기관명', 'N/A')}")
                print(f"    공고일: {result.get('공고일', 'N/A')}")

                # 상세정보 조회
                if result.get('상세링크'):
                    await asyncio.sleep(2)  # 과도한 요청 방지
                    detail = await crawler.get_bid_detail_public(result['상세링크'])
                    if detail:
                        print(f"    상세정보: {len(detail)}개 항목")
                        if detail.get('첨부파일'):
                            print(f"    첨부파일: {len(detail['첨부파일'])}개")
        else:
            print("❌ 검색 결과 없음")

        # 2. 나라장터 메인페이지 확인
        print("\n2. 나라장터 메인페이지 접근성 확인")
        async with crawler.session.get("https://www.g2b.go.kr") as response:
            print(f"메인페이지 상태: HTTP {response.status}")

        # 3. 공개 가능한 API 엔드포인트 확인
        print("\n3. 공개 API 엔드포인트 확인")

        # 입찰공고 통합검색 (신규)
        bid_search_url = "https://www.g2b.go.kr:8340/search/smartSearch.do"

        search_data = {
            "searchType": "bid",  # 입찰공고
            "searchKeyword": "시스템",  # 검색어
            "fromBidDt": (datetime.now() - timedelta(days=7)).strftime("%Y%m%d"),
            "toBidDt": datetime.now().strftime("%Y%m%d"),
            "currentPageNo": "1",
            "countPerPage": "10"
        }

        try:
            async with crawler.session.post(bid_search_url, data=search_data) as response:
                if response.status == 200:
                    result = await response.text()
                    # JSON 응답인지 확인
                    try:
                        json_data = json.loads(result)
                        print(f"✅ 통합검색 API 응답: {type(json_data)}")
                    except:
                        print(f"✅ 통합검색 응답 (HTML): {len(result)}자")
                else:
                    print(f"❌ 통합검색 실패: HTTP {response.status}")
        except Exception as e:
            print(f"❌ 통합검색 오류: {e}")

    finally:
        await crawler.close()

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_narajangteo())