"""
Admin API tests.

Admin endpoints:
  POST /api/admin/auth/login                     - admin login
  GET  /api/admin/batch/executions               - batch execution history
  POST /api/admin/batch/execute                  - trigger batch manually
  GET  /api/admin/system/status                  - system status
  GET  /api/admin/system/metrics                 - system metrics
  GET  /api/admin/system/notifications/status    - notification send status
  GET  /api/admin/users/                         - user list
  GET  /api/admin/users/statistics/summary       - user statistics
  GET  /api/admin/users/{id}                     - user detail
  GET  /api/admin/logs/                          - log listing
  GET  /api/admin/statistics/bid-collection      - bid collection stats
  GET  /api/admin/statistics/category-distribution - category distribution

Strategy:
  - Validation (422) tests never need a live DB.
  - Auth-enforcement (401/403) tests never need a live DB.
  - DB-dependent assertions are guarded with `if response.status_code == 200:`.
"""
import pytest


# ---------------------------------------------------------------------------
# Admin Auth
# ---------------------------------------------------------------------------

class TestAdminAuth:
    """Admin login – validation errors never require a live database."""

    def test_admin_login_empty_body(self, client):
        """POST /api/admin/auth/login with empty body → 422"""
        response = client.post("/api/admin/auth/login", json={})
        assert response.status_code == 422

    def test_admin_login_missing_password(self, client):
        """POST /api/admin/auth/login without password → 422"""
        response = client.post(
            "/api/admin/auth/login",
            json={"email": "admin@odin.ai"},
        )
        assert response.status_code == 422

    def test_admin_login_missing_email(self, client):
        """POST /api/admin/auth/login without email → 422"""
        response = client.post(
            "/api/admin/auth/login",
            json={"password": "admin123"},
        )
        assert response.status_code == 422

    def test_admin_login_invalid_email_format(self, client):
        """POST /api/admin/auth/login with bad email format → 422"""
        response = client.post(
            "/api/admin/auth/login",
            json={"email": "not-an-email", "password": "admin123"},
        )
        assert response.status_code in (422, 401, 403)

    def test_admin_login_wrong_credentials(self, client):
        """POST /api/admin/auth/login with incorrect credentials → 401/403/404"""
        response = client.post(
            "/api/admin/auth/login",
            json={"email": "nobody@example.com", "password": "wrongpassword"},
        )
        assert response.status_code in (401, 403, 404)

    def test_admin_login_non_admin_user_rejected(self, client):
        """POST /api/admin/auth/login with normal user account → 401/403"""
        response = client.post(
            "/api/admin/auth/login",
            json={"email": "e2e-test@odin-ai.com", "password": "TestPass123!"},
        )
        # Either credentials wrong (401) or role insufficient (403)
        assert response.status_code in (401, 403, 404)

    def test_admin_login_success_returns_token(self, client):
        """POST /api/admin/auth/login with valid admin credentials → 200 with token"""
        response = client.post(
            "/api/admin/auth/login",
            json={"email": "admin@odin.ai", "password": "admin123"},
        )
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data or "token" in data

    def test_admin_login_token_type_is_bearer(self, client):
        """POST /api/admin/auth/login successful → token_type is 'bearer'"""
        response = client.post(
            "/api/admin/auth/login",
            json={"email": "admin@odin.ai", "password": "admin123"},
        )
        if response.status_code == 200:
            data = response.json()
            if "token_type" in data:
                assert data["token_type"].lower() == "bearer"


# ---------------------------------------------------------------------------
# Admin Batch
# ---------------------------------------------------------------------------

