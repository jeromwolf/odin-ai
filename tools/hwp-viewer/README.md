# HWP Viewer

> 🚀 한글(HWP) 파일에서 텍스트를 추출하고 마크다운으로 변환하는 도구

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 특징

- ✅ HWP 파일 텍스트 추출 (한글 완벽 지원)
- ✅ 마크다운 변환 (중요 정보 자동 강조)
- ✅ CLI 도구 제공
- ✅ 검색 가능한 형식으로 변환
- ✅ 다양한 프로젝트에서 재사용 가능
- ✅ 이모지 옵션 (기본: 미포함)

## 설치

### 소스에서 설치
```bash
git clone <repository-url>
cd hwp-viewer

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 의존성 설치
pip install -r requirements.txt
```

## 사용법

### 1. CLI 도구 (추천)
```bash
# 기본 텍스트 추출
python cli/hwp_cli.py extract document.hwp

# 마크다운으로 변환 (깔끔한 버전 - 권장)
python cli/hwp_cli.py extract document.hwp -o output.md --format md

# 이모지 포함 마크다운 (필요시)
python cli/hwp_cli.py extract document.hwp -o output.md --format md --emoji

# 문서 정보 조회
python cli/hwp_cli.py info document.hwp
```

### 2. Python 라이브러리
```python
from hwp_viewer import HWPParser

# 텍스트 추출
parser = HWPParser()
doc = parser.parse("document.hwp")
print(doc.raw_text)

# 상세 정보
print(doc.metadata)    # 문서 메타데이터
print(doc.paragraphs)  # 단락별 텍스트
print(len(doc.tables)) # 테이블 개수
```

### 3. 마크다운 검색 활용
```bash
# 생성된 마크다운 파일에서 검색
grep -i "IoT" output.md              # 키워드 검색
grep "서울대학교" output.md           # 기관명 검색
grep "2025년" output.md              # 날짜 검색
```

## CLI 명령어

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `extract` | 텍스트 추출 | `python cli/hwp_cli.py extract doc.hwp -o out.md` |
| `info` | 문서 정보 | `python cli/hwp_cli.py info doc.hwp` |
| `search` | 텍스트 검색 | `python cli/hwp_cli.py search doc.hwp "키워드"` |

## 프로젝트 구조

```
hwp-viewer/
├── hwp_viewer/         # 핵심 라이브러리
├── cli/                # CLI 도구
├── tests/              # 테스트
└── doc/                # 문서
```

## 기술 스택

- **Core**: Python 3.11+
- **HWP 파싱**: pyhwp, hwp5, olefile
- **마크다운**: 자체 제작 포맷터 (중요 정보 자동 강조)
- **CLI**: Click
- **텍스트 처리**: 정규표현식 기반 패턴 매칭

## 지원 기능

### 현재 지원 ✅
- **텍스트 추출**: 한글 완벽 지원 (UTF-8, CP949, EUC-KR 자동 감지)
- **마크다운 변환**: 중요 정보 자동 강조 (날짜, 금액, 키워드, 특이사항)
- **메타데이터**: 제목, 작성자, 키워드 등
- **구조화**: 제목 레벨, 단락, 리스트 자동 변환
- **검색 최적화**: 이모지 없는 깔끔한 형식 (기본)

### 제한사항 ⚠️
- **표(테이블)**: 현재 `<표>` 플레이스홀더로만 표시 (추후 개발 예정)
- **이미지**: 추출 불가 (추후 개발 예정)
- **차트/그래프**: 지원하지 않음
- **복잡한 레이아웃**: 기본 구조만 지원

### 추후 개발 계획 📋
- **표 데이터 추출**: LibreOffice 연동 또는 고급 파싱 기법
- **이미지 추출**: OLE 스트림에서 이미지 파일 분리
- **한글 수식**: 수식 텍스트 변환
- **스타일 정보**: 폰트, 색상 등 서식 정보 보존

## 다른 프로젝트에서 사용

### Odin-AI 예제
```python
# Odin-AI에서 HWP 처리
from hwp_viewer import HWPParser

class RFPProcessor:
    def __init__(self):
        self.hwp_parser = HWPParser()

    def process_rfp(self, hwp_file):
        # HWP에서 텍스트 추출
        text = self.hwp_parser.extract_text(hwp_file)

        # AI 분석을 위한 전처리
        processed = self.preprocess(text)

        return processed
```

### 일반 웹 서비스 예제
```python
from fastapi import FastAPI, UploadFile
from hwp_viewer import HWPParser

app = FastAPI()
parser = HWPParser()

@app.post('/hwp-extract')
async def extract_hwp(file: UploadFile):
    # HWP 내용 추출
    doc = parser.parse(file)
    return {'text': doc.raw_text}
```

## 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

## 라이선스

MIT License - 자유롭게 사용하고 수정할 수 있습니다.

## 문의

- Issue: https://github.com/yourusername/hwp-viewer/issues
- Email: your-email@example.com

## 사용 예시

### 공공조달 문서 처리
```bash
# 구매규격서 처리
python cli/hwp_cli.py extract 구매규격서.hwp -o 규격서.md --format md

# 중요 정보 검색
grep "서울대학교\|IoT\|2025년" 규격서.md
```

### 연구보고서 처리
```bash
# 연구보고서 처리
python cli/hwp_cli.py extract 연구보고서.hwp -o 보고서.md --format md

# 키워드 검색
grep -i "AI\|딥러닝\|머신러닝" 보고서.md
```

## 라이선스

MIT License - 자유롭게 사용하고 수정할 수 있습니다.

## 관련 프로젝트

- [PDF Viewer](../pdf-viewer/) - PDF 파일 처리 도구
- [Odin-AI](https://github.com/yourusername/odin-ai) - 공공조달 AI 플랫폼