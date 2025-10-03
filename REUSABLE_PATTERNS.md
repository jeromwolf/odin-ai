# 재사용 가능한 개발 패턴 및 방법론

ODIN-AI 프로젝트에서 검증된 개발 방법론과 아키텍처 패턴 모음

---

## 🎯 1. 모듈형 개발 방법론

### 핵심 원칙: "한 번에 하나씩, 독립적으로"

#### ✅ 기능 추가 체크리스트
```bash
□ 1. 현재 작동 중인 기능 목록 작성
□ 2. Git 브랜치 생성 (feature/기능명)
□ 3. 영향 범위 분석
□ 4. 독립 모듈로 개발
□ 5. 기존 기능 테스트
□ 6. 문제 없을 시에만 병합
```

#### 모듈 분리 원칙
```
project/
├── services/
│   ├── core.ts           # ⚠️ 절대 직접 수정 금지
│   ├── featureA.ts       # 기능 A 전용
│   └── featureB.ts       # 기능 B 전용 (새로 생성)
```

#### 공통 파일 수정 규칙
```typescript
// ❌ 잘못된 방법: 공통 파일 직접 수정
// core.ts 파일에 새 기능 추가
export async function newFeature() { ... }

// ✅ 올바른 방법: 별도 파일 생성 후 import
// featureB.ts 생성
import { coreClient } from './core';
export const featureBService = {
  doSomething: () => coreClient.process(...)
}
```

#### 단계별 개발 프로세스
```
1단계: 백엔드 API 독립 파일로 생성
2단계: 프론트엔드 서비스 독립 파일로 생성
3단계: 컴포넌트 독립 생성
4단계: 라우팅 추가 (App.tsx는 최소 수정)
5단계: 각 단계마다 기존 기능 테스트
```

---

## 🚨 2. 안전한 개발 전략

### 작업 전 안전 체크리스트
```bash
# 1. 현재 상태 스냅샷 저장
git status && git stash save "작업 전 백업"

# 2. 기존 기능 작동 확인
curl -s "http://localhost:8000/api/existing-feature" | jq .status

# 3. 영향 범위 분석서 작성
echo "# 작업: [기능명]" > impact.md
echo "- 수정할 파일: (새 파일만)" >> impact.md
echo "- 영향받지 않을 파일: (기존 파일 목록)" >> impact.md

# 4. 독립 브랜치 생성
git checkout -b feature/기능명

# 5. 롤백 계획 수립
echo "문제 발생 시: git stash && git checkout main" >> rollback.md
```

### 절대 금지 사항
```bash
# ❌ 절대 하지 말 것
1. 공통 파일 직접 수정 (main.py, api.ts, App.tsx)
2. 여러 기능 동시 작업
3. import 경로 일괄 변경
4. 테스트 없이 커밋
5. 큰 단위 변경

# ✅ 반드시 지킬 것
1. 새 기능은 새 파일에
2. 한 번에 하나씩만
3. 각 단계마다 테스트
4. 작은 단위로 커밋
5. 문제 시 즉시 롤백
```

### 안전한 파일 구조 설계
```
backend/
├── api/
│   ├── core.py          # 🔒 수정 금지
│   ├── existing.py      # 🔒 수정 금지
│   └── new_feature.py   # ✅ 새 기능 (독립)
│
├── services/            # 독립 서비스 모듈
│   ├── new_service.py   # ✅ 새 기능
│   └── another_service.py
│
└── main.py              # 🔒 최소한의 수정만
```

---

## 🏗️ 3. 배치 처리 시스템 아키텍처

### 모듈형 배치 시스템 구조
```
batch/
├── modules/                  # 개별 기능 모듈
│   ├── collector.py         # 데이터 수집 모듈
│   ├── downloader.py        # 파일 다운로드 모듈
│   ├── processor.py         # 문서 처리 모듈
│   └── reporter.py          # 결과 보고 모듈
└── production_batch.py      # 메인 오케스트레이터
```

