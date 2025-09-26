# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ 최우선 원칙: 개인정보 보호

**절대 규칙**: 어떤 상황에서도 로그에 개인정보를 남기지 않습니다.

## 🔧 모듈형 개발 방법론 (2025-09-26 추가) - 매우 중요!

### 🎯 핵심 원칙: "한 번에 하나씩, 독립적으로"

#### ❌ 실제 발생한 문제 (2025-09-26)
- **상황**: 북마크 기능 추가 작업
- **결과**: 검색 기능까지 작동 불능
- **원인**: 공통 모듈(api.ts) 수정으로 연쇄 오류 발생

### ✅ 올바른 개발 방법론

#### 1. **기능 추가 시 체크리스트**
```bash
□ 1. 현재 작동 중인 기능 목록 작성
□ 2. Git 브랜치 생성 (feature/bookmark-add)
□ 3. 영향 범위 분석
□ 4. 독립 모듈로 개발
□ 5. 기존 기능 테스트
□ 6. 문제 없을 시에만 병합
```

#### 2. **모듈 분리 원칙**
```
frontend/
├── services/
│   ├── api.ts           # ⚠️ 절대 직접 수정 금지
│   ├── searchService.ts # 검색 전용
│   └── bookmarkService.ts # 북마크 전용 (새로 생성)
```

#### 3. **공통 파일 수정 규칙**
- **api.ts, App.tsx, types/**: 직접 수정 금지
- **필요시**: 별도 파일 생성 후 import
```typescript
// ❌ 잘못된 방법
// api.ts 직접 수정
async getBookmarks() { ... }

// ✅ 올바른 방법
// bookmarkService.ts 생성
import apiClient from './api';
export const bookmarkService = {
  getBookmarks: () => apiClient.get('/bookmarks')
}
```

#### 4. **단계별 개발 프로세스**
```
1단계: 백엔드 API 독립 파일로 생성
2단계: 프론트엔드 서비스 독립 파일로 생성
3단계: 컴포넌트 독립 생성
4단계: 라우팅 추가 (App.tsx는 최소 수정)
5단계: 각 단계마다 기존 기능 테스트
```

#### 5. **롤백 전략**
```bash
# 문제 발생 시 즉시
git status           # 변경 파일 확인
git diff            # 변경 내용 확인
git stash           # 임시 저장
git checkout -- .   # 전체 되돌리기
```

#### 6. **의존성 관리**
```typescript
// 각 모듈의 의존성을 명확히 표시
/**
 * Dependencies:
 * - apiClient (read-only)
 * - types/bookmark.types
 *
 * Used by:
 * - pages/Bookmarks.tsx
 * - components/BookmarkButton.tsx
 */
