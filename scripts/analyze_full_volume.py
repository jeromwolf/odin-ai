#!/usr/bin/env python3
"""
전체 카테고리 일주일 데이터 볼륨 분석 스크립트
- 4개 카테고리(공사/용역/물품/외자) API를 일주일치 조회
- 일별/카테고리별 건수 집계
- 문서 파일 사이즈 샘플링 (카테고리별 10건씩)
- 스토리지 추정치 계산
"""

import requests
import urllib.parse
import time
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from collections import defaultdict

# API 설정
API_KEY_ENCODED = os.getenv('BID_API_KEY', '6h2l2VPWSfA2vG3xSFr7gf6iwaZT2dmzcoCOzklLnOIJY6sw17lrwHNQ3WxPdKMDIN%2FmMlv2vBTWTIzBDPKVdw%3D%3D')
API_KEY = urllib.parse.unquote(API_KEY_ENCODED)

BASE_URL = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService"

ENDPOINTS = {
    "공사": f"{BASE_URL}/getBidPblancListInfoCnstwk",
    "용역": f"{BASE_URL}/getBidPblancListInfoServc",
    "물품": f"{BASE_URL}/getBidPblancListInfoThng",
    "외자": f"{BASE_URL}/getBidPblancListInfoFrgcpt",
}

# 결과 저장
results = {
    "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "period": {},
    "daily_counts": defaultdict(lambda: defaultdict(int)),
    "category_totals": {},
    "file_size_samples": defaultdict(list),
    "projections": {},
}