### 배치 실행 플로우
```python
class BatchOrchestrator:
    def run(self):
        # Phase 1: 데이터 수집
        collector = CollectorModule()
        data = collector.collect()

        # Phase 2: 파일 다운로드
        downloader = DownloaderModule()
        files = downloader.download(data)

        # Phase 3: 데이터 처리
        processor = ProcessorModule()
        results = processor.process(files)

        # Phase 4: 결과 보고
        reporter = ReporterModule()
        reporter.send_report(results)
```

### 배치 크기 전략
```python
BATCH_SIZES = {
    'small': 10,      # 테스트용
    'medium': 50,     # 일반 운영
    'large': 200,     # 대량 처리
    'xlarge': 1000,   # 전체 재구축
}

def get_batch_size(total_items: int) -> str:
    if total_items < 50:
        return 'small'
    elif total_items < 200:
        return 'medium'
    elif total_items < 1000:
        return 'large'
    else:
        return 'xlarge'
```

### 에러 핸들링 전략
```python
class ResilientProcessor:
    def process_with_retry(self, item, max_retries=3):
        for attempt in range(max_retries):
            try:
                return self.process(item)
            except TemporaryError as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 지수 백오프
                    continue
                else:
                    self.log_failure(item, e)
            except PermanentError as e:
                self.log_failure(item, e)
                break
```

---

## 📊 4. React + TypeScript 프론트엔드 패턴

### React Query를 활용한 상태 관리
```typescript
// API 호출 및 캐싱
const { data, isLoading, error } = useQuery({
  queryKey: ['feature', id],
  queryFn: () => apiClient.getFeature(id),
  staleTime: 10000, // 10초간 캐시 유지
  gcTime: 300000,   // 5분 후 가비지 컬렉션
});

// 낙관적 업데이트
const mutation = useMutation({
  mutationFn: (data) => apiClient.updateFeature(data),
  onMutate: async (newData) => {
    // 이전 데이터 백업
    await queryClient.cancelQueries({ queryKey: ['feature'] });
    const previousData = queryClient.getQueryData(['feature']);

    // 낙관적 업데이트
    queryClient.setQueryData(['feature'], newData);

    return { previousData };
  },
  onError: (err, newData, context) => {
    // 에러 시 롤백
    queryClient.setQueryData(['feature'], context.previousData);
  },
  onSuccess: () => {
    // 성공 시 캐시 무효화
    queryClient.invalidateQueries({ queryKey: ['feature'] });
  },
});
```

### Material-UI 컴포넌트 패턴
```typescript
// 일관된 레이아웃 구조
<Box sx={{ maxWidth: 1200, margin: '0 auto', padding: 3 }}>
  <Paper elevation={3} sx={{ padding: 3, marginBottom: 3 }}>
    <Typography variant="h5" gutterBottom>
      제목
    </Typography>
    <Divider sx={{ marginY: 2 }} />
    {/* 컨텐츠 */}
  </Paper>
</Box>

// 반응형 그리드
<Grid container spacing={3}>
  <Grid item xs={12} md={6} lg={4}>
    <Card>
      {/* 카드 내용 */}
    </Card>
  </Grid>
</Grid>

// 드롭다운 메뉴 위치 안정화
<Menu
  anchorEl={anchorEl}
  open={Boolean(anchorEl)}
  onClose={handleClose}
  anchorOrigin={{
    vertical: 'bottom',
    horizontal: 'right',
  }}
  transformOrigin={{
    vertical: 'top',
    horizontal: 'right',
  }}
  slotProps={{
    paper: {
      sx: {
        overflow: 'visible',
        filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
        mt: 1.5,
      },
    }
  }}
/>
```

