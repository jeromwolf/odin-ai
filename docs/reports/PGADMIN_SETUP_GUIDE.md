# 📊 pgAdmin4 설정 가이드 - Odin-AI 데이터베이스

## 🚀 pgAdmin 실행 및 초기 설정

### 1단계: pgAdmin 실행
- **방법 1**: Applications 폴더 → pgAdmin 4.app 실행
- **방법 2**: Spotlight(⌘+Space) → "pgAdmin" 검색 → 실행
- **방법 3**: Launchpad에서 pgAdmin 아이콘 클릭

### 2단계: 마스터 패스워드 설정
pgAdmin을 처음 실행하면 마스터 패스워드 설정 화면이 나타납니다.

```
Master Password 설정:
- 패스워드: admin1234 (또는 원하는 패스워드)
- 이 패스워드는 pgAdmin 접근용입니다.
```

## 🔗 Odin-AI 데이터베이스 서버 추가

### 3단계: 새 서버 추가
1. pgAdmin 웹 인터페이스가 브라우저에서 열림 (자동)
2. 왼쪽 사이드바에서 **"Servers"** 우클릭
3. **"Register" → "Server..."** 선택

### 4단계: 서버 정보 입력

#### 📋 General 탭
```
Name: Odin-AI Database
Server group: Servers
Comments: Odin-AI 공공조달 데이터베이스
```

#### 🔌 Connection 탭
```
Host name/address: localhost
Port: 5432
Maintenance database: odin_ai
Username: odin_user
Password: odin_password
```

#### ⚙️ Advanced 탭 (선택사항)
```
DB restriction: odin_ai
```

### 5단계: 연결 확인
- **"Save"** 버튼 클릭
- 연결 성공 시 왼쪽에 "Odin-AI Database" 서버가 나타남

## 📊 데이터베이스 탐색

### 데이터베이스 구조
```
Odin-AI Database
└── Databases
    └── odin_ai
        └── Schemas
            └── public
                └── Tables
                    ├── bid_announcements (입찰공고) - 1건
                    ├── bid_documents (입찰문서) - 1건
                    ├── collection_logs (수집로그) - 2건
                    ├── users (사용자) - 0건
                    └── ... 기타 13개 테이블
```

### 테이블 데이터 확인 방법
1. **테이블 우클릭** → **"View/Edit Data"** → **"All Rows"**
2. 또는 테이블 선택 후 상단의 **"데이터 보기"** 아이콘 클릭

## 🔍 주요 기능 사용법

### 📋 데이터 조회 (Query Tool)
1. 데이터베이스 선택 후 **Tools** → **Query Tool**
2. SQL 쿼리 입력 예시:
```sql
-- 입찰공고 전체 조회
SELECT * FROM bid_announcements;

-- 수집로그 최근 순으로 조회
SELECT * FROM collection_logs ORDER BY collection_date DESC;

-- 문서 처리 상태별 집계
SELECT processing_status, COUNT(*)
FROM bid_documents
GROUP BY processing_status;
```

### 📊 테이블 구조 확인
- 테이블 우클릭 → **"Properties"**
- **"Columns"** 탭에서 컬럼 정보 확인
- **"Constraints"** 탭에서 제약조건 확인

### 🔄 데이터 새로고침
- F5 키 또는 새로고침 버튼 클릭
- 실시간으로 Collector가 추가한 데이터 확인 가능

## 🎯 Collector 테스트 결과 확인

### 현재 저장된 데이터
```sql
-- 테스트 입찰공고 확인
SELECT bid_notice_no, bid_notice_name, notice_inst_name, created_at
FROM bid_announcements;

-- 결과: TEST20250917001 | Collector 테스트용 입찰공고...

-- 문서 처리 상태 확인
SELECT file_name, file_type, download_status, processing_status
FROM bid_documents;

-- 결과: test_collector_document.hwp | hwp | pending | pending

-- 수집 로그 확인
SELECT collection_type, status, total_found, new_items, notes
FROM collection_logs ORDER BY collection_date DESC;

-- 결과:
-- collector_test | completed | 1 | 1 | Collector 종합 테스트 실행
-- api | completed | 0 | 0 | (SSL 네트워크 이슈)
```

## 🌐 웹 인터페이스 주소

pgAdmin은 기본적으로 다음 주소에서 실행됩니다:
- **http://127.0.0.1:5050** (또는 자동 할당된 포트)
- 브라우저가 자동으로 열리지 않으면 수동으로 접속

## 🔧 문제 해결

### 연결 실패 시
1. PostgreSQL 서비스 상태 확인:
   ```bash
   brew services list | grep postgresql
   ```

2. PostgreSQL 시작:
   ```bash
   brew services start postgresql@14
   ```

3. 데이터베이스 존재 확인:
   ```bash
   psql postgres -c "\l" | grep odin_ai
   ```

### 패스워드 오류 시
환경변수 파일 확인:
```bash
cat .env | grep DATABASE_URL
```

## 💡 추가 팁

### 📌 북마크 기능
자주 사용하는 쿼리를 북마크로 저장 가능

### 📈 모니터링
- **Dashboard** 탭에서 실시간 통계 확인
- 서버 성능 및 연결 상태 모니터링

### 🔄 백업/복원
- **Tools** → **Backup** 또는 **Restore**
- 전체 데이터베이스 또는 개별 테이블 백업 가능

---

## 🎉 완료!

이제 pgAdmin에서 Odin-AI 데이터베이스의 모든 테이블과 데이터를 확인할 수 있습니다.

**주요 확인 사항:**
- ✅ 입찰공고 1건 (TEST20250917001)
- ✅ 입찰문서 1건 (test_collector_document.hwp)
- ✅ 수집로그 2건 (collector_test + api)
- ✅ 17개 테이블 구조
- ✅ 실시간 데이터 업데이트

**접속 정보 요약:**
- 호스트: localhost:5432
- DB: odin_ai
- 계정: odin_user / odin_password

Collector가 실행될 때마다 이 데이터베이스에 새로운 데이터가 추가됩니다!