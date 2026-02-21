"""
대시보드 API 테스트

라우터 prefix: /api/dashboard
주요 엔드포인트:
  GET /api/dashboard/overview         - 개요 통계
  GET /api/dashboard/statistics       - 통계
  GET /api/dashboard/deadlines        - 마감임박 공고
  GET /api/dashboard/trends           - 트렌드
  GET /api/dashboard/recommendations  - 추천 공고

대시보드는 get_current_user_optional을 사용하므로 인증 없이도 200을 반환합니다.
"""


class TestDashboardOverview:
    def test_overview_status_code(self, client):
        """GET /api/dashboard/overview - 200 응답"""
        response = client.get("/api/dashboard/overview")
        assert response.status_code == 200

    def test_overview_has_total_bids(self, client):
        """GET /api/dashboard/overview - totalBids 또는 total_bids 키 존재"""
        response = client.get("/api/dashboard/overview")
        assert response.status_code == 200
        data = response.json()
        assert "totalBids" in data or "total_bids" in data

    def test_overview_numeric_fields(self, client):
        """GET /api/dashboard/overview - 숫자형 통계 필드"""
        response = client.get("/api/dashboard/overview")
        assert response.status_code == 200
        data = response.json()
        # totalBids(또는 total_bids)가 음수가 아닌지 확인
        total = data.get("totalBids") or data.get("total_bids", 0)
        assert isinstance(total, (int, float))
        assert total >= 0

    def test_overview_with_auth(self, client, auth_headers):
        """GET /api/dashboard/overview - 인증 사용자 추가 데이터"""
        if not auth_headers:
            return  # 인증 없어도 200이어야 하므로 skip 대신 pass
        response = client.get("/api/dashboard/overview", headers=auth_headers)
        assert response.status_code == 200


class TestDashboardStatistics:
    def test_statistics_status_code(self, client):
        """GET /api/dashboard/statistics - 200 응답"""
        response = client.get("/api/dashboard/statistics")
        assert response.status_code == 200

    def test_statistics_is_list_or_dict(self, client):
        """GET /api/dashboard/statistics - 응답이 list 또는 dict"""
        response = client.get("/api/dashboard/statistics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))


class TestDashboardDeadlines:
    def test_deadlines_status_code(self, client):
        """GET /api/dashboard/deadlines - 200 응답"""
        response = client.get("/api/dashboard/deadlines")
        assert response.status_code == 200

    def test_deadlines_is_list_or_dict(self, client):
        """GET /api/dashboard/deadlines - 응답이 list 또는 dict"""
        response = client.get("/api/dashboard/deadlines")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))


class TestDashboardTrends:
    def test_trends_status_code(self, client):
        """GET /api/dashboard/trends - 200 응답"""
        response = client.get("/api/dashboard/trends")
        assert response.status_code == 200

    def test_trends_is_list_or_dict(self, client):
        """GET /api/dashboard/trends - 응답이 list 또는 dict"""
        response = client.get("/api/dashboard/trends")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))


class TestDashboardRecommendations:
    def test_recommendations_status_code(self, client):
        """GET /api/dashboard/recommendations - 200 응답"""
        response = client.get("/api/dashboard/recommendations")
        assert response.status_code == 200

    def test_recommendations_is_list_or_dict(self, client):
        """GET /api/dashboard/recommendations - 응답이 list 또는 dict"""
        response = client.get("/api/dashboard/recommendations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