### 사용자 경험 최적화 패턴
```typescript
// 디바운스 검색
const [searchQuery, setSearchQuery] = useState('');
const debouncedSearch = useMemo(
  () => debounce((value: string) => {
    executeSearch(value);
  }, 300),
  []
);

useEffect(() => {
  debouncedSearch(searchQuery);
}, [searchQuery, debouncedSearch]);

// 무한 스크롤
const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
  queryKey: ['items'],
  queryFn: ({ pageParam = 0 }) => apiClient.getItems(pageParam),
  getNextPageParam: (lastPage, pages) => lastPage.nextCursor,
});

// 낙관적 UI 업데이트
const handleToggle = async (id: string) => {
  // 즉시 UI 반영
  setLocalState(prev => !prev);

  try {
    await apiClient.toggle(id);
    queryClient.invalidateQueries(['items']);
  } catch (error) {
    // 실패 시 되돌림
    setLocalState(prev => !prev);
    showErrorMessage('작업 실패');
  }
};
```

---

## 🔐 5. FastAPI 백엔드 아키텍처

### API 라우터 구조
```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from .models import Item, ItemCreate
from .dependencies import get_current_user

router = APIRouter(prefix="/api/items", tags=["items"])

@router.get("/", response_model=List[Item])
async def get_items(
    skip: int = 0,
    limit: int = 100,
    user = Depends(get_current_user)
):
    """아이템 목록 조회"""
    return await ItemService.get_items(user.id, skip, limit)

@router.post("/", response_model=Item)
async def create_item(
    item: ItemCreate,
    user = Depends(get_current_user)
):
    """아이템 생성"""
    return await ItemService.create_item(user.id, item)
```

### 데이터베이스 연결 관리
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_size=20,
    max_overflow=40
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@asynccontextmanager
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### 에러 핸들링 패턴
```python
from fastapi import HTTPException, status

class AppException(Exception):
    """기본 애플리케이션 예외"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message}
    )

# 사용 예시
async def get_item(item_id: int):
    item = await db.get(Item, item_id)
    if not item:
        raise AppException(
            f"Item {item_id} not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    return item
```

---

## 🔄 6. 실시간 모니터링 및 디버깅

### 실시간 API 상태 확인
```bash
#!/bin/bash
# monitor.sh - API 상태 실시간 모니터링

while true; do
  echo "=== $(date) ==="

  # 기능별 API 테스트
  echo "Search API: $(curl -s localhost:8000/api/search?q=test | jq -r .total // 'FAIL')"
  echo "Profile API: $(curl -s localhost:8000/api/profile | jq -r .email // 'FAIL')"
  echo "Dashboard API: $(curl -s localhost:8000/api/dashboard | jq -r .totalItems // 'FAIL')"

  echo ""
  sleep 5
done
```

### 로깅 전략
```python
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging(app_name: str, log_level: str = "INFO"):
    """구조화된 로깅 설정"""

    # 로그 디렉토리 생성
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 파일 핸들러 (10MB 크기, 5개 백업)
    file_handler = RotatingFileHandler(
        log_dir / f"{app_name}.log",
        maxBytes=10*1024*1024,
        backupCount=5
    )
    file_handler.setFormatter(formatter)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # 루트 로거 설정
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# ⚠️ 개인정보 보호 로깅
def safe_log(logger, message: str, user_id: str = None):
    """개인정보를 제외한 안전한 로깅"""
    if user_id:
        # 사용자 ID는 해시 처리
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]
        logger.info(f"{message} (user_hash: {user_hash})")
    else:
        logger.info(message)
```

---

## 🧪 7. 테스트 자동화 시스템

### 테스트 구조
```python
import pytest
from httpx import AsyncClient

class TestFeatureAPI:
    """기능별 API 테스트"""

    @pytest.mark.asyncio
    async def test_create_item(self, async_client: AsyncClient):
        """아이템 생성 테스트"""
        response = await async_client.post(
            "/api/items",
            json={"name": "Test Item", "price": 1000}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Item"
        assert data["price"] == 1000

    @pytest.mark.asyncio
    async def test_get_items_pagination(self, async_client: AsyncClient):
        """페이지네이션 테스트"""
        response = await async_client.get(
            "/api/items?skip=0&limit=10"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
```

