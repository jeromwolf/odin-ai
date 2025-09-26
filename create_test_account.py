#!/usr/bin/env python3
"""
테스트 계정 생성 스크립트
"""
import requests
import json

def create_test_account():
    """테스트용 계정 생성"""
    url = "http://localhost:8000/api/auth/register"

    # 테스트 계정 정보
    user_data = {
        "email": "demo@odin-ai.com",
        "username": "demo_user",
        "password": "demo123456",
        "full_name": "데모 사용자",
        "company": "오딘AI 테스트"
    }

    try:
        response = requests.post(url, json=user_data)

        if response.status_code == 200:
            result = response.json()
            print("✅ 테스트 계정 생성 성공!")
            print(f"📧 이메일: {result['email']}")
            print(f"👤 사용자명: {result['username']}")
            print(f"👨‍💼 이름: {result['full_name']}")
            print(f"🏢 회사: {result.get('company', 'N/A')}")
            print(f"✅ 활성화: {result['is_active']}")
            print(f"📨 이메일인증: {result['email_verified']}")

        else:
            print(f"❌ 계정 생성 실패: {response.status_code}")
            print(f"오류 메시지: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인하세요.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def test_login():
    """생성된 계정으로 로그인 테스트"""
    url = "http://localhost:8000/api/auth/login"

    login_data = {
        "email": "demo@odin-ai.com",
        "password": "demo123456"
    }

    try:
        response = requests.post(url, json=login_data)

        if response.status_code == 200:
            result = response.json()
            print("\n✅ 로그인 성공!")
            print(f"🔑 액세스 토큰: {result['access_token'][:50]}...")
            print(f"🔄 리프레시 토큰: {result['refresh_token'][:50]}...")
            print(f"⏰ 만료시간: {result['expires_in']}초")
            return result['access_token']
        else:
            print(f"\n❌ 로그인 실패: {response.status_code}")
            print(f"오류 메시지: {response.text}")
            return None

    except Exception as e:
        print(f"\n❌ 로그인 오류: {e}")
        return None

if __name__ == "__main__":
    print("🚀 ODIN-AI 테스트 계정 생성 중...")
    create_test_account()

    print("\n🔐 로그인 테스트 중...")
    access_token = test_login()

    if access_token:
        print("\n📋 로그인 정보 요약:")
        print("=" * 40)
        print("이메일: demo@odin-ai.com")
        print("비밀번호: demo123456")
        print("사용자명: demo_user")
        print("=" * 40)