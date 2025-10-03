# 관리자 웹 시스템 개발 태스크

> ODIN-AI 시스템 모니터링 및 관리를 위한 관리자 전용 웹 대시보드
> **연계 문서**: `/docs/TASK_MANAGEMENT.md` - Phase 1 확장

---

## 📊 시스템 구성 현황

### 현재 운영 중인 3가지 시스템
1. **배치 프로그램** (`batch/production_batch.py`)
   - 공공데이터 API 수집
   - HWP/PDF 문서 다운로드 및 처리
   - 일일 3-6회 크론잡 실행

2. **알림 서비스** (`batch/modules/notification_matcher.py`)
   - 사용자 알림 규칙 매칭
   - 이메일 발송
   - 실시간 알림 전송

3. **사용자 웹** (Frontend: React + Backend: FastAPI)
   - 입찰 검색 및 조회
   - 북마크 관리
   - 알림 설정
   - 대시보드

### 신규 추가: 4번째 시스템
4. **관리자 웹** (Admin Dashboard) ⭐ 신규
   - 배치 프로그램 모니터링
   - 시스템 상태 확인
   - 에러 로그 조회
   - 사용자 관리
   - 통계 및 분석

---

## 🎯 Phase 1: 관리자 웹 시스템 설계 및 기획 (1주)

### 1.1 요구사항 정의 및 기능 명세 ✅ **완료**
- [x] **배치 모니터링 요구사항**
  - [x] 실시간 배치 실행 상태 확인
  - [x] 배치 실행 이력 조회 (성공/실패)
  - [x] 배치별 처리 통계 (수집/다운로드/처리 건수)
  - [x] 실행 시간 분석 (평균/최대/최소)
  - [x] 에러 발생 현황 및 상세 로그

- [x] **시스템 상태 모니터링 요구사항**
  - [x] 서버 리소스 사용량 (CPU, Memory, Disk)
  - [x] 데이터베이스 연결 상태
  - [x] API 응답 시간 모니터링
  - [x] 알림 발송 현황

- [x] **사용자 관리 요구사항**
  - [x] 사용자 목록 조회 (가입일, 구독 플랜)
  - [x] 사용자 상세 정보 확인
  - [x] 사용자별 활동 로그
  - [x] 사용자 계정 관리 (활성화/비활성화)

- [x] **통계 및 분석 요구사항**
  - [x] 일별/주별/월별 입찰 수집 통계
  - [x] 카테고리별 분포 차트
  - [x] 사용자 증가 추세
  - [x] 알림 발송 성공률

- [x] **시스템 관리 요구사항**
  - [x] 배치 수동 실행 기능
  - [x] 로그 파일 다운로드
  - [x] 데이터베이스 백업 관리
  - [x] 시스템 설정 변경

**테스트**: ✅ 요구사항 리뷰, 사용자 스토리 검증 완료
**완료 조건**: ✅ 기능 명세서 작성 완료 (`docs/admin/REQUIREMENTS.md`)

---

### 1.2 데이터베이스 스키마 설계 ✅ **완료**
- [x] **배치 실행 로그 테이블**
  ```sql
  CREATE TABLE batch_execution_logs (
      id SERIAL PRIMARY KEY,
      batch_type VARCHAR(50),           -- collector/downloader/processor/notification
      status VARCHAR(20),                -- running/success/failed
      start_time TIMESTAMP,
      end_time TIMESTAMP,
      duration_seconds INTEGER,
      total_items INTEGER,
      success_items INTEGER,
      failed_items INTEGER,
      error_message TEXT,
      created_at TIMESTAMP DEFAULT NOW()
  );
  ```

- [x] **배치 처리 상세 로그 테이블** (batch_detail_logs)
- [x] **시스템 메트릭 테이블** (system_metrics)
  ```sql
  CREATE TABLE system_metrics (
      id SERIAL PRIMARY KEY,
      metric_type VARCHAR(50),          -- cpu/memory/disk/api_response_time
      metric_value FLOAT,
      recorded_at TIMESTAMP DEFAULT NOW()
  );
  ```

- [ ] **관리자 활동 로그 테이블**
  ```sql
  CREATE TABLE admin_activity_logs (
      id SERIAL PRIMARY KEY,
      admin_user_id INTEGER REFERENCES users(id),
      action VARCHAR(100),               -- batch_manual_run/user_deactivate 등
      target_type VARCHAR(50),
      target_id INTEGER,
      details JSONB,
      ip_address VARCHAR(50),
      created_at TIMESTAMP DEFAULT NOW()
  );
  ```

