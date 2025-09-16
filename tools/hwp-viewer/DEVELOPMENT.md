# HWP Viewer 개발 현황

## 📅 개발 일자: 2025-09-16

## ✅ 완료된 작업

### 1. 프로젝트 구조 설정
- ✅ 독립 도구로 설계 (다른 프로젝트에서 재사용 가능)
- ✅ Python 패키지 구조 구현
- ✅ 가상환경 설정 및 의존성 설치

### 2. 핵심 기능 구현
- ✅ **HWPParser**: HWP 파일 파싱 클래스
  - olefile 기반 파싱
  - pyhwp 라이브러리 지원 (설치 시)
  - zlib 압축 해제 지원
  - 메타데이터 추출

- ✅ **HWPConverter**: 파일 형식 변환
  - PDF 변환 (LibreOffice 필요)
  - HTML 변환 (LibreOffice 필요)
  - TXT 변환 (내장 파서 사용)

- ✅ **TextExtractor**: 텍스트 추출 전문
  - 전체 텍스트 추출
  - 단락별 추출
  - 키워드 검색
  - 정규표현식 패턴 매칭

- ✅ **MetadataExtractor**: 메타데이터 추출
  - 문서 정보 (제목, 작성자, 날짜 등)
  - 통계 정보 (글자 수, 단어 수 등)

### 3. 인터페이스
- ✅ **REST API 서버** (FastAPI)
  - `/extract`: 텍스트 추출
  - `/parse`: 상세 파싱
  - `/convert`: 형식 변환
  - `/health`: 서비스 상태

- ✅ **CLI 도구**
  - `extract`: 텍스트 추출
  - `info`: 파일 정보 표시
  - `search`: 텍스트 검색
  - `convert`: 형식 변환

### 4. 테스트
- ✅ 모듈 임포트 테스트
- ✅ API 서버 동작 확인
- ✅ CLI 도구 동작 확인

## 🚧 개발 중 / 개선 필요 사항

### 1. HWP 파싱 정확도
- 현재 기본적인 텍스트 추출만 가능
- 복잡한 HWP 구조 (테이블, 이미지, 차트) 파싱 필요
- pyhwp/hwp5 라이브러리 통합 개선 필요

### 2. 변환 기능
- LibreOffice 설치 필요 (PDF/HTML 변환)
- 변환 품질 개선 필요
- 더 많은 출력 형식 지원 (DOCX, Markdown 등)

### 3. 테이블 처리
- 테이블 구조 파싱 미구현
- CSV/JSON 형식 내보내기 필요

### 4. 성능 최적화
- 대용량 파일 처리
- 메모리 사용량 최적화
- 병렬 처리

## 🔧 설치 및 사용법

### 설치
```bash
cd /Users/blockmeta/Desktop/blockmeta/project/tools/hwp-viewer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Python 라이브러리로 사용
```python
from hwp_viewer import HWPParser

parser = HWPParser()
text = parser.extract_text("document.hwp")
print(text)
```

### API 서버 실행
```bash
uvicorn api.app:app --reload --port 8123
# http://localhost:8123/docs 에서 API 문서 확인
```

### CLI 사용
```bash
# 텍스트 추출
python cli/hwp_cli.py extract document.hwp

# 파일 정보
python cli/hwp_cli.py info document.hwp --json

# 텍스트 검색
python cli/hwp_cli.py search document.hwp "검색어"
```

## 📊 기술 스택

- **Core**: Python 3.11+
- **HWP 파싱**: olefile, pyhwp
- **API**: FastAPI, Uvicorn
- **CLI**: Click
- **변환**: LibreOffice (선택사항)

## 🎯 향후 계획

### Phase 1 - 기본 기능 강화
- [ ] HWP 5.0 완전 지원
- [ ] 테이블 파싱 구현
- [ ] 이미지 추출
- [ ] 더 나은 에러 처리

### Phase 2 - 변환 기능 확장
- [ ] Markdown 변환
- [ ] DOCX 변환
- [ ] JSON 구조화 출력
- [ ] 배치 처리

### Phase 3 - 고급 기능
- [ ] 웹 UI 개발
- [ ] Docker 이미지 배포
- [ ] NPM 패키지 래퍼
- [ ] 클라우드 서비스화

## 🔗 Odin-AI 연동

이 도구는 Odin-AI 프로젝트에서 HWP RFP 문서 처리에 활용됩니다:

```python
# Odin-AI에서 사용 예시
from hwp_viewer import HWPParser

class RFPProcessor:
    def __init__(self):
        self.hwp_parser = HWPParser()

    def process_rfp(self, hwp_path):
        # HWP에서 텍스트 추출
        text = self.hwp_parser.extract_text(hwp_path)

        # AI 분석을 위한 전처리
        processed = self.preprocess_for_ai(text)

        return processed
```

## 📝 참고사항

- HWP 파일 형식은 한글과컴퓨터의 독자 형식
- 완벽한 파싱은 공식 SDK 없이는 제한적
- LibreOffice를 통한 변환이 가장 현실적인 대안
- 나라장터 RFP 문서는 대부분 텍스트 중심이라 현재 수준에서도 활용 가능

## 🐛 알려진 이슈

1. pyhwp 라이브러리 import 경로 문제
2. 복잡한 HWP 문서에서 텍스트 순서 보장 안됨
3. 암호화된 HWP 파일 미지원
4. 일부 특수 문자 깨짐 현상

## 📧 문의

- 프로젝트 위치: `/Users/blockmeta/Desktop/blockmeta/project/tools/hwp-viewer/`
- 관련 프로젝트: Odin-AI