```

### 🚨 절대 하지 말아야 할 것
1. **여러 기능 동시 작업** - 북마크 + 검색 동시 수정 ❌
2. **공통 모듈 직접 수정** - api.ts, types/index.ts ❌
3. **테스트 없이 병합** - 기존 기능 확인 필수 ❌
4. **큰 단위로 커밋** - 작은 단위로 자주 커밋 ✅

### 📝 개발 전 체크리스트 템플릿
```markdown
## 작업: [기능명]
- [ ] 현재 정상 작동 기능: 검색 ✅, 대시보드 ✅
- [ ] Git 브랜치 생성: feature/[기능명]
- [ ] 영향받을 파일 목록:
- [ ] 독립 모듈 생성 계획:
- [ ] 테스트 계획:
- [ ] 롤백 계획:
```

---

## ⚠️ 중요한 실수 기록 (2025-09-23)

### 🚨 **반복되는 치명적 실수: 날짜 설정 오류**

**실수 내용**:
- 사용자가 **"오늘 날짜로 하라"**고 명확히 지시했음에도 불구하고
- API 검색 기간을 **2025년 1월** (8개월 전)로 잘못 설정
- 결과적으로 과거 마감된 입찰만 처리하여 의미없는 작업 수행

**실수 코드**:
```python
f"inqryBgnDt=202501010000&"    # ❌ 2025년 1월 (과거)
f"inqryEndDt=202501310000&"    # ❌ 2025년 1월 (과거)
```

**올바른 코드**:
```python
f"inqryBgnDt=202509160000&"    # ✅ 2025년 9월 (현재)
f"inqryEndDt=202510232359&"    # ✅ 2025년 10월 (미래)
```

**교훈**:
1. 사용자 지시사항을 정확히 읽고 이해할 것
2. 날짜 관련 작업 시 현재 날짜 확인 필수
3. 같은 실수를 반복하지 않도록 주의깊게 작업할 것

---

## 🔄 배치 프로그램 운영 가이드 (2025-09-26 추가)

### 📊 왜 정기적인 배치가 필요한가?
- 공공기관들이 **하루 중 언제든** 새 입찰공고를 등록
- 오전 9시에 39개 → 오전 9시 20분에 42개 (20분만에 3개 추가)
- API는 실시간으로 새 공고를 반영

### 🚀 권장 배치 스케줄 (하루 3회)

#### 1. **운영 환경 (Production)**
```bash
# crontab -e 로 설정
0 7 * * * cd /path/to/odin-ai && python3 batch/production_batch.py
0 12 * * * cd /path/to/odin-ai && python3 batch/production_batch.py
0 18 * * * cd /path/to/odin-ai && python3 batch/production_batch.py

# 또는 환경변수 명시
0 7,12,18 * * * cd /path/to/odin-ai && DATABASE_URL="postgresql://user@host/db" python3 batch/production_batch.py
```

#### 2. **테스트 환경 (Development)**
```bash
# 스키마 변경, 필드 추가 등 테스트 시에만 사용
DB_FILE_INIT=true TEST_MODE=false python3 batch/production_batch.py

# 일반 테스트 (증분 업데이트)
python3 batch/production_batch.py
```

### ⚠️ DB_FILE_INIT 사용 주의
- **DB_FILE_INIT=true**: 모든 데이터 삭제 후 재수집 (테스트용)
- **DB_FILE_INIT=false** 또는 **생략**: 증분 업데이트 (운영용)
- 운영 환경에서는 **절대 DB_FILE_INIT=true 사용 금지**

### 📈 배치 실행 통계
- 평균 수집: 40~50개/일 (신규 공고)
- 처리 시간: 약 5~10분
- 성공률: HWP 95%, HWPX 90%, PDF 0% (PyPDF2 미설치)

---

## 📌 개선사항 TODO (2025-09-24)

### 배치 시스템 개선 필요사항
**상세 내용**: `docs/BATCH_IMPROVEMENTS.md` 참조

#### 🔴 즉시 개선 필요
1. **중복 체크 로직**: 업데이트된 공고 반영 안 됨
2. **정보 추출 패턴**: prices 3개만 추출 (패턴 부족)

#### 🟡 중요 개선사항
1. **트랜잭션 관리**: 데이터 일관성 보장 필요
2. **에러 핸들링**: 원인별 재시도 전략 필요
3. **HWPX 처리**: 3개 실패 원인 파악 필요

#### 🟢 향후 개선사항
1. **ZIP 파일 처리**: 나중에 구현 예정
2. **배치 크기 동적 조절**
3. **실시간 모니터링**

---

## ⚠️ 데이터 정확성 개선 필요 (2025-09-26 추가)

### 카테고리 및 지역 정보 검증 필요
- **문제점**: "일반공사"와 "전국"이 기본값으로 너무 자주 나타남
- **원인**:
  - 문서 파싱 시 정확한 카테고리 추출 실패
  - 지역제한 정보가 명시되지 않은 경우 "전국"으로 기본 설정
- **개선 필요사항**:
  - 더 정교한 패턴 매칭 알고리즘 개발
  - 문서 내 실제 카테고리 정보 위치 파악
  - 지역제한 정보 추출 로직 개선
  - 신뢰도 점수 시스템 도입 고려

---

## 🏷️ 태그 알고리즘 개선 계획 (2025-09-26 추가)

### 발견된 문제점 (2025-09-26)
- **현상**: 건설공사에 "소프트웨어" 태그가 잘못 붙음
- **원인**: 오래된/다른 태그 생성 시스템에서 잘못된 매핑
- **대응**: 20개 잘못된 태그 자동 제거 완료 ✅

### 태그 알고리즘 고도화 필요사항

#### 🔴 우선순위 1: 컨텍스트 기반 태그 생성
```python
# 현재 문제점: 단순 키워드 매칭
'IT': ['시스템', '소프트웨어', 'SW', '개발', '구축', '프로그램']