- [ ] **배치 처리 상세 로그 테이블**
  ```sql
  CREATE TABLE batch_detail_logs (
      id SERIAL PRIMARY KEY,
      execution_id INTEGER REFERENCES batch_execution_logs(id),
      log_level VARCHAR(20),            -- INFO/WARNING/ERROR
      message TEXT,
      context JSONB,                     -- 추가 컨텍스트 정보
      created_at TIMESTAMP DEFAULT NOW()
  );
  ```

**테스트**: 스키마 검증, 인덱스 성능 테스트
**완료 조건**: 마이그레이션 스크립트 작성 및 실행

---

### 1.3 화면 설계 (Wireframe)
- [ ] **대시보드 메인 화면**
  - [ ] 시스템 상태 요약 카드 (4개)
    - 배치 실행 상태 (성공/실패/실행중)
    - 오늘 수집된 입찰 건수
    - 활성 사용자 수
    - 시스템 리소스 사용률
  - [ ] 최근 배치 실행 이력 (테이블)
  - [ ] 실시간 에러 알림 (알림 패널)
  - [ ] 시스템 리소스 차트 (라인 차트)

- [ ] **배치 모니터링 화면**
  - [ ] 배치 실행 이력 테이블
    - 필터: 날짜, 배치 타입, 상태
    - 정렬: 실행 시간, 처리 건수
  - [ ] 배치 상세 정보 모달
    - 실행 통계
    - 에러 로그
    - 처리 시간 분석
  - [ ] 수동 실행 버튼 (권한 필요)

- [ ] **시스템 모니터링 화면**
  - [ ] 실시간 메트릭 차트
    - CPU 사용률
    - 메모리 사용률
    - 디스크 사용률
  - [ ] API 응답 시간 차트
  - [ ] 데이터베이스 상태
  - [ ] 알림 발송 현황

- [ ] **사용자 관리 화면**
  - [ ] 사용자 목록 테이블
    - 검색: 이메일, 이름
    - 필터: 구독 플랜, 가입일
  - [ ] 사용자 상세 모달
    - 기본 정보
    - 활동 로그
    - 알림 규칙
    - 북마크 목록
  - [ ] 사용자 관리 액션
    - 계정 활성화/비활성화
    - 구독 플랜 변경
    - 비밀번호 초기화

- [ ] **로그 조회 화면**
  - [ ] 로그 검색 필터
    - 날짜 범위
    - 로그 레벨
    - 키워드 검색
  - [ ] 로그 테이블 (페이지네이션)
  - [ ] 로그 상세 모달
  - [ ] 로그 다운로드 기능

- [ ] **통계 및 분석 화면**
  - [ ] 입찰 수집 통계 차트
    - 일별/주별/월별 추이
    - 카테고리별 분포
  - [ ] 사용자 증가 차트
  - [ ] 알림 발송 통계
  - [ ] 시스템 성능 지표

**테스트**: UI/UX 리뷰, 사용성 테스트
**완료 조건**: Figma 또는 손그림 Wireframe 완성

---

### 1.4 기술 스택 선정
- [ ] **백엔드**
  - [ ] FastAPI (기존과 동일)
  - [ ] PostgreSQL (기존 DB 활용)
  - [ ] Redis (실시간 메트릭 캐싱)
  - [ ] Celery (배치 수동 실행용)

- [ ] **프론트엔드**
  - [ ] React + TypeScript (기존과 동일)
  - [ ] Material-UI (기존과 동일)
  - [ ] Recharts (차트 라이브러리)
  - [ ] React Query (상태 관리)

- [ ] **모니터링 도구**
  - [ ] Prometheus (메트릭 수집)
  - [ ] Grafana (대시보드 - 선택사항)
  - [ ] Loguru (로깅 - 기존)

**테스트**: 기술 스택 검증, POC 구현
**완료 조건**: 기술 스택 문서화 및 승인

---

## 🎯 Phase 2: 관리자 웹 백엔드 API 구현 (2주) ✅ **완료**

