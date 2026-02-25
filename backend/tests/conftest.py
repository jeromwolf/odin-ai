"""
ODIN-AI Backend Test Configuration

DATABASE_URL and SECRET_KEY must be set in the environment before running tests.
Example:
    export DATABASE_URL="postgresql://blockmeta@localhost:5432/odin_db"
    export SECRET_KEY="test-secret-key"
    pytest
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient

# backend 디렉토리를 path에 추가 (main.py, api/, auth/ 등 직접 임포트 가능하도록)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient (세션 전체에서 재사용)"""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def base_url():
    """API base URL (TestClient는 상대 경로 사용)"""
    return ""


@pytest.fixture
def auth_headers(client):
    """인증된 요청 헤더 (테스트 사용자 로그인).

    e2e-test@odin-ai.com 계정이 없으면 빈 dict를 반환합니다.
    테스트에서는 `if not auth_headers: pytest.skip(...)` 패턴으로 처리하세요.
    """
    response = client.post("/api/auth/login", json={
        "email": "e2e-test@odin-ai.com",
        "password": "TestPass123!"
    })
    if response.status_code == 200:
        token = response.json().get("access_token", "")
        if token:
            return {"Authorization": f"Bearer {token}"}
    return {}


@pytest.fixture
def admin_headers(client):
    """관리자 인증 헤더.

    admin@odin.ai 계정이 없으면 빈 dict를 반환합니다.
    """
    response = client.post("/api/admin/auth/login", json={
        "email": "admin@odin.ai",
        "password": "admin123"
    })
    if response.status_code == 200:
        token = response.json().get("access_token", "")
        if token:
            return {"Authorization": f"Bearer {token}"}
    return {}
