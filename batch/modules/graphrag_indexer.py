#!/usr/bin/env python
"""
GraphRAG Indexer Module
LazyGraphRAG 접근법: 엔티티 추출 + 커뮤니티 감지 + 요약 생성

- 엔티티 추출: Ollama EXAONE 3.5 (로컬 LLM, $0)
- 커뮤니티 감지: Louvain 알고리즘 (NetworkX)
- 임베딩: KURE-v1 (로컬, 1024 dim)
"""

import os
import re
import json
import hashlib
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

try:
    import community as community_louvain
    LOUVAIN_AVAILABLE = True
except ImportError:
    LOUVAIN_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False


ENTITY_TYPES = [
    "Organization",   # 발주기관, 수요기관
    "Project",         # 프로젝트/공사 유형
    "Technology",      # 기술/공법
    "Region",          # 지역
    "Regulation",      # 법규/기준
    "Material",        # 자재/장비
]

ENTITY_EXTRACT_PROMPT = """당신은 한국 공공입찰 전문가입니다.
아래 입찰공고 정보에서 핵심 엔티티를 추출하세요.

입찰공고:
제목: {title}
기관: {org}
카테고리: {category}
예정가격: {price}

엔티티 타입: Organization, Project, Technology, Region, Regulation, Material

JSON 배열로만 답변하세요. 다른 텍스트는 포함하지 마세요.
[{{"type": "엔티티타입", "name": "엔티티명", "desc": "한줄설명"}}]

답변:"""

COMMUNITY_SUMMARY_PROMPT = """다음은 공공입찰 데이터에서 발견된 엔티티 그룹입니다.
이 그룹의 특성을 한국어로 2-3문장으로 요약하세요.

엔티티 목록:
{entities}

관련 입찰 수: {bid_count}건
주요 카테고리: {categories}

요약:"""