### 2.1 배치 모니터링 API ✅
- [x] **배치 실행 이력 조회 API** ✅
  ```python
  GET /api/admin/batch/executions
  - Query params: start_date, end_date, batch_type, status, page, limit
  - Response: { executions: [], total: 100, page: 1 }
  ```
  **구현 파일**: `/backend/api/admin_batch.py:98-194`

- [x] **배치 상세 정보 조회 API** ✅
  ```python
  GET /api/admin/batch/executions/{execution_id}
  - Response: { execution_info, detail_logs, statistics }
  ```
  **구현 파일**: `/backend/api/admin_batch.py:196-291`

- [x] **배치 수동 실행 API** ✅
  ```python
  POST /api/admin/batch/execute
  - Body: { batch_type: "collector", test_mode, date_range }
  - Response: { task_id, status, message }
  ```
  **구현 파일**: `/backend/api/admin_batch.py:378-428`

- [x] **배치 실행 통계 API** ✅
  ```python
  GET /api/admin/batch/statistics
  - Query params: start_date, end_date, batch_type
  - Response: { batch_type, total_executions, success_rate, avg_duration_seconds }
  ```
  **구현 파일**: `/backend/api/admin_batch.py:293-376`

**테스트**: ✅ API 엔드포인트 구현 완료
**완료 조건**: ✅ 4개 API 구현 완료

---

### 2.2 시스템 모니터링 API ✅
- [x] **시스템 메트릭 조회 API** ✅
  ```python
  GET /api/admin/system/metrics
  - Query params: metric_type, start_time, end_time, limit
  - Response: { metrics: [{ metric_type, metric_value, recorded_at }], summary }
  ```
  **구현 파일**: `/backend/api/admin_system.py:81-166`

- [x] **실시간 시스템 상태 API** ✅
  ```python
  GET /api/admin/system/status
  - Response: { cpu_percent, memory_percent, disk_percent, db_status, db_connections }
  ```
  **구현 파일**: `/backend/api/admin_system.py:168-246`
  **사용 라이브러리**: psutil (CPU, Memory, Disk 모니터링)

- [x] **API 성능 통계 API** ✅
  ```python
  GET /api/admin/system/api-performance
  - Query params: start_time, end_time
  - Response: { endpoints: [{ endpoint, avg_response_time, max_response_time, request_count, error_rate }] }
  ```
  **구현 파일**: `/backend/api/admin_system.py:248-310`

- [x] **알림 발송 현황 API** ✅
  ```python
  GET /api/admin/system/notifications/status
  - Query params: start_time, end_time
  - Response: { total_sent, success_count, failed_count, success_rate, failure_reasons }
  ```
  **구현 파일**: `/backend/api/admin_system.py:312-388`

**테스트**: ✅ 메트릭 수집 및 API 구현 완료
**완료 조건**: ✅ 4개 API 구현 완료

---

### 2.3 사용자 관리 API ✅
- [x] **사용자 목록 조회 API** ✅
  ```python
  GET /api/admin/users
  - Query params: search, is_active, page, limit
  - Response: { users: [], total, page }
  ```
  **구현 파일**: `/backend/api/admin_users.py:43-99`

- [x] **사용자 상세 정보 API** ✅
  ```python
  GET /api/admin/users/{user_id}
  - Response: { user, statistics, recent_activity }
  ```
  **구현 파일**: `/backend/api/admin_users.py:101-152`

- [x] **사용자 계정 관리 API** ✅
  ```python
  PATCH /api/admin/users/{user_id}
  - Body: { is_active }
  - Response: { success, message }
  ```
  **구현 파일**: `/backend/api/admin_users.py:154-173`

- [x] **사용자 통계 요약 API** ✅
  ```python
  GET /api/admin/users/statistics/summary
  - Response: { total_users, active_users, inactive_users, new_users_last_30_days }
  ```
  **구현 파일**: `/backend/api/admin_users.py:175-204`

**테스트**: ✅ CRUD 및 통계 API 구현 완료
**완료 조건**: ✅ 4개 API 구현 완료

---

### 2.4 로그 조회 및 분석 API ✅
- [x] **로그 검색 API** ✅
  ```python
  GET /api/admin/logs
  - Query params: start_date, end_date, level, keyword, page, limit
  - Response: { logs: [], total, page }
  ```
  **구현 파일**: `/backend/api/admin_logs.py:37-103`

