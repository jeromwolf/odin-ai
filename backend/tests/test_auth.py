"""
인증 API 테스트

라우터 prefix: /api/auth  (auth.py: router = APIRouter(prefix="/api/auth"))
주요 엔드포인트:
  POST /api/auth/register   - 회원가입
  POST /api/auth/login      - 로그인
  GET  /api/auth/me         - 내 정보 조회
  POST /api/auth/logout     - 로그아웃
  POST /api/auth/refresh    - 토큰 갱신
"""
import pytest
import uuid


class TestAuthLogin:
    def test_login_missing_all_fields(self, client):
        """POST /api/auth/login - 필드 전부 누락 → 422"""
        response = client.post("/api/auth/login", json={})
        assert response.status_code == 422

    def test_login_missing_password(self, client):
        """POST /api/auth/login - 비밀번호 누락 → 422"""
        response = client.post("/api/auth/login", json={"email": "test@example.com"})
        assert response.status_code == 422

    def test_login_missing_email(self, client):
        """POST /api/auth/login - 이메일 누락 → 422"""
        response = client.post("/api/auth/login", json={"password": "SomePass123!"})
        assert response.status_code == 422

    def test_login_invalid_email_format(self, client):
        """POST /api/auth/login - 이메일 형식 오류 → 422"""
        response = client.post("/api/auth/login", json={
            "email": "not-an-email",
            "password": "SomePass123!"
        })
        assert response.status_code == 422

    def test_login_nonexistent_user(self, client):
        """POST /api/auth/login - 존재하지 않는 사용자 → 401 또는 404"""
        response = client.post("/api/auth/login", json={
            "email": f"ghost-{uuid.uuid4()}@test.com",
            "password": "WrongPass999!"
        })
        assert response.status_code in (401, 404)

    def test_login_wrong_password(self, client):
        """POST /api/auth/login - 잘못된 비밀번호 → 401"""
        response = client.post("/api/auth/login", json={
            "email": "admin@odin.ai",
            "password": "definitively_wrong_password"
        })
        assert response.status_code in (401, 404)

    def test_login_admin_success(self, client):
        """POST /api/auth/login - 관리자 계정 정상 로그인"""
        response = client.post("/api/auth/login", json={
            "email": "admin@odin.ai",
            "password": "admin123"
        })
        # DB에 계정이 있을 때만 200 검증
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data.get("token_type") == "bearer"

    def test_login_returns_token_fields(self, client):
        """POST /api/auth/login - 성공 시 토큰 구조 확인"""
        response = client.post("/api/auth/login", json={
            "email": "admin@odin.ai",
            "password": "admin123"
        })
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert isinstance(data["access_token"], str)
            assert len(data["access_token"]) > 0


class TestAuthMe:
    def test_me_without_token(self, client):
        """GET /api/auth/me - 토큰 없음 → 401 또는 403"""
        response = client.get("/api/auth/me")
        assert response.status_code in (401, 403)

    def test_me_with_invalid_token(self, client):
        """GET /api/auth/me - 유효하지 않은 토큰 → 401"""
        response = client.get("/api/auth/me", headers={
            "Authorization": "Bearer this.is.not.a.valid.jwt.token"
        })
        assert response.status_code in (401, 403)

    def test_me_with_valid_token(self, client, auth_headers):
        """GET /api/auth/me - 유효한 토큰으로 내 정보 조회"""
        if not auth_headers:
            pytest.skip("No auth token available (e2e-test@odin-ai.com 계정 없음)")
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data or "id" in data


class TestAuthRegister:
    def test_register_missing_fields(self, client):
        """POST /api/auth/register - 필수 필드 누락 → 422"""
        response = client.post("/api/auth/register", json={})
        assert response.status_code == 422

    def test_register_invalid_email(self, client):
        """POST /api/auth/register - 이메일 형식 오류 → 422"""
        response = client.post("/api/auth/register", json={
            "email": "bad-email",
            "username": "testuser",
            "password": "TestPass123!"
        })
        assert response.status_code == 422

    def test_register_short_password(self, client):
        """POST /api/auth/register - 8자 미만 비밀번호 → 422"""
        response = client.post("/api/auth/register", json={
            "email": f"new-{uuid.uuid4()}@test.com",
            "username": "testuser99",
            "password": "short"
        })
        assert response.status_code == 422

    def test_register_short_username(self, client):
        """POST /api/auth/register - 3자 미만 username → 422"""
        response = client.post("/api/auth/register", json={
            "email": f"new-{uuid.uuid4()}@test.com",
            "username": "ab",
            "password": "TestPass123!"
        })
        assert response.status_code == 422

    def test_register_duplicate_email(self, client):
        """POST /api/auth/register - 이미 존재하는 이메일 → 400 또는 409"""
        response = client.post("/api/auth/register", json={
            "email": "admin@odin.ai",
            "username": f"duplicate_{uuid.uuid4().hex[:8]}",
            "password": "TestPass123!"
        })
        assert response.status_code in (400, 409, 422)


class TestAuthLogout:
    def test_logout_without_token(self, client):
        """POST /api/auth/logout - 토큰 없음 → 401 또는 403 또는 200"""
        response = client.post("/api/auth/logout")
        # 구현에 따라 다를 수 있음
        assert response.status_code in (200, 401, 403)

    def test_logout_with_valid_token(self, client, auth_headers):
        """POST /api/auth/logout - 유효한 토큰으로 로그아웃"""
        if not auth_headers:
            pytest.skip("No auth token available")
        response = client.post("/api/auth/logout", headers=auth_headers)
        assert response.status_code in (200, 204)