def query_api(endpoint_url, start_str, end_str, page_no=1, num_of_rows=100):
    """API 단일 페이지 조회"""
    params = {
        'serviceKey': API_KEY,
        'pageNo': str(page_no),
        'numOfRows': str(num_of_rows),
        'type': 'json',
        'inqryDiv': '1',
        'inqryBgnDt': start_str,
        'inqryEndDt': end_str
    }

    try:
        response = requests.get(endpoint_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if 'response' in data and 'body' in data['response']:
            body = data['response']['body']
            items = body.get('items', [])
            total_count = body.get('totalCount', 0)
            return items, total_count
        else:
            # 에러 응답 확인
            if 'response' in data and 'header' in data['response']:
                header = data['response']['header']
                result_code = header.get('resultCode', 'unknown')
                result_msg = header.get('resultMsg', 'unknown')
                print(f"    API 에러: {result_code} - {result_msg}")
            return [], 0
    except Exception as e:
        print(f"    API 호출 실패: {e}")
        return [], 0


def count_category_for_date(category, endpoint_url, date_str):
    """특정 날짜의 카테고리별 공고 건수 조회 (totalCount만 확인)"""
    start = f"{date_str}0000"
    end = f"{date_str}2359"

    _, total_count = query_api(endpoint_url, start, end, page_no=1, num_of_rows=1)
    return total_count


def collect_all_items_for_period(category, endpoint_url, start_date, end_date):
    """기간 전체 아이템 수집 (파일사이즈 분석용, 최대 300건)"""
    start_str = start_date.strftime('%Y%m%d0000')
    end_str = end_date.strftime('%Y%m%d2359')

    all_items = []
    page_no = 1
    max_items = 300  # 분석용으로 충분

    while len(all_items) < max_items:
        items, total_count = query_api(endpoint_url, start_str, end_str, page_no=page_no, num_of_rows=100)

        if not items:
            break

        all_items.extend(items)
        print(f"    {category}: 페이지 {page_no} - {len(items)}건 수집 (전체 {total_count}건)")

        if len(all_items) >= total_count or len(all_items) >= max_items:
            break

        page_no += 1
        time.sleep(0.3)

    return all_items[:max_items], total_count


def sample_file_sizes(category, items, max_samples=10):
    """문서 URL에서 파일 사이즈 샘플링 (HEAD 요청)"""
    sampled = 0
    sizes = []

    for item in items:
        if sampled >= max_samples:
            break

        doc_url = item.get('stdNtceDocUrl')
        if not doc_url:
            continue

        try:
            resp = requests.head(doc_url, timeout=10, allow_redirects=True)
            content_length = resp.headers.get('Content-Length')
            content_type = resp.headers.get('Content-Type', 'unknown')

            if content_length:
                size_kb = int(content_length) / 1024
                sizes.append({
                    "bid_no": item.get('bidNtceNo', 'unknown'),
                    "file_name": item.get('ntceSpecFileNm1', 'unknown'),
                    "size_kb": round(size_kb, 1),
                    "content_type": content_type,
                })
                sampled += 1
        except Exception as e:
            pass

        time.sleep(0.2)

    return sizes


def format_number(n):
    """숫자를 천단위 콤마로 포맷"""
    return f"{n:,}"


def main():
    print("=" * 70)
    print("  ODIN-AI 전체 카테고리 일주일 데이터 볼륨 분석")
    print("=" * 70)

    # 분석 기간: 최근 7일
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    results["period"] = {
        "start": start_date.strftime("%Y-%m-%d"),
        "end": end_date.strftime("%Y-%m-%d"),
    }

    print(f"\n분석 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    print(f"카테고리: {', '.join(ENDPOINTS.keys())}")

    # ============================================================
    # Phase 1: 일별/카테고리별 건수 조회
    # ============================================================
    print(f"\n{'=' * 70}")
    print("Phase 1: 일별/카테고리별 공고 건수 조회")
    print(f"{'=' * 70}")

    daily_data = defaultdict(dict)
    category_week_totals = defaultdict(int)

    for day_offset in range(7):
        date = start_date + timedelta(days=day_offset)
        date_str = date.strftime('%Y%m%d')
        date_display = date.strftime('%Y-%m-%d')
        day_name = ['월', '화', '수', '목', '금', '토', '일'][date.weekday()]

        print(f"\n  {date_display} ({day_name}):")

        day_total = 0
        for category, endpoint_url in ENDPOINTS.items():
            count = count_category_for_date(category, endpoint_url, date_str)
            daily_data[date_display][category] = count
            category_week_totals[category] += count
            day_total += count
            print(f"    {category}: {format_number(count)}건")
            time.sleep(0.3)  # API 부하 방지

        daily_data[date_display]["합계"] = day_total
        print(f"    ────────────")
        print(f"    합계: {format_number(day_total)}건")

    results["daily_counts"] = dict(daily_data)
    results["category_totals"] = dict(category_week_totals)

    # 주간 요약
    grand_total = sum(category_week_totals.values())
    avg_daily = grand_total / 7

    print(f"\n{'─' * 50}")
    print(f"주간 요약:")
    print(f"{'─' * 50}")
    for cat, total in sorted(category_week_totals.items(), key=lambda x: -x[1]):
        pct = (total / grand_total * 100) if grand_total > 0 else 0
        print(f"  {cat}: {format_number(total)}건 ({pct:.1f}%)")
    print(f"  ────────────")
    print(f"  전체: {format_number(grand_total)}건 (일평균 {avg_daily:.0f}건)")

    # ============================================================
    # Phase 2: 카테고리별 문서 파일 사이즈 샘플링
    # ============================================================
    print(f"\n{'=' * 70}")
    print("Phase 2: 카테고리별 문서 파일 사이즈 샘플링 (각 10건)")
    print(f"{'=' * 70}")

    all_file_sizes = {}
    # 최근 3일 데이터에서 샘플링
    sample_start = end_date - timedelta(days=3)

    for category, endpoint_url in ENDPOINTS.items():
        print(f"\n  [{category}] 샘플 수집 중...")
        items, total = collect_all_items_for_period(category, endpoint_url, sample_start, end_date)

        if items:
            # 문서 URL이 있는 아이템 필터링
            doc_items = [item for item in items if item.get('stdNtceDocUrl')]
            print(f"    문서 URL 보유: {len(doc_items)}/{len(items)}건 ({len(doc_items)/len(items)*100:.1f}%)")

            # 파일 사이즈 샘플링
            sizes = sample_file_sizes(category, doc_items, max_samples=10)
            all_file_sizes[category] = sizes

            if sizes:
                avg_size = sum(s['size_kb'] for s in sizes) / len(sizes)
                min_size = min(s['size_kb'] for s in sizes)
                max_size = max(s['size_kb'] for s in sizes)
                print(f"    파일 사이즈 (KB): 평균={avg_size:.1f}, 최소={min_size:.1f}, 최대={max_size:.1f}")
            else:
                print(f"    파일 사이즈 측정 실패")
        else:
            print(f"    데이터 없음")

        time.sleep(1)

    results["file_size_samples"] = all_file_sizes

    # ============================================================
    # Phase 3: 스토리지 추정치 계산
    # ============================================================
    print(f"\n{'=' * 70}")
    print("Phase 3: 스토리지 추정치 계산")
    print(f"{'=' * 70}")

    # 카테고리별 평균 파일 사이즈
    category_avg_sizes = {}
    for cat, sizes in all_file_sizes.items():
        if sizes:
            category_avg_sizes[cat] = sum(s['size_kb'] for s in sizes) / len(sizes)
        else:
            category_avg_sizes[cat] = 150  # 기본값 150KB

    # DB 레코드 오버헤드 (메타데이터, 인덱스 등)
    DB_OVERHEAD_KB = 5  # 공고당 약 5KB DB 오버헤드
    MARKDOWN_RATIO = 0.1  # 원본 대비 마크다운 비율 (~10%)

    print(f"\n카테고리별 스토리지 분석:")
    print(f"{'─' * 60}")

    total_daily_storage_mb = 0
    for cat in ENDPOINTS.keys():
        daily_count = category_week_totals.get(cat, 0) / 7
        avg_file_kb = category_avg_sizes.get(cat, 150)
        doc_pct = 0.7  # 문서 보유 비율 가정 70%

        # 일일 스토리지 = (파일 + 마크다운 + DB) * 건수
        per_bid_kb = (avg_file_kb * doc_pct) + (avg_file_kb * doc_pct * MARKDOWN_RATIO) + DB_OVERHEAD_KB
        daily_mb = (daily_count * per_bid_kb) / 1024

        total_daily_storage_mb += daily_mb

        print(f"  {cat}:")
        print(f"    일평균 건수: {daily_count:.0f}건")
        print(f"    평균 파일 크기: {avg_file_kb:.1f} KB")
        print(f"    건당 스토리지: {per_bid_kb:.1f} KB")
        print(f"    일일 스토리지: {daily_mb:.1f} MB")

    print(f"\n{'─' * 60}")
    print(f"전체 일일 스토리지: {total_daily_storage_mb:.1f} MB/일")
    print(f"월간 스토리지: {total_daily_storage_mb * 30:.0f} MB/월 ({total_daily_storage_mb * 30 / 1024:.1f} GB/월)")
    print(f"연간 스토리지: {total_daily_storage_mb * 365:.0f} MB/년 ({total_daily_storage_mb * 365 / 1024:.1f} GB/년)")

    # 1년/3년/5년 누적
    print(f"\n누적 스토리지 추정:")
    for years in [1, 2, 3, 5]:
        cumulative_gb = total_daily_storage_mb * 365 * years / 1024
        print(f"  {years}년: {cumulative_gb:.1f} GB")

    # GCP 비용 추정
    print(f"\n{'=' * 70}")
    print("Phase 4: GCP 비용 추정 (전체 카테고리 기준)")
    print(f"{'=' * 70}")

    monthly_gb = total_daily_storage_mb * 30 / 1024
    yearly_gb = total_daily_storage_mb * 365 / 1024

    print(f"\n  월간 데이터 증가: {monthly_gb:.1f} GB")
    print(f"  연간 데이터 증가: {yearly_gb:.1f} GB")

    # 시나리오별 GCP 비용
    scenarios = [
        {
            "name": "MVP (1년차)",
            "compute": "e2-small ($13.80/월)",
            "db": f"Cloud SQL Basic ($10/월, 10GB + {yearly_gb:.0f}GB/년)",
            "storage": f"Cloud Storage ($0.02/GB, ~{yearly_gb:.0f}GB)",
            "total_monthly": 13.80 + 10 + (yearly_gb / 12 * 0.02) + 5,
        },
        {
            "name": "Production (2년차)",
            "compute": "e2-medium ($26/월)",
            "db": f"Cloud SQL Standard ($25/월, 50GB + {yearly_gb*2:.0f}GB)",
            "storage": f"Cloud Storage ($0.02/GB, ~{yearly_gb*2:.0f}GB)",
            "total_monthly": 26 + 25 + (yearly_gb * 2 * 0.02 / 12) + 10,
        },
        {
            "name": "Growth (3년차+)",
            "compute": "n2-standard-2 ($52/월)",
            "db": f"Cloud SQL HA ($80/월, 100GB + {yearly_gb*3:.0f}GB)",
            "storage": f"Cloud Storage ($0.02/GB, ~{yearly_gb*3:.0f}GB)",
            "total_monthly": 52 + 80 + (yearly_gb * 3 * 0.02 / 12) + 15,
        },
    ]

    for s in scenarios:
        print(f"\n  [{s['name']}]")
        print(f"    컴퓨팅: {s['compute']}")
        print(f"    DB: {s['db']}")
        print(f"    스토리지: {s['storage']}")
        print(f"    예상 월비용: ${s['total_monthly']:.0f}/월")

    # 결과 저장
    results["projections"] = {
        "daily_bids_total": round(avg_daily),
        "daily_storage_mb": round(total_daily_storage_mb, 1),
        "monthly_storage_gb": round(monthly_gb, 1),
        "yearly_storage_gb": round(yearly_gb, 1),
        "category_avg_file_sizes_kb": {k: round(v, 1) for k, v in category_avg_sizes.items()},
    }

    # JSON 보고서 저장
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports',
                                f'volume_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    # defaultdict를 일반 dict로 변환
    serializable_results = json.loads(json.dumps(results, default=str, ensure_ascii=False))

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 70}")
    print(f"분석 완료! 보고서 저장: {report_path}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