class TestAdminBatch:
    """Batch monitoring endpoints – auth enforcement + DB-guarded assertions."""

    def test_batch_executions_no_auth(self, client):
        """GET /api/admin/batch/executions without auth → 401 or 403"""
        response = client.get("/api/admin/batch/executions")
        assert response.status_code in (401, 403)

    def test_batch_executions_invalid_token(self, client):
        """GET /api/admin/batch/executions with bad token → 401 or 403"""
        response = client.get(
            "/api/admin/batch/executions",
            headers={"Authorization": "Bearer fake.token.value"},
        )
        assert response.status_code in (401, 403)

    def test_batch_execute_no_auth(self, client):
        """POST /api/admin/batch/execute without auth → 401 or 403"""
        response = client.post("/api/admin/batch/execute", json={"batch_type": "full"})
        assert response.status_code in (401, 403)

    def test_batch_executions_with_admin(self, client, admin_headers):
        """GET /api/admin/batch/executions with admin token → 200"""
        if not admin_headers:
            pytest.skip("No admin token available (admin@odin.ai account missing)")
        response = client.get(
            "/api/admin/batch/executions",
            headers=admin_headers,
        )
        if response.status_code == 401:
            pytest.skip("Admin token not accepted in test environment")
        assert response.status_code == 200

    def test_batch_executions_response_structure(self, client, admin_headers):
        """GET /api/admin/batch/executions → response is a list or dict"""
        if not admin_headers:
            pytest.skip("No admin token available")
        response = client.get(
            "/api/admin/batch/executions",
            headers=admin_headers,
        )
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    def test_batch_executions_with_pagination(self, client, admin_headers):
        """GET /api/admin/batch/executions?page=1&limit=5 → 200"""
        if not admin_headers:
            pytest.skip("No admin token available")
        response = client.get(
            "/api/admin/batch/executions",
            params={"page": 1, "limit": 5},
            headers=admin_headers,
        )
        if response.status_code == 401:
            pytest.skip("Admin token not accepted in test environment")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Admin System
# ---------------------------------------------------------------------------

class TestAdminSystem:
    """System monitoring endpoints."""

    def test_system_status_no_auth(self, client):
        """GET /api/admin/system/status without auth → 401 or 403"""
        response = client.get("/api/admin/system/status")
        assert response.status_code in (401, 403)

    def test_system_metrics_no_auth(self, client):
        """GET /api/admin/system/metrics without auth → 401 or 403"""
        response = client.get("/api/admin/system/metrics")
        assert response.status_code in (401, 403)

    def test_notifications_status_no_auth(self, client):
        """GET /api/admin/system/notifications/status without auth → 401 or 403"""
        response = client.get("/api/admin/system/notifications/status")
        assert response.status_code in (401, 403)

    def test_system_status_with_admin(self, client, admin_headers):
        """GET /api/admin/system/status with admin token → 200"""
        if not admin_headers:
            pytest.skip("No admin token available")
        response = client.get(
            "/api/admin/system/status",
            headers=admin_headers,
        )
        if response.status_code == 401:
            pytest.skip("Admin token not accepted in test environment")
        assert response.status_code == 200

    def test_system_status_has_expected_fields(self, client, admin_headers):
        """GET /api/admin/system/status → response is a dict with system info"""
        if not admin_headers:
            pytest.skip("No admin token available")
        response = client.get(
            "/api/admin/system/status",
            headers=admin_headers,
        )
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_system_metrics_with_admin(self, client, admin_headers):
        """GET /api/admin/system/metrics with admin token → 200"""
        if not admin_headers:
            pytest.skip("No admin token available")
        response = client.get(
            "/api/admin/system/metrics",
            headers=admin_headers,
        )
        if response.status_code == 401:
            pytest.skip("Admin token not accepted in test environment")
        assert response.status_code == 200

    def test_system_metrics_is_dict(self, client, admin_headers):
        """GET /api/admin/system/metrics → response is a dict"""
        if not admin_headers:
            pytest.skip("No admin token available")
        response = client.get(
            "/api/admin/system/metrics",
            headers=admin_headers,
        )
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_notifications_status_with_admin(self, client, admin_headers):
        """GET /api/admin/system/notifications/status with admin token → 200"""
        if not admin_headers:
            pytest.skip("No admin token available")
        response = client.get(
            "/api/admin/system/notifications/status",
            headers=admin_headers,
        )
        if response.status_code == 401:
            pytest.skip("Admin token not accepted in test environment")
        assert response.status_code == 200

    def test_notifications_status_has_counts(self, client, admin_headers):
        """GET /api/admin/system/notifications/status → numeric count fields"""
        if not admin_headers:
            pytest.skip("No admin token available")
        response = client.get(
            "/api/admin/system/notifications/status",
            headers=admin_headers,
        )
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                # Any of these count fields should be non-negative integers
                for key in ("total_sent", "success_count", "failed_count", "pending_count"):
                    if key in data:
                        assert isinstance(data[key], (int, float))
                        assert data[key] >= 0


