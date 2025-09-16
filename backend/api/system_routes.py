"""
시스템 관련 API 엔드포인트
"""

from fastapi import APIRouter
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import platform
import sys

router = APIRouter(prefix="/api/system", tags=["시스템"])


class SystemTimeResponse(BaseModel):
    """시스템 시간 응답 모델"""
    current_datetime: datetime
    current_date: str
    current_time: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int
    day_of_week: str
    timezone: str
    timestamp: float
    formatted_kr: str
    formatted_iso: str


class SystemInfoResponse(BaseModel):
    """시스템 정보 응답 모델"""
    platform: str
    python_version: str
    hostname: str
    current_time: SystemTimeResponse


@router.get("/time", response_model=SystemTimeResponse)
async def get_current_time():
    """
    현재 시스템 시간 조회

    한국 시간(KST) 기준으로 현재 날짜와 시간을 반환합니다.
    """
    # 한국 시간대 (UTC+9)
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)

    # 요일 매핑
    weekdays = {
        0: "월요일",
        1: "화요일",
        2: "수요일",
        3: "목요일",
        4: "금요일",
        5: "토요일",
        6: "일요일"
    }

    return SystemTimeResponse(
        current_datetime=now,
        current_date=now.strftime("%Y-%m-%d"),
        current_time=now.strftime("%H:%M:%S"),
        year=now.year,
        month=now.month,
        day=now.day,
        hour=now.hour,
        minute=now.minute,
        second=now.second,
        day_of_week=weekdays[now.weekday()],
        timezone="Asia/Seoul (KST)",
        timestamp=now.timestamp(),
        formatted_kr=now.strftime("%Y년 %m월 %d일 %H시 %M분 %S초"),
        formatted_iso=now.isoformat()
    )


@router.get("/date")
async def get_current_date():
    """
    현재 날짜만 간단히 조회

    오늘 날짜를 다양한 형식으로 반환합니다.
    """
    kst = timezone(timedelta(hours=9))
    today = datetime.now(kst)

    return {
        "today": today.strftime("%Y-%m-%d"),
        "year": today.year,
        "month": today.month,
        "day": today.day,
        "formatted": {
            "korean": f"{today.year}년 {today.month}월 {today.day}일",
            "iso": today.strftime("%Y-%m-%d"),
            "api_format": today.strftime("%Y%m%d"),  # API 조회용
            "display": today.strftime("%Y.%m.%d")
        },
        "day_of_week": ["월", "화", "수", "목", "금", "토", "일"][today.weekday()],
        "is_weekend": today.weekday() >= 5
    }


@router.get("/info", response_model=SystemInfoResponse)
async def get_system_info():
    """
    시스템 정보 조회

    서버 플랫폼, Python 버전 등 시스템 정보를 반환합니다.
    """
    time_info = await get_current_time()

    return SystemInfoResponse(
        platform=platform.system(),
        python_version=sys.version.split()[0],
        hostname=platform.node(),
        current_time=time_info
    )


@router.get("/date-range")
async def get_date_range(days: int = 7):
    """
    날짜 범위 생성

    입찰공고 조회 등에 사용할 날짜 범위를 생성합니다.

    Args:
        days: 조회할 일수 (기본값: 7일)
    """
    kst = timezone(timedelta(hours=9))
    end_date = datetime.now(kst)
    start_date = end_date - timedelta(days=days)

    return {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "days": days,
        "api_format": {
            "start": start_date.strftime("%Y%m%d0000"),  # API 조회용 시작
            "end": end_date.strftime("%Y%m%d2359")       # API 조회용 종료
        },
        "description": f"최근 {days}일간 ({start_date.strftime('%m/%d')} ~ {end_date.strftime('%m/%d')})"
    }


@router.get("/business-days")
async def get_business_days(days: int = 5):
    """
    영업일 기준 날짜 범위

    주말을 제외한 영업일 기준으로 날짜를 계산합니다.

    Args:
        days: 영업일 수 (기본값: 5일)
    """
    kst = timezone(timedelta(hours=9))
    end_date = datetime.now(kst)
    current = end_date
    business_days = []

    while len(business_days) < days:
        if current.weekday() < 5:  # 월-금
            business_days.append(current.strftime("%Y-%m-%d"))
        current -= timedelta(days=1)

    return {
        "business_days": business_days,
        "start_date": business_days[-1],
        "end_date": business_days[0],
        "total_days": days,
        "includes_weekend": False
    }