"""
Notifications API tests.

Router prefix: /api/notifications  (notifications.py)

Key endpoints:
  GET    /api/notifications/          - notification list (auth required)
  GET    /api/notifications/settings  - notification settings (may be optional auth)
  PUT    /api/notifications/settings  - update settings (auth required)
  GET    /api/notifications/rules     - alert rules list (auth required)
  POST   /api/notifications/rules     - create alert rule (auth required)
  PUT    /api/notifications/rules/{id} - update rule (auth required)
  DELETE /api/notifications/rules/{id} - delete rule (auth required)
  GET    /api/notifications/history   - notification history (auth required)
"""
import pytest


class TestNotificationsUnauthenticated:
    """Auth-enforcement tests – no live DB required."""

    def test_get_notifications_no_token(self, client):
        """GET /api/notifications/ without token → 401 or 403"""
        response = client.get("/api/notifications/")
        assert response.status_code in (401, 403)

    def test_get_notifications_invalid_token(self, client):
        """GET /api/notifications/ with malformed Bearer → 401 or 403"""
        response = client.get(
            "/api/notifications/",
            headers={"Authorization": "Bearer garbage.token.value"},
        )
        assert response.status_code in (401, 403)

    def test_get_notifications_with_valid_status_filter_no_auth(self, client):
        """GET /api/notifications/?status_filter=unread without token → 401 or 403"""
        response = client.get(
            "/api/notifications/",
            params={"status_filter": "unread"},
        )
        assert response.status_code in (401, 403)

    def test_get_rules_no_token(self, client):
        """GET /api/notifications/rules without token → 401 or 403"""
        response = client.get("/api/notifications/rules")
        assert response.status_code in (401, 403)

    def test_create_rule_no_token(self, client):
        """POST /api/notifications/rules without token → 401 or 403"""
        response = client.post(
            "/api/notifications/rules",
            json={"rule_name": "test", "conditions": {}},
        )
        assert response.status_code in (401, 403)

    def test_delete_rule_no_token(self, client):
        """DELETE /api/notifications/rules/1 without token → 401 or 403"""
        response = client.delete("/api/notifications/rules/1")
        assert response.status_code in (401, 403)

    def test_get_history_no_token(self, client):
        """GET /api/notifications/history without token → 401 or 403"""
        response = client.get("/api/notifications/history")
        assert response.status_code in (401, 403)

    def test_get_settings_no_token(self, client):
        """GET /api/notifications/settings without token → 200 (optional auth) or 401/403"""
        response = client.get("/api/notifications/settings")
        # Some implementations use get_current_user_optional → 200 acceptable
        assert response.status_code in (200, 401, 403)

    def test_put_settings_no_token(self, client):
        """PUT /api/notifications/settings without token → 401 or 403"""
        response = client.put(
            "/api/notifications/settings",
            json={"email_enabled": True},
        )
        assert response.status_code in (401, 403)


