"""
온톨로지 서비스 모듈
공공입찰 도메인 지식 기반 개념 확장, 분류, 관계 탐색

Tables:
    - ontology_concepts: 개념 계층 (id, concept_name, parent_id, level, keywords[], synonyms[])
    - ontology_relations: 개념 간 관계 (source_concept_id, target_concept_id, relation_type, weight)
    - bid_ontology_mappings: 입찰-개념 매핑 (bid_notice_no, concept_id, confidence, source)

DB Functions:
    - fn_get_descendant_concepts(root_id) -> (concept_id, concept_name, level, path)
    - fn_get_expanded_keywords(root_id) -> TEXT[]
"""

import logging
import time
import threading
from typing import List, Dict, Optional, Set, Tuple

from psycopg2.extras import RealDictCursor

from database import get_db_connection

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# In-memory cache with TTL
# ---------------------------------------------------------------------------

class _TTLCache:
    """Thread-safe in-memory cache with per-key TTL."""

    def __init__(self, default_ttl: float = 300.0):
        self._store: Dict[str, Tuple[float, object]] = {}
        self._lock = threading.Lock()
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[object]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if time.time() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: object, ttl: float = None) -> None:
        with self._lock:
            self._store[key] = (time.time() + (ttl or self._default_ttl), value)

    def invalidate(self, key: str = None) -> None:
        with self._lock:
            if key is None:
                self._store.clear()
            else:
                self._store.pop(key, None)


# Module-level caches (5 min default TTL)
_concept_cache = _TTLCache(default_ttl=300.0)
# Longer TTL for tree/stats that rarely change
_tree_cache = _TTLCache(default_ttl=600.0)


def invalidate_ontology_cache() -> None:
    """Clear all ontology caches. Call after concept/relation mutations."""
    _concept_cache.invalidate()
    _tree_cache.invalidate()
    logger.info("Ontology caches invalidated")


# ---------------------------------------------------------------------------
# Core query helpers
# ---------------------------------------------------------------------------

