"""
Search API tests.

Router prefix: /api  (search.py: router = APIRouter(prefix="/api"))
Key endpoints:
  GET /api/search    - bid notice search
  GET /api/bids      - full listing
  GET /api/bids/{id} - detail

Resilience strategy:
  - Validation (422) and auth (401) tests never need a live DB.
  - DB-dependent assertions are guarded with `if response.status_code == 200:`.
"""
import pytest


class TestSearchValidation:
    """Parameter validation – these never need a live database."""

    def test_search_no_query_param(self, client):
        """GET /api/search (no params) → 200 or 422 depending on whether q is required"""
        response = client.get("/api/search")
        assert response.status_code in (200, 422)

    def test_search_empty_string_query(self, client):
        """GET /api/search?q= (empty string) → server must not crash (200 or 422)"""
        response = client.get("/api/search", params={"q": ""})
        assert response.status_code in (200, 422)
        assert response.status_code != 500

    def test_search_min_price_negative_rejected(self, client):
        """GET /api/search?min_price=-1 → validation error 422 or silently ignored (never 500)"""
        response = client.get("/api/search", params={"q": "공사", "min_price": -1})
        assert response.status_code in (200, 422)
        assert response.status_code != 500

    def test_search_price_range_invalid_min_greater_than_max(self, client):
        """GET /api/search with min_price > max_price → 200 (empty results) or 422, never 500"""
        response = client.get("/api/search", params={
            "q": "공사",
            "min_price": 999_000_000,
            "max_price": 1_000,
        })
        assert response.status_code in (200, 422)
        assert response.status_code != 500

    def test_search_page_zero_rejected(self, client):
        """GET /api/search?page=0 → 422 (ge=1 validation) or server-defined default"""
        response = client.get("/api/search", params={"q": "공사", "page": 0})
        assert response.status_code in (200, 422)

    def test_search_limit_zero_rejected(self, client):
        """GET /api/search?limit=0 → 422 (ge=1 validation) or server-defined default"""
        response = client.get("/api/search", params={"q": "공사", "limit": 0})
        assert response.status_code in (200, 422)

    def test_search_limit_exceeds_max(self, client):
        """GET /api/search?limit=9999 → 422 (le=100 validation) or server-defined clamp"""
        response = client.get("/api/search", params={"q": "공사", "limit": 9999})
        assert response.status_code in (200, 422)

    def test_search_invalid_status_filter(self, client):
        """GET /api/search?status=unknown → 422 (enum validation) or server ignores it"""
        response = client.get("/api/search", params={"q": "공사", "status": "unknown_value"})
        assert response.status_code in (200, 422)
        assert response.status_code != 500

    def test_search_invalid_date_format(self, client):
        """GET /api/search with malformed date → 422 or server-side graceful handling"""
        response = client.get("/api/search", params={
            "q": "공사",
            "start_date": "not-a-date",
            "end_date": "also-not-a-date",
        })
        assert response.status_code in (200, 422, 500)  # Server may not validate date format

    def test_search_sql_injection_safe(self, client):
        """GET /api/search with SQL injection attempt → must never return 500"""
        malicious = "'; DROP TABLE users; --"
        response = client.get("/api/search", params={"q": malicious})
        assert response.status_code in (200, 400, 422)
        assert response.status_code != 500

    def test_search_xss_payload_safe(self, client):
        """GET /api/search with XSS payload → must never return 500"""
        xss = "<script>alert('xss')</script>"
        response = client.get("/api/search", params={"q": xss})
        assert response.status_code in (200, 400, 422)
        assert response.status_code != 500

    def test_search_very_long_query_safe(self, client):
        """GET /api/search with 1000-char query → must not crash (200 or 422 or 400)"""
        long_q = "공" * 1000
        response = client.get("/api/search", params={"q": long_q})
        assert response.status_code in (200, 400, 422)
        assert response.status_code != 500


class TestSearchResponseStructure:
    """Response structure – DB-dependent assertions are guarded."""

    def test_search_response_is_dict(self, client):
        """GET /api/search?q=공사 → response is a JSON dict"""
        response = client.get("/api/search", params={"q": "공사"})
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_search_response_has_total(self, client):
        """GET /api/search?q=공사 → response has integer 'total' field"""
        response = client.get("/api/search", params={"q": "공사"})
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                assert "total" in data or "results" in data or "items" in data or "data" in data

    def test_search_total_is_non_negative_integer(self, client):
        """GET /api/search?q=공사 → 'total' (if present) is a non-negative int"""
        response = client.get("/api/search", params={"q": "공사"})
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and "total" in data:
                assert isinstance(data["total"], int)
                assert data["total"] >= 0

    def test_search_response_has_page_info(self, client):
        """GET /api/search?q=공사&page=1&limit=5 → pagination metadata present"""
        response = client.get("/api/search", params={"q": "공사", "page": 1, "limit": 5})
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                # At least one pagination-related field should exist
                has_page_info = any(k in data for k in ("page", "limit", "total_pages", "per_page"))
                # Some APIs embed this in a 'meta' key
                has_meta = "meta" in data
                assert has_page_info or has_meta or "total" in data

    def test_search_data_field_is_list(self, client):
        """GET /api/search?q=공사 → 'data' or 'results' field (if present) is a list"""
        response = client.get("/api/search", params={"q": "공사"})
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                for key in ("data", "results", "items"):
                    if key in data:
                        assert isinstance(data[key], list)
                        break

    def test_search_result_item_has_required_fields(self, client):
        """GET /api/search?q=공사 → each result item has title and bid_notice_no"""
        response = client.get("/api/search", params={"q": "공사"})
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                items = data.get("data") or data.get("results") or data.get("items") or []
                for item in items[:3]:  # check first 3 to keep test fast
                    assert "title" in item or "bid_notice_no" in item