# 개선안: 컨텍스트 고려한 매칭
def smart_tag_matching(title, content):
    if "시스템" in title:
        if any(word in title for word in ["공사", "건설", "시공"]):
            return "건설"  # "시설관리시스템 공사" → 건설
        elif any(word in title for word in ["개발", "구축", "SW"]):
            return "IT"    # "정보시스템 개발" → IT
```

#### 🟡 우선순위 2: 신뢰도 점수 시스템
- 태그별 매칭 확신도 점수 (0.0-1.0)
- 여러 카테고리 후보 중 가장 높은 점수 선택
- 불확실한 경우 수동 검토 플래그 설정

#### 🟡 우선순위 3: 학습 기반 태그 개선
- 사용자 피드백 수집 (태그 수정/삭제)
- 잘못된 태그 패턴 학습 및 방지
- 정기적인 태그 품질 검증

#### 🟢 우선순위 4: 고급 태그 기능
- 계층형 태그 (건설 > 토목 > 도로)
- 동의어 태그 처리 (SW = 소프트웨어)
- 시간에 따른 태그 트렌드 분석

### 개선 작업 계획
1. **Phase 1**: 컨텍스트 기반 매칭 로직 개발
2. **Phase 2**: 신뢰도 점수 시스템 구현
3. **Phase 3**: 사용자 피드백 기반 학습 시스템
4. **Phase 4**: 태그 품질 모니터링 대시보드

### 기술적 구현 방안
```python
class SmartTagGenerator:
    def __init__(self):
        self.context_rules = self._load_context_rules()
        self.confidence_model = self._load_confidence_model()

    def generate_tags_with_confidence(self, announcement):
        candidate_tags = self._extract_candidate_tags(announcement)

        for tag in candidate_tags:
            confidence = self._calculate_confidence(tag, announcement)
            if confidence > 0.8:
                return tag
            elif confidence > 0.5:
                # 수동 검토 필요
                return tag + "_REVIEW"

        return "기타"  # 기본값
```

---

## 📈 대시보드 및 검색 시스템 고도화 (2025-09-26 완료)

### ✅ 완료된 주요 기능들

#### 🔧 대시보드 차트 데이터 연동 및 개선
- ✅ **주간 입찰 트렌드 차트**: 실제 데이터베이스 데이터로 연동 완료
- ✅ **카테고리별 분포 차트**: 태그 기반 실시간 카테고리 통계 표시
- ✅ **시간 표시 개선**: "96.2시간 남음" → "4일 0시간 남음" 형태로 개선
- ✅ **차트 클릭 기능**: 카테고리 클릭 시 해당 카테고리 검색 페이지로 자동 이동

#### 🔍 검색 시스템 품질 개선
- ✅ **태그 기반 검색 강화**: 제목, 기관명, 태그를 모두 포함한 통합 검색
- ✅ **잘못된 태그 정리**: 건설공사에 붙은 "소프트웨어" 태그 20개 자동 제거
- ✅ **카테고리 일관성**: 차트 분포와 검색 결과 완전 일치
- ✅ **URL 기반 검색**: 쿼리 파라미터 지원으로 뒤로가기/새로고침 가능

#### 🎯 UX/UI 개선사항
- ✅ **직관적 네비게이션**: 대시보드 → 검색 원클릭 이동
- ✅ **시각적 힌트**: "💡 카테고리를 클릭하여 해당 항목 검색하기" 안내
- ✅ **반응형 인터페이스**: 클릭 가능한 요소 cursor: pointer 적용

### 🛠️ 기술적 구현 세부사항

#### 대시보드 차트 클릭 기능
```typescript
const handleCategoryClick = (category: string) => {
  navigate(`/search?q=${encodeURIComponent(category)}`);
};

