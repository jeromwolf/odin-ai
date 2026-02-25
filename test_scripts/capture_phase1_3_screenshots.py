#!/usr/bin/env python3
"""
Phase 1~3 스크린샷 캡처 스크립트
Playwright를 사용하여 주요 페이지 및 API 결과를 캡처합니다.
"""

import subprocess
import json
import os
import time
import requests

SCREENSHOT_DIR = "/Users/blockmeta/Desktop/workspace/odin-ai/docs/screenshots/phase1_3"
API_BASE = "http://localhost:9000/api"
FRONTEND_URL = "http://localhost:3000"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def save_api_screenshot(name, url, description):
    """API 응답을 JSON으로 저장하고 요약 생성"""
    try:
        r = requests.get(url, timeout=120)
        data = r.json()
        # Save JSON
        json_path = os.path.join(SCREENSHOT_DIR, f"{name}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  ✅ {name}: {description} → {json_path}")
        return data
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        return None

def capture_playwright_screenshot(name, url, description, wait_ms=3000):
    """Playwright로 페이지 스크린샷 캡처"""
    screenshot_path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    try:
        result = subprocess.run(
            ["npx", "playwright", "screenshot",
             "--browser", "chromium",
             "--wait-for-timeout", str(wait_ms),
             "--viewport-size", "1280,900",
             url, screenshot_path],
            capture_output=True, text=True,
            timeout=30,
            cwd="/Users/blockmeta/Desktop/workspace/odin-ai/frontend"
        )
        if os.path.isfile(screenshot_path):
            size = os.path.getsize(screenshot_path)
            print(f"  ✅ {name}: {description} → {screenshot_path} ({size//1024}KB)")
            return True
        else:
            print(f"  ⚠️ {name}: screenshot not created, trying python method")
            return False
    except Exception as e:
        print(f"  ⚠️ {name}: Playwright failed ({e}), trying alternative")
        return False

print("="*60)
print("  Phase 1~3 스크린샷 및 API 응답 캡처")
print("="*60)

# ===== API 응답 캡처 =====
print("\n📡 API 응답 캡처:")

# Phase 1: RAG
save_api_screenshot(
    "01_rag_status",
    f"{API_BASE}/rag/status",
    "RAG 시스템 상태 (임베딩 + LLM + GraphRAG)"
)

save_api_screenshot(
    "02_rag_search_road",
    f"{API_BASE}/rag/search?q=도로공사&limit=5",
    "RAG 하이브리드 검색 (도로공사)"
)

save_api_screenshot(
    "03_rag_search_disaster",
    f"{API_BASE}/rag/search?q=재해복구 소하천&limit=5",
    "RAG 하이브리드 검색 (재해복구 소하천)"
)

save_api_screenshot(
    "04_rag_ask",
    f"{API_BASE}/rag/ask?q=경기도 건설 입찰 조건은?&limit=3",
    "RAG Q&A (EXAONE 3.5 답변)"
)

# Phase 2: Graph
save_api_screenshot(
    "05_graph_status",
    f"{API_BASE}/graph/status",
    "Neo4j 그래프 상태 (노드/관계)"
)

save_api_screenshot(
    "06_graph_tag_construction",
    f"{API_BASE}/graph/tag/건설",
    "태그 네트워크 (건설)"
)

save_api_screenshot(
    "07_graph_region_chungnam",
    f"{API_BASE}/graph/region/충청남도",
    "지역별 입찰 (충청남도)"
)

# Phase 3: GraphRAG
save_api_screenshot(
    "08_graphrag_global_ask_trend",
    f"{API_BASE}/rag/global-ask?q=충청남도 건설 트렌드&top_communities=5",
    "GraphRAG 글로벌 Q&A (충청남도 건설 트렌드)"
)

save_api_screenshot(
    "09_graphrag_global_ask_disaster",
    f"{API_BASE}/rag/global-ask?q=재해복구 사업 현황&top_communities=3",
    "GraphRAG 글로벌 Q&A (재해복구 사업 현황)"
)

# ===== 프론트엔드 스크린샷 =====
print("\n📸 프론트엔드 스크린샷 캡처:")

# Check if frontend is ready
for i in range(10):
    try:
        r = requests.get(FRONTEND_URL, timeout=5)
        if r.status_code == 200:
            print(f"  프론트엔드 준비 완료 ({i+1}회 시도)")
            break
    except:
        time.sleep(3)
else:
    print("  ⚠️ 프론트엔드 서버 미응답 - 스크린샷 건너뜀")

# Try Playwright screenshots
pages = [
    ("10_frontend_graph_explorer", f"{FRONTEND_URL}/graph", "지식 그래프 탐색기 페이지", 5000),
    ("11_frontend_dashboard", f"{FRONTEND_URL}/dashboard", "대시보드 페이지", 3000),
    ("12_frontend_search", f"{FRONTEND_URL}/search", "검색 페이지", 3000),
]

for name, url, desc, wait in pages:
    capture_playwright_screenshot(name, url, desc, wait)

print("\n✅ 캡처 완료!")
print(f"📁 저장 위치: {SCREENSHOT_DIR}")

# List all captured files
files = sorted(os.listdir(SCREENSHOT_DIR))
print(f"\n📄 캡처된 파일 목록 ({len(files)}개):")
for f in files:
    size = os.path.getsize(os.path.join(SCREENSHOT_DIR, f))
    print(f"  - {f} ({size//1024}KB)")