- [x] **로그 파일 다운로드 API** ✅
  ```python
  GET /api/admin/logs/download/{log_date}
  - Response: ZIP file download (Content-Type: application/zip)
  ```
  **구현 파일**: `/backend/api/admin_logs.py:105-140`
  **사용 라이브러리**: zipfile, io.BytesIO

- [x] **에러 로그 통계 API** ✅
  ```python
  GET /api/admin/logs/errors/statistics
  - Query params: start_date, end_date
  - Response: { top_errors: [{ message, count }], error_trend: [{ date, count }] }
  ```
  **구현 파일**: `/backend/api/admin_logs.py:142-210`

**테스트**: ✅ 로그 검색, 다운로드, 통계 API 구현 완료
**완료 조건**: ✅ 3개 API 구현 완료

---

### 2.5 통계 및 분석 API ✅
- [x] **입찰 수집 통계 API** ✅
  ```python
  GET /api/admin/statistics/bid-collection
  - Query params: start_date, end_date, group_by (day/week/month)
  - Response: { stats: [{ date, total_collected, new_bids, total_amount }], summary }
  ```
  **구현 파일**: `/backend/api/admin_statistics.py:86-139`

- [x] **카테고리별 분포 API** ✅
  ```python
  GET /api/admin/statistics/category-distribution
  - Query params: start_date, end_date
  - Response: { categories: [{ category, count, percentage, total_amount }], total_bids }
  ```
  **구현 파일**: `/backend/api/admin_statistics.py:142-205`

- [x] **사용자 증가 추이 API** ✅
  ```python
  GET /api/admin/statistics/user-growth
  - Query params: start_date, end_date
  - Response: { growth: [{ date, new_users, total_users, active_users }], summary }
  ```
  **구현 파일**: `/backend/api/admin_statistics.py:208-294`

- [x] **알림 발송 통계 API** ✅
  ```python
  GET /api/admin/statistics/notifications
  - Query params: start_date, end_date
  - Response: { stats: [{ date, total_sent, success_count, success_rate }], summary }
  ```
  **구현 파일**: `/backend/api/admin_statistics.py:297-388`

**테스트**: ✅ 통계 계산 및 API 구현 완료
**완료 조건**: ✅ 4개 API 구현 완료

---

### 2.6 관리자 인증 및 권한 관리 ✅
- [x] **관리자 로그인 API** ✅
  ```python
  POST /api/admin/auth/login
  - Body: { email, password }
  - Response: { access_token, token_type, admin_info }
  ```
  **구현 파일**: `/backend/api/admin_auth.py:131-203`
  **보안**: bcrypt 비밀번호 검증, JWT 토큰 발급

- [x] **관리자 권한 검증 Dependency** ✅
  ```python
  async def get_current_admin(credentials: HTTPAuthorizationCredentials)
  - JWT 토큰 검증
  - 관리자 권한 확인 (admin, super_admin)
  ```
  **구현 파일**: `/backend/api/admin_auth.py:71-117`

- [x] **관리자 활동 로그 기록** ✅
  ```python
  # 관리자 로그인/로그아웃 활동 자동 로깅
  - admin_activity_logs 테이블에 INSERT
  - 로그: 로그인, 로그아웃, 배치 수동 실행 등
  ```
  **구현 파일**: `/backend/api/admin_auth.py:195-253`

- [x] **로그아웃 API** ✅
  ```python
  POST /api/admin/auth/logout
  - 활동 로그 기록 후 응답
  ```
  **구현 파일**: `/backend/api/admin_auth.py:206-229`

- [x] **현재 관리자 정보 API** ✅
  ```python
  GET /api/admin/auth/me
  - Response: { id, email, username, role, last_login_at }
  ```
  **구현 파일**: `/backend/api/admin_auth.py:232-262`

- [x] **관리자 활동 로그 조회 API** ✅
  ```python
  GET /api/admin/auth/activity-logs
  - Query params: limit
  - Response: { logs: [{ activity_type, description, created_at }], total }
  ```
  **구현 파일**: `/backend/api/admin_auth.py:265-307`

**테스트**: ✅ 권한 검증, JWT 인증, 로그 기록 완료
**완료 조건**: ✅ 관리자 인증 시스템 완성

---

