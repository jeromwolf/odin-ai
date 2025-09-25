# 🏗️ ODIN-AI 시스템 아키텍처 설계

> 작성일: 2025-09-25
> 주제: 배치/알림/웹 프로세스 분리 전략

## 📊 아키텍처 옵션 비교

### Option 1: 2개 프로세스 (배치+알림 통합)
```
[배치 프로세스]                    [웹 서버]
├─ 데이터 수집                     ├─ FastAPI
├─ 문서 처리                       ├─ React Frontend
├─ DB 저장                         └─ API 제공
└─ 알림 처리 ←── 문제: 책임 과다
```

### Option 2: 3개 프로세스 (완전 분리) ⭐ 추천
```
[배치 프로세스]    [알림 서비스]    [웹 서버]
├─ 데이터 수집      ├─ 매칭 엔진     ├─ FastAPI
├─ 문서 처리        ├─ 발송 큐       ├─ React
├─ DB 저장          └─ 채널 관리     └─ API
└─ 이벤트 발행 ───→ 이벤트 구독
```

## 🎯 추천: 3개 프로세스 분리

### 이유:

**1. 단일 책임 원칙 (SRP)**
- 배치: 데이터 수집/처리만
- 알림: 매칭/발송만
- 웹: API 서비스만

**2. 독립적 스케일링**
- 배치: 1일 1-2회 실행
- 알림: 실시간 또는 주기적
- 웹: 24시간 상시 운영

**3. 장애 격리**
- 알림 실패해도 배치는 정상
- 배치 실패해도 웹은 정상
- 각각 독립적으로 재시작 가능

**4. 유지보수성**
- 알림 로직 변경 시 배치 영향 없음
- 각 서비스 독립 배포 가능
- 명확한 경계와 인터페이스

## 🔄 제안하는 아키텍처

### 1. 이벤트 기반 느슨한 결합
```python
# 배치 완료 후 이벤트 발행
class BatchProcessor:
    def complete_batch(self):
        # 데이터 처리 완료
        self.save_to_database()

        # 이벤트 발행 (Redis Pub/Sub 또는 DB Queue)
        event = {
            "type": "BATCH_COMPLETED",
            "timestamp": datetime.now(),
            "stats": {
                "new_bids": 45,
                "updated_bids": 12
            },
            "bid_ids": [...]
        }
        self.publish_event(event)
```

### 2. 메시지 큐 활용 (Redis/RabbitMQ)
```yaml
Redis Channels:
  - batch:completed     # 배치 완료 알림
  - alert:trigger       # 알림 트리거
  - alert:result        # 알림 결과

Database Queue Tables:
  - event_queue         # 이벤트 큐
  - alert_queue         # 알림 대기열
  - process_status      # 프로세스 상태
```

### 3. 프로세스별 책임

#### A. 배치 프로세스 (`batch_service.py`)
```python
# 실행: 매일 09:00, 18:00
class BatchService:
    def run(self):
        # 1. 데이터 수집
        new_bids = self.collect_from_api()

        # 2. 문서 처리
        processed = self.process_documents(new_bids)

        # 3. DB 저장
        self.save_to_db(processed)

        # 4. 완료 이벤트 발행
        self.publish_event({
            "type": "BATCH_COMPLETED",
            "new_bid_ids": [bid.id for bid in new_bids],
            "timestamp": datetime.now()
        })
```

#### B. 알림 서비스 (`alert_service.py`)
```python
# 실행: 상시 대기 (이벤트 리스너)
class AlertService:
    def __init__(self):
        self.subscribe_to_events()

    def on_batch_completed(self, event):
        # 1. 새 입찰 조회
        new_bids = self.get_new_bids(event['new_bid_ids'])

        # 2. 알림 규칙 매칭
        matches = self.match_with_rules(new_bids)

        # 3. 알림 큐 생성
        self.queue_alerts(matches)

        # 4. 발송 처리
        self.process_alert_queue()

    def run_scheduled_digests(self):
        # 일일/주간 다이제스트 처리
        pass
```

#### C. 웹 서버 (`web_service.py`)
```python
# 실행: 24시간 상시
@app.get("/api/process/status")
async def get_process_status():
    return {
        "batch": check_batch_status(),
        "alert": check_alert_status(),
        "web": "running"
    }

@app.post("/api/alerts/rules")
async def create_alert_rule(rule: AlertRule):
    # 알림 규칙 생성 (DB만 수정)
    return save_alert_rule(rule)
```

## 📁 디렉토리 구조

