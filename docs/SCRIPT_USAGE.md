# 🚀 ODIN-AI 실행 스크립트 가이드

## 📋 스크립트 목록

### 1. `run.sh` - 메인 실행 스크립트
모든 서비스를 관리하는 통합 스크립트입니다.

```bash
# 실행 권한 부여 (최초 1회)
chmod +x run.sh

# 전체 시스템 시작
./run.sh start

# 시스템 중지
./run.sh stop

# 시스템 재시작
./run.sh restart

# 상태 확인
./run.sh status

# 개발 모드 (실시간 로그)
./run.sh dev

# 배치 작업 실행
./run.sh batch
./run.sh batch --test    # 테스트 모드
./run.sh batch --init    # DB 초기화 포함

# 테스트 실행
./run.sh test

# 로그 확인
./run.sh logs            # 모든 로그
./run.sh logs --backend  # 백엔드만
./run.sh logs --frontend # 프론트엔드만

# 초기 설정
./run.sh setup

# 클린업
./run.sh clean           # 캐시 정리
./run.sh clean --logs    # 로그도 삭제
```

### 2. `setup.sh` - 초기 설정 스크립트
프로젝트 초기 설정을 자동화합니다.

```bash
# 실행 권한 부여 (최초 1회)
chmod +x setup.sh

# 초기 설정 실행
./setup.sh
```

**수행 작업:**
- ✅ OS 확인 (macOS/Linux)
- ✅ 필수 소프트웨어 확인 (Python, Node.js, PostgreSQL, Redis)
- ✅ Python 가상환경 생성
- ✅ Python/Node 패키지 설치
- ✅ 환경 변수 파일 생성 (.env)
- ✅ 디렉토리 구조 생성
- ✅ 데이터베이스 설정
- ✅ Git hooks 설정

### 3. `quick-start.sh` - 빠른 시작
별도 터미널에서 백엔드와 프론트엔드를 동시에 실행합니다.

```bash
# 실행 권한 부여 (최초 1회)
chmod +x quick-start.sh

# 빠른 시작
./quick-start.sh
```

**특징:**
- 새 터미널 창에서 백엔드/프론트엔드 각각 실행
- 자동으로 브라우저 열기
- 실시간 로그 확인 가능

---

## 🎯 사용 시나리오

### 📌 처음 시작하는 경우
```bash
# 1. 초기 설정
./setup.sh

# 2. 환경 변수 설정
vi .env  # API 키 입력

# 3. 시스템 시작
./run.sh start

# 4. 브라우저에서 접속
# http://localhost:3000
```

### 📌 개발 작업
```bash
# 개발 모드로 실행 (hot-reload)
./run.sh dev

# 또는 빠른 시작 (별도 터미널)
./quick-start.sh
```

### 📌 배치 작업
```bash
# 일반 배치 실행
./run.sh batch

# DB 초기화 후 배치
./run.sh batch --init

# 테스트 모드
./run.sh batch --test
```

### 📌 문제 해결
```bash
# 상태 확인
./run.sh status

# 로그 확인
./run.sh logs

# 시스템 재시작
./run.sh restart

# 클린업 후 재시작
./run.sh clean
./run.sh start
```

---

## 🔧 환경 변수 설정

`.env` 파일에 다음 항목들을 설정해야 합니다:

```bash
# 필수 설정
SECRET_KEY=<자동생성됨>
DATABASE_URL=postgresql://<user>@localhost:5432/odin_db

# API 키 (필수)
DATA_SERVICE_KEY=<공공데이터포털 API키>
OPENAI_API_KEY=<OpenAI API키>

# 선택 설정
REDIS_URL=redis://localhost:6379
DEBUG=False
LOG_LEVEL=INFO

# 이메일 설정 (배치 리포트용)
EMAIL_ENABLED=true
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com
EMAIL_TO=recipient@example.com
```

---

## 📊 시스템 구성

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend   │────▶│  PostgreSQL │
│  (Port 3000)│     │  (Port 8000)│     │  (Port 5432)│
└─────────────┘     └─────────────┘     └─────────────┘
                            │
                            ▼
                    ┌─────────────┐
                    │    Redis    │
                    │  (Port 6379)│
                    └─────────────┘
```

---

## 🚨 트러블슈팅

### 포트가 이미 사용 중인 경우
```bash
# 포트 사용 프로세스 확인
lsof -i :3000  # 프론트엔드
lsof -i :8000  # 백엔드

# 강제 종료
./run.sh stop
```

### PostgreSQL 연결 실패
```bash
# PostgreSQL 상태 확인
pg_isready

# PostgreSQL 시작 (macOS)
brew services start postgresql@15

# PostgreSQL 시작 (Linux)
sudo systemctl start postgresql
```

### Redis 연결 실패 (선택사항)
```bash
# Redis 시작 (macOS)
brew services start redis

# Redis 시작 (Linux)
sudo systemctl start redis
```

### 패키지 설치 문제
```bash
# Python 패키지 재설치
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Node 패키지 재설치
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

## 💡 팁

### tmux 사용 (권장)
```bash
# tmux 설치
brew install tmux  # macOS
apt install tmux   # Linux

# 개발 모드 실행 시 tmux 자동 사용
./run.sh dev
```

### 로그 실시간 모니터링
```bash
# 모든 로그 동시 확인
tail -f logs/*.log

# 특정 로그만 확인
tail -f logs/backend.log
tail -f logs/frontend.log
```

### 성능 모니터링
```bash
# 시스템 리소스 확인
htop  # 또는 top

# PostgreSQL 쿼리 모니터링
psql -d odin_db -c "SELECT * FROM pg_stat_activity;"
```

---

## 📝 주의사항

1. **환경 변수**: `.env` 파일의 API 키를 반드시 설정
2. **Python 버전**: Python 3.8 이상 필요
3. **Node.js 버전**: Node.js 14 이상 필요
4. **PostgreSQL**: 15 버전 권장
5. **포트**: 3000, 8000, 5432 포트가 사용 가능해야 함

---

## 📞 문제 발생 시

1. 로그 확인: `./run.sh logs`
2. 상태 확인: `./run.sh status`
3. 클린 재시작: `./run.sh clean && ./run.sh start`
4. GitHub Issues에 문제 제보