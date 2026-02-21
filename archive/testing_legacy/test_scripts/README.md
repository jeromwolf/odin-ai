# Test Scripts Directory

이 디렉토리는 개발 과정에서 작성된 다양한 테스트 스크립트들을 포함합니다.

## 📁 디렉토리 구조

### API 테스트 (7개)
- `test_api_*.py`: 공공데이터포털 API 테스트
- `test_public_api.py`: 공공 API 연동 테스트
- `test_direct_api.py`: 직접 API 호출 테스트

### G2B/나라장터 크롤링 테스트 (8개)
- `test_g2b_*.py`: 나라장터 웹 크롤링 관련 테스트
- 브라우저 체크, 메뉴 검색, 팝업 처리 등 포함

### HWP 문서 처리 테스트 (6개)
- `test_*hwp*.py`: HWP 파일 다운로드 및 파싱
- `test_bidntce*.py`: 입찰공고 URL 처리
- `test_integrated_hwp_processor.py`: 통합 HWP 처리 시스템 테스트

### Selenium 테스트 (2개)
- `test_selenium_crawler.py`: Selenium 크롤러 테스트
- `test_simple_selenium.py`: 간단한 Selenium 테스트

### 기타
- `api_capability_analysis.py`: API 기능 분석 스크립트
- `migration_log.txt`: 파일 이동 로그 (2025-09-17)

## 🚨 주의사항

이 스크립트들은 개발/테스트 목적으로만 사용되어야 하며, 프로덕션 환경에서는 사용하지 마세요.
정식 테스트는 `/tests` 디렉토리의 pytest 기반 테스트를 사용하세요.

## 실행 방법

```bash
# 개별 스크립트 실행
python test_scripts/test_api_simple.py

# 가상환경 활성화 후 실행 권장
source venv/bin/activate
python test_scripts/test_integrated_hwp_processor.py
```