// PieChart onClick 이벤트
onClick={(data) => {
  if (data && data.category) {
    handleCategoryClick(data.category);
  }
}}
```

#### 검색 페이지 URL 파라미터 처리
```typescript
useEffect(() => {
  const searchParams = new URLSearchParams(location.search);
  const queryParam = searchParams.get('q');
  if (queryParam) {
    setSearchQuery(queryParam);
    executeSearch(queryParam);
  }
}, [location.search]);
```

#### 태그 데이터 정리 스크립트
- 건설/공사 키워드가 있는 입찰에서 "소프트웨어" 태그 자동 제거
- 정규식 기반 컨텍스트 분석으로 잘못된 분류 감지
- 27건 → 7건으로 "소프트웨어" 카테고리 정제

### 📊 개선된 사용자 플로우
```
대시보드 카테고리 차트 → 특정 카테고리 클릭 →
자동으로 /search?q=카테고리명 이동 → 해당 카테고리 입찰 결과 표시
```

### 🎯 다음 우선순위 작업
1. **알림등록 화면 작업** - 사용자 맞춤 알림 설정
2. **북마크 기능 구현** - 관심 입찰 저장 및 관리
3. **AI 매칭 기능 구현** - 개인화된 입찰 추천

---

## Project Context Summary (2025-09-26 오후 업데이트)

### 🚀 프로젝트 현황
- **현재 날짜**: 2025년 9월 26일
- **단계**: ✅ **Phase 3 전체 사용자 인터페이스 구현 완료**
- **프로젝트명**: ODIN-AI (공공입찰 정보 분석 플랫폼)

### ✅ 완료된 작업 (2025-09-26 오후 기준)

#### 📱 프론트엔드 페이지 완전 구현 (2025-09-26 오후)
- ✅ **페이지 구조 개편**
  - 입찰목록 페이지 제거 (입찰검색과 중복)
  - 알림설정 페이지 신규 추가
- ✅ **알림설정 페이지 (Notifications.tsx)**
  - 이메일/푸시 알림 설정 (SMS 제외 - 비용 절감)
  - 키워드별 알림 등록 (최대 10개)
  - 가격 범위 설정 기능
  - 일일 다이제스트 옵션
- ✅ **프로필 페이지 (Profile.tsx)**
  - 개인정보 편집 (이름, 회사, 직책 등)
  - 활동 통계 대시보드
  - 비밀번호 변경 기능
  - 최근 활동 내역 표시
- ✅ **설정 페이지 (Settings.tsx)**
  - 앱 설정 (다크모드, 언어, 자동저장)
  - 알림 설정 (이메일, 푸시, 소리)
  - 개인정보 및 보안 관리
  - 데이터 내보내기/삭제
  - 계정 삭제 기능
- ✅ **구독관리 페이지 (Subscription.tsx)**
  - 3단계 요금제 비교 (베이직/프로/엔터프라이즈)
  - 실시간 사용량 모니터링
  - 결제 내역 관리
  - 플랜 업그레이드/취소
- ✅ **UI/UX 버그 수정**
  - 프로필 드롭다운 메뉴 자동 닫기 구현
  - Material-UI 일관성 개선

#### 🔧 대시보드 및 검색 개선 (2025-09-26 오전)
- ✅ 대시보드 차트 클릭 기능 추가
- ✅ 태그 기반 검색 API 개선
- ✅ 잘못된 태그 분류 정리 (소프트웨어 20개)
- ✅ 검색 페이지 인기 태그 버튼 추가

#### 🔧 배치 시스템 문제 해결 (2025-09-26 오전)
- ✅ 가상환경 활성화로 PDF 처리 성공
- ✅ 처리 성공률 93.9% 달성 (355/380)

### ✅ 완료된 작업 (2025-09-25 기준)

#### 🧪 테스트 자동화 시스템 구축 (2025-09-25 오후)
- ✅ **200개 테스트 체크리스트 및 자동화 완료**
  - 10개 카테고리 215개 테스트 구현
  - 테스트 성공률: 98.6% (212/215 통과)
  - 초기 87.4% → 최종 98.6% (11.2% 개선)
- ✅ **FastAPI 백엔드 API 개선**
  - 인증/인가: JWT 토큰, XSS 방어 강화
  - 검색 API: 500자 제한, 필터링, 정렬
  - 북마크 API: bid_notice_no 기반 처리
  - AI 추천: 콘텐츠 기반, 협업 필터링
  - 대시보드: 5개 통계 엔드포인트
  - 구독/결제: 4개 플랜 (Free/Basic/Pro/Enterprise)
  - 알림 시스템: 규칙 CRUD 작업
- ✅ **데이터베이스 스키마 개선**
  - user_bookmarks: bid_notice_no 컬럼 추가
  - bid_extracted_info: extracted_data JSONB 컬럼
  - 인덱스 최적화 및 JSONB 쿼리 지원

#### 🔍 검색 시스템 완성 (2025-09-25 오전)
- ✅ **실제 DB 연동 완료**
  - PostgreSQL 69개 공고 데이터 실시간 검색
  - 검색 필터: 날짜, 가격, 기관, 상태
  - 정렬: 관련도순, 날짜순, 가격순
- ✅ **대시보드 API DB 연동**
  - 실시간 통계: 총 69건, 활성 63건, 총액 385억
  - 마감임박 공고 표시
  - AI 추천 시스템 (예정가격 기반)
- ✅ **프론트엔드 통합**
  - React + TypeScript 검색 UI
  - Material-UI 컴포넌트
  - React Query v5 상태관리
  - 실시간 자동완성 및 필터링

### ✅ 완료된 작업 (2025-09-24 기준)

#### 📊 배치 시스템 테스트 (2025-09-24)
- ✅ 배치 프로그램 정상 작동 확인
- ✅ 오늘 날짜 공고 69개 수집 성공
- ✅ 문서 처리 성공률 94% (63/67)
- ⚠️ ZIP 파일 처리 미지원 (1개 스킵)
- ⚠️ HWPX 파일 일부 실패 (3개)

#### 📊 데이터 수집 및 처리 시스템
- ✅ 공공데이터포털 API 연동 완료 (95개 최신 공고 수집)
- ✅ 표 파싱 시스템 구현 (100% 성공률, 17/17 파일)
- ✅ 고도화된 정보 추출 시스템 구현
  - 공사기간 (duration_days, duration_text)
  - 지역제한 (region_restriction)
  - 하도급 규정 (subcontract_allowed, subcontract_ratio)
  - 자격요건 (qualification_summary)
  - 특수조건 (special_conditions)
- ✅ 데이터베이스 스키마 확장 (7개 신규 컬럼 추가)

#### 🔧 시스템 개선사항
- ✅ 배치 처리 시스템 구현 (Small/Medium/Large/XLarge)
- ✅ 병렬 처리 구현 (최대 20개 동시 처리)
- ✅ 타임아웃 설정 관리 시스템
- ✅ 설정 관리 시스템 (src/core/config.py)
- ✅ 디렉토리 구조 최적화

### 📁 프로젝트 구조

```
odin-ai/
├── backend/               # FastAPI 백엔드
│   ├── api/              # API 라우트
│   ├── services/         # 비즈니스 로직
│   └── database/         # DB 모델
├── src/                  # 핵심 모듈
│   ├── collector/        # 데이터 수집
│   ├── services/         # 문서 처리 서비스
│   ├── database/         # 데이터베이스 모델
│   └── core/            # 설정 관리
├── storage/              # 파일 저장소
│   ├── downloads/        # 다운로드 파일
│   └── markdown/         # 변환된 MD 파일
├── test_scripts/         # 테스트 스크립트
└── tools/               # 외부 도구
    ├── hwp-viewer/      # HWP 처리 도구
    └── pdf-viewer/      # PDF 처리 도구
