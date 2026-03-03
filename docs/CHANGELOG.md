# CHANGELOG

ODIN-AI 프로젝트 변경 이력 및 버그 수정 기록

---

## 2026-02-25: RAG + Neo4j + GraphRAG 대규모 보강

### 작업 내용
- 임베딩 커버리지 17.4% → 45.7% (8,665/18,977건) 확대 중
- Neo4j 노드 476 → 18,977건 전체 동기화 완료
- Neo4j 관계 42,183 → 16,514,393개 (SIMILAR_TO 포함)
- GraphRAG 엔티티 100 → 856개

### 인프라 변경
- Neo4j 메모리 증가: 트랜잭션 358MB → 1GB, 힙 512MB → 1GB
- `.env`에 `ENABLE_GRAPHRAG=true` 추가 (기존 누락)

### 발견된 문제
- `ENABLE_GRAPHRAG` 미설정으로 배치 Phase 3.7 항상 스킵됨
- Neo4j `sync_incremental(24h)`가 과거 데이터 미동기화 → `sync_all()` 1회 실행으로 해결

---

## 2026-02-22: 2026년 실시간 데이터 수집 및 E2E 테스트

### 작업 내용
- 공공데이터포털 API 키 갱신 (만료 키 교체)
- 9건 신규 입찰공고 수집 (2026-02-22 당일)
- Playwright E2E 59/59 통과, 38개 스크린샷 갱신

### 버그 수정: 관리자 JWT 인증
- **문제**: `python-jose`가 `sub` 클레임을 문자열로 요구하나 정수로 저장됨
- **수정**: `admin_auth.py`에서 `str(user_id)` 변환 추가

---

## 2025-11-10: 통합 테스트 + 버그 수정

### 테스트 결과
- 총 86개 테스트 (Phase 0 + Phase 2): 67개 통과, 실패 0개
- 최종 점수: 78점/100점 (B+ 등급)

### 버그 #1: 알림 매칭 가격 필터 (치명적)
- **증상**: 가격 범위 설정이 완전히 무시됨
- **원인**: 코드가 `price_min`/`price_max` 키를 찾지만 DB는 `min_price`/`max_price`로 저장
- **수정**: 두 형식 모두 지원 (`conditions.get('min_price') or conditions.get('price_min')`)
- **교훈**: DB 스키마-코드 일관성 검증 필수, 단위 테스트 필수

### 버그 #2: 알림 시간 범위 설정
- **증상**: `since_hours=4` 기본값이 너무 짧아 알림 누락
- **수정**: 기본값 4시간 → 168시간(1주일)로 변경

### 버그 #3: TypeScript 타입 중복
- **증상**: `BidDetail` interface와 const 이름 충돌
- **수정**: interface를 `BidDetailData`로 변경

### 버그 #4: 관리자 통계 API 컬럼명
- **증상**: `publish_date` 컬럼 없음 에러
- **수정**: `publish_date` → `announcement_date` 일괄 변경

---

## 2025-10-29~30: 알림 이메일 발송 시스템 완성

### 작업 내용
- 4명 사용자에게 350개 알림 매칭, 4개 이메일 발송 100% 성공
- Gmail SMTP 인증 (앱 비밀번호) 연동 완료
- `notification_send_logs` 테이블에 발송 기록 저장

### 주의사항
- Gmail 앱 비밀번호: 스페이스 없이 연속 입력 (`gkutwlrladpzpxxt`)
- `.env`에서 따옴표 금지: `EMAIL_PASSWORD=xxx` (O) / `EMAIL_PASSWORD="xxx"` (X)

---

## 2025-10-20: 관리자 배치 모니터링

### 작업 내용
- 관리자 화면에서 수동 배치 실행 기능 (날짜/알림 선택)
- Port 8000 → 9000 이전 (충돌 해결)
- 143개 신규 공고 수집, 118개 문서 다운로드

---

## 2025-10-03: 관리자 웹 구축 + UserManagement 리팩토링

### 작업 내용
- 관리자 6개 페이지 API 연동 (로그인, 대시보드, 배치, 시스템, 사용자, 로그)
- `last_login_at` → `last_login` 컬럼명 수정
- COALESCE 추가 (빈 테이블 집계 시 NULL 방지)

### 리팩토링: UserManagement
- 681줄 1개 파일 → 9개 파일 (총 934줄) 모듈화
- 패턴: `index.tsx` + `types.ts` + `utils.tsx` + `hooks/` + `components/`

---

## 2025-09-29: 북마크 + 인증 + 알림 시스템

### 작업 내용
- 북마크: 대시보드(읽기전용) + 검색페이지(CRUD) 역할 분리
- 인증: JWT 기반 회원가입/로그인/로그아웃 완전 구현
- 알림설정: 무한 로딩 버그 수정 (`get_current_user_optional` 사용)

---

## 2025-09-26: Phase 3 사용자 인터페이스 완성

### 작업 내용
- 알림설정, 프로필, 설정, 구독관리 4개 페이지 신규 생성
- 대시보드 차트 클릭 → 검색 연동
- 태그 기반 통합검색 구현
- 잘못된 태그 20개 자동 정리

### 배치 결과
- 469개 공고, 93.9% 처리 성공률 (355/380)

---

## 2025-09-25: 테스트 자동화 시스템

### 작업 내용
- 215개 테스트 구현, 98.6% 통과 (212/215)
- FastAPI 백엔드 API 대폭 개선 (인증, 검색, 북마크, AI 추천, 구독)

---

## 2025-09-24: 배치 시스템 모듈화

### 작업 내용
- `batch/modules/` 구조로 분리 (collector, downloader, processor, email_reporter)
- 69개 공고 수집, 94% 문서 처리 성공률

---

## 2025-09-23: 프로젝트 시작

### 초기 구현
- 공공데이터포털 API 연동
- HWP 표 파싱 시스템 (100% 성공률)
- 정보 추출 시스템 (prices, schedule, qualifications)
- PostgreSQL 스키마 설계
