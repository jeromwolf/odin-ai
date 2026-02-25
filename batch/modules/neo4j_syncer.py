#!/usr/bin/env python
"""
Neo4j Graph Synchronization Module
PostgreSQL -> Neo4j 그래프 데이터베이스 동기화

노드 타입:
  - BidAnnouncement: 입찰공고
  - Organization: 발주기관
  - Tag: 태그
  - Region: 지역 (시/도)

관계:
  - (BidAnnouncement)-[:ISSUED_BY]->(Organization)
  - (BidAnnouncement)-[:TAGGED_WITH]->(Tag)
  - (BidAnnouncement)-[:IN_REGION]->(Region)
  - (BidAnnouncement)-[:SIMILAR_TO {score}]->(BidAnnouncement)
"""

import os
import re
import json
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from loguru import logger

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("neo4j 패키지가 설치되지 않았습니다. pip install neo4j")


# 한국 시/도 매핑 테이블
REGION_PATTERNS = [
    # 광역시/특별시/특별자치시
    (r'서울', '서울특별시'),
    (r'부산', '부산광역시'),
    (r'대구', '대구광역시'),
    (r'인천', '인천광역시'),
    (r'광주광역', '광주광역시'),
    (r'대전', '대전광역시'),
    (r'울산', '울산광역시'),
    (r'세종', '세종특별자치시'),
    # 도
    (r'경기', '경기도'),
    (r'강원', '강원특별자치도'),
    (r'충청?북|충북', '충청북도'),
    (r'충청?남|충남', '충청남도'),
    (r'전라?북|전북', '전라북도'),
    (r'전라?남|전남', '전라남도'),
    (r'경상?북|경북', '경상북도'),
    (r'경상?남|경남', '경상남도'),
    (r'제주', '제주특별자치도'),
]


def extract_region(organization_name: str) -> Optional[str]:
    """발주기관명에서 시/도 지역을 추출한다.

    Args:
        organization_name: 발주기관명 (예: '충남 공주시', '경기도 수원시', '서울특별시')

    Returns:
        추출된 시/도 이름 또는 None
    """
    if not organization_name:
        return None

    for pattern, region_name in REGION_PATTERNS:
        if re.search(pattern, organization_name):
            return region_name

    return None