def get_concept_by_name(concept_name: str) -> Optional[Dict]:
    """개념명으로 온톨로지 개념 조회.

    Returns:
        dict with keys: id, concept_name, concept_name_en, parent_id, level,
        description, keywords, synonyms, is_active, display_order
        or None if not found.
    """
    cache_key = f"concept_name:{concept_name}"
    cached = _concept_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT id, concept_name, concept_name_en, parent_id, level,
                       description, keywords, synonyms, is_active, display_order
                FROM ontology_concepts
                WHERE concept_name = %s AND is_active = true
                """,
                (concept_name,),
            )
            row = cursor.fetchone()
            if row is None:
                return None

            result = {
                "id": row["id"],
                "concept_name": row["concept_name"],
                "concept_name_en": row["concept_name_en"],
                "parent_id": row["parent_id"],
                "level": row["level"],
                "description": row["description"],
                "keywords": row["keywords"] or [],
                "synonyms": row["synonyms"] or [],
                "is_active": row["is_active"],
                "display_order": row["display_order"],
            }
            _concept_cache.set(cache_key, result)
            return result

    except Exception as e:
        logger.error(f"get_concept_by_name('{concept_name}') failed: {e}")
        return None


def _get_concept_by_id(concept_id: int) -> Optional[Dict]:
    """Internal helper: fetch concept by ID (cached)."""
    cache_key = f"concept_id:{concept_id}"
    cached = _concept_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT id, concept_name, concept_name_en, parent_id, level,
                       description, keywords, synonyms, is_active, display_order
                FROM ontology_concepts
                WHERE id = %s AND is_active = true
                """,
                (concept_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None

            result = {
                "id": row["id"],
                "concept_name": row["concept_name"],
                "concept_name_en": row["concept_name_en"],
                "parent_id": row["parent_id"],
                "level": row["level"],
                "description": row["description"],
                "keywords": row["keywords"] or [],
                "synonyms": row["synonyms"] or [],
                "is_active": row["is_active"],
                "display_order": row["display_order"],
            }
            _concept_cache.set(cache_key, result)
            return result

    except Exception as e:
        logger.error(f"_get_concept_by_id({concept_id}) failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Descendant / keyword expansion
# ---------------------------------------------------------------------------

def get_descendant_concept_ids(concept_id: int) -> List[int]:
    """재귀적으로 모든 하위 개념 ID 반환 (자기 자신 포함).

    Uses the DB function ``fn_get_descendant_concepts`` which performs a
    recursive CTE walk of the ontology tree.

    Example::

        get_descendant_concept_ids(토목공사.id)
        # => [토목공사.id, 도로공사.id, 교량공사.id, 터널공사.id, ...]
    """
    cache_key = f"descendants:{concept_id}"
    cached = _concept_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT concept_id FROM fn_get_descendant_concepts(%s)",
                (concept_id,),
            )
            ids = [row["concept_id"] for row in cursor.fetchall()]
            _concept_cache.set(cache_key, ids)
            return ids

    except Exception as e:
        logger.error(f"get_descendant_concept_ids({concept_id}) failed: {e}")
        return []


def get_expanded_keywords(concept_name: str) -> List[str]:
    """개념명으로부터 확장된 키워드 목록 반환.

    Collects:
    - 해당 개념의 keywords + synonyms
    - 모든 하위 개념의 keywords + synonyms (via ``fn_get_expanded_keywords``)
    - 관련 개념(relatedTo, similarTo)의 keywords (weight >= 0.5)

    Example::

        get_expanded_keywords("도로공사")
        # => ["도로", "포장", "아스팔트", "노면", "교량", "다리", "터널", ...]
    """
    cache_key = f"expanded_kw:{concept_name}"
    cached = _concept_cache.get(cache_key)
    if cached is not None:
        return cached

    concept = get_concept_by_name(concept_name)
    if concept is None:
        return []

    concept_id = concept["id"]
    all_keywords: Set[str] = set()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 1. Use DB function to get self + descendant keywords/synonyms
            cursor.execute(
                "SELECT fn_get_expanded_keywords(%s) AS expanded_keywords",
                (concept_id,),
            )
            row = cursor.fetchone()
            if row and row["expanded_keywords"]:
                all_keywords.update(row["expanded_keywords"])

            # 2. Related concepts (relatedTo, similarTo) with weight >= 0.5
            cursor.execute(
                """
                SELECT oc.keywords, oc.synonyms
                FROM ontology_relations r
                JOIN ontology_concepts oc ON oc.id = r.target_concept_id
                WHERE r.source_concept_id = %s
                  AND r.relation_type IN ('relatedTo', 'similarTo')
                  AND r.weight >= 0.5
                  AND oc.is_active = true
                """,
                (concept_id,),
            )
            for kw_row in cursor.fetchall():
                if kw_row["keywords"]:
                    all_keywords.update(kw_row["keywords"])
                if kw_row["synonyms"]:
                    all_keywords.update(kw_row["synonyms"])

        # Filter out empty strings
        result = sorted(kw for kw in all_keywords if kw)
        _concept_cache.set(cache_key, result)
        return result

    except Exception as e:
        logger.error(f"get_expanded_keywords('{concept_name}') failed: {e}")
        return []


# ---------------------------------------------------------------------------
# Search expansion (CRITICAL - called on every search, must be fast <50ms)
# ---------------------------------------------------------------------------

def _load_keyword_to_concept_map() -> Dict[str, List[int]]:
    """Build a reverse index: keyword -> [concept_id, ...].

    Loaded once and cached for 5 minutes.  This enables O(1) lookup of
    which concept a search query matches, avoiding per-query table scans.
    """
    cache_key = "kw_concept_map"
    cached = _concept_cache.get(cache_key)
    if cached is not None:
        return cached

    mapping: Dict[str, List[int]] = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT id, keywords, synonyms, concept_name
                FROM ontology_concepts
                WHERE is_active = true
                """
            )
            for row in cursor.fetchall():
                cid = row["id"]
                keywords = row["keywords"] or []
                synonyms = row["synonyms"] or []
                concept_name_val = row["concept_name"] or ""

                # Map each keyword/synonym to this concept
                for kw in keywords:
                    kw_lower = kw.lower()
                    if kw_lower:
                        mapping.setdefault(kw_lower, []).append(cid)
                for syn in synonyms:
                    syn_lower = syn.lower()
                    if syn_lower:
                        mapping.setdefault(syn_lower, []).append(cid)
                # Also map the concept name itself
                if concept_name_val:
                    mapping.setdefault(concept_name_val.lower(), []).append(cid)

        _concept_cache.set(cache_key, mapping, ttl=300.0)
        return mapping

    except Exception as e:
        logger.error(f"_load_keyword_to_concept_map failed: {e}")
        return {}


def expand_search_terms(query: str) -> List[str]:
    """검색어를 온톨로지 기반으로 확장.

    Algorithm:
    1. query가 어떤 개념의 keyword/synonym/concept_name에 매칭되는지 찾기
    2. 매칭된 개념의 하위 개념 키워드 수집
    3. 관련 개념 키워드 수집 (weight >= 0.6)
    4. 중복 제거 후 정렬하여 반환

    Performance target: <50ms (uses cached reverse index).

    Example::

        expand_search_terms("도로")
        # => ["도로", "포장", "아스팔트", "노면", "차도", "보도", "교량", "다리", ...]

    Returns:
        Empty list if no ontology match found (caller should fall back to
        the original query for plain keyword search).
    """
    if not query or not query.strip():
        return []

    query_lower = query.strip().lower()

    # Step 1: Find matching concepts via cached reverse index (O(1))
    kw_map = _load_keyword_to_concept_map()

    matched_concept_ids: Set[int] = set()
    # Exact match first
    if query_lower in kw_map:
        matched_concept_ids.update(kw_map[query_lower])

    # If no exact match, try substring match against concept names only
    # (limited to concept_name field for speed)
    if not matched_concept_ids:
        for kw, cids in kw_map.items():
            if query_lower in kw or kw in query_lower:
                matched_concept_ids.update(cids)
                if len(matched_concept_ids) >= 5:
                    break  # Limit to avoid over-expansion

    if not matched_concept_ids:
        return []

    # Step 2 & 3: Collect expanded keywords for each matched concept
    all_terms: Set[str] = set()
    all_terms.add(query)  # Always include the original query

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            for cid in matched_concept_ids:
                # Descendant keywords via DB function (fast, stable)
                cursor.execute(
                    "SELECT fn_get_expanded_keywords(%s) AS expanded_keywords",
                    (cid,),
                )
                row = cursor.fetchone()
                if row and row["expanded_keywords"]:
                    all_terms.update(row["expanded_keywords"])

                # Related concepts with weight >= 0.6
                cursor.execute(
                    """
                    SELECT oc.keywords, oc.synonyms
                    FROM ontology_relations r
                    JOIN ontology_concepts oc ON oc.id = r.target_concept_id
                    WHERE r.source_concept_id = %s
                      AND r.relation_type IN ('relatedTo', 'similarTo')
                      AND r.weight >= 0.6
                      AND oc.is_active = true
                    """,
                    (cid,),
                )
                for rel_row in cursor.fetchall():
                    if rel_row["keywords"]:
                        all_terms.update(rel_row["keywords"])
                    if rel_row["synonyms"]:
                        all_terms.update(rel_row["synonyms"])

    except Exception as e:
        logger.error(f"expand_search_terms('{query}') failed: {e}")
        return []

    # Remove empty strings and return sorted
    return sorted(term for term in all_terms if term)


# ---------------------------------------------------------------------------
# Bid classification
# ---------------------------------------------------------------------------

def _load_classification_concepts() -> List[Dict]:
    """Load all leaf/mid-level concepts (level >= 2) with keywords for classification.

    Cached for 5 minutes.
    """
    cache_key = "classification_concepts"
    cached = _concept_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT id, concept_name, level, keywords, synonyms
                FROM ontology_concepts
                WHERE level >= 2 AND is_active = true
                ORDER BY level DESC, display_order
                """
            )
            concepts = []
            for row in cursor.fetchall():
                concepts.append({
                    "id": row["id"],
                    "concept_name": row["concept_name"],
                    "level": row["level"],
                    "keywords": [kw.lower() for kw in (row["keywords"] or []) if kw],
                    "synonyms": [syn.lower() for syn in (row["synonyms"] or []) if syn],
                })
            _concept_cache.set(cache_key, concepts)
            return concepts

    except Exception as e:
        logger.error(f"_load_classification_concepts failed: {e}")
        return []


