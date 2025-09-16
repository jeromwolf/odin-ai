"""
크롤러 관리자
API와 크롤러를 통합 관리하는 서비스
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from backend.services.public_data_client import public_data_client
from backend.services.g2b_crawler import G2BCrawler
from backend.models.database import SessionLocal
from backend.models.bid_models import BidAnnouncement
from loguru import logger


class DataSource(Enum):
    """데이터 소스 타입"""
    API = "api"
    CRAWLER = "crawler"
    HYBRID = "hybrid"


@dataclass
class CrawlConfig:
    """크롤링 설정"""
    use_api: bool = True
    use_crawler: bool = True
    api_priority: bool = True  # API를 우선적으로 사용
    max_pages: int = 10
    delay_between_requests: float = 2.0
    max_retries: int = 3


class CrawlerManager:
    """크롤러 통합 관리자"""

    def __init__(self):
        self.api_client = public_data_client
        self.crawler = None
        self.config = CrawlConfig()

        # 통계
        self.stats = {
            "api_requests": 0,
            "crawler_requests": 0,
            "successful_items": 0,
            "failed_items": 0,
            "duplicate_items": 0
        }

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.crawler = G2BCrawler()
        await self.crawler.setup_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.crawler:
            await self.crawler.close_session()

    async def collect_bid_data(
        self,
        source: DataSource = DataSource.HYBRID,
        start_date: str = None,
        end_date: str = None,
        max_items: int = 100,
        keywords: List[str] = None
    ) -> Dict[str, Any]:
        """통합 입찰 데이터 수집"""

        logger.info(f"입찰 데이터 수집 시작 (소스: {source.value}, 최대: {max_items}건)")

        collected_items = []
        errors = []

        try:
            if source == DataSource.API or source == DataSource.HYBRID:
                # API 데이터 수집
                api_items = await self._collect_from_api(
                    start_date, end_date, max_items, keywords
                )
                collected_items.extend(api_items.get("items", []))
                self.stats["api_requests"] += 1

            if source == DataSource.CRAWLER or source == DataSource.HYBRID:
                # 크롤러 데이터 수집
                remaining_items = max_items - len(collected_items)
                if remaining_items > 0:
                    crawler_items = await self._collect_from_crawler(
                        start_date, end_date, remaining_items, keywords
                    )
                    collected_items.extend(crawler_items.get("items", []))
                    self.stats["crawler_requests"] += 1

            # 중복 제거
            unique_items = self._remove_duplicates(collected_items)
            self.stats["duplicate_items"] += len(collected_items) - len(unique_items)

            # 데이터베이스 저장
            saved_count = await self._save_to_database(unique_items)
            self.stats["successful_items"] += saved_count

            return {
                "success": True,
                "total_collected": len(collected_items),
                "unique_items": len(unique_items),
                "saved_items": saved_count,
                "source": source.value,
                "stats": self.stats,
                "items": unique_items[:10],  # 상위 10건만 반환
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"데이터 수집 실패: {e}")
            errors.append(str(e))

            return {
                "success": False,
                "error": str(e),
                "errors": errors,
                "stats": self.stats,
                "timestamp": datetime.now().isoformat()
            }

    async def _collect_from_api(
        self,
        start_date: str,
        end_date: str,
        max_items: int,
        keywords: List[str]
    ) -> Dict[str, Any]:
        """공공데이터포털 API에서 데이터 수집"""

        logger.info("API에서 데이터 수집 중...")

        try:
            # 날짜 기본값 설정
            if not start_date:
                start_date = datetime.now().strftime("%Y%m%d0000")
            if not end_date:
                end_date = (datetime.now() + timedelta(days=30)).strftime("%Y%m%d2359")

            # API 호출
            result = await self.api_client.get_bid_construction_list(
                page=1,
                size=min(max_items, 100),  # API 최대 100건 제한
                inquiry_div="1",  # 전체
                start_date=start_date,
                end_date=end_date
            )

            if result.get("success"):
                items = result.get("items", [])
                logger.info(f"API에서 {len(items)}건 수집 성공")

                # 데이터 정규화
                normalized_items = [self._normalize_api_data(item) for item in items]

                return {
                    "success": True,
                    "items": normalized_items,
                    "source": "api"
                }
            else:
                logger.warning(f"API 호출 실패: {result}")
                return {"success": False, "items": []}

        except Exception as e:
            logger.error(f"API 데이터 수집 실패: {e}")
            return {"success": False, "error": str(e), "items": []}

    async def _collect_from_crawler(
        self,
        start_date: str,
        end_date: str,
        max_items: int,
        keywords: List[str]
    ) -> Dict[str, Any]:
        """크롤러에서 데이터 수집"""

        logger.info("크롤러에서 데이터 수집 중...")

        try:
            if not self.crawler:
                logger.error("크롤러가 초기화되지 않았습니다")
                return {"success": False, "items": []}

            # 날짜 형식 변환 (크롤러용)
            crawler_start = self._convert_date_for_crawler(start_date)
            crawler_end = self._convert_date_for_crawler(end_date)

            # 키워드 조합
            keyword_str = " ".join(keywords) if keywords else ""

            # 크롤러 호출
            result = await self.crawler.get_bid_announcements(
                page=1,
                keyword=keyword_str,
                start_date=crawler_start,
                end_date=crawler_end
            )

            if result.get("success"):
                items = result.get("items", [])
                logger.info(f"크롤러에서 {len(items)}건 수집 성공")

                # 데이터 정규화
                normalized_items = [self._normalize_crawler_data(item) for item in items]

                return {
                    "success": True,
                    "items": normalized_items[:max_items],
                    "source": "crawler"
                }
            else:
                logger.warning(f"크롤러 호출 실패: {result}")
                return {"success": False, "items": []}

        except Exception as e:
            logger.error(f"크롤러 데이터 수집 실패: {e}")
            return {"success": False, "error": str(e), "items": []}

    def _normalize_api_data(self, api_item: Dict[str, Any]) -> Dict[str, Any]:
        """API 데이터 정규화"""
        try:
            return {
                "bid_notice_no": api_item.get("bidNtceNo", ""),
                "bid_notice_name": api_item.get("bidNtceNm", ""),
                "notice_inst_name": api_item.get("ntceInsttNm", ""),
                "demand_inst_name": api_item.get("dminsttNm", ""),
                "bid_notice_date": self._parse_api_datetime(api_item.get("bidNtceDt")),
                "bid_close_date": self._parse_api_datetime(api_item.get("bidClseDt")),
                "open_bid_date": self._parse_api_datetime(api_item.get("opengDt")),
                "presumpt_price": self._parse_price(api_item.get("presmptPrce")),
                "budget_amount": self._parse_price(api_item.get("bdgtAmt")),
                "bid_method": api_item.get("bidMethdNm", ""),
                "bid_type": api_item.get("bidKindNm", ""),
                "industry_type": api_item.get("indstrytyNm", ""),
                "source": "api",
                "raw_data": api_item
            }
        except Exception as e:
            logger.warning(f"API 데이터 정규화 실패: {e}")
            return {"source": "api", "raw_data": api_item}

    def _normalize_crawler_data(self, crawler_item: Dict[str, Any]) -> Dict[str, Any]:
        """크롤러 데이터 정규화"""
        try:
            return {
                "bid_notice_no": crawler_item.get("bid_notice_no", ""),
                "bid_notice_name": crawler_item.get("bid_notice_name", ""),
                "notice_inst_name": crawler_item.get("agency", ""),
                "bid_method": crawler_item.get("bid_method", ""),
                "announcement_date": crawler_item.get("announcement_date", ""),
                "deadline_date": crawler_item.get("deadline_date", ""),
                "opening_date": crawler_item.get("opening_date", ""),
                "source": "crawler",
                "detail_url": crawler_item.get("detail_url", ""),
                "raw_data": crawler_item
            }
        except Exception as e:
            logger.warning(f"크롤러 데이터 정규화 실패: {e}")
            return {"source": "crawler", "raw_data": crawler_item}

    def _parse_api_datetime(self, date_str: str) -> Optional[datetime]:
        """API 날짜 문자열 파싱"""
        if not date_str:
            return None

        try:
            # API는 보통 YYYYMMDDHHMM 형식
            if len(date_str) >= 12:
                return datetime.strptime(date_str[:12], "%Y%m%d%H%M")
            elif len(date_str) >= 8:
                return datetime.strptime(date_str[:8], "%Y%m%d")
        except ValueError:
            pass

        return None

    def _parse_price(self, price_str: str) -> Optional[int]:
        """가격 문자열 파싱"""
        if not price_str:
            return None

        try:
            # 숫자가 아닌 문자 제거
            price_clean = ''.join(filter(str.isdigit, str(price_str)))
            return int(price_clean) if price_clean else None
        except ValueError:
            return None

    def _convert_date_for_crawler(self, date_str: str) -> str:
        """크롤러용 날짜 형식 변환"""
        if not date_str:
            return ""

        try:
            # YYYYMMDDHHMM -> YYYY/MM/DD 형식으로 변환
            if len(date_str) >= 8:
                year = date_str[:4]
                month = date_str[4:6]
                day = date_str[6:8]
                return f"{year}/{month}/{day}"
        except Exception:
            pass

        return date_str

    def _remove_duplicates(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 항목 제거"""
        seen_notices = set()
        unique_items = []

        for item in items:
            bid_no = item.get("bid_notice_no", "")
            if bid_no and bid_no not in seen_notices:
                seen_notices.add(bid_no)
                unique_items.append(item)
            elif not bid_no:
                # 공고번호가 없는 경우, 공고명으로 중복 체크
                bid_name = item.get("bid_notice_name", "")
                name_key = f"name_{hash(bid_name)}"
                if name_key not in seen_notices:
                    seen_notices.add(name_key)
                    unique_items.append(item)

        logger.info(f"중복 제거: {len(items)}건 → {len(unique_items)}건")
        return unique_items

    async def _save_to_database(self, items: List[Dict[str, Any]]) -> int:
        """데이터베이스에 저장"""
        if not items:
            return 0

        saved_count = 0
        db = SessionLocal()

        try:
            for item in items:
                try:
                    # 기존 항목 확인
                    bid_no = item.get("bid_notice_no")
                    if bid_no:
                        existing = db.query(BidAnnouncement).filter(
                            BidAnnouncement.bid_notice_no == bid_no
                        ).first()

                        if existing:
                            logger.debug(f"기존 항목 스킵: {bid_no}")
                            continue

                    # 새 항목 생성
                    bid_item = BidAnnouncement(
                        bid_notice_no=item.get("bid_notice_no", ""),
                        bid_notice_name=item.get("bid_notice_name", ""),
                        notice_inst_name=item.get("notice_inst_name", ""),
                        demand_inst_name=item.get("demand_inst_name", ""),
                        bid_notice_date=item.get("bid_notice_date"),
                        bid_close_date=item.get("bid_close_date"),
                        open_bid_date=item.get("open_bid_date"),
                        presumpt_price=item.get("presumpt_price"),
                        budget_amount=item.get("budget_amount"),
                        bid_method=item.get("bid_method", ""),
                        bid_type=item.get("bid_type", ""),
                        industry_type=item.get("industry_type", ""),
                        bid_status="공고중",  # 기본값
                        api_service=item.get("source", ""),
                        raw_data=item.get("raw_data", {})
                    )

                    db.add(bid_item)
                    saved_count += 1

                except Exception as e:
                    logger.warning(f"항목 저장 실패: {e}")
                    self.stats["failed_items"] += 1
                    continue

            db.commit()
            logger.info(f"데이터베이스 저장 완료: {saved_count}건")

        except Exception as e:
            logger.error(f"데이터베이스 저장 오류: {e}")
            db.rollback()
            raise
        finally:
            db.close()

        return saved_count

    async def get_crawl_stats(self) -> Dict[str, Any]:
        """크롤링 통계 조회"""
        db = SessionLocal()

        try:
            # 데이터베이스 통계
            total_bids = db.query(BidAnnouncement).count()
            api_bids = db.query(BidAnnouncement).filter(
                BidAnnouncement.api_service == "api"
            ).count()
            crawler_bids = db.query(BidAnnouncement).filter(
                BidAnnouncement.api_service == "crawler"
            ).count()

            return {
                "runtime_stats": self.stats,
                "database_stats": {
                    "total_bids": total_bids,
                    "api_sourced": api_bids,
                    "crawler_sourced": crawler_bids
                },
                "config": {
                    "use_api": self.config.use_api,
                    "use_crawler": self.config.use_crawler,
                    "max_pages": self.config.max_pages
                },
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"통계 조회 실패: {e}")
            return {"error": str(e)}
        finally:
            db.close()

    async def health_check(self) -> Dict[str, Any]:
        """크롤러 매니저 상태 확인"""
        try:
            # API 클라이언트 상태
            api_status = await self.api_client.test_connection()

            # 크롤러 상태
            crawler_status = {"status": "not_initialized"}
            if self.crawler:
                crawler_status = await self.crawler.health_check()

            return {
                "success": True,
                "manager_status": "healthy",
                "api_status": api_status,
                "crawler_status": crawler_status,
                "stats": self.stats,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"상태 확인 실패: {e}")
            return {
                "success": False,
                "manager_status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }