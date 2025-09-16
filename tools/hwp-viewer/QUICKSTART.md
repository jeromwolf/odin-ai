# HWP Viewer 빠른 시작 가이드

## 🚨 중요: 가상환경 활성화 필수!

이 프로젝트는 Python 가상환경을 사용합니다. 모든 명령어는 **가상환경이 활성화된 상태**에서 실행해야 합니다.

## 1. 가상환경 활성화

```bash
# 프로젝트 디렉토리로 이동
cd /Users/blockmeta/Desktop/blockmeta/project/tools/hwp-viewer

# 가상환경 활성화
source venv/bin/activate

# 활성화 확인 (프롬프트에 (venv)가 표시됨)
(venv) blockmeta@Mac hwp-viewer %
```

## 2. API 서버 실행

### 방법 1: 직접 실행 (권장)
```bash
# 가상환경 활성화 후
source venv/bin/activate

# 서버 실행
uvicorn api.app:app --reload
```

### 방법 2: 스크립트 사용
```bash
# 실행 스크립트 사용 (가상환경 자동 활성화)
./run_server.sh
```

서버가 실행되면:
- API 문서: http://localhost:8123/docs
- 헬스 체크: http://localhost:8123/health

## 3. CLI 사용

```bash
# 가상환경 활성화 필수!
source venv/bin/activate

# 도움말
python cli/hwp_cli.py --help

# 텍스트 추출
python cli/hwp_cli.py extract sample.hwp

# 파일 정보
python cli/hwp_cli.py info sample.hwp
```

## 4. Python 코드에서 사용

```python
# 가상환경에서 Python 실행
source venv/bin/activate
python

# Python 코드
from hwp_viewer import HWPParser

parser = HWPParser()
text = parser.extract_text("document.hwp")
print(text)
```

## 5. 문제 해결

### "ModuleNotFoundError: No module named 'olefile'" 오류
👉 **원인**: 가상환경을 활성화하지 않고 실행
👉 **해결**: `source venv/bin/activate` 실행 후 다시 시도

### 패키지 설치 확인
```bash
# 가상환경 활성화 후
source venv/bin/activate

# 설치된 패키지 확인
pip list

# 필요시 재설치
pip install -r requirements.txt
```

## 6. 가상환경 비활성화

작업이 끝나면:
```bash
deactivate
```

## 💡 팁

1. **항상 가상환경 활성화 확인**: 프롬프트에 `(venv)` 표시 확인
2. **VS Code 사용 시**: Python 인터프리터를 `venv/bin/python`으로 설정
3. **새 터미널 열 때마다**: `source venv/bin/activate` 실행 필요

## 📝 요약 체크리스트

- [ ] 프로젝트 디렉토리로 이동
- [ ] `source venv/bin/activate` 실행
- [ ] 프롬프트에 `(venv)` 표시 확인
- [ ] 원하는 명령 실행 (uvicorn, python 등)
- [ ] 작업 완료 후 `deactivate`