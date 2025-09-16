# HWP 한글 깨짐 문제 해결 가이드

## 🔍 문제 상황

HWP 파일에서 텍스트를 추출할 때 한글이 깨져서 나오는 문제 (네모 박스로 표시)

## 🛠️ 해결 방법

### 1. pyhwp의 hwp5txt 명령어 사용 (권장)

가장 정확한 방법입니다:

```bash
# 가상환경 활성화
source venv/bin/activate

# hwp5txt로 직접 추출
hwp5txt your_file.hwp > output.txt

# 또는 Python에서
python -m hwp5 txt your_file.hwp
```

### 2. 개선된 파서 사용

`parser_improved.py`를 만들어 여러 방법을 순차적으로 시도합니다:

```python
from hwp_viewer.parser_improved import ImprovedHWPParser

parser = ImprovedHWPParser()
text = parser.extract_text("your_file.hwp")
print(text)
```

### 3. 테스트 스크립트 실행

```bash
# 가상환경 활성화 후
source venv/bin/activate

# 테스트 실행
python test_korean.py your_file.hwp
```

## 📝 기술적 원인

### HWP 파일의 특성
1. **독자 형식**: 한글과컴퓨터의 자체 바이너리 형식
2. **압축**: zlib으로 압축된 섹션 존재
3. **인코딩**: UTF-16 LE, CP949 등 여러 인코딩 혼재
4. **구조**: OLE 컴파운드 파일 구조

### 파싱 어려움
- 공식 SDK 없이는 완벽한 파싱 어려움
- 텍스트가 여러 스트림에 분산 저장
- 제어 코드와 텍스트가 섞여 있음

## ✅ 개선 사항

### 1. 인코딩 자동 감지
```python
encodings = ['utf-16-le', 'utf-16', 'cp949', 'euc-kr', 'utf-8']
```

### 2. 여러 추출 방법 시도
1. hwp5txt 명령어
2. pyhwp Python 모듈
3. strings 명령어 (시스템)
4. 바이너리 직접 파싱

### 3. 한글 검증
```python
# 한글 유니코드 범위 확인
if any('\uac00' <= char <= '\ud7af' for char in text):
    # 한글이 포함된 텍스트
```

## 🚀 권장 사용법

### 명령줄에서:
```bash
# 가상환경 활성화
source venv/bin/activate

# hwp5txt 사용 (가장 정확)
hwp5txt document.hwp

# CLI 도구 사용
python cli/hwp_cli.py extract document.hwp
```

### Python 코드에서:
```python
# 개선된 파서 사용
from hwp_viewer.parser_improved import ImprovedHWPParser

parser = ImprovedHWPParser()
doc = parser.parse("document.hwp")
print(doc.raw_text)
```

### API에서:
```bash
# 서버 실행
source venv/bin/activate
uvicorn api.app:app --reload

# 파일 업로드로 추출
curl -X POST "http://localhost:8123/extract" \
  -F "file=@document.hwp"
```

## ⚠️ 제한 사항

1. **완벽하지 않음**: 복잡한 서식, 테이블, 이미지는 손실
2. **순서 보장 안됨**: 텍스트 순서가 바뀔 수 있음
3. **메타데이터 제한**: 일부 문서 정보만 추출 가능

## 💡 추가 개선 방안

### 1. LibreOffice 활용
```bash
# LibreOffice로 텍스트 변환
soffice --headless --convert-to txt document.hwp
```

### 2. 온라인 변환 서비스
- 한컴오피스 웹 서비스
- Google Docs 변환

### 3. 상용 솔루션
- 한글과컴퓨터 공식 SDK
- 서드파티 변환 라이브러리

## 🔗 참고 자료

- [pyhwp 문서](https://github.com/mete0r/pyhwp)
- [HWP 파일 구조](https://www.hancom.com/etc/hwpspec.html)
- [나라장터 문서 처리 가이드](https://www.g2b.go.kr)

## 📞 문제 해결

여전히 한글이 깨진다면:

1. HWP 파일 버전 확인 (5.0 이상 권장)
2. 파일 손상 여부 확인
3. 다른 변환 도구 시도
4. 원본 파일을 한컴오피스에서 다시 저장

---

*최종 업데이트: 2025-09-16*