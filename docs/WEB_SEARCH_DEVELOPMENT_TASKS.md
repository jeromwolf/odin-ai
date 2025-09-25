# 🔍 웹 검색 기능 개발 태스크

**작성일**: 2025-09-24
**목표**: 입찰공고 검색 웹 애플리케이션 구현

## 📊 현재 상태 분석

### ✅ 이미 구현된 부분

#### Backend (FastAPI)
- **기본 구조**: FastAPI 앱 설정 완료 (`src/backend/main.py`)
- **API 라우트**:
  - `/api/search/` - 통합 검색 엔드포인트
  - `/api/search/bids` - 입찰공고 검색
  - `/api/search/documents` - 문서 검색
  - `/api/search/companies` - 기업 검색
  - `/api/search/suggest` - 자동완성
  - `/api/search/facets` - 패싯 정보
- **CORS 설정**: 완료
- **데이터베이스 모델**: 기본 구조 있음

#### Frontend (React + TypeScript)
- **기본 설정**: React 18, TypeScript, Material-UI
- **라우팅**: React Router 설정
- **상태관리**: Redux Toolkit, React Query
- **페이지 구조**: 기본 페이지들 생성
- **Search.tsx**: 빈 페이지 (개발 필요)

### ❌ 미구현 부분

#### Backend
1. **SearchService 구현** (`backend.services.search_service`)
2. **데이터베이스 연결 설정**
3. **실제 검색 로직 구현**
4. **페이지네이션 처리**
5. **검색 인덱싱**

#### Frontend
1. **검색 UI 컴포넌트**
2. **필터 UI**
3. **검색 결과 표시**
4. **페이지네이션 UI**
5. **API 연동**

---

## 🎯 개발 태스크 (우선순위별)

### Phase 1: Backend 기본 구현 (2-3일)

#### Task 1.1: SearchService 구현
```python
# src/backend/services/search_service.py
- [ ] SearchService 클래스 생성
- [ ] 기본 검색 메서드 구현
- [ ] 필터링 로직 구현
- [ ] 정렬 로직 구현
```

#### Task 1.2: 데이터베이스 연결
```python
# src/backend/models/database.py
- [ ] get_db() 함수 구현
- [ ] 세션 관리
- [ ] 연결 풀 설정
```

#### Task 1.3: 검색 쿼리 구현
```python
- [ ] Full-text search 설정
- [ ] LIKE 검색 구현
- [ ] 필터 조건 쿼리 구현
- [ ] 페이지네이션 쿼리
```

---

### Phase 2: Frontend 검색 UI (2-3일)

#### Task 2.1: 검색 컴포넌트 개발
```tsx
# src/components/search/
- [ ] SearchBar.tsx - 검색 입력창
- [ ] SearchFilters.tsx - 필터 패널
- [ ] SearchResults.tsx - 결과 리스트
- [ ] SearchPagination.tsx - 페이지네이션
```

#### Task 2.2: 검색 페이지 구현
```tsx
# src/pages/Search.tsx
- [ ] 레이아웃 구성
- [ ] 컴포넌트 통합
- [ ] 상태 관리
- [ ] URL 쿼리 파라미터 처리
```

#### Task 2.3: API 서비스 연동
```tsx
# src/services/searchService.ts
- [ ] API 클라이언트 설정
- [ ] 검색 API 호출 함수
- [ ] 에러 처리
- [ ] 캐싱 설정
```

---

### Phase 3: 고급 기능 (2-3일)

#### Task 3.1: 검색 최적화
- [ ] 검색 인덱스 생성 (PostgreSQL)
- [ ] 디바운싱 적용
- [ ] 검색 결과 캐싱
- [ ] 무한 스크롤 구현

#### Task 3.2: 자동완성 기능
- [ ] 자동완성 API 연동
- [ ] 자동완성 UI 컴포넌트
- [ ] 검색 히스토리 저장
- [ ] 인기 검색어 표시

#### Task 3.3: 필터 고도화
- [ ] 날짜 범위 선택기
- [ ] 가격 범위 슬라이더
- [ ] 다중 선택 필터
- [ ] 필터 초기화 기능

---

### Phase 4: 통합 및 테스트 (1-2일)

#### Task 4.1: 통합 테스트
- [ ] API 엔드투엔드 테스트
- [ ] UI 컴포넌트 테스트
- [ ] 성능 테스트
- [ ] 에러 케이스 테스트

#### Task 4.2: 최종 마무리
- [ ] 로딩 상태 처리
- [ ] 에러 메시지 UI
- [ ] 빈 결과 처리
- [ ] 반응형 디자인 확인

---

## 🚀 빠른 시작 가이드

### 1. Backend 서버 실행
```bash
cd src
uvicorn backend.main:app --reload --port 8000
```

### 2. Frontend 개발 서버 실행
```bash
cd frontend
npm install
npm start
```

### 3. 데이터베이스 확인
```bash
psql -d odin_db -c "SELECT COUNT(*) FROM bid_announcements;"
```

---

## 📝 개발 순서 추천

### Day 1-2: Backend 기본
1. SearchService 뼈대 구현
2. 간단한 검색 쿼리 작성
3. API 테스트 (Swagger UI)

### Day 3-4: Frontend 기본
1. 검색 UI 컴포넌트 개발
2. API 연동
3. 기본 검색 동작 확인

### Day 5-6: 통합 및 개선
1. 필터 기능 추가
2. 페이지네이션 완성
3. 성능 최적화

### Day 7: 테스트 및 마무리
1. 버그 수정
2. UI/UX 개선
3. 문서화

---

## ⚠️ 주의사항

1. **CORS 설정**: Frontend 개발 시 proxy 설정 확인
2. **환경변수**: `.env` 파일 설정 필수
3. **데이터베이스**: 실제 데이터 있는지 확인
4. **타입 안정성**: TypeScript 타입 정의 철저히

---

## 📊 예상 결과물

### 검색 페이지 기능
- ✅ 키워드 검색
- ✅ 필터링 (날짜, 가격, 기관)
- ✅ 정렬 (관련도, 날짜, 가격)
- ✅ 페이지네이션
- ✅ 검색 결과 표시
- ✅ 자동완성
- ✅ 검색 히스토리

### 성능 목표
- 검색 응답: < 500ms
- 자동완성: < 200ms
- 페이지 로드: < 2s

---

## 🔗 참고 자료

- FastAPI Docs: https://fastapi.tiangolo.com/
- React Query: https://tanstack.com/query
- Material-UI: https://mui.com/
- PostgreSQL Full-text Search: https://www.postgresql.org/docs/current/textsearch.html