#!/usr/bin/env python3
"""실패한 4개 테스트 디버깅 스크립트"""

import requests
import json

BASE_URL = "http://localhost:8000"

def get_jwt_token():
    """JWT 토큰 획득"""
    # 테스트 사용자로 로그인
    login_data = {
        "email": "test@odin-ai.com",
        "password": "TestPassword123!"
    }

    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"로그인 실패: {response.status_code} - {response.text}")
        return None

def debug_bookmark_add():
    """BOOKMARK-001: 북마크 추가 디버깅"""
    print("\n" + "="*60)
    print("🔍 BOOKMARK-001: 북마크 추가 디버깅")
    print("="*60)

    token = get_jwt_token()
    if not token:
        print("❌ JWT 토큰 획득 실패")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 북마크 데이터
    bookmark_data = {
        "bid_notice_no": "TEST-001",
        "title": "JWT 테스트 북마크",
        "memo": "디버깅용 북마크"
    }

    print(f"📤 요청 데이터: {json.dumps(bookmark_data, ensure_ascii=False)}")
    print(f"🔐 헤더: Authorization: Bearer {token[:20]}...")

    # API 호출
    response = requests.post(f"{BASE_URL}/api/bookmarks/",
                           headers=headers, json=bookmark_data)

    print(f"📥 응답 상태: {response.status_code}")
    print(f"📥 응답 헤더: {dict(response.headers)}")

    try:
        response_data = response.json()
        print(f"📥 응답 데이터: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
    except:
        print(f"📥 응답 텍스트: {response.text}")

    # 분석
    if response.status_code == 201:
        print("✅ 북마크 추가 성공!")
        return response.json().get("id")
    elif response.status_code == 409:
        print("⚠️ 북마크 중복 (이미 존재)")
        return "existing"
    elif response.status_code == 400:
        print("❌ 잘못된 요청 데이터")
    elif response.status_code == 401:
        print("❌ 인증 실패")
    elif response.status_code == 422:
        print("❌ 유효성 검사 실패")
    else:
        print(f"❌ 예상치 못한 오류: {response.status_code}")

    return None

def debug_notification_create():
    """NOTIF-001: 알림 규칙 생성 디버깅"""
    print("\n" + "="*60)
    print("🔍 NOTIF-001: 알림 규칙 생성 디버깅")
    print("="*60)

    token = get_jwt_token()
    if not token:
        print("❌ JWT 토큰 획득 실패")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 알림 규칙 데이터
    alert_data = {
        "rule_name": "디버깅 테스트 알림",
        "rule_type": "price",
        "description": "가격 기반 알림 규칙",
        "conditions": {"min_price": 1000000}
    }

    print(f"📤 요청 데이터: {json.dumps(alert_data, ensure_ascii=False)}")

    # API 호출
    response = requests.post(f"{BASE_URL}/api/notifications/alerts",
                           headers=headers, json=alert_data)

    print(f"📥 응답 상태: {response.status_code}")

    try:
        response_data = response.json()
        print(f"📥 응답 데이터: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
    except:
        print(f"📥 응답 텍스트: {response.text}")

    # 분석
    if response.status_code == 201:
        print("✅ 알림 규칙 생성 성공!")
        return response.json().get("id")
    elif response.status_code == 404:
        print("❌ 알림 API 엔드포인트가 없음")
    elif response.status_code == 400:
        print("❌ 잘못된 요청 데이터")
    elif response.status_code == 401:
        print("❌ 인증 실패")
    elif response.status_code == 422:
        print("❌ 유효성 검사 실패")
    else:
        print(f"❌ 예상치 못한 오류: {response.status_code}")

    return None

def debug_bookmark_delete():
    """BOOKMARK-003: 북마크 삭제 디버깅"""
    print("\n" + "="*60)
    print("🔍 BOOKMARK-003: 북마크 삭제 디버깅")
    print("="*60)

    token = get_jwt_token()
    if not token:
        print("❌ JWT 토큰 획득 실패")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 먼저 북마크 목록 조회
    print("📋 북마크 목록 조회 중...")
    list_response = requests.get(f"{BASE_URL}/api/bookmarks/", headers=headers)

    print(f"📥 목록 응답 상태: {list_response.status_code}")

    if list_response.status_code == 200:
        bookmarks = list_response.json()
        print(f"📥 북마크 개수: {len(bookmarks)}")

        if bookmarks:
            bookmark_id = bookmarks[0]["id"]
            print(f"🎯 삭제할 북마크 ID: {bookmark_id}")

            # 북마크 삭제 시도
            delete_response = requests.delete(f"{BASE_URL}/api/bookmarks/{bookmark_id}",
                                            headers=headers)

            print(f"📥 삭제 응답 상태: {delete_response.status_code}")

            if delete_response.status_code == 204:
                print("✅ 북마크 삭제 성공!")
            elif delete_response.status_code == 404:
                print("❌ 북마크를 찾을 수 없음")
            else:
                print(f"❌ 삭제 실패: {delete_response.status_code}")
                try:
                    print(f"📥 응답: {delete_response.json()}")
                except:
                    print(f"📥 응답 텍스트: {delete_response.text}")
        else:
            print("⚠️ 삭제할 북마크가 없음")
    else:
        print(f"❌ 목록 조회 실패: {list_response.status_code}")

def check_api_endpoints():
    """API 엔드포인트 확인"""
    print("\n" + "="*60)
    print("🔍 API 엔드포인트 상태 확인")
    print("="*60)

    endpoints = [
        ("북마크 목록", "GET", "/api/bookmarks/"),
        ("북마크 생성", "POST", "/api/bookmarks/"),
        ("알림 목록", "GET", "/api/notifications/"),
        ("알림 규칙", "POST", "/api/notifications/alerts"),
        ("추천", "GET", "/api/recommendations/content-based?bid_notice_no=TEST-001"),
    ]

    token = get_jwt_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    for name, method, endpoint in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", headers=headers, json={})

            status = "✅" if response.status_code < 400 else "❌"
            print(f"{status} {name}: {response.status_code} ({method} {endpoint})")

        except Exception as e:
            print(f"❌ {name}: 연결 오류 - {e}")

def main():
    """메인 디버깅 함수"""
    print("🔧 실패한 4개 테스트 디버깅 시작")
    print("현재 실패 항목:")
    print("  - BOOKMARK-001: 북마크 추가")
    print("  - BOOKMARK-002: 북마크 중복 방지")
    print("  - BOOKMARK-003: 북마크 삭제")
    print("  - NOTIF-001: 알림 규칙 생성")

    # API 엔드포인트 확인
    check_api_endpoints()

    # 각 테스트 디버깅
    bookmark_id = debug_bookmark_add()
    debug_notification_create()
    debug_bookmark_delete()

    print("\n" + "="*60)
    print("📊 디버깅 결과 요약")
    print("="*60)
    print("위 결과를 바탕으로 다음과 같은 개선이 필요합니다:")
    print()
    print("1. 북마크 추가 실패 원인 확인 필요")
    print("2. 알림 API 엔드포인트 구현 상태 확인")
    print("3. 권한 및 데이터베이스 제약조건 점검")
    print("4. API 응답 형식 표준화")

if __name__ == "__main__":
    main()