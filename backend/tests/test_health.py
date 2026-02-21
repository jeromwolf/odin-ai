"""
Health check and root endpoint tests.

These tests only hit static FastAPI endpoints and do not require live DB data.
They verify the API server starts correctly, returns the expected structure,
and handles the health-check contract.
"""


class TestRootEndpoint:
    def test_root_returns_200(self, client):
        """GET / → 200 OK always (no DB needed)"""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_json(self, client):
        """GET / → response body is valid JSON dict"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_root_contains_message(self, client):
        """GET / → response contains a 'message' or 'name' field"""
        response = client.get("/")
        data = response.json()
        assert "message" in data or "name" in data

    def test_root_contains_version(self, client):
        """GET / → response contains a 'version' field"""
        response = client.get("/")
        data = response.json()
        assert "version" in data

    def test_root_version_is_string(self, client):
        """GET / → 'version' value is a non-empty string"""
        response = client.get("/")
        data = response.json()
        if "version" in data:
            assert isinstance(data["version"], str)
            assert len(data["version"]) > 0

    def test_root_message_is_string(self, client):
        """GET / → 'message' value is a string when present"""
        response = client.get("/")
        data = response.json()
        if "message" in data:
            assert isinstance(data["message"], str)


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        """GET /health → always 200, even when DB is down (report unhealthy, not 5xx)"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_json(self, client):
        """GET /health → response body is a JSON dict"""
        response = client.get("/health")
        data = response.json()
        assert isinstance(data, dict)

    def test_health_has_status_field(self, client):
        """GET /health → 'status' field is present"""
        response = client.get("/health")
        data = response.json()
        assert "status" in data

    def test_health_status_valid_value(self, client):
        """GET /health → status is 'healthy' or 'unhealthy'"""
        response = client.get("/health")
        data = response.json()
        assert data["status"] in ("healthy", "unhealthy")

    def test_health_has_timestamp(self, client):
        """GET /health → 'timestamp' field is present"""
        response = client.get("/health")
        data = response.json()
        assert "timestamp" in data

    def test_health_timestamp_is_string(self, client):
        """GET /health → 'timestamp' is a non-empty string"""
        response = client.get("/health")
        data = response.json()
        ts = data.get("timestamp")
        assert isinstance(ts, str) and len(ts) > 0

    def test_health_has_services(self, client):
        """GET /health → 'services' section is present"""
        response = client.get("/health")
        data = response.json()
        assert "services" in data

    def test_health_services_is_dict(self, client):
        """GET /health → 'services' is a dict"""
        response = client.get("/health")
        data = response.json()
        assert isinstance(data["services"], dict)

    def test_health_services_has_database(self, client):
        """GET /health → services contains 'database' key"""
        response = client.get("/health")
        data = response.json()
        assert "database" in data["services"]

    def test_health_database_status_valid(self, client):
        """GET /health → database status is 'connected' or 'disconnected'"""
        response = client.get("/health")
        db_status = response.json()["services"]["database"]
        assert db_status in ("connected", "disconnected")

    def test_health_has_version(self, client):
        """GET /health → 'version' field is present"""
        response = client.get("/health")
        data = response.json()
        assert "version" in data

    def test_health_services_has_redis(self, client):
        """GET /health → services contains 'redis' key"""
        response = client.get("/health")
        data = response.json()
        assert "redis" in data["services"]

    def test_health_redis_status_valid(self, client):
        """GET /health → redis status is 'connected' or 'disconnected'"""
        response = client.get("/health")
        redis_status = response.json()["services"]["redis"]
        assert redis_status in ("connected", "disconnected")

    def test_health_healthy_when_db_connected(self, client):
        """GET /health → status is 'healthy' only when database is 'connected'"""
        response = client.get("/health")
        data = response.json()
        db_status = data["services"]["database"]
        overall = data["status"]
        if db_status == "connected":
            assert overall == "healthy"
        else:
            assert overall == "unhealthy"