### E2E 테스트 체크리스트
```python
FEATURE_TESTS = {
    "인증": [
        "회원가입 성공",
        "로그인 성공",
        "JWT 토큰 발급",
        "인증 실패 처리",
        "로그아웃"
    ],
    "검색": [
        "키워드 검색",
        "필터링",
        "정렬",
        "페이지네이션",
        "빈 결과 처리"
    ],
    "CRUD": [
        "생성 성공",
        "조회 성공",
        "수정 성공",
        "삭제 성공",
        "권한 검증"
    ]
}

def run_all_tests():
    """모든 테스트 자동 실행"""
    results = {"total": 0, "passed": 0, "failed": 0}

    for category, tests in FEATURE_TESTS.items():
        print(f"\n=== {category} 테스트 ===")
        for test_name in tests:
            results["total"] += 1
            try:
                # 테스트 실행
                run_test(category, test_name)
                results["passed"] += 1
                print(f"✅ {test_name}")
            except Exception as e:
                results["failed"] += 1
                print(f"❌ {test_name}: {e}")

    # 결과 요약
    success_rate = (results["passed"] / results["total"]) * 100
    print(f"\n성공률: {success_rate:.1f}% ({results['passed']}/{results['total']})")
```

---

## 📈 8. 성능 최적화 패턴

### 데이터베이스 쿼리 최적화
```python
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload

# ❌ N+1 쿼리 문제
async def get_users_bad():
    users = await db.execute(select(User))
    for user in users.scalars():
        # 각 사용자마다 별도 쿼리 발생
        user.items  # N+1 문제!

# ✅ Eager Loading
async def get_users_good():
    stmt = select(User).options(
        selectinload(User.items),  # 관계 데이터 미리 로드
        joinedload(User.profile)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

# 인덱스 활용
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)  # 인덱스
    created_at = Column(DateTime, index=True)  # 인덱스
    status = Column(String, index=True)  # 인덱스

    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),  # 복합 인덱스
    )
```

### 캐싱 전략
```python
from functools import lru_cache
from aiocache import cached
import redis.asyncio as redis

# 메모리 캐시 (간단한 데이터)
@lru_cache(maxsize=128)
def get_config(key: str):
    """설정값 캐싱"""
    return load_config(key)

# Redis 캐시 (분산 환경)
redis_client = redis.from_url("redis://localhost")

@cached(ttl=300)  # 5분 캐시
async def get_popular_items():
    """인기 아이템 목록 캐싱"""
    items = await db.execute(
        select(Item)
        .order_by(Item.view_count.desc())
        .limit(10)
    )
    return items.scalars().all()

# 수동 캐시 무효화
async def update_item(item_id: int, data: dict):
    """아이템 수정 시 캐시 삭제"""
    await db.update(Item, item_id, data)
    await redis_client.delete(f"item:{item_id}")
```

---

## 🔒 9. 보안 모범 사례

### JWT 인증 구현
```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta = None):
    """JWT 토큰 생성"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    """JWT 토큰 검증"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """현재 사용자 조회"""
    user_id = verify_token(token)
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

### XSS 방어
```python
import bleach
from markupsafe import escape

def sanitize_html(content: str) -> str:
    """HTML 살균 처리"""
    allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li']
    allowed_attrs = {'a': ['href', 'title']}
    return bleach.clean(
        content,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True
    )

def safe_output(user_input: str) -> str:
    """사용자 입력 안전 출력"""
    return escape(user_input)
```

---

## 🎯 10. 프로젝트 시작 템플릿

### 빠른 시작 스크립트
```bash
#!/bin/bash
# quick-start.sh - 프로젝트 빠른 시작

set -e  # 에러 시 즉시 중단

echo "🚀 프로젝트 시작 중..."

# 1. 환경변수 확인
if [ ! -f .env ]; then
    echo "❌ .env 파일이 없습니다."
    exit 1
