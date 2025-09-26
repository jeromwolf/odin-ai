"""
배치 시스템 알림 처리 모듈
새로 수집된 입찰 공고에 대해 알림 규칙을 검사하고 알림을 발송
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any

from backend.services.alert_engine import AlertEngine, BidAnnouncement
from database import get_db_connection

logger = logging.getLogger(__name__)

class AlertProcessor:
    """배치 시스템용 알림 처리기"""

    def __init__(self):
        self.alert_engine = AlertEngine()

    def process_new_bids_for_alerts(self) -> Dict[str, Any]:
        """
        새로 수집된 입찰 공고들에 대해 알림 처리

        Returns:
            Dict[str, Any]: 처리 결과 통계
        """
        try:
            logger.info("=== 알림 처리 시작 ===")

            # 오늘 수집된 새로운 입찰 공고들 조회
            new_bids = self._get_todays_new_bids()

            if not new_bids:
                logger.info("새로운 입찰 공고가 없어 알림 처리를 건너뜁니다")
                return {
                    'status': 'success',
                    'total_bids': 0,
                    'notifications_sent': 0,
                    'message': '새로운 입찰 공고 없음'
                }

            logger.info(f"오늘 새로 수집된 입찰 공고: {len(new_bids)}개")

            # 비동기 알림 처리 실행
            stats = asyncio.run(self.alert_engine.process_new_bids(new_bids))

            # 배치 결과 요약 이메일 발송
            asyncio.run(self.alert_engine.notification_service.send_batch_summary(stats))

            result = {
                'status': 'success',
                'message': f"{stats['notifications_sent']}개 알림 발송 완료",
                **stats
            }

            logger.info(f"알림 처리 완료: {result}")
            return result

        except Exception as e:
            logger.error(f"알림 처리 중 오류 발생: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'total_bids': 0,
                'notifications_sent': 0
            }

    def _get_todays_new_bids(self) -> List[BidAnnouncement]:
        """오늘 새로 수집된 입찰 공고들 조회"""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    bid_notice_no,
                    title,
                    organization_name,
                    estimated_price,
                    bid_start_date,
                    bid_end_date,
                    region_restriction,
                    bid_category,
                    qualification_summary,
                    contract_method,
                    created_at
                FROM bid_announcements
                WHERE DATE(created_at) = CURRENT_DATE
                  AND title IS NOT NULL
                  AND organization_name IS NOT NULL
                ORDER BY created_at DESC
            """

            cursor.execute(query)
            bids = []

            for row in cursor.fetchall():
                bid = BidAnnouncement(
                    bid_notice_no=row[0],
                    title=row[1] or "",
                    organization_name=row[2] or "",
                    estimated_price=float(row[3]) if row[3] else None,
                    bid_start_date=row[4],
                    bid_end_date=row[5],
                    region_restriction=row[6],
                    bid_category=row[7],
                    qualification_summary=row[8],
                    contract_method=row[9],
                    created_at=row[10]
                )
                bids.append(bid)

            return bids

    def process_scheduled_notifications(self) -> Dict[str, Any]:
        """스케줄된 알림들 처리 (일일/주간 요약)"""
        try:
            logger.info("=== 스케줄된 알림 처리 시작 ===")

            # 비동기 처리 실행
            asyncio.run(self.alert_engine.process_scheduled_notifications())

            result = {
                'status': 'success',
                'message': '스케줄된 알림 처리 완료'
            }

            logger.info("스케줄된 알림 처리 완료")
            return result

        except Exception as e:
            logger.error(f"스케줄된 알림 처리 중 오류: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def cleanup_old_notifications(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """오래된 알림 기록 정리"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # 90일 이상 된 읽은 알림들 삭제
                cleanup_query = """
                    DELETE FROM alert_notifications
                    WHERE created_at < CURRENT_DATE - INTERVAL '%s days'
                      AND (status = 'sent' AND read_at IS NOT NULL)
                """

                cursor.execute(cleanup_query, (days_to_keep,))
                deleted_count = cursor.rowcount
                conn.commit()

                result = {
                    'status': 'success',
                    'message': f'{deleted_count}개의 오래된 알림 기록 정리 완료'
                }

                logger.info(f"알림 기록 정리 완료: {deleted_count}개 삭제")
                return result

        except Exception as e:
            logger.error(f"알림 기록 정리 중 오류: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def get_alert_system_stats(self) -> Dict[str, Any]:
        """알림 시스템 통계 조회"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                stats = {}

                # 활성 알림 규칙 수
                cursor.execute("SELECT COUNT(*) FROM alert_rules WHERE is_active = true")
                stats['active_rules'] = cursor.fetchone()[0]

                # 오늘 발송된 알림 수
                cursor.execute("""
                    SELECT COUNT(*) FROM alert_notifications
                    WHERE DATE(created_at) = CURRENT_DATE AND status = 'sent'
                """)
                stats['today_notifications'] = cursor.fetchone()[0]

                # 최근 7일 알림 발송 현황
                cursor.execute("""
                    SELECT
                        DATE(created_at) as date,
                        COUNT(*) as count
                    FROM alert_notifications
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                      AND status = 'sent'
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """)
                weekly_stats = []
                for row in cursor.fetchall():
                    weekly_stats.append({
                        'date': row[0].isoformat(),
                        'notifications': row[1]
                    })
                stats['weekly_notifications'] = weekly_stats

                # 채널별 발송 현황 (최근 30일)
                cursor.execute("""
                    SELECT
                        channel,
                        COUNT(*) as total,
                        COUNT(CASE WHEN status = 'sent' THEN 1 END) as sent,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
                    FROM alert_notifications
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY channel
                """)
                channel_stats = {}
                for row in cursor.fetchall():
                    channel, total, sent, failed = row
                    channel_stats[channel] = {
                        'total': total,
                        'sent': sent,
                        'failed': failed,
                        'success_rate': round(sent / total * 100, 2) if total > 0 else 0
                    }
                stats['channel_stats'] = channel_stats

                return {
                    'status': 'success',
                    'stats': stats
                }

        except Exception as e:
            logger.error(f"알림 시스템 통계 조회 중 오류: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

def main():
    """테스트용 메인 함수"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    processor = AlertProcessor()

    # 새로운 입찰 공고에 대한 알림 처리
    result = processor.process_new_bids_for_alerts()
    print("알림 처리 결과:", result)

    # 시스템 통계 조회
    stats_result = processor.get_alert_system_stats()
    print("시스템 통계:", stats_result)

if __name__ == "__main__":
    main()