class GraphRAGIndexer:
    """LazyGraphRAG 인덱서"""

    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv(
            'DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db'
        )
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'exaone3.5:7.8b')

        # 임베딩 모델 (lazy load)
        self._embed_model = None

        # 통계
        self._stats = {
            'entities_extracted': 0,
            'communities_detected': 0,
            'embeddings_generated': 0,
        }

    def _get_embed_model(self):
        """KURE-v1 임베딩 모델 (lazy load)"""
        if self._embed_model is None and EMBEDDING_AVAILABLE:
            self._embed_model = SentenceTransformer('nlpai-lab/KURE-v1')
            logger.info("KURE-v1 임베딩 모델 로드 완료")
        return self._embed_model

    def _call_ollama(self, prompt: str, max_tokens: int = 500) -> str:
        """Ollama API 호출"""
        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx 패키지 필요")

        response = httpx.post(
            f"{self.ollama_url}/api/generate",
            json={
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": max_tokens}
            },
            timeout=60.0
        )
        response.raise_for_status()
        return response.json().get("response", "")

    def _make_entity_id(self, entity_type: str, entity_name: str) -> str:
        """엔티티 고유 ID 생성"""
        raw = f"{entity_type}:{entity_name}".lower().strip()
        return hashlib.md5(raw.encode()).hexdigest()[:16]

    # --------------------------------------------------
    # 엔티티 추출
    # --------------------------------------------------

    def extract_entities_from_bids(self, limit: int = None, since_hours: int = None) -> List[dict]:
        """입찰공고에서 엔티티 추출

        Args:
            limit: 처리할 최대 공고 수
            since_hours: 최근 N시간 내 공고만 처리
        """
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()

        # 이미 처리된 공고 제외
        query = """
            SELECT ba.bid_notice_no, ba.title, ba.organization_name,
                   ba.category, ba.estimated_price
            FROM bid_announcements ba
            WHERE ba.bid_notice_no NOT IN (
                SELECT DISTINCT source_bid_notice_no
                FROM graphrag_entities
                WHERE source_bid_notice_no IS NOT NULL
            )
        """
        params = []

        if since_hours:
            query += " AND ba.created_at >= %s"
            params.append(datetime.now() - timedelta(hours=since_hours))

        query += " ORDER BY ba.created_at DESC"

        if limit:
            query += " LIMIT %s"
            params.append(limit)

        cursor.execute(query, params)
        bids = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()

        if not bids:
            logger.info("엔티티 추출 대상 공고 없음")
            return []

        total = len(bids)
        logger.info(f"엔티티 추출 대상: {total}건")
        all_entities = []

        for i, row in enumerate(bids, 1):
            bid = dict(zip(columns, row))
            entities = self._extract_entities_for_bid(bid)
            all_entities.extend(entities)
            if i % 10 == 0 or i == total:
                logger.info(f"엔티티 추출 진행: {i}/{total} ({i/total*100:.1f}%) - 누적 엔티티: {len(all_entities)}개")

        # DB에 저장
        if all_entities:
            self._save_entities(all_entities)

        self._stats['entities_extracted'] = len(all_entities)
        logger.info(f"엔티티 추출 완료: {len(all_entities)}개")
        return all_entities

    def _extract_entities_for_bid(self, bid: dict) -> List[dict]:
        """단일 공고에서 엔티티 추출"""
        title = bid.get('title', '')
        org = bid.get('organization_name', '')
        category = bid.get('category', '')
        price = bid.get('estimated_price')
        bid_no = bid.get('bid_notice_no')

        # 규칙 기반 기본 엔티티 (LLM 없이도 동작)
        entities = []

        # 1. 기관 엔티티
        if org:
            entities.append({
                'entity_type': 'Organization',
                'entity_name': org,
                'description': f'발주기관: {org}',
                'source_bid_notice_no': bid_no,
            })

        # 2. 지역 엔티티 (기관명에서 추출)
        region = self._extract_region(org)
        if region:
            entities.append({
                'entity_type': 'Region',
                'entity_name': region,
                'description': f'지역: {region}',
                'source_bid_notice_no': bid_no,
            })

        # 3. LLM 기반 엔티티 추출 시도
        if HTTPX_AVAILABLE:
            try:
                price_str = f"{price:,.0f}원" if price else "미정"
                prompt = ENTITY_EXTRACT_PROMPT.format(
                    title=title, org=org, category=category, price=price_str
                )
                response = self._call_ollama(prompt, max_tokens=500)
                llm_entities = self._parse_entity_response(response, bid_no)
                entities.extend(llm_entities)
            except Exception as e:
                logger.debug(f"LLM 엔티티 추출 실패 [{bid_no}]: {e}")

        # 4. 규칙 기반 프로젝트 유형 추출 (폴백)
        project_type = self._extract_project_type(title)
        if project_type:
            entities.append({
                'entity_type': 'Project',
                'entity_name': project_type,
                'description': f'프로젝트 유형: {project_type}',
                'source_bid_notice_no': bid_no,
            })

        return entities

    def _parse_entity_response(self, response: str, bid_no: str) -> List[dict]:
        """LLM 응답에서 엔티티 JSON 파싱"""
        entities = []
        try:
            # JSON 배열 추출
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if not match:
                return []

            parsed = json.loads(match.group())
            if not isinstance(parsed, list):
                return []

            for item in parsed:
                etype = item.get('type', '')
                ename = item.get('name', '')
                edesc = item.get('desc', '')

                if not ename or len(ename) < 2:
                    continue
                if etype not in ENTITY_TYPES:
                    continue

                entities.append({
                    'entity_type': etype,
                    'entity_name': ename,
                    'description': edesc,
                    'source_bid_notice_no': bid_no,
                })
        except (json.JSONDecodeError, KeyError):
            pass

        return entities

    def _extract_region(self, org_name: str) -> Optional[str]:
        """기관명에서 지역 추출"""
        if not org_name:
            return None
        patterns = [
            (r'서울', '서울특별시'), (r'부산', '부산광역시'),
            (r'대구', '대구광역시'), (r'인천', '인천광역시'),
            (r'광주광역', '광주광역시'), (r'대전', '대전광역시'),
            (r'울산', '울산광역시'), (r'세종', '세종특별자치시'),
            (r'경기', '경기도'), (r'강원', '강원특별자치도'),
            (r'충북', '충청북도'), (r'충남|충청남', '충청남도'),
            (r'전북', '전라북도'), (r'전남|전라남', '전라남도'),
            (r'경북|경상북', '경상북도'), (r'경남|경상남', '경상남도'),
            (r'제주', '제주특별자치도'),
        ]
        for pat, region in patterns:
            if re.search(pat, org_name):
                return region
        return None

    def _extract_project_type(self, title: str) -> Optional[str]:
        """제목에서 프로젝트 유형 추출 (규칙 기반)"""
        type_patterns = [
            (r'도로|포장|아스콘', '도로공사'),
            (r'상수|하수|배수|관로', '상하수도공사'),
            (r'건축|신축|증축|리모델링', '건축공사'),
            (r'교량|터널|고가', '교량공사'),
            (r'조경|녹지|공원', '조경공사'),
            (r'전기|배전|수전', '전기공사'),
            (r'통신|네트워크|CCTV', '통신공사'),
            (r'소하천|하천|제방', '하천공사'),
            (r'유지보수|보수|정비', '유지보수'),
            (r'철거|해체', '철거공사'),
            (r'시스템|소프트웨어|개발', 'IT개발'),
        ]
        for pat, ptype in type_patterns:
            if re.search(pat, title):
                return ptype
        return None

    def _save_entities(self, entities: List[dict]):
        """엔티티를 DB에 저장 (UPSERT)"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()

        saved = 0
        for ent in entities:
            entity_id = self._make_entity_id(ent['entity_type'], ent['entity_name'])
            try:
                cursor.execute("""
                    INSERT INTO graphrag_entities
                        (entity_id, entity_type, entity_name, description, source_bid_notice_no)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (entity_id) DO UPDATE SET
                        updated_at = NOW()
                """, (
                    entity_id,
                    ent['entity_type'],
                    ent['entity_name'],
                    ent.get('description', ''),
                    ent.get('source_bid_notice_no'),
                ))
                saved += 1
            except Exception as e:
                logger.debug(f"엔티티 저장 실패: {e}")

        conn.commit()
        conn.close()
        logger.info(f"엔티티 DB 저장: {saved}건")

    # --------------------------------------------------
    # 커뮤니티 감지
    # --------------------------------------------------

    def detect_communities(self) -> dict:
        """엔티티 공동 출현 그래프 → Louvain 커뮤니티 감지"""
        if not NETWORKX_AVAILABLE or not LOUVAIN_AVAILABLE:
            logger.warning("networkx 또는 python-louvain 미설치 - 커뮤니티 감지 건너뜀")
            return {}

        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()

        # 같은 공고에 나타난 엔티티 쌍 조회
        cursor.execute("""
            SELECT e1.entity_id, e1.entity_name, e1.entity_type,
                   e2.entity_id, e2.entity_name, e2.entity_type
            FROM graphrag_entities e1
            JOIN graphrag_entities e2
                ON e1.source_bid_notice_no = e2.source_bid_notice_no
                AND e1.entity_id < e2.entity_id
        """)
        pairs = cursor.fetchall()
        conn.close()

        if not pairs:
            logger.info("커뮤니티 감지: 엔티티 쌍 없음")
            return {}

        # NetworkX 그래프 구축
        G = nx.Graph()
        for e1_id, e1_name, e1_type, e2_id, e2_name, e2_type in pairs:
            G.add_node(e1_id, name=e1_name, type=e1_type)
            G.add_node(e2_id, name=e2_name, type=e2_type)
            if G.has_edge(e1_id, e2_id):
                G[e1_id][e2_id]['weight'] += 1
            else:
                G.add_edge(e1_id, e2_id, weight=1)

        logger.info(f"공동출현 그래프: {G.number_of_nodes()} 노드, {G.number_of_edges()} 엣지")

        # Louvain 커뮤니티 감지
        partition = community_louvain.best_partition(G, resolution=1.0)
        num_communities = max(partition.values()) + 1 if partition else 0

        logger.info(f"Louvain 커뮤니티: {num_communities}개 감지")

        # 커뮤니티별 엔티티 그룹화
        communities = {}
        for node_id, comm_id in partition.items():
            if comm_id not in communities:
                communities[comm_id] = []
            node_data = G.nodes[node_id]
            communities[comm_id].append({
                'entity_id': node_id,
                'entity_name': node_data.get('name', ''),
                'entity_type': node_data.get('type', ''),
            })

        # DB에 커뮤니티 ID 업데이트
        self._update_community_ids(partition)

        # 커뮤니티 요약 생성 및 저장
        self._save_communities(communities)

        self._stats['communities_detected'] = num_communities
        return {'num_communities': num_communities, 'graph_nodes': G.number_of_nodes()}

    def _update_community_ids(self, partition: dict):
        """엔티티 테이블에 커뮤니티 ID 업데이트"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()

        for entity_id, comm_id in partition.items():
            cursor.execute("""
                UPDATE graphrag_entities SET community_id = %s, updated_at = NOW()
                WHERE entity_id = %s
            """, (comm_id, entity_id))

        conn.commit()
        conn.close()
        logger.info(f"커뮤니티 ID 업데이트: {len(partition)}건")

    def _save_communities(self, communities: dict):
        """커뮤니티 정보 DB 저장"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()

        total_comms = len(communities)
        for ci, (comm_id, members) in enumerate(communities.items(), 1):
            entity_count = len(members)
            # 관련 공고 수 조회
            entity_ids = [m['entity_id'] for m in members]
            cursor.execute("""
                SELECT COUNT(DISTINCT source_bid_notice_no)
                FROM graphrag_entities
                WHERE entity_id = ANY(%s) AND source_bid_notice_no IS NOT NULL
            """, (entity_ids,))
            bid_count = cursor.fetchone()[0] or 0

            # 상위 5개 엔티티로 제목 생성
            top_names = [m['entity_name'] for m in members[:5]]
            title = ", ".join(top_names)
            if len(members) > 5:
                title += f" 외 {len(members)-5}개"

            # LLM 요약 생성 시도
            summary = self._generate_community_summary(members, bid_count)

            findings = [
                {'entity': m['entity_name'], 'type': m['entity_type']}
                for m in members[:10]
            ]

            cursor.execute("""
                INSERT INTO graphrag_communities
                    (community_id, title, summary, findings, entity_count, bid_count)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (community_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    summary = EXCLUDED.summary,
                    findings = EXCLUDED.findings,
                    entity_count = EXCLUDED.entity_count,
                    bid_count = EXCLUDED.bid_count,
                    updated_at = NOW()
            """, (
                comm_id, title, summary,
                json.dumps(findings, ensure_ascii=False),
                entity_count, bid_count
            ))
            if ci % 10 == 0 or ci == total_comms:
                logger.info(f"커뮤니티 저장 진행: {ci}/{total_comms} ({ci/total_comms*100:.1f}%)")

        conn.commit()
        conn.close()
        logger.info(f"커뮤니티 저장: {len(communities)}건")

    def _generate_community_summary(self, members: list, bid_count: int) -> str:
        """커뮤니티 요약 생성 (Ollama)"""
        if not HTTPX_AVAILABLE:
            return self._generate_rule_summary(members, bid_count)

        try:
            entity_list = "\n".join([
                f"- [{m['entity_type']}] {m['entity_name']}"
                for m in members[:10]
            ])
            categories = set(m['entity_type'] for m in members)

            prompt = COMMUNITY_SUMMARY_PROMPT.format(
                entities=entity_list,
                bid_count=bid_count,
                categories=", ".join(categories)
            )
            return self._call_ollama(prompt, max_tokens=200)
        except Exception as e:
            logger.debug(f"커뮤니티 요약 생성 실패: {e}")
            return self._generate_rule_summary(members, bid_count)

    def _generate_rule_summary(self, members: list, bid_count: int) -> str:
        """규칙 기반 커뮤니티 요약 (LLM 폴백)"""
        types = {}
        for m in members:
            t = m['entity_type']
            types[t] = types.get(t, 0) + 1

        parts = [f"{t} {c}개" for t, c in sorted(types.items(), key=lambda x: -x[1])]
        return f"이 그룹은 {', '.join(parts)}로 구성되며, {bid_count}건의 입찰공고와 관련됩니다."

    # --------------------------------------------------
    # 엔티티 임베딩
    # --------------------------------------------------

    def generate_embeddings(self, batch_size: int = 32) -> int:
        """임베딩이 없는 엔티티에 KURE-v1 임베딩 생성"""
        model = self._get_embed_model()
        if model is None:
            logger.warning("임베딩 모델 로드 실패 - 건너뜀")
            return 0

        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT entity_id, entity_name, entity_type, description
            FROM graphrag_entities
            WHERE embedding IS NULL
        """)
        rows = cursor.fetchall()

        if not rows:
            logger.info("임베딩 생성 대상 없음")
            conn.close()
            return 0

        logger.info(f"엔티티 임베딩 생성: {len(rows)}건")

        count = 0
        total_batches = (len(rows) + batch_size - 1) // batch_size
        for bi, i in enumerate(range(0, len(rows), batch_size), 1):
            batch = rows[i:i + batch_size]
            texts = [
                f"{r[2]}: {r[1]}. {r[3] or ''}" for r in batch
            ]

            embeddings = model.encode(texts, normalize_embeddings=True)

            for j, row in enumerate(batch):
                entity_id = row[0]
                emb = embeddings[j].tolist()
                cursor.execute("""
                    UPDATE graphrag_entities SET embedding = %s, updated_at = NOW()
                    WHERE entity_id = %s
                """, (str(emb), entity_id))
                count += 1

            if bi % 5 == 0 or bi == total_batches:
                logger.info(f"엔티티 임베딩 진행: {count}/{len(rows)} ({count/len(rows)*100:.1f}%)")

        conn.commit()
        conn.close()
        self._stats['embeddings_generated'] = count
        logger.info(f"엔티티 임베딩 완료: {count}건")
        return count

    # --------------------------------------------------
    # 전체/증분 실행
    # --------------------------------------------------

    def run_full(self, limit: int = None) -> dict:
        """전체 인덱싱: 추출 → 커뮤니티 → 임베딩"""
        logger.info("GraphRAG 전체 인덱싱 시작")
        start = datetime.now()

        entities = self.extract_entities_from_bids(limit=limit)
        comm_result = self.detect_communities()
        embed_count = self.generate_embeddings()

        elapsed = (datetime.now() - start).total_seconds()
        self._stats['elapsed_seconds'] = round(elapsed, 1)
        logger.info(f"GraphRAG 전체 인덱싱 완료: {elapsed:.1f}초")
        return self._stats

    def run_incremental(self, since_hours: int = 24, limit: int = None) -> dict:
        """증분 인덱싱: 최근 공고만 추출 → 커뮤니티 재계산"""
        logger.info(f"GraphRAG 증분 인덱싱 시작 (최근 {since_hours}시간)")
        start = datetime.now()

        entities = self.extract_entities_from_bids(
            limit=limit, since_hours=since_hours
        )

        if entities:
            self.detect_communities()
            self.generate_embeddings()

        elapsed = (datetime.now() - start).total_seconds()
        self._stats['elapsed_seconds'] = round(elapsed, 1)
        logger.info(f"GraphRAG 증분 인덱싱 완료: {elapsed:.1f}초")
        return self._stats

    def get_stats(self) -> dict:
        """GraphRAG 현황 통계"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM graphrag_entities")
        total_entities = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM graphrag_entities WHERE embedding IS NOT NULL")
        embedded = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM graphrag_communities")
        total_communities = cursor.fetchone()[0]

        cursor.execute("""
            SELECT entity_type, COUNT(*) FROM graphrag_entities
            GROUP BY entity_type ORDER BY COUNT(*) DESC
        """)
        type_dist = {r[0]: r[1] for r in cursor.fetchall()}

        conn.close()

        return {
            'total_entities': total_entities,
            'embedded_entities': embedded,
            'total_communities': total_communities,
            'entity_type_distribution': type_dist,
        }


if __name__ == "__main__":
    import argparse

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    parser = argparse.ArgumentParser(description='GraphRAG 인덱서')
    parser.add_argument('--mode', choices=['full', 'incremental', 'stats'],
                        default='full', help='실행 모드')
    parser.add_argument('--limit', type=int, default=None,
                        help='처리할 최대 공고 수')
    parser.add_argument('--since-hours', type=int, default=24,
                        help='증분 인덱싱 시간 범위 (시간)')
    args = parser.parse_args()

    indexer = GraphRAGIndexer()

    if args.mode == 'full':
        result = indexer.run_full(limit=args.limit)
        print(f"\n전체 인덱싱 완료: {json.dumps(result, indent=2, ensure_ascii=False)}")
    elif args.mode == 'incremental':
        result = indexer.run_incremental(
            since_hours=args.since_hours, limit=args.limit
        )
        print(f"\n증분 인덱싱 완료: {json.dumps(result, indent=2, ensure_ascii=False)}")
    elif args.mode == 'stats':
        stats = indexer.get_stats()
        print(f"\nGraphRAG 통계: {json.dumps(stats, indent=2, ensure_ascii=False)}")