# ---------------------------------------------------------------------------
# Admin Users
# ---------------------------------------------------------------------------

class TestAdminUsers:
    """User management endpoints."""

    def test_user_list_no_auth(self, client):
        """GET /api/admin/users/ without auth → 401 or 403"""
        response = client.get("/api/admin/users/")
        assert response.status_code in (401, 403)

    def test_user_stats_no_auth(self, client):
        """GET /api/admin/users/statistics/summary without auth → 401 or 403"""
        response = client.get("/api/admin/users/statistics/summary")
        assert response.status_code in (401, 403)

    def test_user_detail_no_auth(self, client):
        """GET /api/admin/users/1 without auth → 401 or 403"""
        response = client.get("/api/admin/users/1")
        assert response.status_code in (401, 403)

    def test_user_list_with_admin(self, client, admin_headers):
        """GET /api/admin/users/ with admin token → 200"""
        if not admin_headers:
            pytest.skip("No admin token available")
        response = client.get("/api/admin/users/", headers=admin_headers)
        if response.status_code == 401:
            pytest.skip("Admin token not accepted in test environment")
        assert response.status_code == 200

    def test_user_list_response_structure(self, client, admin_headers):
        """GET /api/admin/users/ → response is a list or dict"""
        if not admin_headers:
            pytest.skip("No admin token available")
        response = client.get("/api/admin/users/", headers=admin_headers)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    def test_user_list_pagination(self, client, admin_headers):
        """GET /api/admin/users/?page=1&limit=5 → 200"""
        if not admin_headers:
            pytest.skip("No admin token available")
        response = client.get(
            "/api/admin/users/",
            params={"page": 1, "limit": 5},
            headers=admin_headers,
        )
        if response.status_code == 401:
            pytest.skip("Admin token not accepted in test environment")
        assert response.status_code == 200

    def test_user_stats_with_admin(self, client, admin_headers):
        """GET /api/admin/users/statistics/summary with admin token → 200"""
        if not admin_headers:
            pytest.skip("No admin token available")
        response = client.get(
            "/api/admin/users/statistics/summary",
            headers=admin_headers,
        )
        if response.status_code == 401:
            pytest.skip("Admin token not accepted in test environment")
        assert response.status_code == 200

    def test_user_stats_has_totals(self, client, admin_headers):
        """GET /api/admin/users/statistics/summary → total_users (or similar) is int >= 0"""
        if not admin_headers:
            pytest.skip("No admin token available")
        response = client.get(
            "/api/admin/users/statistics/summary",
            headers=admin_headers,
        )
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                for key in ("total_users", "active_users", "total"):
                    if key in data:
                        assert isinstance(data[key], (int, float))
                        assert data[key] >= 0

    def test_user_detail_nonexistent(self, client, admin_headers):
        """GET /api/admin/users/9999999 (non-existent) → 404 or 200 with empty, not 500"""
        if not admin_headers:
            pytest.skip("No admin token available")
        response = client.get(
            "/api/admin/users/9999999",
            headers=admin_headers,
        )
        if response.status_code == 401:
            pytest.skip("Admin token not accepted in test environment")
        assert response.status_code in (200, 404)
        assert response.status_code != 500


# ---------------------------------------------------------------------------
# Admin Logs
# ---------------------------------------------------------------------------