fi

# 2. 가상환경 활성화
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ 가상환경이 없습니다. python -m venv venv 실행 필요"
    exit 1
fi

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 데이터베이스 마이그레이션
alembic upgrade head

# 5. 백엔드 서버 시작 (백그라운드)
python -m uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# 6. 프론트엔드 서버 시작
cd frontend
npm install
npm start &
FRONTEND_PID=$!

# 7. 종료 핸들러
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT

echo "✅ 서버 시작 완료!"
echo "   - 백엔드: http://localhost:8000"
echo "   - 프론트엔드: http://localhost:3000"
echo "   - Ctrl+C로 종료"

wait
```

### 환경변수 템플릿
```bash
# .env.example

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (선택)
EMAIL_ENABLED=false
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Redis (선택)
REDIS_URL=redis://localhost:6379

# 개발 모드
DEBUG=true
LOG_LEVEL=INFO
```

---

## 📚 11. 개발 워크플로우 체크리스트

### 새 기능 개발 플로우
```markdown
## 기능 개발 체크리스트

### Phase 1: 계획 (30분)
- [ ] 기능 요구사항 문서화
- [ ] 영향 범위 분석
- [ ] 데이터베이스 스키마 변경 필요 여부 확인
- [ ] API 엔드포인트 설계
- [ ] 프론트엔드 컴포넌트 구조 설계

### Phase 2: 백엔드 구현 (2-4시간)
- [ ] 새 API 파일 생성 (api/new_feature.py)
- [ ] 서비스 로직 구현 (services/new_feature_service.py)
- [ ] 데이터베이스 모델 추가/수정
- [ ] 유닛 테스트 작성
- [ ] API 문서 업데이트 (Swagger)

### Phase 3: 프론트엔드 구현 (2-4시간)
- [ ] 서비스 파일 생성 (services/newFeatureService.ts)
- [ ] 컴포넌트 생성 (components/NewFeature.tsx)
- [ ] React Query 훅 설정
- [ ] 라우팅 추가 (App.tsx 최소 수정)
- [ ] UI/UX 테스트

### Phase 4: 통합 테스트 (1-2시간)
- [ ] E2E 테스트 실행
- [ ] 기존 기능 회귀 테스트
- [ ] 성능 테스트
- [ ] 에러 핸들링 검증

### Phase 5: 배포 준비 (30분)
- [ ] 환경변수 확인
- [ ] 마이그레이션 스크립트 준비
- [ ] 롤백 계획 수립
- [ ] 문서 업데이트
```

---

## 🎓 12. 핵심 교훈 요약

### DO (반드시 할 것)
1. **모듈화**: 새 기능은 항상 독립 파일로
2. **테스트**: 각 단계마다 기존 기능 검증
3. **작은 커밋**: 기능별로 세분화된 커밋
4. **문서화**: 코드와 함께 문서 업데이트
5. **롤백 준비**: 언제든 되돌릴 수 있게

### DON'T (절대 하지 말 것)
1. **공통 파일 수정**: core, main, App 직접 수정 금지
2. **동시 작업**: 여러 기능 한꺼번에 작업 금지
3. **무분별한 import 변경**: 기존 경로 유지
4. **큰 단위 변경**: 한 번에 너무 많이 수정
5. **개인정보 로깅**: 절대로 로그에 개인정보 포함 금지

### 성공 지표
- ✅ 새 기능 추가해도 기존 기능 100% 유지
- ✅ 테스트 성공률 95% 이상
- ✅ 배포 후 롤백 필요 없음
- ✅ 코드 리뷰 통과율 90% 이상

---

## 📞 트러블슈팅 가이드

### 문제: 새 기능 추가 후 기존 기능 실패
```bash
# 즉시 롤백
git stash save "응급백업_$(date +%Y%m%d_%H%M%S)"
git checkout main
git reset --hard HEAD

