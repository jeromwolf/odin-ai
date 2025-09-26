#!/usr/bin/env python3
"""북마크 테스트 수정 확인 스크립트"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_bookmark_fixes():
    """북마크 API 수정사항 테스트"""
    print("🔧 북마크 API 수정사항 테스트")

    # 1. 로그인
    login_data = {
        "email": "test@odin-ai.com",
        "password": "TestPassword123!"
    }

    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ 로그인 실패: {response.status_code}")
        try:
            print(f"   응답: {response.json()}")
        except:
            print(f"   응답 텍스트: {response.text}")
        return False

    token = response.json().get("access_token")
    if not token:
        print("❌ JWT 토큰 획득 실패")
        return False

    print("✅ 로그인 성공")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. 북마크 추가 (notes 필드 사용)
    bookmark_data = {
        "bid_notice_no": "TEST-001",
        "title": "수정된 북마크 테스트",
        "notes": "memo 대신 notes 필드 사용",  # 수정된 필드명
        "tags": []
    }

    response = requests.post(f"{BASE_URL}/api/bookmarks/",
                           headers=headers, json=bookmark_data)

    print(f"📤 북마크 추가 요청: {json.dumps(bookmark_data, ensure_ascii=False)}")
    print(f"📥 응답 상태: {response.status_code}")

    if response.status_code == 200 or response.status_code == 201:
        print("✅ 북마크 추가 성공!")
        response_data = response.json()
        bookmark_id = response_data.get("bookmark_id") or response_data.get("id")
        return bookmark_id
    elif response.status_code == 409:
        print("⚠️ 북마크 중복 (정상)")
        return "existing"
    else:
        try:
            error = response.json()
            print(f"❌ 북마크 추가 실패: {error}")
        except:
            print(f"❌ 북마크 추가 실패: {response.text}")
        return None

if __name__ == "__main__":
    print("🚀 북마크 API 수정사항 테스트")
    print("="*50)
    bookmark_result = test_bookmark_fixes()
    print(f"결과: {bookmark_result}")