```
odin-ai/
├── services/                  # 독립 서비스들
│   ├── batch/                # 배치 서비스
│   │   ├── main.py
│   │   ├── collectors/
│   │   ├── processors/
│   │   └── requirements.txt
│   │
│   ├── alert/                # 알림 서비스
│   │   ├── main.py
│   │   ├── matcher.py
│   │   ├── sender.py
│   │   └── requirements.txt
│   │
│   └── web/                  # 웹 서비스
│       ├── main.py
│       ├── api/
│       └── requirements.txt
│
├── shared/                   # 공유 모듈
│   ├── database/            # DB 모델
│   ├── events/              # 이벤트 시스템
│   └── utils/               # 공통 유틸
│
└── docker-compose.yml        # 전체 오케스트레이션
```

## 🐳 Docker Compose 구성

```yaml
version: '3.8'

services:
  # PostgreSQL
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: odin_db
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis (이벤트 버스 + 캐시)
  redis:
    image: redis:7
    ports:
      - "6379:6379"

  # 배치 서비스 (크론으로 실행)
  batch:
    build: ./services/batch
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://...
      REDIS_URL: redis://redis:6379
    volumes:
      - ./storage:/app/storage

  # 알림 서비스 (상시 실행)
  alert:
    build: ./services/alert
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://...
      REDIS_URL: redis://redis:6379
      EMAIL_HOST: smtp.gmail.com
      SMS_API_KEY: ...

  # 웹 서비스 (API + Frontend)
  web:
    build: ./services/web
    ports:
      - "8000:8000"
      - "3000:3000"
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://...
      REDIS_URL: redis://redis:6379

  # 스케줄러 (배치 실행 관리)
  scheduler:
    image: mcuadros/ofelia:latest
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./ofelia.ini:/etc/ofelia/config.ini

volumes:
  postgres_data:
```

## 🚦 프로세스 관리

### 1. Systemd 서비스 (Production)
```ini
# /etc/systemd/system/odin-batch.service
[Unit]
Description=ODIN Batch Service
After=postgresql.service

[Service]
Type=simple
User=odin
WorkingDirectory=/opt/odin/services/batch
ExecStart=/usr/bin/python3 main.py
Restart=on-failure

# /etc/systemd/system/odin-alert.service
[Unit]
Description=ODIN Alert Service
After=postgresql.service redis.service

[Service]
Type=simple
User=odin
WorkingDirectory=/opt/odin/services/alert
ExecStart=/usr/bin/python3 main.py
Restart=always
```

### 2. Supervisor 설정 (Alternative)
```ini
[program:odin-batch]
command=python3 main.py
directory=/opt/odin/services/batch
autostart=false
autorestart=false

[program:odin-alert]
command=python3 main.py
directory=/opt/odin/services/alert
autostart=true
autorestart=true

[program:odin-web]
command=uvicorn main:app --host 0.0.0.0 --port 8000
directory=/opt/odin/services/web
autostart=true
autorestart=true
```

## 📊 모니터링

### 상태 체크 API
```python
# GET /api/health
{
    "status": "healthy",
    "services": {
        "batch": {
            "status": "idle",
            "last_run": "2025-09-25T09:00:00",
            "next_run": "2025-09-25T18:00:00"
        },
        "alert": {
            "status": "running",
            "queue_size": 5,
            "processing_rate": "12/min"
        },
        "web": {
            "status": "running",
            "uptime": "5d 12h 30m"
        }
    }
}
```

## 💡 장점 정리

### 3개 프로세스 분리의 장점:

1. **확장성**
   - 알림이 많아지면 알림 서비스만 스케일 업
   - 배치는 필요시에만 실행

2. **안정성**
   - 한 서비스 장애가 전체에 영향 없음
   - 독립적 재시작/배포

3. **개발 효율성**
   - 팀별로 서비스 담당 가능
   - 명확한 API 경계

4. **성능**
   - 알림 처리가 배치를 지연시키지 않음
   - 각 서비스 최적화 가능

5. **유연성**
   - 알림 서비스를 다른 이벤트에도 활용 가능
   - 향후 실시간 입찰 모니터링 추가 시 용이

## 🎯 구현 순서

### Phase 1: 기본 분리 (1주)
1. 배치 프로세스 리팩토링 (이벤트 발행 추가)
2. 알림 서비스 뼈대 구축
3. Redis 이벤트 버스 구현

### Phase 2: 알림 서비스 구현 (2주)
1. 이벤트 리스너
2. 매칭 엔진
3. 발송 시스템

### Phase 3: 통합 및 최적화 (1주)
1. Docker Compose 설정
2. 모니터링 대시보드
3. 로그 통합

## 📝 결론

**3개 프로세스 분리를 강력 추천합니다.**

- 초기 구현은 조금 복잡하지만
- 장기적으로 유지보수와 확장이 훨씬 용이
- 마이크로서비스 아키텍처의 장점 활용
- 각 서비스가 단순하고 명확한 책임

특히 알림 서비스는 향후 다양한 이벤트 소스(실시간 크롤링, 사용자 액션 등)와 연동될 가능성이 크므로, 독립 서비스로 분리하는 것이 현명합니다.