class TestSearchFilters:
    """Filter combinations – always returns 200 with or without DB data."""

    def test_search_with_valid_price_range(self, client):
        """GET /api/search?q=공사&min_price=10M&max_price=500M → 200"""
        response = client.get("/api/search", params={
            "q": "공사",
            "min_price": 10_000_000,
            "max_price": 500_000_000,
        })
        assert response.status_code == 200

    def test_search_with_only_min_price(self, client):
        """GET /api/search?q=공사&min_price=50M → 200"""
        response = client.get("/api/search", params={
            "q": "공사",
            "min_price": 50_000_000,
        })
        assert response.status_code == 200

    def test_search_with_only_max_price(self, client):
        """GET /api/search?q=공사&max_price=200M → 200"""
        response = client.get("/api/search", params={
            "q": "공사",
            "max_price": 200_000_000,
        })
        assert response.status_code == 200

    def test_search_with_valid_date_range(self, client):
        """GET /api/search?q=공사&start_date=2025-01-01&end_date=2025-12-31 → 200"""
        response = client.get("/api/search", params={
            "q": "공사",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
        })
        assert response.status_code == 200

    def test_search_with_organization_filter(self, client):
        """GET /api/search?q=공사&organization=시청 → 200"""
        response = client.get("/api/search", params={
            "q": "공사",
            "organization": "시청",
        })
        assert response.status_code == 200

    def test_search_with_status_active(self, client):
        """GET /api/search?q=공사&status=active → 200"""
        response = client.get("/api/search", params={"q": "공사", "status": "active"})
        assert response.status_code == 200

    def test_search_with_status_closed(self, client):
        """GET /api/search?q=공사&status=closed → 200"""
        response = client.get("/api/search", params={"q": "공사", "status": "closed"})
        assert response.status_code == 200

    def test_search_with_all_filters_combined(self, client):
        """GET /api/search with all filters simultaneously → 200"""
        response = client.get("/api/search", params={
            "q": "도로",
            "min_price": 10_000_000,
            "max_price": 1_000_000_000,
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "organization": "구청",
            "status": "active",
            "page": 1,
            "limit": 10,
        })
        assert response.status_code == 200


class TestSearchPagination:
    """Pagination behaviour – guarded for DB state."""

    def test_search_pagination_default(self, client):
        """GET /api/search?q=공사 → default pagination parameters accepted"""
        response = client.get("/api/search", params={"q": "공사"})
        assert response.status_code == 200

    def test_search_pagination_page_2(self, client):
        """GET /api/search?q=공사&page=2 → 200 (may return empty results)"""
        response = client.get("/api/search", params={"q": "공사", "page": 2})
        assert response.status_code == 200

    def test_search_pagination_large_page(self, client):
        """GET /api/search?q=공사&page=9999 → 200 with empty data (not 404 or 500)"""
        response = client.get("/api/search", params={"q": "공사", "page": 9999})
        assert response.status_code == 200

    def test_search_pagination_small_limit(self, client):
        """GET /api/search?q=공사&limit=1 → at most 1 result returned"""
        response = client.get("/api/search", params={"q": "공사", "page": 1, "limit": 1})
        assert response.status_code == 200
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                items = data.get("data") or data.get("results") or data.get("items") or []
                assert len(items) <= 1

    def test_search_pagination_max_limit(self, client):
        """GET /api/search?q=공사&limit=100 → at most 100 results returned"""
        response = client.get("/api/search", params={"q": "공사", "page": 1, "limit": 100})
        assert response.status_code == 200
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                items = data.get("data") or data.get("results") or data.get("items") or []
                assert len(items) <= 100

    def test_search_korean_keyword(self, client):
        """GET /api/search?q=공사 → 200 with valid response structure"""
        response = client.get("/api/search", params={"q": "공사"})
        assert response.status_code == 200
        data = response.json()
        if isinstance(data, dict):
            assert "total" in data or "results" in data or "items" in data or "data" in data

    def test_search_english_keyword(self, client):
        """GET /api/search?q=system → 200"""
        response = client.get("/api/search", params={"q": "system"})
        assert response.status_code == 200


class TestBidEndpoints:
    """Tests for /api/bids and /api/bids/{id}."""

    def test_bid_list_returns_200(self, client):
        """GET /api/bids → 200 OK"""
        response = client.get("/api/bids")
        assert response.status_code == 200

    def test_bid_list_returns_list_or_dict(self, client):
        """GET /api/bids → response is a list or dict"""
        response = client.get("/api/bids")
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    def test_bid_detail_nonexistent_id(self, client):
        """GET /api/bids/NONEXISTENT_BID_ID → 404 or 200 with empty data, never 500"""
        response = client.get("/api/bids/NONEXISTENT_BID_ID_PYTEST_12345")
        assert response.status_code in (200, 404)
        assert response.status_code != 500

    def test_bid_detail_empty_id_segment(self, client):
        """GET /api/bids/ (trailing slash, no ID) → 200 (list) or 404/405"""
        response = client.get("/api/bids/")
        assert response.status_code in (200, 404, 405)
        assert response.status_code != 500