```

### 🛠️ 기술 스택

#### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + SQLAlchemy (확장 스키마)
- **Queue**: Celery + Redis (예정)
- **비동기 처리**: asyncio, aiohttp

#### 문서 처리 및 정보 추출
- **HWP**: hwp5txt + 고도화 파서
- **표 파싱**: regex 기반 패턴 매칭
- **정보 추출**: EnhancedInfoExtractor
- **신뢰도 평가**: confidence_score 시스템

### 📈 성능 지표

- **API 수집**: 95개 공고 (현재 날짜 기준)
- **표 파싱 성공률**: 100% (17/17 파일)
- **정보 추출 카테고리**:
  - prices: 95개 (예정가격)
  - schedule: 285개 (일정 정보)
  - qualifications: 95개 (자격요건)
  - duration: 42개 (공사기간)
  - region: 38개 (지역제한)
  - subcontract: 45개 (하도급)
- **처리 속도**: 실시간 처리 가능
- **테스트 커버리지**: 98.6% (212/215 테스트 통과)
  - 완벽한 카테고리: AUTH, SEARCH, REC, DASH, SUB, DB, PERF, SEC

### 🎯 다음 단계 (Phase 3)

1. **AI 분석 기능**
   - GPT-4 통합
   - RAG 시스템 구현
   - 입찰 성공률 예측 모델
   - 자동 요약 및 인사이트 생성

2. **고급 검색 기능**
   - 벡터 임베딩 검색
   - 유사 공고 추천
   - 자연어 검색 처리

3. **사용자 경험 개선**
   - 실시간 알림 시스템
   - 개인화 대시보드
   - 모바일 반응형 최적화

### 🔑 주요 명령어

```bash
# 빠른 시작
./start-simple.sh         # 가장 간단한 실행
./quick-start.sh         # 새 터미널로 실행
./restart.sh             # 재시작 스크립트