# 서버 재시작
pkill -f uvicorn
python -m uvicorn main:app --reload
```

### 문제: 데이터베이스 마이그레이션 실패
```bash
# 마이그레이션 롤백
alembic downgrade -1

# 스키마 확인
psql -d dbname -c "\d tablename"

# 수동 수정 후 재시도
alembic upgrade head
```

### 문제: 프론트엔드 빌드 실패
```bash
# 캐시 삭제
rm -rf node_modules package-lock.json
npm install

# 타입 에러 확인
npm run type-check

# 린트 확인
npm run lint
```

---

## 🔐 13. 개인정보 보호 및 로깅 관리

### 핵심 원칙: 절대 로그에 개인정보 남기지 않기

#### ⚠️ 개인정보 보호 규칙
```python
# ❌ 절대 금지 - 개인정보 로그 출력
logger.info(f"사용자 로그인: {user.email}")  # 이메일 노출
logger.debug(f"비밀번호 해시: {hashed_pw}")  # 보안 정보 노출
logger.info(f"전화번호: {user.phone}")       # 개인정보 노출

# ✅ 안전한 로깅 - 해시 처리
import hashlib

def safe_user_id(user_id: str) -> str:
    """사용자 ID를 해시 처리하여 안전하게 로깅"""
    return hashlib.sha256(str(user_id).encode()).hexdigest()[:8]

logger.info(f"사용자 로그인 성공 (user_hash: {safe_user_id(user.id)})")
```

#### 로깅 시스템 구조
```python
from loguru import logger
from pathlib import Path
from datetime import datetime

# 로그 디렉토리 설정
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 로그 파일 설정 (날짜별 분리, 자동 로테이션)
log_file = log_dir / f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logger.add(
    str(log_file),
    rotation="10 MB",      # 10MB마다 새 파일
    retention="30 days",   # 30일간 보관
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
)
```

#### 로그 파일 관리 전략
```python
import os
from pathlib import Path
from datetime import datetime, timedelta