### 2.7 main.py 라우터 등록 ✅
- [x] **모든 관리자 API 라우터 등록** ✅
  ```python
  # 6개 관리자 API 라우터 등록
  - admin_auth_router
  - admin_batch_router
  - admin_system_router
  - admin_users_router
  - admin_logs_router
  - admin_statistics_router
  ```
  **구현 파일**: `/backend/main.py:117-163`

**테스트**: ✅ FastAPI 서버 시작 시 자동 라우터 등록
**완료 조건**: ✅ 모든 API 엔드포인트 접근 가능

---

## 🎯 Phase 3: 관리자 웹 프론트엔드 구현 (2주)

### 3.1 프로젝트 구조 설정
- [ ] **디렉토리 구조 생성**
  ```
  frontend/src/pages/admin/
  ├── Dashboard.tsx           # 메인 대시보드
  ├── BatchMonitoring.tsx     # 배치 모니터링
  ├── SystemMonitoring.tsx    # 시스템 모니터링
  ├── UserManagement.tsx      # 사용자 관리
  ├── LogViewer.tsx           # 로그 조회
  └── Statistics.tsx          # 통계 및 분석
  ```

- [ ] **관리자 전용 라우팅**
  ```typescript
  /admin/dashboard
  /admin/batch
  /admin/system
  /admin/users
  /admin/logs
  /admin/statistics
  ```

- [ ] **관리자 레이아웃 컴포넌트**
  ```typescript
  AdminLayout.tsx
  - Sidebar 메뉴
  - Header (로그아웃 버튼)
  - Breadcrumb
  ```

**테스트**: 라우팅 테스트, 레이아웃 렌더링
**완료 조건**: 프로젝트 구조 및 라우팅 설정 완료

---

### 3.2 대시보드 메인 화면
- [ ] **시스템 상태 카드 컴포넌트**
  ```typescript
  <Grid container spacing={3}>
    <Grid item xs={12} md={3}>
      <StatusCard title="배치 실행 상태" value={batchStatus} />
    </Grid>
    <Grid item xs={12} md={3}>
      <StatusCard title="오늘 수집 입찰" value={todayBids} />
    </Grid>
    <Grid item xs={12} md={3}>
      <StatusCard title="활성 사용자" value={activeUsers} />
    </Grid>
    <Grid item xs={12} md={3}>
      <StatusCard title="시스템 상태" value={systemHealth} />
    </Grid>
  </Grid>
  ```

- [ ] **최근 배치 실행 이력 테이블**
  ```typescript
  <TableContainer>
    <Table>
      <TableHead>
        <TableRow>
          <TableCell>배치 타입</TableCell>
          <TableCell>실행 시간</TableCell>
          <TableCell>상태</TableCell>
          <TableCell>처리 건수</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>{recentExecutions.map(...)}</TableBody>
    </Table>
  </TableContainer>
  ```

- [ ] **실시간 시스템 리소스 차트**
  ```typescript
  <LineChart data={systemMetrics}>
    <Line dataKey="cpu" stroke="#8884d8" />
    <Line dataKey="memory" stroke="#82ca9d" />
  </LineChart>
  ```

- [ ] **실시간 데이터 업데이트 (WebSocket 또는 Polling)**
  ```typescript
  useEffect(() => {
    const interval = setInterval(() => {
      refetch(); // React Query refetch
    }, 5000); // 5초마다 갱신
    return () => clearInterval(interval);
  }, []);
  ```

**테스트**: 컴포넌트 렌더링, 실시간 업데이트
**완료 조건**: 대시보드 메인 화면 완성

---

### 3.3 배치 모니터링 화면
- [ ] **배치 실행 이력 테이블**
  - [ ] 날짜 필터 (DateRangePicker)
  - [ ] 배치 타입 필터 (Select)
  - [ ] 상태 필터 (Chip)
  - [ ] 페이지네이션

- [ ] **배치 상세 정보 모달**
  ```typescript
  <Dialog open={openDetail} onClose={handleClose}>
    <DialogTitle>배치 실행 상세</DialogTitle>
    <DialogContent>
      <Typography>실행 ID: {execution.id}</Typography>
      <Typography>처리 시간: {execution.duration}</Typography>
      <Divider />
      <Typography variant="h6">에러 로그</Typography>
      <Box>{execution.error_logs.map(...)}</Box>
    </DialogContent>
  </Dialog>
  ```