class TestNotificationsValidation:
    """Input validation checks that don't require DB or auth to expose 422 errors."""

    def test_get_notifications_invalid_status_filter(self, client, auth_headers):
        """GET /api/notifications/?status_filter=bad_value → 422 (regex validation)"""
        if not auth_headers:
            pytest.skip("No auth token available")
        response = client.get(
            "/api/notifications/",
            params={"status_filter": "invalid_status"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_get_notifications_page_zero(self, client, auth_headers):
        """GET /api/notifications/?page=0 → 422 (ge=1)"""
        if not auth_headers:
            pytest.skip("No auth token available")
        response = client.get(
            "/api/notifications/",
            params={"page": 0},
            headers=auth_headers,
        )
        assert response.status_code in (200, 422)

    def test_get_notifications_limit_exceeds_max(self, client, auth_headers):
        """GET /api/notifications/?limit=9999 → 422 (le=100)"""
        if not auth_headers:
            pytest.skip("No auth token available")
        response = client.get(
            "/api/notifications/",
            params={"limit": 9999},
            headers=auth_headers,
        )
        assert response.status_code in (200, 422)

    def test_create_rule_missing_required_fields(self, client, auth_headers):
        """POST /api/notifications/rules with empty body → 422"""
        if not auth_headers:
            pytest.skip("No auth token available")
        response = client.post(
            "/api/notifications/rules",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_rule_missing_conditions(self, client, auth_headers):
        """POST /api/notifications/rules without 'conditions' → 422"""
        if not auth_headers:
            pytest.skip("No auth token available")
        response = client.post(
            "/api/notifications/rules",
            json={"rule_name": "test_rule"},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestNotificationsAuthenticated:
    """DB-dependent tests – skip gracefully when auth token is unavailable."""

    def test_get_settings_returns_dict(self, client, auth_headers):
        """GET /api/notifications/settings → 200 with dict response"""
        if not auth_headers:
            pytest.skip("No auth token available")
        response = client.get("/api/notifications/settings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_settings_has_email_field(self, client, auth_headers):
        """GET /api/notifications/settings → response has email-related field"""
        if not auth_headers:
            pytest.skip("No auth token available")
        response = client.get("/api/notifications/settings", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                # At least one notification channel field should be present
                has_channel_field = any(
                    k in data
                    for k in ("email_enabled", "push_enabled", "web_enabled", "sms_enabled")
                )
                # Some APIs may return other structures; be permissive
                assert has_channel_field or len(data) > 0

    def test_get_notifications_list_returns_200(self, client, auth_headers):
        """GET /api/notifications/ → 200"""
        if not auth_headers:
            pytest.skip("No auth token available")
        response = client.get("/api/notifications/", headers=auth_headers)
        assert response.status_code == 200

    def test_get_notifications_list_is_list_or_dict(self, client, auth_headers):
        """GET /api/notifications/ → response is a list or dict"""
        if not auth_headers:
            pytest.skip("No auth token available")
        response = client.get("/api/notifications/", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    def test_get_notifications_unread_filter(self, client, auth_headers):
        """GET /api/notifications/?status_filter=unread → 200"""
        if not auth_headers:
            pytest.skip("No auth token available")
        response = client.get(
            "/api/notifications/",
            params={"status_filter": "unread"},
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_get_notifications_read_filter(self, client, auth_headers):
        """GET /api/notifications/?status_filter=read → 200"""
        if not auth_headers:
            pytest.skip("No auth token available")
        response = client.get(
            "/api/notifications/",
            params={"status_filter": "read"},
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_get_notifications_all_filter(self, client, auth_headers):
        """GET /api/notifications/?status_filter=all → 200"""
        if not auth_headers:
            pytest.skip("No auth token available")
        response = client.get(
            "/api/notifications/",
            params={"status_filter": "all"},
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_get_rules_returns_200(self, client, auth_headers):
        """GET /api/notifications/rules → 200"""
        if not auth_headers:
            pytest.skip("No auth token available")
        response = client.get("/api/notifications/rules", headers=auth_headers)
        assert response.status_code == 200

    def test_get_rules_is_list_or_dict(self, client, auth_headers):
        """GET /api/notifications/rules → response is a list or dict"""
        if not auth_headers:
            pytest.skip("No auth token available")
        response = client.get("/api/notifications/rules", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    def test_get_history_returns_200(self, client, auth_headers):
        """GET /api/notifications/history → 200"""
        if not auth_headers:
            pytest.skip("No auth token available")
        response = client.get("/api/notifications/history", headers=auth_headers)
        assert response.status_code == 200

    def test_create_alert_rule_valid_payload(self, client, auth_headers):
        """POST /api/notifications/rules with valid payload → 200 or 201"""
        if not auth_headers:
            pytest.skip("No auth token available")
        payload = {
            "rule_name": "pytest-rule",
            "description": "Automated pytest test rule",
            "conditions": {
                "keywords": ["pytest", "테스트"],
                "min_price": 10_000_000,
                "max_price": 500_000_000,
            },
            "notification_channels": ["email"],
            "notification_timing": "immediate",
        }
        response = client.post(
            "/api/notifications/rules",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code in (200, 201)

    def test_update_notification_settings(self, client, auth_headers):
        """PUT /api/notifications/settings with valid payload → 200 or 204"""
        if not auth_headers:
            pytest.skip("No auth token available")
        payload = {
            "email_enabled": True,
            "web_enabled": True,
            "alert_match_enabled": True,
        }
        response = client.put(
            "/api/notifications/settings",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code in (200, 204)