def classify_bid(
    title: str,
    organization_name: str = "",
    extracted_text: str = "",
) -> List[Dict]:
    """입찰공고를 온톨로지 개념으로 분류.

    Algorithm:
    1. Get all leaf/mid-level concepts (level >= 2) with their keywords
    2. For each concept, count keyword matches in title + org + text
    3. Calculate confidence = matched_keywords / total_keywords
    4. Boost confidence if title contains concept_name directly (+0.3)
    5. Return top 5 matches with confidence >= 0.3

    Returns:
        List of ``{concept_id, concept_name, confidence, level}``
        sorted by confidence DESC, max 5 results.
    """
    if not title:
        return []

    # Combine all text sources, lowered for case-insensitive matching
    combined = (title + " " + organization_name + " " + extracted_text).lower()
    title_lower = title.lower()

    concepts = _load_classification_concepts()
    if not concepts:
        return []

    scored: List[Dict] = []

    for concept in concepts:
        all_kw = concept["keywords"] + concept["synonyms"]
        if not all_kw:
            continue

        total_keywords = len(all_kw)
        matched_count = sum(1 for kw in all_kw if kw in combined)

        if matched_count == 0:
            continue

        confidence = matched_count / total_keywords

        # Boost if concept_name appears directly in title
        if concept["concept_name"].lower() in title_lower:
            confidence = min(confidence + 0.3, 1.0)

        if confidence >= 0.3:
            scored.append({
                "concept_id": concept["id"],
                "concept_name": concept["concept_name"],
                "confidence": round(confidence, 3),
                "level": concept["level"],
            })

    # Sort by confidence DESC, take top 5
    scored.sort(key=lambda x: x["confidence"], reverse=True)
    return scored[:5]