- [ ] **배치 수동 실행 버튼 및 확인 다이얼로그**
  ```typescript
  <Button onClick={handleManualRun}>
    배치 수동 실행
  </Button>
  <ConfirmDialog
    title="배치를 수동으로 실행하시겠습니까?"
    onConfirm={executeBatch}
  />
  ```

**테스트**: 필터링, 정렬, 모달 동작
**완료 조건**: 배치 모니터링 화면 완성

---

### 3.4 시스템 모니터링 화면
- [ ] **실시간 메트릭 차트 (Recharts)**
  ```typescript
  <ResponsiveContainer width="100%" height={300}>
    <AreaChart data={metrics}>
      <Area type="monotone" dataKey="cpu" stroke="#8884d8" />
      <Area type="monotone" dataKey="memory" stroke="#82ca9d" />
    </AreaChart>
  </ResponsiveContainer>
  ```

- [ ] **시스템 상태 표시기**
  ```typescript
  <Box>
    <Typography>데이터베이스: {dbStatus === 'healthy' ? '✅' : '❌'}</Typography>
    <Typography>Redis: {redisStatus === 'healthy' ? '✅' : '❌'}</Typography>
    <Typography>API 서버: {apiStatus === 'healthy' ? '✅' : '❌'}</Typography>
  </Box>
  ```

- [ ] **알림 발송 현황**
  ```typescript
  <Grid container>
    <Grid item xs={4}>
      <Metric title="발송 성공" value={successCount} color="success" />
    </Grid>
    <Grid item xs={4}>
      <Metric title="발송 실패" value={failedCount} color="error" />
    </Grid>
    <Grid item xs={4}>
      <Metric title="성공률" value={successRate + '%'} color="info" />
    </Grid>
  </Grid>
  ```

**테스트**: 차트 렌더링, 실시간 업데이트
**완료 조건**: 시스템 모니터링 화면 완성

---

### 3.5 사용자 관리 화면
- [ ] **사용자 목록 테이블**
  - [ ] 검색 (이메일, 이름)
  - [ ] 필터 (구독 플랜, 활성 상태)
  - [ ] 정렬 (가입일, 마지막 로그인)
  - [ ] 페이지네이션

- [ ] **사용자 상세 모달**
  ```typescript
  <Dialog fullWidth maxWidth="md">
    <Tabs value={tab} onChange={handleTabChange}>
      <Tab label="기본 정보" />
      <Tab label="활동 로그" />
      <Tab label="알림 규칙" />
      <Tab label="북마크" />
    </Tabs>
    <TabPanel value={tab} index={0}>
      {/* 사용자 기본 정보 */}
    </TabPanel>
  </Dialog>
  ```

- [ ] **사용자 관리 액션**
  ```typescript
  <IconButton onClick={handleActivateUser}>
    <CheckCircle />
  </IconButton>
  <IconButton onClick={handleDeactivateUser}>
    <Cancel />
  </IconButton>
  <IconButton onClick={handleResetPassword}>
    <VpnKey />
  </IconButton>
  ```

**테스트**: CRUD 동작, 권한 검증
**완료 조건**: 사용자 관리 화면 완성

---

### 3.6 로그 조회 화면
- [ ] **로그 검색 필터 UI**
  ```typescript
  <Box>
    <DateRangePicker label="날짜 범위" />
    <Select label="로그 레벨" options={['INFO', 'WARNING', 'ERROR']} />
    <TextField label="키워드 검색" />
    <Button onClick={handleSearch}>검색</Button>
  </Box>
  ```

- [ ] **로그 테이블 (가상 스크롤)**
  ```typescript
  <TableVirtuoso
    data={logs}
    components={VirtuosoTableComponents}
    fixedHeaderContent={fixedHeaderContent}
    itemContent={rowContent}
  />
  ```

- [ ] **로그 다운로드 기능**
  ```typescript
  <Button onClick={handleDownloadLogs}>
    <Download /> 로그 다운로드 (.zip)
  </Button>
  ```

**테스트**: 검색 성능, 대량 로그 렌더링
**완료 조건**: 로그 조회 화면 완성

---

### 3.7 통계 및 분석 화면
- [ ] **입찰 수집 통계 차트**
  ```typescript
  <BarChart data={bidStatistics}>
    <Bar dataKey="count" fill="#8884d8" />
    <XAxis dataKey="date" />
    <YAxis />
  </BarChart>
  ```

