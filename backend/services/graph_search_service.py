"""
Neo4j 그래프 검색 서비스
관계 기반 입찰공고 탐색 및 패턴 분석
"""

import os
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Neo4j driver - graceful import
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("neo4j 패키지 미설치 - 그래프 검색 비활성화")


class GraphSearchService:
    """Neo4j 기반 그래프 검색 서비스"""

    def __init__(self):
        if not NEO4J_AVAILABLE:
            raise ImportError("neo4j 패키지 필요: pip install neo4j")

        self._url = os.getenv("NEO4J_URL", "bolt://localhost:7687")
        self._user = os.getenv("NEO4J_USER", "neo4j")
        self._password = os.getenv("NEO4J_PASSWORD", "")
        self._driver = GraphDatabase.driver(self._url, auth=(self._user, self._password))
        logger.info(f"Neo4j 그래프 검색 서비스 초기화: {self._url}")

    def close(self):
        if self._driver:
            self._driver.close()

    def is_available(self) -> bool:
        """Neo4j 연결 상태 확인"""
        try:
            with self._driver.session() as session:
                session.run("RETURN 1")
            return True
        except Exception:
            return False

    def get_status(self) -> dict:
        """Neo4j 상태 및 통계"""
        try:
            with self._driver.session() as session:
                bid_count = session.run(
                    "MATCH (b:BidAnnouncement) RETURN count(b) AS c"
                ).single()["c"]
                org_count = session.run(
                    "MATCH (o:Organization) RETURN count(o) AS c"
                ).single()["c"]
                tag_count = session.run(
                    "MATCH (t:Tag) RETURN count(t) AS c"
                ).single()["c"]
                region_count = session.run(
                    "MATCH (r:Region) RETURN count(r) AS c"
                ).single()["c"]
                rel_count = session.run(
                    "MATCH ()-[r]->() RETURN count(r) AS c"
                ).single()["c"]
                similar_count = session.run(
                    "MATCH ()-[r:SIMILAR_TO]->() RETURN count(r) AS c"
                ).single()["c"]

            return {
                "connected": True,
                "nodes": {
                    "BidAnnouncement": bid_count,
                    "Organization": org_count,
                    "Tag": tag_count,
                    "Region": region_count,
                },
                "relationships": {
                    "total": rel_count,
                    "SIMILAR_TO": similar_count,
                },
            }
        except Exception as e:
            logger.error(f"Neo4j 상태 조회 실패: {e}")
            return {"connected": False, "error": "Neo4j 상태 조회 실패"}

    def search_related(
        self, bid_notice_no: str, depth: int = 2, limit: int = 20
    ) -> dict:
        """특정 입찰공고의 관련 입찰 탐색 (SIMILAR_TO + 같은 기관 + 같은 태그)"""
        try:
            with self._driver.session() as session:
                # 1. Direct SIMILAR_TO relationships
                similar = session.run(
                    """
                    MATCH (b:BidAnnouncement {bid_notice_no: $bid_no})
                          -[r:SIMILAR_TO]-(related:BidAnnouncement)
                    RETURN related.bid_notice_no AS bid_notice_no,
                           related.title AS title,
                           related.estimated_price AS estimated_price,
                           related.organization_name AS organization_name,
                           related.category AS category,
                           r.score AS similarity_score,
                           'similar' AS relation_type
                    ORDER BY r.score DESC
                    LIMIT $limit
                    """,
                    bid_no=bid_notice_no,
                    limit=limit,
                ).data()

                # 2. Same organization bids
                same_org = session.run(
                    """
                    MATCH (b:BidAnnouncement {bid_notice_no: $bid_no})
                          -[:ISSUED_BY]->(org:Organization)
                          <-[:ISSUED_BY]-(related:BidAnnouncement)
                    WHERE related.bid_notice_no <> $bid_no
                    RETURN related.bid_notice_no AS bid_notice_no,
                           related.title AS title,
                           related.estimated_price AS estimated_price,
                           related.organization_name AS organization_name,
                           related.category AS category,
                           org.name AS shared_org,
                           'same_org' AS relation_type
                    LIMIT $limit
                    """,
                    bid_no=bid_notice_no,
                    limit=limit,
                ).data()

                # 3. Shared tags
                shared_tags = session.run(
                    """
                    MATCH (b:BidAnnouncement {bid_notice_no: $bid_no})
                          -[:TAGGED_WITH]->(tag:Tag)
                          <-[:TAGGED_WITH]-(related:BidAnnouncement)
                    WHERE related.bid_notice_no <> $bid_no
                    WITH related, COLLECT(tag.name) AS shared_tags,
                         COUNT(tag) AS tag_count
                    RETURN related.bid_notice_no AS bid_notice_no,
                           related.title AS title,
                           related.estimated_price AS estimated_price,
                           related.organization_name AS organization_name,
                           shared_tags,
                           tag_count,
                           'shared_tags' AS relation_type
                    ORDER BY tag_count DESC
                    LIMIT $limit
                    """,
                    bid_no=bid_notice_no,
                    limit=limit,
                ).data()

            return {
                "bid_notice_no": bid_notice_no,
                "similar": similar,
                "same_organization": same_org,
                "shared_tags": shared_tags,
                "total_related": len(similar) + len(same_org) + len(shared_tags),
            }
        except Exception as e:
            logger.error(f"관련 입찰 검색 실패 [{bid_notice_no}]: {e}")
            raise

    def get_org_network(self, org_name: str, limit: int = 50) -> dict:
        """기관 네트워크 - 해당 기관의 입찰, 태그, 지역 관계"""
        try:
            with self._driver.session() as session:
                # Bids by this org
                bids = session.run(
                    """
                    MATCH (org:Organization)-[:ISSUED_BY]-(b:BidAnnouncement)
                    WHERE org.name CONTAINS $org_name
                    RETURN b.bid_notice_no AS bid_notice_no,
                           b.title AS title,
                           b.estimated_price AS estimated_price,
                           b.category AS category,
                           b.announcement_date AS announcement_date
                    ORDER BY b.announcement_date DESC
                    LIMIT $limit
                    """,
                    org_name=org_name,
                    limit=limit,
                ).data()

                # Tag distribution for this org
                tags = session.run(
                    """
                    MATCH (org:Organization)-[:ISSUED_BY]-(b:BidAnnouncement)
                          -[:TAGGED_WITH]->(t:Tag)
                    WHERE org.name CONTAINS $org_name
                    RETURN t.name AS tag, COUNT(*) AS count
                    ORDER BY count DESC
                    LIMIT 20
                    """,
                    org_name=org_name,
                ).data()

                # Total stats
                stats = session.run(
                    """
                    MATCH (org:Organization)-[:ISSUED_BY]-(b:BidAnnouncement)
                    WHERE org.name CONTAINS $org_name
                    RETURN org.name AS name,
                           COUNT(b) AS total_bids,
                           SUM(b.estimated_price) AS total_amount,
                           AVG(b.estimated_price) AS avg_amount
                    """,
                    org_name=org_name,
                ).data()

            return {
                "organization": org_name,
                "stats": stats[0] if stats else {},
                "bids": bids,
                "tag_distribution": tags,
            }
        except Exception as e:
            logger.error(f"기관 네트워크 조회 실패 [{org_name}]: {e}")
            raise

    def get_tag_network(self, tag_name: str, limit: int = 30) -> dict:
        """태그 네트워크 - 특정 태그와 관련된 입찰 및 co-occurring 태그"""
        try:
            with self._driver.session() as session:
                bids = session.run(
                    """
                    MATCH (t:Tag {name: $tag_name})<-[:TAGGED_WITH]-(b:BidAnnouncement)
                    RETURN b.bid_notice_no AS bid_notice_no,
                           b.title AS title,
                           b.estimated_price AS estimated_price,
                           b.organization_name AS organization_name,
                           b.category AS category
                    ORDER BY b.announcement_date DESC
                    LIMIT $limit
                    """,
                    tag_name=tag_name,
                    limit=limit,
                ).data()

                # Co-occurring tags
                co_tags = session.run(
                    """
                    MATCH (t:Tag {name: $tag_name})<-[:TAGGED_WITH]-(b:BidAnnouncement)
                          -[:TAGGED_WITH]->(other:Tag)
                    WHERE other.name <> $tag_name
                    RETURN other.name AS tag, COUNT(*) AS co_count
                    ORDER BY co_count DESC
                    LIMIT 15
                    """,
                    tag_name=tag_name,
                ).data()

            return {
                "tag": tag_name,
                "total_bids": len(bids),
                "bids": bids,
                "co_occurring_tags": co_tags,
            }
        except Exception as e:
            logger.error(f"태그 네트워크 조회 실패 [{tag_name}]: {e}")
            raise

    def get_region_bids(self, region_name: str, limit: int = 30) -> dict:
        """지역별 입찰 조회"""
        try:
            with self._driver.session() as session:
                bids = session.run(
                    """
                    MATCH (r:Region)<-[:IN_REGION]-(b:BidAnnouncement)
                    WHERE r.name CONTAINS $region_name
                    RETURN b.bid_notice_no AS bid_notice_no,
                           b.title AS title,
                           b.estimated_price AS estimated_price,
                           b.organization_name AS organization_name,
                           b.category AS category,
                           r.name AS region
                    ORDER BY b.announcement_date DESC
                    LIMIT $limit
                    """,
                    region_name=region_name,
                    limit=limit,
                ).data()

            return {
                "region": region_name,
                "total_bids": len(bids),
                "bids": bids,
            }
        except Exception as e:
            logger.error(f"지역별 입찰 조회 실패 [{region_name}]: {e}")
            raise


# Singleton
_graph_service: Optional[GraphSearchService] = None


def get_graph_search_service() -> Optional[GraphSearchService]:
    """그래프 검색 서비스 싱글턴"""
    global _graph_service
    if _graph_service is not None:
        return _graph_service

    if not NEO4J_AVAILABLE:
        return None

    neo4j_url = os.getenv("NEO4J_URL")
    if not neo4j_url:
        return None

    try:
        _graph_service = GraphSearchService()
        return _graph_service
    except Exception as e:
        logger.error(f"그래프 검색 서비스 초기화 실패: {e}")
        return None