# ---------------------------------------------------------------------------
# Related concepts
# ---------------------------------------------------------------------------

def get_related_concepts(
    concept_id: int,
    relation_types: List[str] = None,
    min_weight: float = 0.5,
) -> List[Dict]:
    """관련 개념 조회 (ontology_relations 테이블).

    Args:
        concept_id: Source concept ID.
        relation_types: Filter by relation types.
            Possible values: ``['relatedTo', 'requires', 'similarTo', 'excludes']``.
            If None, returns all relation types.
        min_weight: Minimum relation weight (0.0-1.0).

    Returns:
        List of ``{concept_id, concept_name, relation_type, weight}``
        sorted by weight DESC.
    """
    cache_key = f"related:{concept_id}:{relation_types}:{min_weight}"
    cached = _concept_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            if relation_types:
                cursor.execute(
                    """
                    SELECT oc.id, oc.concept_name, r.relation_type, r.weight
                    FROM ontology_relations r
                    JOIN ontology_concepts oc ON oc.id = r.target_concept_id
                    WHERE r.source_concept_id = %s
                      AND r.relation_type = ANY(%s)
                      AND r.weight >= %s
                      AND oc.is_active = true
                    ORDER BY r.weight DESC
                    """,
                    (concept_id, relation_types, min_weight),
                )
            else:
                cursor.execute(
                    """
                    SELECT oc.id, oc.concept_name, r.relation_type, r.weight
                    FROM ontology_relations r
                    JOIN ontology_concepts oc ON oc.id = r.target_concept_id
                    WHERE r.source_concept_id = %s
                      AND r.weight >= %s
                      AND oc.is_active = true
                    ORDER BY r.weight DESC
                    """,
                    (concept_id, min_weight),
                )

            results = []
            for row in cursor.fetchall():
                results.append({
                    "concept_id": row["id"],
                    "concept_name": row["concept_name"],
                    "relation_type": row["relation_type"],
                    "weight": row["weight"],
                })

            _concept_cache.set(cache_key, results)
            return results

    except Exception as e:
        logger.error(f"get_related_concepts({concept_id}) failed: {e}")
        return []