- [ ] **카테고리별 분포 파이 차트**
  ```typescript
  <PieChart>
    <Pie data={categoryDistribution} dataKey="value" nameKey="name" />
  </PieChart>
  ```

- [ ] **사용자 증가 추이 라인 차트**
  ```typescript
  <LineChart data={userGrowth}>
    <Line dataKey="users" stroke="#82ca9d" />
  </LineChart>
  ```

- [ ] **날짜 범위 선택 및 그룹핑 옵션**
  ```typescript
  <Select label="그룹핑" options={['일별', '주별', '월별']} />
  ```

**테스트**: 차트 렌더링, 데이터 정확도
**완료 조건**: 통계 및 분석 화면 완성

---

## 🎯 Phase 4: 배포 및 운영 설정 (1주)

### 4.1 배치 로깅 시스템 통합
- [ ] **production_batch.py 로그 DB 저장**
  ```python
  class BatchLogger:
      def __init__(self, batch_type):
          self.batch_type = batch_type
          self.execution_id = None

      def start(self):
          # batch_execution_logs 테이블에 INSERT
          self.execution_id = insert_execution_log(...)

      def log(self, level, message, context=None):
          # batch_detail_logs 테이블에 INSERT
          insert_detail_log(self.execution_id, level, message, context)

      def finish(self, status, stats):
          # batch_execution_logs 업데이트
          update_execution_log(self.execution_id, status, stats)
  ```

- [ ] **모든 배치 모듈에 로거 적용**
  ```python
  # batch/modules/collector.py
  batch_logger = BatchLogger('collector')
  batch_logger.start()
  try:
      # 수집 로직
      batch_logger.log('INFO', 'API 호출 성공', {'count': 100})
  except Exception as e:
      batch_logger.log('ERROR', str(e))
  finally:
      batch_logger.finish('success', stats)
  ```

**테스트**: 로그 저장 검증, 성능 영향 확인
**완료 조건**: 배치 실행 로그 자동 저장

---

### 4.2 시스템 메트릭 수집기 구현
- [ ] **메트릭 수집 스크립트**
  ```python
  # scripts/collect_metrics.py
  import psutil

  def collect_system_metrics():
      cpu = psutil.cpu_percent()
      memory = psutil.virtual_memory().percent
      disk = psutil.disk_usage('/').percent

      save_metric('cpu', cpu)
      save_metric('memory', memory)
      save_metric('disk', disk)
  ```

- [ ] **크론잡 설정 (1분마다)**
  ```bash
  * * * * * cd /path/to/odin-ai && python scripts/collect_metrics.py
  ```

- [ ] **API 응답 시간 미들웨어**
  ```python
  @app.middleware("http")
  async def log_api_performance(request: Request, call_next):
      start_time = time.time()
      response = await call_next(request)
      duration = time.time() - start_time

      save_metric('api_response_time', duration, {
          'path': request.url.path
      })

      return response
  ```

**테스트**: 메트릭 수집 정확도, 저장 성능
**완료 조건**: 시스템 메트릭 자동 수집

---

### 4.3 관리자 웹 배포
- [ ] **Docker 이미지 빌드**
  ```dockerfile
  # Dockerfile.admin (frontend와 동일하나 /admin 라우트만)
  FROM node:18-alpine
  WORKDIR /app
  COPY package*.json ./
  RUN npm install
  COPY . .
  RUN npm run build
  CMD ["npm", "start"]
  ```

- [ ] **Nginx 설정 (서브도메인 또는 /admin 경로)**
  ```nginx
  # admin.odin-ai.com 또는 odin-ai.com/admin
  location /admin {
      proxy_pass http://admin-web:3001;
      proxy_set_header Host $host;
  }
  ```

- [ ] **환경변수 설정**
  ```bash
  REACT_APP_ADMIN_API_URL=https://api.odin-ai.com/admin
  REACT_APP_ADMIN_AUTH_REQUIRED=true
  ```

**테스트**: 배포 테스트, HTTPS 확인
**완료 조건**: 관리자 웹 프로덕션 배포

---

### 4.4 보안 설정
- [ ] **관리자 전용 IP 화이트리스트 (선택사항)**
  ```python
  ADMIN_ALLOWED_IPS = ["123.456.789.0", "회사 IP"]

  @app.middleware("http")
  async def check_admin_ip(request: Request, call_next):
      if request.url.path.startswith("/api/admin"):
          client_ip = request.client.host
          if client_ip not in ADMIN_ALLOWED_IPS:
              raise HTTPException(403, "Access denied")
      return await call_next(request)
  ```