class Neo4jSyncer:
    """PostgreSQL -> Neo4j 그래프 동기화 클래스"""

    def __init__(self, db_url: str, neo4j_url: str, neo4j_user: str, neo4j_password: str):
        """초기화

        Args:
            db_url: PostgreSQL 연결 URL
            neo4j_url: Neo4j bolt URL (예: bolt://localhost:7687)
            neo4j_user: Neo4j 사용자명
            neo4j_password: Neo4j 비밀번호
        """
        if not NEO4J_AVAILABLE:
            raise ImportError("neo4j 패키지가 필요합니다. pip install neo4j==5.18.0")

        self.db_url = db_url
        self.neo4j_url = neo4j_url
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password

        # Neo4j 드라이버 연결
        self.driver = GraphDatabase.driver(
            neo4j_url,
            auth=(neo4j_user, neo4j_password)
        )
        # 연결 확인
        self.driver.verify_connectivity()
        logger.info(f"Neo4j 연결 성공: {neo4j_url}")

        # 통계
        self._stats = {
            'organizations_synced': 0,
            'tags_synced': 0,
            'regions_synced': 0,
            'bids_synced': 0,
            'issued_by_created': 0,
            'tagged_with_created': 0,
            'in_region_created': 0,
            'similar_to_created': 0,
        }

    def sync_all(self) -> dict:
        """전체 동기화: 노드 먼저, 관계 그 다음

        Returns:
            동기화 통계 딕셔너리
        """
        start_time = datetime.now()
        logger.info("Neo4j 전체 동기화 시작")

        sync_log_id = self._log_sync_start('full')

        try:
            # 1. 제약조건/인덱스 생성
            self._create_constraints()

            # 2. 노드 동기화
            self._sync_organizations()
            self._sync_tags()
            self._sync_regions()
            self._sync_bids()

            # 3. 관계 생성
            self._create_relationships()

            # 4. 유사도 엣지 생성
            self._create_similarity_edges()

            elapsed = (datetime.now() - start_time).total_seconds()
            self._stats['elapsed_seconds'] = round(elapsed, 1)
            self._stats['sync_type'] = 'full'

            logger.info(f"Neo4j 전체 동기화 완료: {elapsed:.1f}초")
            logger.info(f"  동기화 통계: {json.dumps(self._stats, ensure_ascii=False)}")

            self._log_sync_complete(sync_log_id, self._stats)
            return self._stats

        except Exception as e:
            logger.error(f"Neo4j 전체 동기화 실패: {e}")
            self._log_sync_failed(sync_log_id, str(e))
            raise

    def sync_incremental(self, since_hours: int = 24) -> dict:
        """증분 동기화: 최근 추가/수정된 공고만 동기화

        Args:
            since_hours: 몇 시간 전부터의 데이터를 처리할지

        Returns:
            동기화 통계 딕셔너리
        """
        start_time = datetime.now()
        since_dt = datetime.now() - timedelta(hours=since_hours)
        logger.info(f"Neo4j 증분 동기화 시작 (최근 {since_hours}시간)")

        sync_log_id = self._log_sync_start('incremental')

        try:
            # 제약조건 확인
            self._create_constraints()

            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()

            # 최근 변경된 공고 조회
            cursor.execute("""
                SELECT bid_notice_no, title, estimated_price, category, status,
                       announcement_date, bid_end_date,
                       organization_name, organization_code
                FROM bid_announcements
                WHERE created_at >= %s OR updated_at >= %s
                ORDER BY created_at DESC
            """, (since_dt, since_dt))

            bids = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            if not bids:
                logger.info("증분 동기화: 새로운 공고 없음")
                conn.close()
                self._log_sync_complete(sync_log_id, self._stats)
                return self._stats

            bid_rows = [dict(zip(columns, row)) for row in bids]
            bid_nos = [r['bid_notice_no'] for r in bid_rows]

            logger.info(f"증분 동기화 대상: {len(bid_rows)}건")

            # 해당 공고의 태그 조회
            cursor.execute("""
                SELECT btr.bid_notice_no, bt.tag_name
                FROM bid_tag_relations btr
                JOIN bid_tags bt ON btr.tag_id = bt.tag_id
                WHERE btr.bid_notice_no = ANY(%s)
            """, (bid_nos,))
            tag_relations = cursor.fetchall()

            conn.close()

            # 노드 동기화 (해당 공고 관련 데이터만)
            orgs = {}
            regions = {}
            tags = set()

            for row in bid_rows:
                org_name = row.get('organization_name')
                org_code = row.get('organization_code')
                if org_name:
                    orgs[org_name] = org_code

                region = extract_region(org_name)
                if region:
                    regions[region] = True

            for _, tag_name in tag_relations:
                tags.add(tag_name)

            # Neo4j에 노드 MERGE
            self._merge_organizations(list(orgs.items()))
            self._merge_tags(list(tags))
            self._merge_regions(list(regions.keys()))
            self._merge_bids(bid_rows)

            # 관계 생성 (해당 공고만)
            self._create_relationships_for_bids(bid_rows, tag_relations)

            # 유사도 엣지 (해당 공고만)
            self._create_similarity_edges_for_bids(bid_nos)

            elapsed = (datetime.now() - start_time).total_seconds()
            self._stats['elapsed_seconds'] = round(elapsed, 1)
            self._stats['sync_type'] = 'incremental'

            logger.info(f"Neo4j 증분 동기화 완료: {elapsed:.1f}초")
            self._log_sync_complete(sync_log_id, self._stats)
            return self._stats

        except Exception as e:
            logger.error(f"Neo4j 증분 동기화 실패: {e}")
            self._log_sync_failed(sync_log_id, str(e))
            raise

    def _create_constraints(self):
        """Neo4j 유니크 제약조건 및 인덱스 생성"""
        constraints = [
            ("CREATE CONSTRAINT bid_unique IF NOT EXISTS "
             "FOR (b:BidAnnouncement) REQUIRE b.bid_notice_no IS UNIQUE"),
            ("CREATE CONSTRAINT org_unique IF NOT EXISTS "
             "FOR (o:Organization) REQUIRE o.name IS UNIQUE"),
            ("CREATE CONSTRAINT tag_unique IF NOT EXISTS "
             "FOR (t:Tag) REQUIRE t.name IS UNIQUE"),
            ("CREATE CONSTRAINT region_unique IF NOT EXISTS "
             "FOR (r:Region) REQUIRE r.name IS UNIQUE"),
        ]

        with self.driver.session() as session:
            for cypher in constraints:
                try:
                    session.run(cypher)
                except Exception as e:
                    # 이미 존재하는 제약조건은 무시
                    if "already exists" not in str(e).lower():
                        logger.warning(f"제약조건 생성 경고: {e}")

        logger.info("Neo4j 제약조건/인덱스 생성 완료")

    # --------------------------------------------------
    # 전체 동기화용 메서드
    # --------------------------------------------------

    def _sync_organizations(self):
        """PostgreSQL에서 조직 데이터를 읽어 Neo4j에 동기화"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT organization_name, organization_code
            FROM bid_announcements
            WHERE organization_name IS NOT NULL
        """)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return

        self._merge_organizations(rows)

    def _merge_organizations(self, rows: list):
        """Organization 노드 MERGE

        Args:
            rows: [(org_name, org_code), ...]
        """
        if not rows:
            return

        batch_data = []
        for item in rows:
            if isinstance(item, tuple):
                name, code = item
            else:
                name = item.get('organization_name') or item[0]
                code = item.get('organization_code') or item[1] if len(item) > 1 else None
            if name:
                batch_data.append({'name': name, 'code': code or ''})

        if not batch_data:
            return

        cypher = """
        UNWIND $batch AS row
        MERGE (o:Organization {name: row.name})
        SET o.code = row.code
        """

        with self.driver.session() as session:
            session.run(cypher, batch=batch_data)

        self._stats['organizations_synced'] = len(batch_data)
        logger.info(f"  Organization 노드: {len(batch_data)}개 동기화")

    def _sync_tags(self):
        """PostgreSQL에서 태그를 읽어 Neo4j에 동기화"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT tag_name FROM bid_tags WHERE tag_name IS NOT NULL")
        rows = cursor.fetchall()
        conn.close()

        tag_names = [r[0] for r in rows]
        self._merge_tags(tag_names)

    def _merge_tags(self, tag_names: list):
        """Tag 노드 MERGE"""
        if not tag_names:
            return

        batch_data = [{'name': n} for n in tag_names if n]

        cypher = """
        UNWIND $batch AS row
        MERGE (t:Tag {name: row.name})
        """

        with self.driver.session() as session:
            session.run(cypher, batch=batch_data)

        self._stats['tags_synced'] = len(batch_data)
        logger.info(f"  Tag 노드: {len(batch_data)}개 동기화")

    def _sync_regions(self):
        """발주기관명에서 지역 추출 후 Neo4j에 동기화"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT organization_name
            FROM bid_announcements
            WHERE organization_name IS NOT NULL
        """)
        rows = cursor.fetchall()
        conn.close()

        regions = set()
        for (org_name,) in rows:
            region = extract_region(org_name)
            if region:
                regions.add(region)

        self._merge_regions(list(regions))

    def _merge_regions(self, region_names: list):
        """Region 노드 MERGE"""
        if not region_names:
            return

        batch_data = [{'name': n} for n in region_names if n]

        cypher = """
        UNWIND $batch AS row
        MERGE (r:Region {name: row.name})
        """

        with self.driver.session() as session:
            session.run(cypher, batch=batch_data)

        self._stats['regions_synced'] = len(batch_data)
        logger.info(f"  Region 노드: {len(batch_data)}개 동기화")

    def _sync_bids(self):
        """PostgreSQL에서 입찰공고를 읽어 Neo4j에 동기화"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT bid_notice_no, title, estimated_price, category, status,
                   announcement_date, bid_end_date,
                   organization_name, organization_code
            FROM bid_announcements
        """)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()

        bid_rows = [dict(zip(columns, row)) for row in rows]
        self._merge_bids(bid_rows)

    def _merge_bids(self, bid_rows: list):
        """BidAnnouncement 노드 MERGE"""
        if not bid_rows:
            return

        batch_data = []
        for row in bid_rows:
            batch_data.append({
                'bid_notice_no': row['bid_notice_no'],
                'title': row.get('title') or '',
                'estimated_price': row.get('estimated_price'),
                'category': row.get('category') or '',
                'status': row.get('status') or '',
                'announcement_date': (
                    row['announcement_date'].isoformat()
                    if row.get('announcement_date') else None
                ),
                'bid_end_date': (
                    row['bid_end_date'].isoformat()
                    if row.get('bid_end_date') else None
                ),
                'organization_name': row.get('organization_name') or '',
            })

        # 배치 처리 (500개씩)
        batch_size = 500
        for i in range(0, len(batch_data), batch_size):
            chunk = batch_data[i:i + batch_size]

            cypher = """
            UNWIND $batch AS row
            MERGE (b:BidAnnouncement {bid_notice_no: row.bid_notice_no})
            SET b.title = row.title,
                b.estimated_price = row.estimated_price,
                b.category = row.category,
                b.status = row.status,
                b.announcement_date = row.announcement_date,
                b.bid_end_date = row.bid_end_date,
                b.organization_name = row.organization_name
            """

            with self.driver.session() as session:
                session.run(cypher, batch=chunk)

        self._stats['bids_synced'] = len(batch_data)
        logger.info(f"  BidAnnouncement 노드: {len(batch_data)}개 동기화")

    # --------------------------------------------------
    # 관계 생성
    # --------------------------------------------------

    def _create_relationships(self):
        """모든 관계 생성 (전체 동기화용)"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()

        # ISSUED_BY 관계
        cursor.execute("""
            SELECT bid_notice_no, organization_name
            FROM bid_announcements
            WHERE organization_name IS NOT NULL
        """)
        issued_by_data = cursor.fetchall()

        if issued_by_data:
            batch = [{'bid_no': r[0], 'org_name': r[1]} for r in issued_by_data]
            self._batch_create_issued_by(batch)

        # TAGGED_WITH 관계
        cursor.execute("""
            SELECT btr.bid_notice_no, bt.tag_name
            FROM bid_tag_relations btr
            JOIN bid_tags bt ON btr.tag_id = bt.tag_id
        """)
        tagged_data = cursor.fetchall()

        if tagged_data:
            batch = [{'bid_no': r[0], 'tag_name': r[1]} for r in tagged_data]
            self._batch_create_tagged_with(batch)

        # IN_REGION 관계
        cursor.execute("""
            SELECT bid_notice_no, organization_name
            FROM bid_announcements
            WHERE organization_name IS NOT NULL
        """)
        region_data = cursor.fetchall()
        conn.close()

        if region_data:
            batch = []
            for bid_no, org_name in region_data:
                region = extract_region(org_name)
                if region:
                    batch.append({'bid_no': bid_no, 'region_name': region})
            if batch:
                self._batch_create_in_region(batch)

    def _create_relationships_for_bids(self, bid_rows: list, tag_relations: list):
        """특정 공고에 대한 관계만 생성 (증분 동기화용)"""

        # ISSUED_BY
        issued_by_batch = []
        for row in bid_rows:
            org_name = row.get('organization_name')
            if org_name:
                issued_by_batch.append({
                    'bid_no': row['bid_notice_no'],
                    'org_name': org_name
                })
        if issued_by_batch:
            self._batch_create_issued_by(issued_by_batch)

        # TAGGED_WITH
        tagged_batch = [
            {'bid_no': bid_no, 'tag_name': tag_name}
            for bid_no, tag_name in tag_relations
        ]
        if tagged_batch:
            self._batch_create_tagged_with(tagged_batch)

        # IN_REGION
        region_batch = []
        for row in bid_rows:
            region = extract_region(row.get('organization_name'))
            if region:
                region_batch.append({
                    'bid_no': row['bid_notice_no'],
                    'region_name': region
                })
        if region_batch:
            self._batch_create_in_region(region_batch)

    def _batch_create_issued_by(self, batch: list):
        """ISSUED_BY 관계 배치 생성"""
        batch_size = 500
        total = 0

        for i in range(0, len(batch), batch_size):
            chunk = batch[i:i + batch_size]
            cypher = """
            UNWIND $batch AS row
            MATCH (b:BidAnnouncement {bid_notice_no: row.bid_no})
            MATCH (o:Organization {name: row.org_name})
            MERGE (b)-[:ISSUED_BY]->(o)
            """
            with self.driver.session() as session:
                session.run(cypher, batch=chunk)
            total += len(chunk)

        self._stats['issued_by_created'] = total
        logger.info(f"  ISSUED_BY 관계: {total}개 생성")

    def _batch_create_tagged_with(self, batch: list):
        """TAGGED_WITH 관계 배치 생성"""
        batch_size = 500
        total = 0

        for i in range(0, len(batch), batch_size):
            chunk = batch[i:i + batch_size]
            cypher = """
            UNWIND $batch AS row
            MATCH (b:BidAnnouncement {bid_notice_no: row.bid_no})
            MATCH (t:Tag {name: row.tag_name})
            MERGE (b)-[:TAGGED_WITH]->(t)
            """
            with self.driver.session() as session:
                session.run(cypher, batch=chunk)
            total += len(chunk)

        self._stats['tagged_with_created'] = total
        logger.info(f"  TAGGED_WITH 관계: {total}개 생성")

    def _batch_create_in_region(self, batch: list):
        """IN_REGION 관계 배치 생성"""
        batch_size = 500
        total = 0

        for i in range(0, len(batch), batch_size):
            chunk = batch[i:i + batch_size]
            cypher = """
            UNWIND $batch AS row
            MATCH (b:BidAnnouncement {bid_notice_no: row.bid_no})
            MATCH (r:Region {name: row.region_name})
            MERGE (b)-[:IN_REGION]->(r)
            """
            with self.driver.session() as session:
                session.run(cypher, batch=chunk)
            total += len(chunk)

        self._stats['in_region_created'] = total
        logger.info(f"  IN_REGION 관계: {total}개 생성")

    # --------------------------------------------------
    # 유사도 엣지
    # --------------------------------------------------

    # SIMILAR_TO 엣지 제한 상수
    SIMILAR_TOP_K = 10        # 공고당 최대 유사 공고 수
    SIMILAR_MIN_TAGS = 3      # 최소 공유 태그 수 (2→3 상향)
    SIMILAR_BATCH_SIZE = 500  # 배치 처리 단위

    def _create_similarity_edges(self):
        """공유 태그 기반 SIMILAR_TO 관계 생성 (Top-K 제한, 배치 처리)

        기존: 공유 태그 2개 이상인 모든 쌍 → O(n²) = 16.4M 엣지
        개선: 공고당 Top-10만 유지, 최소 공유 태그 3개 → ~95K 엣지
        """
        top_k = self.SIMILAR_TOP_K
        min_tags = self.SIMILAR_MIN_TAGS
        batch_size = self.SIMILAR_BATCH_SIZE

        # 기존 SIMILAR_TO 엣지 삭제
        with self.driver.session() as session:
            session.run("MATCH ()-[r:SIMILAR_TO]-() DELETE r")

        # 전체 BidAnnouncement 노드 수 확인
        with self.driver.session() as session:
            result = session.run("MATCH (b:BidAnnouncement) RETURN COUNT(b) AS cnt")
            total_bids = result.single()['cnt']

        if total_bids == 0:
            self._stats['similar_to_created'] = 0
            return

        # 배치별로 Top-K 유사도 엣지 생성
        total_created = 0
        cypher = f"""
        MATCH (b1:BidAnnouncement)
        WITH b1 ORDER BY b1.bid_notice_no SKIP $offset LIMIT $batch_size
        MATCH (b1)-[:TAGGED_WITH]->(t:Tag)<-[:TAGGED_WITH]-(b2:BidAnnouncement)
        WHERE b1.bid_notice_no <> b2.bid_notice_no
        WITH b1, b2, COUNT(t) AS shared_tags
        WHERE shared_tags >= {min_tags}
        ORDER BY b1.bid_notice_no, shared_tags DESC
        WITH b1, COLLECT({{bid: b2, score: shared_tags}})[0..{top_k}] AS neighbors
        UNWIND neighbors AS n
        MERGE (b1)-[s:SIMILAR_TO]-(n.bid)
        SET s.score = toFloat(n.score)
        RETURN COUNT(s) AS total
        """

        num_batches = (total_bids + batch_size - 1) // batch_size
        for i in range(num_batches):
            offset = i * batch_size
            with self.driver.session() as session:
                result = session.run(cypher, offset=offset, batch_size=batch_size)
                record = result.single()
                batch_total = record['total'] if record else 0
                total_created += batch_total

            if (i + 1) % 10 == 0 or i == num_batches - 1:
                logger.info(f"  SIMILAR_TO 배치 {i+1}/{num_batches}: 누적 {total_created}개")

        self._stats['similar_to_created'] = total_created
        logger.info(f"  SIMILAR_TO 관계 총: {total_created}개 (Top-{top_k}, 최소태그 {min_tags})")

    def _create_similarity_edges_for_bids(self, bid_nos: list):
        """특정 공고에 대한 SIMILAR_TO 관계 생성 (증분, Top-K 제한)"""
        if not bid_nos:
            return

        top_k = self.SIMILAR_TOP_K
        min_tags = self.SIMILAR_MIN_TAGS

        # 대상 공고의 기존 SIMILAR_TO 엣지 삭제 후 재생성
        with self.driver.session() as session:
            session.run("""
                UNWIND $bid_nos AS bid_no
                MATCH (b:BidAnnouncement {bid_notice_no: bid_no})-[r:SIMILAR_TO]-()
                DELETE r
            """, bid_nos=bid_nos)

        cypher = f"""
        UNWIND $bid_nos AS bid_no
        MATCH (b1:BidAnnouncement {{bid_notice_no: bid_no}})-[:TAGGED_WITH]->(t:Tag)<-[:TAGGED_WITH]-(b2:BidAnnouncement)
        WHERE b1.bid_notice_no <> b2.bid_notice_no
        WITH b1, b2, COUNT(t) AS shared_tags
        WHERE shared_tags >= {min_tags}
        ORDER BY b1.bid_notice_no, shared_tags DESC
        WITH b1, COLLECT({{bid: b2, score: shared_tags}})[0..{top_k}] AS neighbors
        UNWIND neighbors AS n
        MERGE (b1)-[s:SIMILAR_TO]-(n.bid)
        SET s.score = toFloat(n.score)
        RETURN COUNT(s) AS total
        """

        with self.driver.session() as session:
            result = session.run(cypher, bid_nos=bid_nos)
            record = result.single()
            total = record['total'] if record else 0

        self._stats['similar_to_created'] = total
        logger.info(f"  SIMILAR_TO 관계 (증분): {total}개 (Top-{top_k}, 최소태그 {min_tags})")

    # --------------------------------------------------
    # 통계 및 유틸리티
    # --------------------------------------------------

    def get_stats(self) -> dict:
        """Neo4j 노드/관계 카운트 반환"""
        stats = {}

        queries = {
            'bid_announcements': "MATCH (n:BidAnnouncement) RETURN COUNT(n) AS cnt",
            'organizations': "MATCH (n:Organization) RETURN COUNT(n) AS cnt",
            'tags': "MATCH (n:Tag) RETURN COUNT(n) AS cnt",
            'regions': "MATCH (n:Region) RETURN COUNT(n) AS cnt",
            'issued_by': "MATCH ()-[r:ISSUED_BY]->() RETURN COUNT(r) AS cnt",
            'tagged_with': "MATCH ()-[r:TAGGED_WITH]->() RETURN COUNT(r) AS cnt",
            'in_region': "MATCH ()-[r:IN_REGION]->() RETURN COUNT(r) AS cnt",
            'similar_to': "MATCH ()-[r:SIMILAR_TO]-() RETURN COUNT(r) AS cnt",
        }

        with self.driver.session() as session:
            for key, cypher in queries.items():
                result = session.run(cypher)
                record = result.single()
                stats[key] = record['cnt'] if record else 0

        return stats

    def close(self):
        """Neo4j 드라이버 종료"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j 드라이버 연결 종료")

    # --------------------------------------------------
    # 동기화 로그 (PostgreSQL)
    # --------------------------------------------------

    def _log_sync_start(self, sync_type: str) -> Optional[int]:
        """동기화 시작 로그를 PostgreSQL에 기록"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO neo4j_sync_log (sync_type, status)
                VALUES (%s, 'running')
                RETURNING id
            """, (sync_type,))
            log_id = cursor.fetchone()[0]
            conn.commit()
            conn.close()
            return log_id
        except Exception as e:
            logger.warning(f"동기화 로그 기록 실패 (시작): {e}")
            return None

    def _log_sync_complete(self, log_id: Optional[int], stats: dict):
        """동기화 완료 로그"""
        if not log_id:
            return
        try:
            total_nodes = (
                stats.get('organizations_synced', 0) +
                stats.get('tags_synced', 0) +
                stats.get('regions_synced', 0) +
                stats.get('bids_synced', 0)
            )
            total_rels = (
                stats.get('issued_by_created', 0) +
                stats.get('tagged_with_created', 0) +
                stats.get('in_region_created', 0) +
                stats.get('similar_to_created', 0)
            )

            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE neo4j_sync_log SET
                    completed_at = NOW(),
                    status = 'completed',
                    nodes_synced = %s,
                    relationships_synced = %s,
                    details = %s
                WHERE id = %s
            """, (total_nodes, total_rels, json.dumps(stats, ensure_ascii=False), log_id))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"동기화 로그 기록 실패 (완료): {e}")

    def _log_sync_failed(self, log_id: Optional[int], error_msg: str):
        """동기화 실패 로그"""
        if not log_id:
            return
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE neo4j_sync_log SET
                    completed_at = NOW(),
                    status = 'failed',
                    error_message = %s
                WHERE id = %s
            """, (error_msg[:2000], log_id))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"동기화 로그 기록 실패 (에러): {e}")


if __name__ == "__main__":
    """독립 실행 테스트"""
    import argparse

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    parser = argparse.ArgumentParser(description='Neo4j 그래프 동기화')
    parser.add_argument('--mode', choices=['full', 'incremental', 'stats'],
                        default='full', help='동기화 모드')
    parser.add_argument('--since-hours', type=int, default=24,
                        help='증분 동기화 시간 범위 (시간)')
    args = parser.parse_args()

    db_url = os.getenv('DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db')
    neo4j_url = os.getenv('NEO4J_URL', 'bolt://localhost:7687')
    neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD', '')

    syncer = Neo4jSyncer(db_url, neo4j_url, neo4j_user, neo4j_password)

    try:
        if args.mode == 'full':
            result = syncer.sync_all()
            print(f"\n전체 동기화 완료: {json.dumps(result, indent=2, ensure_ascii=False)}")
        elif args.mode == 'incremental':
            result = syncer.sync_incremental(since_hours=args.since_hours)
            print(f"\n증분 동기화 완료: {json.dumps(result, indent=2, ensure_ascii=False)}")
        elif args.mode == 'stats':
            stats = syncer.get_stats()
            print(f"\nNeo4j 통계: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    finally:
        syncer.close()