class LogManager:
    """로그 파일 관리 클래스"""

    def __init__(self, log_dir: str = "logs", retention_days: int = 30):
        self.log_dir = Path(log_dir)
        self.retention_days = retention_days
        self.log_dir.mkdir(exist_ok=True)

    def cleanup_old_logs(self):
        """오래된 로그 파일 삭제"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)

        for log_file in self.log_dir.glob("*.log"):
            # 파일 수정 시간 확인
            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)

            if file_mtime < cutoff_date:
                logger.info(f"오래된 로그 삭제: {log_file.name}")
                log_file.unlink()

    def get_log_size(self) -> dict:
        """로그 디렉토리 크기 확인"""
        total_size = 0
        file_count = 0

        for log_file in self.log_dir.glob("*.log"):
            total_size += log_file.stat().st_size
            file_count += 1

        return {
            "total_size_mb": total_size / (1024 * 1024),
            "file_count": file_count,
            "directory": str(self.log_dir)
        }

    def archive_logs(self, archive_name: str = None):
        """로그 파일 압축 아카이브"""
        import zipfile

        if not archive_name:
            archive_name = f"logs_archive_{datetime.now().strftime('%Y%m%d')}.zip"

        archive_path = self.log_dir / archive_name

        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for log_file in self.log_dir.glob("*.log"):
                zipf.write(log_file, log_file.name)
                logger.info(f"로그 아카이브: {log_file.name}")

        logger.info(f"아카이브 생성 완료: {archive_path}")
        return archive_path
```

#### 로그 레벨 전략
```python
import logging
import os

def setup_logging(app_name: str):
    """환경별 로그 레벨 설정"""

    # 환경변수로 로그 레벨 제어
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # 개발/프로덕션 환경 구분
    is_production = os.getenv("ENVIRONMENT", "development") == "production"

    if is_production:
        # 프로덕션: 중요한 로그만
        logger.add(
            f"logs/{app_name}_production.log",
            level="WARNING",  # WARNING 이상만
            rotation="50 MB",
            retention="90 days"
        )
    else:
        # 개발: 모든 로그
        logger.add(
            f"logs/{app_name}_dev.log",
            level="DEBUG",
            rotation="10 MB",
            retention="7 days"
        )

    logger.info(f"로깅 시작: {app_name} (레벨: {log_level})")
```

#### XSS 방어 및 입력 검증
```python
import html
from pydantic import BaseModel, validator, EmailStr

class SafeUserInput(BaseModel):
    """안전한 사용자 입력 처리"""

    full_name: str
    company: str
    email: EmailStr

    @validator('full_name', 'company')
    def sanitize_text(cls, v):
        """HTML 이스케이프 처리"""
        if v:
            return html.escape(v.strip())
        return v

# 사용 예시
def create_user(user_data: SafeUserInput):
    # 이미 sanitize된 데이터 사용
    safe_full_name = user_data.full_name  # HTML 이스케이프 완료
    safe_company = user_data.company      # HTML 이스케이프 완료

    # 데이터베이스 저장
    cursor.execute(
        "INSERT INTO users (full_name, company) VALUES (%s, %s)",
        (safe_full_name, safe_company)
    )
```

#### 비밀번호 관리
```python
from passlib.context import CryptContext

# bcrypt 사용 (권장)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)

# ⚠️ 절대 금지
# logger.info(f"비밀번호: {password}")  # 원본 노출
# logger.debug(f"해시: {hashed}")       # 해시도 노출 금지

# ✅ 안전한 로깅
logger.info("비밀번호 검증 성공")  # 결과만 로깅
```

#### 사용자 정보 관리 모범 사례
```python
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class UserManager:
    """사용자 정보 관리 클래스"""

    @staticmethod
    def safe_log_user_action(user_id: int, action: str):
        """사용자 액션을 안전하게 로깅"""
        user_hash = hashlib.sha256(str(user_id).encode()).hexdigest()[:8]
        logger.info(f"액션: {action} (user_hash: {user_hash})")

    @staticmethod
    def get_user_display_name(user: dict) -> str:
        """표시용 사용자 이름 (개인정보 제외)"""
        username = user.get('username', 'Unknown')
        # 이메일이나 실명 대신 사용자명만
        return username

    @staticmethod
    def anonymize_email(email: str) -> str:
        """이메일 일부 마스킹"""
        if '@' not in email:
            return "***"
        local, domain = email.split('@')
        if len(local) <= 2:
            masked_local = '*' * len(local)
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        return f"{masked_local}@{domain}"

    @staticmethod
    def anonymize_phone(phone: str) -> str:
        """전화번호 마스킹"""
        if len(phone) < 4:
            return '***'
        return phone[:3] + '*' * (len(phone) - 6) + phone[-3:]

# 사용 예시
user = {"id": 123, "email": "user@example.com", "phone": "01012345678"}

# ❌ 잘못된 방법
logger.info(f"사용자 정보: {user}")

# ✅ 올바른 방법
UserManager.safe_log_user_action(user['id'], "로그인")
logger.info(f"이메일: {UserManager.anonymize_email(user['email'])}")
logger.info(f"전화: {UserManager.anonymize_phone(user['phone'])}")
```

#### 데이터베이스 로깅 (감사 로그)
```python
from datetime import datetime

def log_user_activity(conn, user_id: int, action: str, details: dict = None):
    """사용자 활동 감사 로그 (DB 저장)"""

    # 개인정보 제외한 메타데이터만 저장
    cursor = conn.cursor()
    query = """
        INSERT INTO user_activity_logs (
            user_id, action, ip_address, user_agent, created_at
        ) VALUES (%s, %s, %s, %s, %s)
    """

    cursor.execute(query, (
        user_id,
        action,
        details.get('ip_address') if details else None,
        details.get('user_agent') if details else None,
        datetime.utcnow()
    ))

    conn.commit()

    # ⚠️ 개인정보는 로그에 남기지 않음
    logger.info(f"사용자 활동 기록됨: {action}")
```

#### 로그 검색 및 분석 도구
```python
import re
from pathlib import Path
from collections import Counter

class LogAnalyzer:
    """로그 파일 분석 도구"""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)

    def count_errors(self, pattern: str = "ERROR") -> int:
        """에러 로그 카운트"""
        count = 0
        for log_file in self.log_dir.glob("*.log"):
            with open(log_file, 'r', encoding='utf-8') as f:
                count += sum(1 for line in f if pattern in line)
        return count

    def get_top_errors(self, n: int = 10) -> list:
        """가장 많이 발생한 에러 TOP N"""
        errors = Counter()

        for log_file in self.log_dir.glob("*.log"):
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'ERROR' in line:
                        # 에러 메시지 추출 (개인정보 제외)
                        match = re.search(r'ERROR.*?- (.+)', line)
                        if match:
                            error_msg = match.group(1).strip()
                            errors[error_msg] += 1

        return errors.most_common(n)

    def generate_daily_report(self) -> dict:
        """일일 로그 리포트 생성"""
        today = datetime.now().strftime('%Y%m%d')

        report = {
            'date': today,
            'total_logs': 0,
            'errors': 0,
            'warnings': 0,
            'info': 0
        }

        for log_file in self.log_dir.glob(f"*{today}*.log"):
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    report['total_logs'] += 1
                    if 'ERROR' in line:
                        report['errors'] += 1
                    elif 'WARNING' in line:
                        report['warnings'] += 1
                    elif 'INFO' in line:
                        report['info'] += 1

        return report
```

#### 환경변수로 민감정보 관리
```bash
# .env 파일 (절대 Git에 커밋 금지)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SECRET_KEY=your-secret-key-here
JWT_SECRET=jwt-secret-key
SMTP_PASSWORD=email-app-password

# .env.example 파일 (Git에 커밋)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SECRET_KEY=change-this-in-production
JWT_SECRET=change-this-in-production
SMTP_PASSWORD=your-smtp-password
```

```python
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경변수 사용
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

# ⚠️ 절대 금지
# logger.info(f"DB URL: {DATABASE_URL}")  # 민감정보 노출

# ✅ 안전한 로깅
logger.info("데이터베이스 연결 성공")
```

#### .gitignore 설정
```bash
# .gitignore - 민감정보 파일 제외

# 환경변수
.env
.env.local
.env.production

# 로그 파일
logs/
*.log

# 데이터베이스 백업
*.sql
*.dump

# 개인정보 포함 가능성 있는 파일
storage/downloads/*
storage/documents/*
*.csv  # 사용자 데이터 포함 가능
*.xlsx

# 설정 파일
config/secrets.json
config/production.json
```

### 🔒 보안 체크리스트

#### 개발 단계
- [ ] 모든 사용자 입력에 XSS 방어 (html.escape)
- [ ] 비밀번호는 bcrypt로 해싱
- [ ] 환경변수로 민감정보 관리
- [ ] .gitignore에 .env, logs/ 추가
- [ ] 개인정보는 절대 로그에 남기지 않기

#### 프로덕션 배포 전
- [ ] 로그 레벨 WARNING 이상으로 설정
- [ ] 로그 파일 자동 로테이션 설정 (10-50MB)
- [ ] 로그 보관 기간 설정 (30-90일)
- [ ] 데이터베이스 감사 로그 활성화
- [ ] 정기적인 로그 검토 프로세스 수립

#### 운영 중
- [ ] 주간 로그 분석 (에러 패턴 파악)
- [ ] 월간 보안 감사 (개인정보 노출 체크)
- [ ] 로그 디렉토리 용량 모니터링
- [ ] 오래된 로그 아카이브 및 삭제

---

이 문서는 ODIN-AI 프로젝트에서 검증된 실전 패턴들을 정리한 것입니다.
다른 프로젝트에 적용할 때는 프로젝트 특성에 맞게 조정하여 사용하세요.
