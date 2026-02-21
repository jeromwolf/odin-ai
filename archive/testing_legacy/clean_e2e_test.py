#!/usr/bin/env python3
"""
깔끔한 E2E 파이프라인 테스트
프로젝트 구조 정리 후 전체 파이프라인 테스트
"""

import asyncio
import aiohttp
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Dict, Any, List
import urllib.parse

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.shared.config import settings
from src.shared.database import get_db_context, engine
from src.shared.models import BidAnnouncement, BidDocument, Base
from loguru import logger


class CleanE2ETest:
    """깔끔한 E2E 테스트"""

    def __init__(self):
        self.test_results = {
            "test_id": f"CLEAN_E2E_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "start_time": None,
            "phases": {},
            "summary": {}
        }
        self.api_key = urllib.parse.unquote(settings.public_data_api_key)
        self.base_url = settings.public_data_base_url

    async def run_all_tests(self):
        """모든 테스트 실행"""
        self.test_results["start_time"] = datetime.now().isoformat()

        logger.info("=" * 80)
        logger.info("🎯 깔끔한 E2E 파이프라인 테스트 시작")
        logger.info("=" * 80)

        # 1. 데이터베이스 초기화
        self._init_database()

        # 2. API 데이터 수집 테스트
        await self._test_api_collection()

        # 3. 데이터베이스 저장 테스트
        await self._test_database_save()

        # 4. 검색 성능 테스트
        await self._test_search_performance()

        # 5. 결과 요약
        self._generate_summary()

        self.test_results["end_time"] = datetime.now().isoformat()
        return self.test_results

    def _init_database(self):
        """데이터베이스 초기화"""
        logger.info("\n📦 Phase 1: 데이터베이스 초기화")
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("✅ 데이터베이스 테이블 생성 완료")
            self.test_results["phases"]["database_init"] = {"status": "success"}
        except Exception as e:
            logger.error(f"❌ 데이터베이스 초기화 실패: {e}")
            self.test_results["phases"]["database_init"] = {"status": "failed", "error": str(e)}

    async def _test_api_collection(self):
        """API 데이터 수집 테스트"""
        logger.info("\n📡 Phase 2: API 데이터 수집 테스트")
        phase_result = {
            "status": "pending",
            "total_items": 0,
            "unique_items": 0,
            "date_tested": None
        }

        try:
            # 오늘 날짜로 테스트
            target_date = datetime.now()
            date_str = target_date.strftime('%Y%m%d')

            params = {
                'serviceKey': self.api_key,
                'pageNo': 1,
                'numOfRows': 20,  # 20개만 테스트
                'type': 'json',
                'inqryDiv': '1',
                'inqryBgnDt': f'{date_str}0000',
                'inqryEndDt': f'{date_str}2359',
            }

            url = f"{self.base_url}/getBidPblancListInfoCnstwk"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'response' in data and 'body' in data['response']:
                            items = data['response']['body'].get('items', [])
                            phase_result["total_items"] = len(items)

                            # 중복 제거
                            unique = {}
                            for item in items:
                                bid_no = item.get('bidNtceNo')
                                if bid_no and bid_no not in unique:
                                    unique[bid_no] = item

                            phase_result["unique_items"] = len(unique)
                            phase_result["date_tested"] = target_date.strftime('%Y-%m-%d')
                            phase_result["status"] = "success"

                            # 샘플 저장
                            self.test_results["sample_data"] = list(unique.values())[:3]

                            logger.info(f"✅ API 수집 성공: {len(items)}건 (고유 {len(unique)}건)")
                        else:
                            phase_result["status"] = "no_data"
                            logger.warning("⚠️ API 응답에 데이터 없음")
                    else:
                        phase_result["status"] = "failed"
                        phase_result["error"] = f"HTTP {response.status}"
                        logger.error(f"❌ API 오류: {response.status}")

        except Exception as e:
            phase_result["status"] = "failed"
            phase_result["error"] = str(e)
            logger.error(f"❌ API 수집 실패: {e}")

        self.test_results["phases"]["api_collection"] = phase_result

    async def _test_database_save(self):
        """데이터베이스 저장 테스트"""
        logger.info("\n💾 Phase 3: 데이터베이스 저장 테스트")
        phase_result = {
            "status": "pending",
            "saved_count": 0,
            "duplicate_count": 0,
            "error_count": 0
        }

        try:
            sample_data = self.test_results.get("sample_data", [])

            if not sample_data:
                phase_result["status"] = "skipped"
                logger.warning("⚠️ 저장할 데이터 없음")
            else:
                with get_db_context() as db:
                    for item in sample_data:
                        try:
                            bid_notice_no = item.get('bidNtceNo')

                            # 중복 체크
                            existing = db.query(BidAnnouncement).filter(
                                BidAnnouncement.bid_notice_no == bid_notice_no
                            ).first()

                            if existing:
                                phase_result["duplicate_count"] += 1
                                continue

                            # 새 데이터 저장
                            announcement = BidAnnouncement(
                                bid_notice_no=bid_notice_no,
                                title=item.get('bidNtceNm', ''),
                                organization_name=item.get('ntceInsttNm', ''),
                                contact_info=item.get('ntceInsttOfclTelNo', ''),
                                announcement_date=datetime.strptime(
                                    item.get('bidNtceDate', datetime.now().strftime('%Y-%m-%d')),
                                    '%Y-%m-%d'
                                ) if item.get('bidNtceDate') else datetime.now(),
                                bid_amount=int(float(item.get('asignBdgtAmt', 0))) if item.get('asignBdgtAmt') else None,
                                detail_url=item.get('bidNtceDtlUrl', ''),
                                document_url=item.get('stdNtceDocUrl', ''),
                                status='active',
                                created_at=datetime.now(),
                                updated_at=datetime.now()
                            )

                            db.add(announcement)
                            db.commit()
                            phase_result["saved_count"] += 1

                        except Exception as e:
                            db.rollback()
                            phase_result["error_count"] += 1
                            logger.error(f"저장 오류: {e}")

                phase_result["status"] = "success"
                logger.info(f"✅ DB 저장: {phase_result['saved_count']}건 저장, {phase_result['duplicate_count']}건 중복")

        except Exception as e:
            phase_result["status"] = "failed"
            phase_result["error"] = str(e)
            logger.error(f"❌ DB 저장 실패: {e}")

        self.test_results["phases"]["database_save"] = phase_result

    async def _test_search_performance(self):
        """검색 성능 테스트"""
        logger.info("\n🔍 Phase 4: 검색 성능 테스트")
        phase_result = {
            "status": "pending",
            "total_records": 0,
            "search_tests": []
        }

        try:
            with get_db_context() as db:
                total = db.query(BidAnnouncement).count()
                phase_result["total_records"] = total

                if total == 0:
                    phase_result["status"] = "skipped"
                    logger.warning("⚠️ 검색할 데이터 없음")
                else:
                    # 간단한 검색 테스트
                    import time

                    test_queries = ["공사", "입찰", "사업"]

                    for query in test_queries:
                        start_time = time.time()
                        results = db.query(BidAnnouncement).filter(
                            BidAnnouncement.title.contains(query)
                        ).limit(10).all()
                        elapsed = time.time() - start_time

                        phase_result["search_tests"].append({
                            "query": query,
                            "count": len(results),
                            "time": round(elapsed, 3)
                        })

                        logger.info(f"  검색 '{query}': {len(results)}건 ({elapsed:.3f}초)")

                    avg_time = sum(t["time"] for t in phase_result["search_tests"]) / len(phase_result["search_tests"])
                    phase_result["avg_response_time"] = round(avg_time, 3)
                    phase_result["status"] = "success"

                    logger.info(f"✅ 평균 응답 시간: {avg_time:.3f}초")

        except Exception as e:
            phase_result["status"] = "failed"
            phase_result["error"] = str(e)
            logger.error(f"❌ 검색 테스트 실패: {e}")

        self.test_results["phases"]["search_performance"] = phase_result

    def _generate_summary(self):
        """테스트 요약 생성"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 테스트 요약")
        logger.info("=" * 80)

        summary = {
            "total_phases": 4,
            "successful": 0,
            "failed": 0,
            "skipped": 0
        }

        for phase_name, phase_data in self.test_results["phases"].items():
            status = phase_data.get("status", "unknown")
            if status == "success":
                summary["successful"] += 1
            elif status == "failed":
                summary["failed"] += 1
            elif status == "skipped":
                summary["skipped"] += 1

        self.test_results["summary"] = summary

        # 콘솔 출력
        logger.info(f"✅ 성공: {summary['successful']}/{summary['total_phases']}")
        logger.info(f"⚠️ 스킵: {summary['skipped']}/{summary['total_phases']}")
        logger.info(f"❌ 실패: {summary['failed']}/{summary['total_phases']}")

        # 핵심 지표
        api = self.test_results["phases"].get("api_collection", {})
        db = self.test_results["phases"].get("database_save", {})
        search = self.test_results["phases"].get("search_performance", {})

        logger.info(f"\n📈 핵심 지표:")
        logger.info(f"  - API 수집: {api.get('total_items', 0)}건 (고유 {api.get('unique_items', 0)}건)")
        logger.info(f"  - DB 저장: {db.get('saved_count', 0)}건")
        logger.info(f"  - 검색 성능: {search.get('avg_response_time', 'N/A')}초")

        if summary["failed"] == 0:
            logger.info("\n🎉 모든 테스트 성공!")
        else:
            logger.warning(f"\n⚠️ {summary['failed']}개 테스트 실패")

    def save_results(self):
        """결과 저장"""
        results_dir = Path("testing/test_results")
        results_dir.mkdir(parents=True, exist_ok=True)

        result_file = results_dir / f"{self.test_results['test_id']}.json"

        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"\n💾 결과 저장: {result_file}")
        return str(result_file)


async def main():
    """메인 실행 함수"""
    tester = CleanE2ETest()

    # 테스트 실행
    results = await tester.run_all_tests()

    # 결과 저장
    result_file = tester.save_results()

    return results, result_file


if __name__ == "__main__":
    asyncio.run(main())