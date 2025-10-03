# 관리자 웹 시스템 기술 스택

> ODIN-AI 관리자 대시보드 기술 스택 선정 및 근거
> 작성일: 2025-10-02

---

## 📚 목차
1. [기술 스택 개요](#1-기술-스택-개요)
2. [백엔드 기술 스택](#2-백엔드-기술-스택)
3. [프론트엔드 기술 스택](#3-프론트엔드-기술-스택)
4. [모니터링 및 로깅](#4-모니터링-및-로깅)
5. [배포 및 인프라](#5-배포-및-인프라)
6. [개발 도구](#6-개발-도구)
7. [의존성 목록](#7-의존성-목록)

---

## 1. 기술 스택 개요

### 1.1 선정 기준
- ✅ **기존 프로젝트와의 일관성** - 사용자 웹과 동일한 스택 사용
- ✅ **빠른 개발 속도** - 이미 익숙한 기술 활용
- ✅ **확장성** - 향후 기능 추가 용이
- ✅ **안정성** - 검증된 라이브러리 사용

### 1.2 아키텍처 다이어그램
```
┌─────────────────────────────────────────────────────────┐
│                   관리자 웹 브라우저                     │
│                  (React + TypeScript)                    │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/HTTPS
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Nginx (리버스 프록시)                       │
│          /admin → React App (Port 3001)                 │
│          /api/admin → FastAPI (Port 8000)               │
└────────────────────┬────────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
┌──────────────────┐  ┌──────────────────────┐
│  React Frontend  │  │  FastAPI Backend     │
│  (Port 3001)     │  │  (Port 8000)         │
│                  │  │                      │
│  - Material-UI   │  │  - Admin APIs        │
│  - Recharts      │  │  - Batch Control     │
│  - React Query   │  │  - Metrics           │
└──────────────────┘  └─────────┬────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  PostgreSQL (5432)    │
                    │  - Admin Tables       │
                    │  - User Tables        │
                    │  - Batch Logs         │
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Redis (6379)        │
                    │   - Metrics Cache     │
                    │   - Session Store     │
                    └───────────────────────┘
```

---

## 2. 백엔드 기술 스택

### 2.1 웹 프레임워크

#### FastAPI (Python 3.11+)
- **버전**: 0.104.0+
- **선정 이유**:
  - 기존 사용자 웹과 동일한 프레임워크
  - 빠른 성능 (Starlette 기반)
  - 자동 API 문서 생성 (Swagger UI)
  - 타입 힌트 기반 데이터 검증 (Pydantic)
  - 비동기 지원 (async/await)

```python
# 예시 코드
from fastapi import FastAPI, Depends
from typing import List

app = FastAPI(title="ODIN-AI Admin API")

@app.get("/api/admin/batch/executions", response_model=List[BatchExecution])
async def get_batch_executions(
    skip: int = 0,
    limit: int = 20,
    admin = Depends(get_current_admin_user)
):
    return await BatchService.get_executions(skip, limit)
```

### 2.2 데이터베이스

#### PostgreSQL 14+
- **버전**: 14.10+
- **선정 이유**:
  - 기존 프로젝트 사용 중
  - JSONB 지원 (메타데이터 저장)
  - 강력한 인덱싱 (GIN, BRIN)
  - 트랜잭션 안정성
  - 뷰(View) 및 함수(Function) 지원

```sql
-- JSONB 활용 예시
SELECT * FROM batch_detail_logs
WHERE context @> '{"file_type": "hwp"}';
```

#### psycopg2 (PostgreSQL 어댑터)
- **버전**: 2.9.9+
- **용도**: Python에서 PostgreSQL 연결

### 2.3 캐싱 및 세션 관리

#### Redis 7+
- **버전**: 7.2+
- **용도**:
  - 시스템 메트릭 임시 저장 (1분마다 수집)
  - API 응답 캐싱 (통계 데이터)
  - 관리자 세션 저장
  - 실시간 데이터 Pub/Sub (선택사항)

```python
# Redis 캐싱 예시
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 메트릭 캐싱 (5분 TTL)
r.setex('metric:cpu:latest', 300, cpu_percent)

# 통계 캐싱 (1시간 TTL)
r.setex('stats:batch:daily', 3600, json.dumps(stats))
```

### 2.4 백그라운드 작업

#### Celery (선택사항)
- **버전**: 5.3+
- **용도**:
  - 배치 수동 실행
  - 로그 파일 압축 및 다운로드
  - 데이터베이스 백업

```python
# Celery 태스크 예시
from celery import Celery

app = Celery('admin_tasks', broker='redis://localhost:6379/0')

@app.task
def run_batch_manual(batch_type: str):
    # 배치 실행 로직
    return {"status": "success"}
```

### 2.5 인증 및 보안

#### JWT (JSON Web Tokens)
- **라이브러리**: `python-jose[cryptography]`
- **용도**: 관리자 인증 토큰

```python
from jose import jwt

def create_admin_token(admin_id: int):
    payload = {
        "sub": str(admin_id),
        "role": "admin",
        "exp": datetime.utcnow() + timedelta(hours=8)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

#### Passlib (비밀번호 해싱)
- **라이브러리**: `passlib[bcrypt]`
- **알고리즘**: bcrypt

### 2.6 데이터 검증

#### Pydantic
- **버전**: 2.5+
- **용도**: API 요청/응답 검증

```python
from pydantic import BaseModel, Field

class BatchExecutionResponse(BaseModel):
    id: int
    batch_type: str
    status: str
    start_time: datetime
    duration_seconds: int | None
    success_items: int
    failed_items: int
```

---

## 3. 프론트엔드 기술 스택

### 3.1 UI 프레임워크

#### React 18+
- **버전**: 18.2+
- **선정 이유**:
  - 기존 사용자 웹과 동일
  - 컴포넌트 재사용성
  - 풍부한 생태계
  - Virtual DOM 성능

```tsx
// 관리자 대시보드 컴포넌트 예시
import React from 'react';

const AdminDashboard: React.FC = () => {
  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12} md={3}>
          <StatusCard title="배치 상태" value={batchStatus} />
        </Grid>
      </Grid>
    </Box>
  );
};
```

#### TypeScript 5+
- **버전**: 5.0+
- **선정 이유**:
  - 타입 안정성
  - 코드 자동완성
  - 리팩토링 용이

```typescript
// 타입 정의 예시
interface BatchExecution {
  id: number;
  batch_type: 'collector' | 'downloader' | 'processor' | 'notification';
  status: 'running' | 'success' | 'failed';
  start_time: string;
  duration_seconds: number | null;
}
```

### 3.2 UI 컴포넌트 라이브러리

#### Material-UI (MUI) v5
- **버전**: 5.15+
- **선정 이유**:
  - 기존 사용자 웹과 일관성
  - 풍부한 컴포넌트
  - 반응형 디자인 지원
  - 테마 커스터마이징 쉬움

```tsx
import {
  Box, Grid, Card, CardContent, Typography,
  Table, TableBody, TableCell, TableHead, TableRow
} from '@mui/material';

// Material-UI 컴포넌트 활용
<Card elevation={3}>
  <CardContent>
    <Typography variant="h6">배치 실행 이력</Typography>
    <Table>
      {/* ... */}
    </Table>
  </CardContent>
</Card>
```

### 3.3 차트 라이브러리

#### Recharts
- **버전**: 2.10+
- **선정 이유**:
  - React 친화적 (컴포넌트 기반)
  - 다양한 차트 타입 지원
  - 반응형 차트
  - 커스터마이징 쉬움

```tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

<LineChart width={600} height={300} data={metricsData}>
  <CartesianGrid strokeDasharray="3 3" />
  <XAxis dataKey="time" />
  <YAxis />
  <Tooltip />
  <Line type="monotone" dataKey="cpu" stroke="#8884d8" />
  <Line type="monotone" dataKey="memory" stroke="#82ca9d" />
</LineChart>
```

**대안 고려**: Chart.js (더 많은 차트 타입 지원)

### 3.4 상태 관리

#### React Query (TanStack Query) v5
- **버전**: 5.0+
- **용도**:
  - 서버 상태 관리
  - 자동 캐싱 및 리페칭
  - 낙관적 업데이트
  - 무한 스크롤

```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// 배치 실행 이력 조회
const { data, isLoading } = useQuery({
  queryKey: ['batch-executions', filters],
  queryFn: () => fetchBatchExecutions(filters),
  staleTime: 5000, // 5초 캐시
});

// 배치 수동 실행
const mutation = useMutation({
  mutationFn: (batchType: string) => runBatchManual(batchType),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['batch-executions'] });
  },
});
```

#### Zustand (선택사항)
- **용도**: 클라이언트 전역 상태 (사이드바 열림/닫힘 등)

### 3.5 라우팅

#### React Router v6
- **버전**: 6.20+
- **용도**: 페이지 라우팅

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';

<BrowserRouter>
  <Routes>
    <Route path="/admin" element={<AdminLayout />}>
      <Route index element={<Dashboard />} />
      <Route path="batch" element={<BatchMonitoring />} />
      <Route path="system" element={<SystemMonitoring />} />
      <Route path="users" element={<UserManagement />} />
      <Route path="logs" element={<LogViewer />} />
      <Route path="statistics" element={<Statistics />} />
    </Route>
  </Routes>
</BrowserRouter>
```

### 3.6 HTTP 클라이언트

#### Axios
- **버전**: 1.6+
- **용도**: API 요청

```typescript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api/admin',
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터 (JWT 토큰 추가)
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### 3.7 날짜/시간 처리

#### date-fns
- **버전**: 3.0+
- **용도**: 날짜 포맷팅 및 계산

```typescript
import { format, formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';

// 날짜 포맷팅
format(new Date(), 'yyyy-MM-dd HH:mm:ss');

// 상대 시간
formatDistanceToNow(new Date('2025-10-02 18:00:00'), {
  addSuffix: true,
  locale: ko
}); // "2시간 전"
```

---

## 4. 모니터링 및 로깅

### 4.1 로깅

#### Loguru (Python)
- **버전**: 0.7+
- **용도**: 구조화된 로깅

```python
from loguru import logger

# 로그 파일 설정
logger.add(
    "logs/admin_{time}.log",
    rotation="10 MB",
    retention="30 days",
    level="INFO"
)

# 사용
logger.info("관리자 로그인", admin_id=admin.id, ip=request.client.host)
logger.error("배치 실행 실패", batch_type="collector", error=str(e))
```

### 4.2 시스템 메트릭 수집

#### psutil (Python)
- **버전**: 5.9+
- **용도**: CPU, 메모리, 디스크 사용률 수집

```python
import psutil

def collect_system_metrics():
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
    }
```

### 4.3 성능 모니터링 (선택사항)

#### Prometheus + Grafana
- **용도**: 메트릭 수집 및 시각화
- **설치**: Docker Compose

```yaml
# docker-compose.yml
version: '3'
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

---

## 5. 배포 및 인프라

### 5.1 컨테이너화

#### Docker
- **버전**: 24.0+
- **용도**: 애플리케이션 컨테이너화

```dockerfile
# Dockerfile.admin-frontend
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE 3001

CMD ["npm", "start"]
```

```dockerfile
# Dockerfile.admin-backend (기존 backend 재사용)
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  admin-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.admin
    ports:
      - "3001:3001"
    environment:
      - REACT_APP_API_URL=http://localhost:8000

  admin-backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/odin_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:14
    environment:
      POSTGRES_DB: odin_db
      POSTGRES_USER: blockmeta
      POSTGRES_PASSWORD: password
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

### 5.2 웹 서버

#### Nginx
- **버전**: 1.24+
- **용도**: 리버스 프록시, SSL 종료

```nginx
# nginx.conf
server {
    listen 80;
    server_name admin.odin-ai.com;

    # 관리자 프론트엔드
    location /admin {
        proxy_pass http://admin-frontend:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 관리자 API
    location /api/admin {
        proxy_pass http://admin-backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 5.3 환경 변수 관리

#### .env 파일
```bash
# Backend
DATABASE_URL=postgresql://blockmeta@localhost:5432/odin_db
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
ADMIN_JWT_SECRET=admin-jwt-secret-key

# Frontend
REACT_APP_ADMIN_API_URL=https://api.odin-ai.com/admin
REACT_APP_ADMIN_WS_URL=wss://api.odin-ai.com/admin/ws

# 메트릭 수집
METRIC_COLLECTION_INTERVAL=60  # 초

# 로그
LOG_LEVEL=INFO
LOG_FILE_MAX_SIZE=10MB
LOG_RETENTION_DAYS=30
```

---

## 6. 개발 도구

### 6.1 코드 품질

#### ESLint (JavaScript/TypeScript)
```json
{
  "extends": [
    "react-app",
    "plugin:@typescript-eslint/recommended"
  ],
  "rules": {
    "no-console": "warn",
    "@typescript-eslint/no-unused-vars": "error"
  }
}
```

#### Black (Python)
```python
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py311']
```

### 6.2 테스팅

#### Jest + React Testing Library (프론트엔드)
```typescript
import { render, screen } from '@testing-library/react';
import Dashboard from './Dashboard';

test('대시보드가 렌더링됨', () => {
  render(<Dashboard />);
  expect(screen.getByText('배치 상태')).toBeInTheDocument();
});
```

#### pytest (백엔드)
```python
def test_get_batch_executions():
    response = client.get("/api/admin/batch/executions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

### 6.3 버전 관리

#### Git
- **브랜치 전략**: Git Flow
  - `main` - 프로덕션
  - `develop` - 개발
  - `feature/admin-dashboard` - 관리자 웹 개발

---

## 7. 의존성 목록

### 7.1 백엔드 (requirements-admin.txt)
```txt
# 웹 프레임워크
fastapi==0.104.0
uvicorn[standard]==0.24.0
pydantic==2.5.0

# 데이터베이스
psycopg2-binary==2.9.9
sqlalchemy==2.0.23

# 캐싱
redis==5.0.1

# 인증
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# 로깅
loguru==0.7.2

# 시스템 모니터링
psutil==5.9.6

# 백그라운드 작업 (선택사항)
celery==5.3.4

# 유틸리티
python-dotenv==1.0.0
python-multipart==0.0.6
```

### 7.2 프론트엔드 (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.0.0",
    "@mui/material": "^5.15.0",
    "@mui/icons-material": "^5.15.0",
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0",
    "recharts": "^2.10.0",
    "@tanstack/react-query": "^5.0.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.0",
    "date-fns": "^3.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/node": "^20.0.0",
    "eslint": "^8.55.0",
    "@typescript-eslint/eslint-plugin": "^6.15.0",
    "jest": "^29.7.0",
    "@testing-library/react": "^14.1.0"
  }
}
```

---

## 8. 성능 최적화 전략

### 8.1 프론트엔드
- **Code Splitting**: React.lazy() 활용
- **메모이제이션**: useMemo, useCallback
- **가상 스크롤**: react-window (대량 로그 조회 시)
- **이미지 최적화**: WebP 포맷

### 8.2 백엔드
- **데이터베이스 쿼리 최적화**: N+1 쿼리 방지, 인덱스 활용
- **응답 캐싱**: Redis 활용
- **비동기 처리**: async/await
- **페이지네이션**: 대량 데이터 분할 조회

### 8.3 네트워크
- **HTTP/2**: Nginx 설정
- **Gzip 압축**: 정적 파일 압축
- **CDN**: 정적 리소스 배포 (선택사항)

---

## 9. 보안 고려사항

### 9.1 인증 및 권한
- JWT 토큰 만료 시간: 8시간
- Refresh 토큰 사용
- 관리자 역할(Role) 검증

### 9.2 데이터 보호
- HTTPS 강제
- SQL Injection 방지 (Parameterized Query)
- XSS 방지 (HTML 이스케이프)
- CSRF 토큰

### 9.3 로깅
- 개인정보 마스킹
- 민감 정보 제외 (비밀번호, 토큰)

---

## 10. 다음 단계

### Phase 2: 백엔드 API 구현
- FastAPI 프로젝트 초기화
- 데이터베이스 마이그레이션 실행
- Admin API 엔드포인트 개발

### Phase 3: 프론트엔드 구현
- React 프로젝트 초기화
- Material-UI 테마 설정
- 관리자 대시보드 컴포넌트 개발

---

## 📝 기술 스택 요약

| 분류 | 기술 | 버전 | 용도 |
|------|------|------|------|
| **백엔드** | FastAPI | 0.104+ | 웹 프레임워크 |
| | PostgreSQL | 14+ | 데이터베이스 |
| | Redis | 7+ | 캐싱/세션 |
| | Loguru | 0.7+ | 로깅 |
| **프론트엔드** | React | 18.2+ | UI 프레임워크 |
| | TypeScript | 5.0+ | 타입 시스템 |
| | Material-UI | 5.15+ | UI 컴포넌트 |
| | Recharts | 2.10+ | 차트 |
| | React Query | 5.0+ | 상태 관리 |
| **배포** | Docker | 24+ | 컨테이너화 |
| | Nginx | 1.24+ | 웹 서버 |

**선정 근거**: 기존 프로젝트와 일관성 유지, 빠른 개발, 검증된 안정성

---

*이 문서는 개발 진행에 따라 업데이트됩니다.*
