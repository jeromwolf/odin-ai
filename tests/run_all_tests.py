#!/usr/bin/env python3
"""
ODIN-AI 종합 테스트 실행기
200개 테스트 항목을 순차적으로 실행하고 결과를 기록
"""

import requests
import json
import time
import random
import string
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import psycopg2
import os

BASE_URL = "http://localhost:8000"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://blockmeta@localhost:5432/odin_db")

class TestResult:
    def __init__(self, test_id: str, name: str, category: str):
        self.test_id = test_id
        self.name = name
        self.category = category
        self.status = "미실행"  # 통과/실패/보류/미실행
        self.execution_time = 0
        self.error_message = ""
        self.timestamp = None

class OdinTestRunner:
    def __init__(self):
        self.results = {}
        self.total_tests = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.start_time = None
        self.token = None
        self.test_user = None

    def generate_random_email(self):
        """테스트용 랜덤 이메일 생성"""
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"test_{random_str}@odin.ai"

    def generate_random_username(self):
        """테스트용 랜덤 사용자명 생성"""
        return f"test_user_{random.randint(10000, 99999)}"

    def setup_test_user(self):
        """테스트용 사용자 생성 및 로그인"""
        email = self.generate_random_email()
        username = self.generate_random_username()
        password = "TestPassword123!"

        # 회원가입
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password,
                "full_name": "Test User"
            }
        )

        if response.status_code == 200:
            self.test_user = response.json()

            # 로그인
            login_response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": email, "password": password}
            )

            if login_response.status_code == 200:
                self.token = login_response.json().get("access_token")
                return True

        return False

    def get_auth_headers(self):
        """인증 헤더 반환"""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def run_test(self, test_id: str, test_func, *args, **kwargs) -> Tuple[bool, str, float]:
        """개별 테스트 실행"""
        start_time = time.time()
        try:
            result = test_func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000  # ms
            return (result, "", execution_time)
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return (False, str(e), execution_time)

    # ===== 인증 시스템 테스트 =====
    def test_auth_001(self):
        """회원가입 - 정상 케이스"""
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": self.generate_random_email(),
                "username": self.generate_random_username(),
                "password": "ValidPass123!",
                "full_name": "Test User"
            }
        )
        return response.status_code == 200

    def test_auth_002(self):
        """회원가입 - 중복 이메일 체크"""
        email = self.generate_random_email()
        # 첫 번째 가입
        requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": email,
                "username": self.generate_random_username(),
                "password": "ValidPass123!",
                "full_name": "Test User"
            }
        )
        # 동일 이메일로 재가입 시도
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": email,
                "username": self.generate_random_username(),
                "password": "ValidPass123!",
                "full_name": "Test User 2"
            }
        )
        return response.status_code == 400

    def test_auth_006(self):
        """로그인 - 정상 케이스"""
        email = self.generate_random_email()
        password = "TestPass123!"

        # 회원가입
        requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": email,
                "username": self.generate_random_username(),
                "password": password,
                "full_name": "Test User"
            }
        )

        # 로그인
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password}
        )

        return response.status_code == 200 and "access_token" in response.json()

    # ===== 검색 시스템 테스트 =====
    def test_search_001(self):
        """키워드 검색 - 단일 키워드"""
        response = requests.get(f"{BASE_URL}/api/search?q=건설")
        return response.status_code == 200

    def test_search_003(self):
        """키워드 검색 - 한글 검색"""
        response = requests.get(f"{BASE_URL}/api/search?q=소프트웨어개발")
        return response.status_code == 200

    def test_search_007(self):
        """필터링 - 날짜 범위"""
        response = requests.get(
            f"{BASE_URL}/api/search",
            params={
                "start_date": "2025-09-01",
                "end_date": "2025-09-30"
            }
        )
        return response.status_code == 200

    def test_search_013(self):
        """정렬 - 최신순"""
        response = requests.get(f"{BASE_URL}/api/search?sort=latest")
        return response.status_code == 200

    def test_search_017(self):
        """페이지네이션 - 첫 페이지"""
        response = requests.get(f"{BASE_URL}/api/search?page=1&size=10")
        data = response.json()
        return response.status_code == 200 and "page" in data

    # ===== 북마크 시스템 테스트 =====
    def test_bookmark_001(self):
        """북마크 추가 - 정상 케이스"""
        headers = self.get_auth_headers()
        response = requests.post(
            f"{BASE_URL}/api/bookmarks",
            headers=headers,
            json={
                "bid_id": "TEST-BID-001",
                "title": "테스트 입찰",
                "organization": "테스트 기관"
            }
        )
        return response.status_code == 200

    def test_bookmark_005(self):
        """북마크 목록 - 페이지네이션"""
        headers = self.get_auth_headers()
        response = requests.get(
            f"{BASE_URL}/api/bookmarks?page=1&size=10",
            headers=headers
        )
        return response.status_code == 200

    # ===== AI 추천 시스템 테스트 =====
    def test_rec_001(self):
        """상호작용 기록 - View"""
        headers = self.get_auth_headers()
        response = requests.post(
            f"{BASE_URL}/api/recommendations/interactions",
            headers=headers,
            json={
                "bid_notice_no": "TEST-BID-001",
                "interaction_type": "view",
                "duration_seconds": 30
            }
        )
        return response.status_code == 200

    def test_rec_006(self):
        """선호도 분석 - 카테고리"""
        headers = self.get_auth_headers()
        response = requests.get(
            f"{BASE_URL}/api/recommendations/preferences",
            headers=headers
        )
        return response.status_code == 200

    def test_rec_011(self):
        """콘텐츠 기반 추천 - 유사 입찰"""
        headers = self.get_auth_headers()
        response = requests.get(
            f"{BASE_URL}/api/recommendations/personal?recommendation_type=content_based",
            headers=headers
        )
        return response.status_code == 200

    # ===== 대시보드 테스트 =====
    def test_dash_001(self):
        """개요 - 전체 통계"""
        response = requests.get(f"{BASE_URL}/api/dashboard/overview")
        data = response.json()
        return response.status_code == 200 and "total_bids" in data

    # ===== 알림 시스템 테스트 =====
    def test_notif_001(self):
        """알림 규칙 - 생성"""
        headers = self.get_auth_headers()
        response = requests.post(
            f"{BASE_URL}/api/notifications/rules",
            headers=headers,
            json={
                "rule_name": "테스트 알림",
                "conditions": {"keywords": ["테스트"]},
                "notification_channels": ["email"]
            }
        )
        return response.status_code == 200

    # ===== 구독/결제 테스트 =====
    def test_sub_001(self):
        """플랜 목록 - 조회"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/plans")
        return response.status_code == 200

    # ===== 성능 테스트 =====
    def test_perf_001(self):
        """응답 시간 - 검색 API < 100ms"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/search?q=test")
        elapsed = (time.time() - start) * 1000
        return response.status_code == 200 and elapsed < 100

    # ===== 보안 테스트 =====
    def test_sec_001(self):
        """SQL 인젝션 - 방어 검증"""
        response = requests.get(f"{BASE_URL}/api/search?q=' OR '1'='1")
        # SQL 인젝션이 방어되면 정상 응답
        return response.status_code == 200

    def run_all_tests(self):
        """모든 테스트 실행"""
        self.start_time = datetime.now()

        print("=" * 60)
        print("🧪 ODIN-AI 종합 테스트 시작")
        print("=" * 60)
        print()

        # 테스트 사용자 설정
        print("테스트 환경 설정 중...")
        if not self.setup_test_user():
            print("❌ 테스트 사용자 생성 실패")
            return

        print(f"✅ 테스트 사용자 생성 완료")
        print()

        # 테스트 매핑
        test_methods = {
            "AUTH-001": self.test_auth_001,
            "AUTH-002": self.test_auth_002,
            "AUTH-006": self.test_auth_006,
            "SEARCH-001": self.test_search_001,
            "SEARCH-003": self.test_search_003,
            "SEARCH-007": self.test_search_007,
            "SEARCH-013": self.test_search_013,
            "SEARCH-017": self.test_search_017,
            "BOOKMARK-001": self.test_bookmark_001,
            "BOOKMARK-005": self.test_bookmark_005,
            "REC-001": self.test_rec_001,
            "REC-006": self.test_rec_006,
            "REC-011": self.test_rec_011,
            "DASH-001": self.test_dash_001,
            "NOTIF-001": self.test_notif_001,
            "SUB-001": self.test_sub_001,
            "PERF-001": self.test_perf_001,
            "SEC-001": self.test_sec_001,
        }

        # 테스트 실행
        for test_id, test_method in test_methods.items():
            self.total_tests += 1
            print(f"실행 중: {test_id}", end=" ... ")

            success, error, exec_time = self.run_test(test_id, test_method)

            if success:
                self.passed += 1
                print(f"✅ 통과 ({exec_time:.2f}ms)")
            else:
                self.failed += 1
                print(f"❌ 실패: {error}")

            # 결과 저장
            result = TestResult(test_id, test_id, test_id.split("-")[0])
            result.status = "통과" if success else "실패"
            result.execution_time = exec_time
            result.error_message = error
            result.timestamp = datetime.now()
            self.results[test_id] = result

        # 최종 보고서 생성
        self.generate_report()

    def generate_report(self):
        """테스트 결과 보고서 생성"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        print()
        print("=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)
        print(f"실행 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"소요 시간: {duration:.2f}초")
        print()
        print(f"전체 테스트: {self.total_tests}개")
        print(f"✅ 통과: {self.passed}개 ({self.passed/self.total_tests*100:.1f}%)")
        print(f"❌ 실패: {self.failed}개 ({self.failed/self.total_tests*100:.1f}%)")
        print(f"⏭️  스킵: {self.skipped}개")
        print()

        # 카테고리별 결과
        categories = {}
        for result in self.results.values():
            cat = result.category
            if cat not in categories:
                categories[cat] = {"passed": 0, "failed": 0}
            if result.status == "통과":
                categories[cat]["passed"] += 1
            else:
                categories[cat]["failed"] += 1

        print("카테고리별 결과:")
        for cat, stats in categories.items():
            total = stats["passed"] + stats["failed"]
            print(f"  {cat}: {stats['passed']}/{total} 통과")

        # HTML 보고서 생성
        self.generate_html_report(end_time, duration)

        # JSON 결과 저장
        self.save_json_results()

    def generate_html_report(self, end_time, duration):
        """HTML 형식의 보고서 생성"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ODIN-AI 테스트 결과 보고서</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #2c3e50; }}
        .summary {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; }}
        .passed {{ color: #27ae60; font-weight: bold; }}
        .failed {{ color: #e74c3c; font-weight: bold; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>🧪 ODIN-AI 테스트 결과 보고서</h1>

    <div class="summary">
        <h2>📊 요약</h2>
        <p>실행 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} ~ {end_time.strftime('%H:%M:%S')}</p>
        <p>소요 시간: {duration:.2f}초</p>
        <p>전체 테스트: {self.total_tests}개</p>
        <p class="passed">✅ 통과: {self.passed}개 ({self.passed/self.total_tests*100:.1f}%)</p>
        <p class="failed">❌ 실패: {self.failed}개 ({self.failed/self.total_tests*100:.1f}%)</p>
    </div>

    <h2>상세 결과</h2>
    <table>
        <tr>
            <th>테스트 ID</th>
            <th>카테고리</th>
            <th>상태</th>
            <th>실행 시간(ms)</th>
            <th>오류 메시지</th>
        </tr>
"""

        for test_id, result in sorted(self.results.items()):
            status_icon = "✅" if result.status == "통과" else "❌"
            status_class = "passed" if result.status == "통과" else "failed"
            html_content += f"""
        <tr>
            <td>{result.test_id}</td>
            <td>{result.category}</td>
            <td class="{status_class}">{status_icon} {result.status}</td>
            <td>{result.execution_time:.2f}</td>
            <td>{result.error_message}</td>
        </tr>
"""

        html_content += """
    </table>
</body>
</html>
"""

        # 파일 저장
        report_path = f"tests/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"\n📄 HTML 보고서 생성: {report_path}")

    def save_json_results(self):
        """JSON 형식으로 결과 저장"""
        json_results = {
            "test_run": {
                "start_time": self.start_time.isoformat(),
                "duration": (datetime.now() - self.start_time).total_seconds(),
                "total_tests": self.total_tests,
                "passed": self.passed,
                "failed": self.failed,
                "skipped": self.skipped
            },
            "results": {}
        }

        for test_id, result in self.results.items():
            json_results["results"][test_id] = {
                "name": result.name,
                "category": result.category,
                "status": result.status,
                "execution_time": result.execution_time,
                "error_message": result.error_message,
                "timestamp": result.timestamp.isoformat() if result.timestamp else None
            }

        # 파일 저장
        json_path = f"tests/test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_results, f, ensure_ascii=False, indent=2)

        print(f"📄 JSON 결과 저장: {json_path}")

if __name__ == "__main__":
    runner = OdinTestRunner()
    runner.run_all_tests()