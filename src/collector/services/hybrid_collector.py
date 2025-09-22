"""
하이브리드 데이터 수집기
API 우선 + Selenium 백업 전략
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger

from .api_collector import APICollector
from .selenium_collector import SeleniumCollector
from shared.config import settings
from shared.database import get_db_context
from shared.models import CollectionLog


class HybridCollector:
    """
    API + Selenium 하이브리드 수집기

    전략:
    1. 먼저 공공데이터포털 API 시도
    2. SSL 오류 등으로 실패 시 Selenium으로 대체
    3. 두 방법 모두 실패 시 에러 로깅
    """

    def __init__(self):
        self.api_collector = APICollector()
        self.selenium_collector = SeleniumCollector()

    async def collect_monthly_data(
        self,
        start_date: datetime,
        end_date: datetime,
        max_retry: int = 2
    ) -> Dict[str, Any]:
        """
        월간 데이터 수집 (하이브리드 방식)

        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜
            max_retry: 최대 재시도 횟수

        Returns:
            수집 결과 딕셔너리
        """

        # 로그 시작
        with get_db_context() as db:
            log_entry = CollectionLog(
                collection_type="hybrid",
                collection_date=datetime.utcnow(),
                status="running",
                start_time=datetime.utcnow(),
                notes=f"하이브리드 수집: {start_date.date()} ~ {end_date.date()}"
            )
            db.add(log_entry)
            db.commit()
            log_id = log_entry.id

        collection_results = {
            'start_date': start_date,
            'end_date': end_date,
            'total_days': (end_date - start_date).days + 1,
            'api_success_count': 0,
            'api_failure_count': 0,
            'selenium_success_count': 0,
            'selenium_failure_count': 0,
            'total_collected': 0,
            'daily_results': {},
            'error_log': [],
            'method_used': {
                'api_only': 0,
                'selenium_backup': 0,
                'both_failed': 0
            }
        }

        try:
            logger.info(f"🚀 하이브리드 월간 수집 시작: {start_date.date()} ~ {end_date.date()}")

            # 일자별 수집
            current_date = start_date
            while current_date <= end_date:
                logger.info(f"📅 {current_date.strftime('%Y-%m-%d')} 수집 시작...")

                daily_result = await self._collect_daily_data_hybrid(current_date, max_retry)
                collection_results['daily_results'][current_date.strftime('%Y-%m-%d')] = daily_result

                # 통계 업데이트
                if daily_result['success']:
                    collection_results['total_collected'] += daily_result['count']

                    if daily_result['method'] == 'api':
                        collection_results['api_success_count'] += 1
                        collection_results['method_used']['api_only'] += 1
                    elif daily_result['method'] == 'selenium':
                        collection_results['selenium_success_count'] += 1
                        collection_results['method_used']['selenium_backup'] += 1
                else:
                    collection_results['method_used']['both_failed'] += 1

                if daily_result.get('errors'):
                    collection_results['error_log'].extend(daily_result['errors'])

                # 다음 날짜로
                current_date += timedelta(days=1)

                # 요청 간격 (서버 부하 방지)
                await asyncio.sleep(2)

            # 로그 업데이트 (성공)
            with get_db_context() as db:
                log_entry = db.query(CollectionLog).filter(
                    CollectionLog.id == log_id
                ).first()

                if log_entry:
                    log_entry.status = "completed"
                    log_entry.end_time = datetime.utcnow()
                    log_entry.total_found = collection_results['total_collected']
                    log_entry.new_items = collection_results['total_collected']
                    log_entry.notes = f"API: {collection_results['api_success_count']}, Selenium: {collection_results['selenium_success_count']}"
                    db.commit()

            # 결과 요약
            self._log_collection_summary(collection_results)

            return collection_results

        except Exception as e:
            # 로그 업데이트 (실패)
            with get_db_context() as db:
                log_entry = db.query(CollectionLog).filter(
                    CollectionLog.id == log_id
                ).first()

                if log_entry:
                    log_entry.status = "failed"
                    log_entry.end_time = datetime.utcnow()
                    log_entry.error_message = str(e)
                    db.commit()

            logger.error(f"❌ 하이브리드 수집 실패: {e}")
            collection_results['error_log'].append({
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'type': 'hybrid_collector_error'
            })

            return collection_results

    async def _collect_daily_data_hybrid(
        self,
        target_date: datetime,
        max_retry: int = 2
    ) -> Dict[str, Any]:
        """
        일별 데이터 하이브리드 수집

        Args:
            target_date: 대상 날짜
            max_retry: 최대 재시도 횟수

        Returns:
            일별 수집 결과
        """

        daily_result = {
            'date': target_date.strftime('%Y-%m-%d'),
            'success': False,
            'count': 0,
            'method': None,
            'processing_time': 0,
            'errors': [],
            'attempts': {
                'api': {'tried': False, 'success': False, 'error': None},
                'selenium': {'tried': False, 'success': False, 'error': None}
            }
        }

        start_time = datetime.utcnow()

        try:
            # 1단계: API 수집 시도
            logger.info(f"🔄 1단계: API 수집 시도 - {target_date.strftime('%Y-%m-%d')}")

            daily_result['attempts']['api']['tried'] = True

            try:
                api_data = await self.api_collector.collect_bids_by_date(target_date)

                if api_data:
                    daily_result['success'] = True
                    daily_result['count'] = len(api_data)
                    daily_result['method'] = 'api'
                    daily_result['attempts']['api']['success'] = True

                    logger.info(f"✅ API 수집 성공: {len(api_data)}건")
                    return daily_result

                else:
                    logger.warning(f"⚠️ API 수집 결과 없음")
                    daily_result['attempts']['api']['error'] = "No data returned"

            except Exception as api_error:
                logger.warning(f"⚠️ API 수집 실패: {api_error}")
                daily_result['attempts']['api']['error'] = str(api_error)
                daily_result['errors'].append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'method': 'api',
                    'error': str(api_error)
                })

            # 2단계: Selenium 백업 수집
            logger.info(f"🔄 2단계: Selenium 백업 수집 - {target_date.strftime('%Y-%m-%d')}")

            daily_result['attempts']['selenium']['tried'] = True

            try:
                # Selenium은 날짜 범위로 수집 (하루)
                selenium_data = await self.selenium_collector.collect_bids_by_date_range(
                    start_date=target_date,
                    end_date=target_date,
                    max_pages=5  # 하루 분량이므로 적당한 페이지 수
                )

                if selenium_data:
                    daily_result['success'] = True
                    daily_result['count'] = len(selenium_data)
                    daily_result['method'] = 'selenium'
                    daily_result['attempts']['selenium']['success'] = True

                    logger.info(f"✅ Selenium 백업 수집 성공: {len(selenium_data)}건")
                    return daily_result

                else:
                    logger.warning(f"⚠️ Selenium 수집 결과 없음")
                    daily_result['attempts']['selenium']['error'] = "No data returned"

            except Exception as selenium_error:
                logger.error(f"❌ Selenium 수집 실패: {selenium_error}")
                daily_result['attempts']['selenium']['error'] = str(selenium_error)
                daily_result['errors'].append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'method': 'selenium',
                    'error': str(selenium_error)
                })

            # 두 방법 모두 실패
            logger.error(f"❌ {target_date.strftime('%Y-%m-%d')}: API와 Selenium 모두 실패")
            return daily_result

        finally:
            # 처리 시간 계산
            end_time = datetime.utcnow()
            daily_result['processing_time'] = (end_time - start_time).total_seconds()

    def _log_collection_summary(self, results: Dict[str, Any]):
        """수집 결과 요약 로깅"""

        logger.info("=" * 80)
        logger.info("📊 하이브리드 수집 완료 - 결과 요약")
        logger.info("=" * 80)

        logger.info(f"📅 수집 기간: {results['start_date'].date()} ~ {results['end_date'].date()}")
        logger.info(f"📊 총 수집일: {results['total_days']}일")
        logger.info(f"📈 총 수집량: {results['total_collected']}건")

        logger.info("\n🔍 수집 방법별 통계:")
        logger.info(f"   🟢 API만으로 성공: {results['method_used']['api_only']}일")
        logger.info(f"   🟡 Selenium 백업 사용: {results['method_used']['selenium_backup']}일")
        logger.info(f"   🔴 두 방법 모두 실패: {results['method_used']['both_failed']}일")

        # 성공률 계산
        total_success = results['method_used']['api_only'] + results['method_used']['selenium_backup']
        success_rate = (total_success / results['total_days']) * 100 if results['total_days'] > 0 else 0

        logger.info(f"\n📈 전체 성공률: {success_rate:.1f}%")

        if results['error_log']:
            logger.info(f"\n⚠️ 발생한 오류: {len(results['error_log'])}건")
            for error in results['error_log'][-5:]:  # 최근 5개만 표시
                logger.info(f"   - {error.get('method', 'unknown')}: {error.get('error', 'Unknown error')}")

        logger.info("=" * 80)

    async def collect_single_date(self, target_date: datetime) -> Dict[str, Any]:
        """
        단일 날짜 수집 (하이브리드 방식)

        Args:
            target_date: 대상 날짜

        Returns:
            수집 결과
        """
        logger.info(f"🎯 단일 날짜 하이브리드 수집: {target_date.strftime('%Y-%m-%d')}")

        result = await self._collect_daily_data_hybrid(target_date)

        if result['success']:
            logger.info(f"✅ 수집 성공: {result['count']}건 ({result['method']} 방식)")
        else:
            logger.error(f"❌ 수집 실패: 모든 방법 실패")

        return result


# 편의 함수들
async def collect_recent_bids_hybrid(days_back: int = 7) -> Dict[str, Any]:
    """
    최근 며칠간의 입찰 데이터를 하이브리드 방식으로 수집

    Args:
        days_back: 과거 며칠까지

    Returns:
        수집 결과
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    collector = HybridCollector()
    return await collector.collect_monthly_data(start_date, end_date)


async def collect_date_range_hybrid(
    start_date: datetime,
    end_date: datetime
) -> Dict[str, Any]:
    """
    날짜 범위 하이브리드 수집

    Args:
        start_date: 시작 날짜
        end_date: 종료 날짜

    Returns:
        수집 결과
    """
    collector = HybridCollector()
    return await collector.collect_monthly_data(start_date, end_date)