# 프론트엔드 전체 스택
cd frontend
./start-all.sh          # Docker 포함 전체 실행

# 배치 실행
python batch/production_batch.py         # 프로덕션 배치
TEST_MODE=true python batch/production_batch.py  # 테스트 모드

# 개별 서버 실행
python -m uvicorn backend.main:app --reload --port 8000  # 백엔드
cd frontend && npm start                                  # 프론트엔드
```

### ⚠️ 주의사항

1. **개인정보 보호**
   - 로그에 개인정보 절대 포함 금지
   - 민감 정보는 환경변수로 관리

2. **대용량 처리**
   - 1000개 이상: XLarge 배치 사용
   - 메모리 관리 주의
   - 타임아웃 설정 확인

3. **파일 처리**
   - storage 디렉토리 권한 확인
   - 파일명 인코딩 주의 (한글)
   - 압축 파일 내부 구조 확인

### 📝 최근 변경사항 (2025-09-25)

- ✅ 200개 테스트 자동화 시스템 구축
- ✅ FastAPI 백엔드 API 대폭 개선
- ✅ 테스트 성공률 87.4% → 98.6% 달성
- ✅ 구독/결제 API 완전 구현
- ✅ AI 추천 시스템 강화
- ✅ 알림 시스템 CRUD 구현
- ✅ XSS 방어 및 보안 강화

### 📝 이전 변경사항 (2025-09-23)

- ✅ 날짜 처리 오류 수정 (2025년 9월 현재 날짜로)
- ✅ API 필드명 수정 (presmptPrc → presmptPrce)
- ✅ 고도화된 정보 추출 시스템 구현
- ✅ 데이터베이스 스키마 확장 (7개 컬럼 추가)
- ✅ 프로젝트 루트 정리 (33개 파일 → testing/ 폴더로)
- ✅ 불필요한 디렉토리 삭제 (logs_backup 등)

### 🔧 트러블슈팅

**문제**: API 날짜 검색 오류 (과거 날짜 사용)
- **원인**: 환경 변수의 Today's date 미확인
- **해결**: 현재 날짜 확인 후 YYYYMMDDHHmm 형식 사용

**문제**: API 필드명 오류
- **원인**: presmptPrc (틀림) vs presmptPrce (맞음)
- **해결**: API 응답 구조 재확인 및 코드 수정

**문제**: 표 파싱 시 `<표>` 태그만 출력
- **원인**: 실제 표 데이터 추출 실패
- **해결**: regex 기반 패턴 매칭 시스템 구현

### 🏗️ Batch System Module Structure (2025-09-23)

배치 시스템이 모듈화되어 각 기능이 독립적으로 작동하며 디버깅이 용이합니다:

#### 📁 디렉토리 구조
```
batch/
├── modules/                  # 개별 기능 모듈
│   ├── collector.py         # API 수집 모듈
│   ├── downloader.py        # 파일 다운로드 모듈
│   ├── processor.py         # 문서 처리 모듈
│   └── email_reporter.py    # 이메일 보고 모듈
└── production_batch.py      # 메인 오케스트레이터
```

#### 1. **collector.py** (API 수집 모듈)
- 공공데이터포털 API에서 입찰공고 데이터 수집
- 담당 테이블:
  - `bid_announcements`: 공고 메타데이터 저장
  - `bid_documents`: 문서 정보 초기 생성

#### 2. **downloader.py** (파일 다운로드 모듈)
- HWP/PDF 파일 다운로드 및 로컬 저장
- 담당 테이블:
  - `bid_documents`: download_status, storage_path 업데이트

#### 3. **processor.py** (문서 처리 모듈)
- 다운로드된 문서를 마크다운으로 변환
- 정보 추출, 태그 생성, 일정 추출, 첨부파일 처리
- 담당 테이블:
  - `bid_documents`: processing_status, extracted_text 업데이트
  - `bid_extracted_info`: 추출된 정보 저장
  - `bid_schedule`: 일정 정보 저장
  - `bid_tags` & `bid_tag_relations`: 태그 생성 및 관계 설정
  - `bid_attachments`: 첨부파일 정보 저장

#### 4. **email_reporter.py** (이메일 보고 모듈)
- 배치 실행 결과를 HTML 형식으로 이메일 발송
- JSON 보고서 저장
- 담당 테이블: READ-ONLY (통계 수집만)

#### 5. **production_batch.py** (메인 오케스트레이터)
- 모든 모듈을 순차적으로 실행
- 실행 순서: 수집 → 다운로드 → 처리 → 보고
- TEST_MODE 지원 (DB 초기화 옵션)

#### 🚀 실행 방법
```bash
# ⚠️ 중요: 반드시 가상환경 활성화 필요 (PDF, Excel, DOCX 처리 라이브러리 때문)
source venv/bin/activate

