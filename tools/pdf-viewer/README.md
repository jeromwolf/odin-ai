# PDF Viewer

> 🚀 PDF 파일에서 텍스트를 추출하고 마크다운으로 변환하는 도구

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 특징

- ✅ PDF 파일 텍스트 추출 (3가지 파서 지원)
- ✅ 마크다운 변환 (중요 정보 자동 강조)
- ✅ CLI 도구 제공
- ✅ 검색 가능한 형식으로 변환
- ✅ 다양한 프로젝트에서 재사용 가능
- ✅ 이모지 옵션 (기본: 미포함)

## 설치

### 소스에서 설치
```bash
git clone <repository-url>
cd pdf-viewer

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 의존성 설치
pip install -r requirements.txt
```

## 사용법

### 1. CLI 도구 (추천)
```bash
# 기본 텍스트 추출
python cli/pdf_cli.py extract document.pdf

# 마크다운으로 변환 (깔끔한 버전 - 권장)
python cli/pdf_cli.py extract document.pdf -o output.md --format md

# 이모지 포함 마크다운 (필요시)
python cli/pdf_cli.py extract document.pdf -o output.md --format md --emoji

# 특정 파서 사용
python cli/pdf_cli.py extract document.pdf --method pdfplumber

# 문서 정보 조회
python cli/pdf_cli.py info document.pdf
```

### 2. Python 라이브러리
```python
from pdf_viewer import PDFParser
from pdf_viewer.markdown_formatter import PDFMarkdownFormatter

# 기본 텍스트 추출
parser = PDFParser()
doc = parser.parse("document.pdf")
print(doc.raw_text)

# 마크다운 변환
formatter = PDFMarkdownFormatter(use_emoji=False)  # 기본: 이모지 없음
markdown = formatter.format_document("제목", doc.raw_text)
```

### 3. 마크다운 검색 활용
```bash
# 생성된 마크다운 파일에서 검색
grep -i "GPU" output.md              # 키워드 검색
grep "서울대학교" output.md           # 기관명 검색
grep "2025년" output.md              # 날짜 검색
```

## 지원 파서

| 파서 | 특징 | 테이블 지원 | 속도 |
|------|------|-------------|------|
| **pdfplumber** | 테이블 추출 우수 | ✅ 우수 | 보통 |
| **pymupdf** | 빠르고 안정적 | ✅ 기본 | 빠름 |
| **pypdf2** | 기본적인 추출 | ❌ 제한적 | 빠름 |
| **auto** | 자동 선택 (기본) | ✅ 최적화 | - |

## 지원 기능

### 현재 지원 ✅
- **텍스트 추출**: PDF 완벽 지원 (3가지 파서 자동 선택)
- **마크다운 변환**: 중요 정보 자동 강조 (날짜, 금액, 기술키워드, 기관명, 사양, 조건)
- **메타데이터**: 제목, 작성자, 생성도구, 페이지 수 등
- **구조화**: 제목 레벨, 단락, 리스트 자동 변환
- **검색 최적화**: 이모지 없는 깔끔한 형식 (기본)
- **기본 테이블**: 단순한 표 구조 감지

### 제한사항 ⚠️
- **복잡한 표**: 병합 셀, 복잡한 레이아웃의 표는 부정확할 수 있음
- **이미지**: PDF 내 이미지 추출 불가 (텍스트만 추출)
- **그래프/차트**: 이미지 형태의 차트는 인식하지 못함
- **복잡한 레이아웃**: 다단 구성, 복잡한 배치는 순서가 섞일 수 있음
- **스캔된 PDF**: OCR 기능 없음 (텍스트가 있는 PDF만 지원)

### 추후 개발 계획 📋
- **고급 테이블 처리**: 병합 셀, 복잡한 표 구조 지원
- **이미지 추출**: PDF 내 이미지 파일 분리
- **OCR 통합**: 스캔된 PDF 텍스트 인식
- **레이아웃 보존**: 원본 구조 최대한 유지

## 기술 스택

- **Core**: Python 3.11+
- **PDF 파싱**: pdfplumber, pymupdf, pypdf2
- **마크다운**: 자체 제작 포맷터 (중요 정보 자동 강조)
- **CLI**: Click
- **텍스트 처리**: 정규표현식 기반 패턴 매칭

## 다른 프로젝트에서 사용

### Odin-AI 예제
```python
# Odin-AI에서 PDF 처리
from pdf_viewer import PDFParser

class RFPProcessor:
    def __init__(self):
        self.pdf_parser = PDFParser()

    def process_pdf_rfp(self, pdf_file):
        # PDF에서 텍스트 추출
        doc = self.pdf_parser.parse(pdf_file)

        # AI 분석을 위한 전처리
        processed = self.preprocess(doc.raw_text)

        return processed
```

### 일반 웹 서비스 예제
```python
from fastapi import FastAPI, UploadFile
from pdf_viewer import PDFParser

app = FastAPI()
parser = PDFParser()

@app.post('/pdf-extract')
async def extract_pdf(file: UploadFile):
    # PDF 내용 추출
    doc = parser.parse(file)
    return {'text': doc.raw_text}
```

## CLI 명령어

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `extract` | 텍스트 추출 | `python cli/pdf_cli.py extract doc.pdf -o out.md` |
| `info` | 문서 정보 | `python cli/pdf_cli.py info doc.pdf` |
| `search` | 텍스트 검색 | `python cli/pdf_cli.py search doc.pdf "키워드"` |
| `tables` | 테이블 추출 | `python cli/pdf_cli.py tables doc.pdf -o tables/` |

## 사용 예시

### 공공조달 문서 처리
```bash
# 구매규격서 처리
python cli/pdf_cli.py extract 구매규격서.pdf -o 규격서.md --format md

# 중요 정보 검색
grep "서울대학교\|GPU\|2025년" 규격서.md
```

### 연구보고서 처리
```bash
# 연구보고서 처리
python cli/pdf_cli.py extract 연구보고서.pdf -o 보고서.md --format md

# 키워드 검색
grep -i "AI\|딥러닝\|머신러닝" 보고서.md
```

## 라이선스

MIT License - 자유롭게 사용하고 수정할 수 있습니다.

## 관련 프로젝트

- [HWP Viewer](../hwp-viewer/) - HWP 파일 처리 도구
- [Odin-AI](https://github.com/yourusername/odin-ai) - 공공조달 AI 플랫폼