- [ ] **관리자 계정 2FA (선택사항)**
  - [ ] Google Authenticator 연동
  - [ ] 로그인 시 OTP 검증

- [ ] **관리자 활동 로그 자동 기록**
  ```python
  # 모든 관리자 API에 자동 로깅
  @app.middleware("http")
  async def log_admin_activity(request: Request, call_next):
      if request.url.path.startswith("/api/admin"):
          admin_user = get_current_admin_user(request)
          log_admin_action(admin_user.id, request.method, request.url.path)
      return await call_next(request)
  ```

**테스트**: 보안 테스트, 권한 검증
**완료 조건**: 보안 설정 완료

---

### 4.5 알림 설정
- [ ] **시스템 에러 발생 시 관리자 이메일 알림**
  ```python
  def send_admin_alert(subject, message):
      send_email(
          to=ADMIN_EMAIL,
          subject=f"[ODIN-AI Alert] {subject}",
          body=message
      )

  # 배치 실패 시
  if batch_status == 'failed':
      send_admin_alert("배치 실행 실패", f"배치 타입: {batch_type}")
  ```

- [ ] **Slack 웹훅 연동 (선택사항)**
  ```python
  import requests

  def send_slack_notification(message):
      requests.post(SLACK_WEBHOOK_URL, json={"text": message})
  ```

- [ ] **시스템 리소스 임계값 알림**
  ```python
  if cpu_percent > 90:
      send_admin_alert("CPU 사용률 위험", f"현재: {cpu_percent}%")
  ```

**테스트**: 알림 발송 테스트
**완료 조건**: 관리자 알림 시스템 완성

---

## 📊 진행 상황 추적

### Phase 1: 설계 및 기획 (1주) ✅ **완료**
- [x] 1.1 요구사항 정의 및 기능 명세
- [x] 1.2 데이터베이스 스키마 설계
- [x] 1.3 화면 설계 (Wireframe)
- [x] 1.4 기술 스택 선정

**진행률**: 100% [●●●●●●●●●●] ✅

### Phase 2: 백엔드 API 구현 (2주) ✅ **완료**
- [x] 2.1 배치 모니터링 API (4개) ✅
- [x] 2.2 시스템 모니터링 API (4개) ✅
- [x] 2.3 사용자 관리 API (4개) ✅
- [x] 2.4 로그 조회 및 분석 API (3개) ✅
- [x] 2.5 통계 및 분석 API (4개) ✅
- [x] 2.6 관리자 인증 및 권한 관리 ✅

**진행률**: 100% [●●●●●●●●●●] ✅

### Phase 3: 프론트엔드 구현 (2주)
- [ ] 3.1 프로젝트 구조 설정
- [ ] 3.2 대시보드 메인 화면
- [ ] 3.3 배치 모니터링 화면
- [ ] 3.4 시스템 모니터링 화면
- [ ] 3.5 사용자 관리 화면
- [ ] 3.6 로그 조회 화면
- [ ] 3.7 통계 및 분석 화면

**진행률**: 0% [○○○○○○○○○○]

### Phase 4: 배포 및 운영 설정 (1주)
- [ ] 4.1 배치 로깅 시스템 통합
- [ ] 4.2 시스템 메트릭 수집기 구현
- [ ] 4.3 관리자 웹 배포
- [ ] 4.4 보안 설정
- [ ] 4.5 알림 설정

**진행률**: 0% [○○○○○○○○○○]

---

## 🎯 전체 진행률
**총 진행률**: 50% [●●●●●○○○○○]

**Phase 1 완료**: ✅ 2025-10-02
**Phase 2 완료**: ✅ 2025-10-02
**예상 완료일**: 3주 후 (2025-10-23)

---

## 📝 참고 문서
- `/docs/TASK_MANAGEMENT.md` - 메인 태스크 관리 문서
- `/CLAUDE.md` - 프로젝트 컨텍스트 및 개발 가이드
- `/REUSABLE_PATTERNS.md` - 재사용 가능한 개발 패턴

---

*이 문서는 프로젝트 진행에 따라 지속적으로 업데이트됩니다.*