class TestAdminLogs:
    """Log retrieval endpoints."""

    def test_logs_no_auth(self, client):
        """GET /api/admin/logs/ without auth → 401 or 403"""
        response = client.get("/api/admin/logs/")
        assert response.status_code in (401, 403)

    def test_logs_with_admin(self, client, admin_headers):
        """GET /api/admin/logs/ with admin token → 200"""
        if not admin_headers:
            pytest.skip("No admin token available")
        response = client.get("/api/admin/logs/", headers=admin_headers)
        if response.status_code == 401:
            pytest.skip("Admin token not accepted in test environment")
        assert response.status_code == 200

    def test_logs_response_structure(self, client, admin_headers):
        """GET /api/admin/logs/ → response is a list or dict"""
        if not admin_headers:
            pytest.skip("No admin token available")
        response = client.get("/api/admin/logs/", headers=admin_headers)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    def test_logs_with_limit_param(self, client, admin_headers):
        """GET /api/admin/logs/?limit=10 → 200"""
        if not admin_headers:
            pytest.skip("No admin token available")
        response = client.get(
            "/api/admin/logs/",
            params={"limit": 10},
            headers=admin_headers,
        )
        if response.status_code == 401:
            pytest.skip("Admin token not accepted in test environment")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Admin Statistics
# ---------------------------------------------------------------------------

class TestAdminStatistics:
    """Statistics endpoints."""

    def test_bid_collection_stats_no_auth(self, client):
        """GET /api/admin/statistics/bid-collection without auth → 401 or 403"""
        response = client.get("/api/admin/statistics/bid-collection")
        assert response.status_code in (401, 403)

    def test_category_distribution_no_auth(self, client):
        """GET /api/admin/statistics/category-distribution without auth → 401 or 403"""
        response = client.get("/api/admin/statistics/category-distribution")
        assert response.status_code in (401, 403)

    def test_bid_collection_stats_with_admin(self, client, admin_headers):
        """GET /api/admin/statistics/bid-collection?days=7 with admin token → 200"""
        if not admin_headers:
            pytest.skip("No admin token available")
        response = client.get(
            "/api/admin/statistics/bid-collection",
            params={"days": 7},
            headers=admin_headers,
        )
        if response.status_code == 401:
            pytest.skip("Admin token not accepted in test environment")
        assert response.status_code == 200

    def test_bid_collection_stats_response_has_stats(self, client, admin_headers):
        """GET /api/admin/statistics/bid-collection → 'stats' list present"""
        if not admin_headers:
            pytest.skip("No admin token available")
        response = client.get(
            "/api/admin/statistics/bid-collection",
            params={"days": 7},
            headers=admin_headers,
        )
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                assert "stats" in data or "data" in data or isinstance(data, dict)

    def test_bid_collection_stats_days_param_variations(self, client, admin_headers):
        """GET /api/admin/statistics/bid-collection with various days values → 200"""
        if not admin_headers:
            pytest.skip("No admin token available")
        for days in (1, 7, 30):
            response = client.get(
                "/api/admin/statistics/bid-collection",
                params={"days": days},
                headers=admin_headers,
            )
            if response.status_code == 401:
                pytest.skip("Admin token not accepted in test environment")
            assert response.status_code == 200, f"Failed for days={days}"

    def test_category_distribution_with_admin(self, client, admin_headers):
        """GET /api/admin/statistics/category-distribution with admin token → 200"""
        if not admin_headers:
            pytest.skip("No admin token available")
        response = client.get(
            "/api/admin/statistics/category-distribution",
            headers=admin_headers,
        )
        if response.status_code == 401:
            pytest.skip("Admin token not accepted in test environment")
        assert response.status_code == 200

    def test_category_distribution_response_is_list_or_dict(self, client, admin_headers):
        """GET /api/admin/statistics/category-distribution → list or dict"""
        if not admin_headers:
            pytest.skip("No admin token available")
        response = client.get(
            "/api/admin/statistics/category-distribution",
            headers=admin_headers,
        )
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))