# ---------------------------------------------------------------------------
# Tree / Stats (admin UI)
# ---------------------------------------------------------------------------

def get_concept_tree() -> List[Dict]:
    """전체 온톨로지 트리 구조 반환 (관리자 UI용).

    Returns a nested list of root concepts, each with a ``children`` key
    containing recursive sub-trees.

    Structure::

        [
            {
                "id": 1,
                "concept_name": "입찰공고",
                "level": 0,
                "children": [
                    {
                        "id": 2,
                        "concept_name": "공사",
                        "level": 1,
                        "children": [...]
                    },
                    ...
                ]
            }
        ]
    """
    cached = _tree_cache.get("concept_tree")
    if cached is not None:
        return cached

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT id, concept_name, concept_name_en, parent_id, level,
                       description, keywords, synonyms, display_order
                FROM ontology_concepts
                WHERE is_active = true
                ORDER BY level, display_order, concept_name
                """
            )

            # Build flat list
            nodes: Dict[int, Dict] = {}
            for row in cursor.fetchall():
                node = {
                    "id": row["id"],
                    "concept_name": row["concept_name"],
                    "concept_name_en": row["concept_name_en"],
                    "parent_id": row["parent_id"],
                    "level": row["level"],
                    "description": row["description"],
                    "keywords": row["keywords"] or [],
                    "synonyms": row["synonyms"] or [],
                    "display_order": row["display_order"],
                    "children": [],
                }
                nodes[row["id"]] = node

            # Build tree by linking children to parents
            roots: List[Dict] = []
            for node in nodes.values():
                parent_id = node["parent_id"]
                if parent_id is None or parent_id not in nodes:
                    roots.append(node)
                else:
                    nodes[parent_id]["children"].append(node)

            _tree_cache.set("concept_tree", roots)
            return roots

    except Exception as e:
        logger.error(f"get_concept_tree failed: {e}")
        return []


def get_ontology_stats() -> Dict:
    """온톨로지 통계 반환.

    Returns::

        {
            "total_concepts": 150,
            "concepts_per_level": {0: 1, 1: 5, 2: 30, 3: 114},
            "total_relations": 45,
            "total_mappings": 3200,
            "mapping_sources": {"auto": 2800, "manual": 300, "ai": 100}
        }
    """
    cached = _tree_cache.get("ontology_stats")
    if cached is not None:
        return cached

    stats: Dict = {
        "total_concepts": 0,
        "concepts_per_level": {},
        "total_relations": 0,
        "total_mappings": 0,
        "mapping_sources": {},
    }

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Total concepts
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM ontology_concepts WHERE is_active = true"
            )
            stats["total_concepts"] = cursor.fetchone()["cnt"]

            # Concepts per level
            cursor.execute(
                """
                SELECT level, COUNT(*) AS cnt
                FROM ontology_concepts
                WHERE is_active = true
                GROUP BY level
                ORDER BY level
                """
            )
            stats["concepts_per_level"] = {
                row["level"]: row["cnt"] for row in cursor.fetchall()
            }

            # Total relations
            cursor.execute("SELECT COUNT(*) AS cnt FROM ontology_relations")
            stats["total_relations"] = cursor.fetchone()["cnt"]

            # Total mappings
            cursor.execute("SELECT COUNT(*) AS cnt FROM bid_ontology_mappings")
            stats["total_mappings"] = cursor.fetchone()["cnt"]

            # Mapping sources breakdown
            cursor.execute(
                """
                SELECT source, COUNT(*) AS cnt
                FROM bid_ontology_mappings
                GROUP BY source
                """
            )
            stats["mapping_sources"] = {
                row["source"]: row["cnt"] for row in cursor.fetchall()
            }

        _tree_cache.set("ontology_stats", stats)
        return stats

    except Exception as e:
        logger.error(f"get_ontology_stats failed: {e}")
        return stats