# 1. 프로덕션 실행 (기존 데이터 유지하며 신규 데이터만 수집)
DATABASE_URL="postgresql://blockmeta@localhost:5432/odin_db" python batch/production_batch.py

# 2. DB 초기화 + 전체 재실행 (테이블 데이터 삭제 후 처음부터 수집)
DB_FILE_INIT=true TEST_MODE=false DATABASE_URL="postgresql://blockmeta@localhost:5432/odin_db" python batch/production_batch.py

# 3. 완전 초기화 (파일 + DB 모두 삭제 후 재실행)
rm -rf storage/documents/* storage/markdown/*
source venv/bin/activate
DB_FILE_INIT=true TEST_MODE=false DATABASE_URL="postgresql://blockmeta@localhost:5432/odin_db" python batch/production_batch.py

# 이메일 설정 (환경변수)
EMAIL_ENABLED=true
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com
EMAIL_TO=recipient@example.com
```

#### 📊 모듈별 역할 분담
- **데이터 입력**: collector.py, processor.py
- **데이터 갱신**: downloader.py, processor.py
- **읽기 전용**: email_reporter.py
- **조정 역할**: production_batch.py

## 📝 최근 작업 기록 (2025-09-26)

### ✅ 완료된 작업 - 오후 세션

#### 📱 프론트엔드 페이지 완전 구현
- **입찰목록 페이지 제거**: 입찰검색으로 통합
- **알림설정 페이지 신규 생성**:
  - 이메일/푸시 알림만 지원 (SMS 제외 - 비용 절감)
  - 키워드 알림 설정 기능
  - 가격 범위 설정 옵션
- **프로필 페이지 완성**:
  - 개인정보 관리 (이름, 이메일, 회사, 직책 등)
  - 활동 통계 대시보드 (검색 횟수, 북마크 수)
  - 비밀번호 변경 기능
  - 최근 활동 내역 표시
- **설정 페이지 완성**:
  - 앱 설정 (다크모드, 자동저장, 언어 선택)
  - 알림 설정 (이메일, 푸시, 소리)
  - 개인정보 및 보안 설정
  - 데이터 관리 (내보내기, 삭제)
  - 계정 관리 (삭제 기능 포함)
- **구독관리 페이지 완성**:
  - 3단계 요금제 (베이직 무료, 프로 29,000원, 엔터프라이즈 99,000원)
  - 실시간 사용량 모니터링 (검색, 북마크, 알림)
  - 결제 내역 테이블
  - 플랜 업그레이드/취소 기능

#### 🔧 UI/UX 개선사항
- **메뉴 구조 최적화**:
  - 입찰목록 제거, 알림설정 추가
  - 프로필 드롭다운 메뉴에 구독관리 링크
- **프로필 드롭다운 메뉴 버그 수정**:
  - 메뉴 항목 클릭 후 자동 닫기 구현
  - handleMenuClose() 호출 추가
- **Material-UI 기반 일관된 디자인**:
  - 모든 페이지 통일된 레이아웃
  - 반응형 디자인 적용

### ✅ 완료된 작업 - 오전 세션

#### 🔧 가상환경 활성화 문제 해결
- **문제**: PDF/Excel/DOCX 파일 처리 실패 (39개 → 23개)
- **원인**: 배치 실행 시 가상환경 미활성화로 라이브러리 없음
- **해결**: `source venv/bin/activate` 후 배치 실행
- **결과**: PDF 처리 100% 성공 (14개 실패 → 0개)

#### 🎨 대시보드 UI 개선
- **문제**: 카테고리 분포 차트의 레이블 겹침 현상
- **해결**: 파이차트에 범례 추가, 퍼센트만 차트 내 표시
- **변경사항**:
  - 차트 높이 300px → 350px
  - 범례를 통한 카테고리명과 건수 표시
  - Tooltip 문법 오류 수정

#### 📊 최종 배치 처리 결과
- **총 입찰공고**: 469개 수집
- **문서 처리 성공률**: 93.9% (355/380)
- **주요 카테고리 분포**:
  - 건설: 32.8% (349건)
  - 유지보수: 15.5% (165건)
  - 물품: 13.8% (147건)
  - 기계: 9.9% (105건)
  - 조경: 6.1% (65건)

#### 🔄 배치 프로그램 실행 방법 표준화
- **중요**: 반드시 가상환경 활성화 필요
- **완전 초기화**: `rm -rf storage/documents/* storage/markdown/*`
- **표준 실행**: `source venv/bin/activate && DB_FILE_INIT=true TEST_MODE=false DATABASE_URL="postgresql://blockmeta@localhost:5432/odin_db" python batch/production_batch.py`

### 🎯 현재 상태
- **프론트엔드**: 모든 핵심 페이지 구현 완료
- **백엔드**: API 연동 대기 (TODO 주석 포함)
- **배치 시스템**: 93.9% 성공률로 안정적 운영
- **UI/UX**: Material-UI 기반 완성된 디자인

### 🚀 다음 작업 예정
- 백엔드 API와 프론트엔드 연동
- Excel 파일 처리 개선 (22개 실패)
- AI 분석 기능 추가