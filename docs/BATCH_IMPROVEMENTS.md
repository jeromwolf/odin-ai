# 📋 배치 시스템 개선사항
**작성일**: 2025-09-24
**상태**: 개선 예정

## 🎯 개선 우선순위

### 🔴 Priority 1: 즉시 개선 필요
#### 1. 중복 체크 로직 개선
**파일**: `batch/modules/collector.py:164-214`
**현재 문제**:
```python
# 단순히 존재 여부만 체크
if not existing:
    # 신규 저장
else:
    logger.debug(f"⏭️ 이미 존재: {bid_notice_no}")
```
**개선 방안**:
```python
if existing:
    # 업데이트 필요 여부 체크
    if existing.updated_at < item.get('lastUpdated'):
        existing.title = item.get('bidNtceNm')
        existing.updated_at = datetime.now()
        return 'updated'
```

#### 2. 정보 추출 패턴 확장
**파일**: `batch/modules/processor.py:163-167`
**현재 문제**:
- prices 카테고리 3개만 추출 (전체 67개 중)
- 제한적인 regex 패턴

**개선 방안**:
```python
price_patterns = [
    # 기존 패턴
    (r'예정가격\s*[:：]\s*([\d,]+)\s*원', 'estimated_price'),
    # 추가 패턴
    (r'예정\s*가격\s*[:：]\s*([\d,]+)', 'estimated_price'),
    (r'추정금액\s*[:：]\s*([\d,]+)', 'estimated_price'),
    (r'설계금액\s*[:：]\s*([\d,]+)', 'design_price'),
    (r'설계\s*금액\s*[:：]\s*([\d,]+)', 'design_price'),
]
```

---

### 🟡 Priority 2: 중요 개선사항

#### 1. 트랜잭션 관리
**문제**: 각 모듈이 개별적으로 commit → 부분 저장 위험
**개선 방안**:
```python
from contextlib import contextmanager

@contextmanager
def batch_transaction(session):
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
```

#### 2. 에러 핸들링 및 재시도 전략
**파일**: `batch/modules/downloader.py`
**개선 방안**:
```python
retry_strategy = {
    'Timeout': {'delay': 60, 'max_retries': 3},
    'ConnectionError': {'delay': 300, 'max_retries': 2},
    'HTTPError': {'delay': 120, 'max_retries': 1}
}
```

#### 3. HWPX 파일 처리 개선
**현재 문제**: 3개 파일 처리 실패
**조사 필요**:
- 실패 원인 분석
- hwp_advanced_extractor 개선

---

### 🟢 Priority 3: 향후 개선사항

#### 1. ZIP 파일 처리
**상태**: 📌 나중에 처리 예정
**구현 방안**:
```python
async def _extract_zip(self, file_path: Path):
    """ZIP 파일 처리"""
    # 1. 압축 해제
    # 2. 내부 파일 개별 처리
    # 3. 통합 마크다운 생성
```

#### 2. 배치 크기 동적 조절
**개선 방안**:
```python
def calculate_batch_size(total_count):
    if total_count > 500:
        return 50
    elif total_count > 100:
        return 20
    else:
        return 10
```

#### 3. 실시간 모니터링
- 진행률 표시
- 예상 완료 시간
- 성능 메트릭 수집

---

## 📊 현재 성능 지표
- **수집 성공률**: 97% (69/71)
- **다운로드 성공률**: 100% (67/67)
- **처리 성공률**: 94% (63/67)
- **정보 추출**:
  - requirements: 54개
  - contract_details: 6개
  - prices: 3개 ⚠️

---

## 🔧 적용 계획

### Phase 1 (1주 내)
- [ ] 중복 체크 로직
- [ ] 정보 추출 패턴 확장

### Phase 2 (2주 내)
- [ ] 트랜잭션 관리
- [ ] 에러 핸들링 개선
- [ ] HWPX 처리 개선

### Phase 3 (1개월 내)
- [ ] ZIP 파일 처리
- [ ] 동적 배치 크기
- [ ] 모니터링 시스템

---

## 💡 참고사항
- 현재 배치는 **기본 기능 정상 작동**
- 프로덕션 안정성을 위해 우선순위별 개선 필요
- ZIP 파일은 전체 67개 중 1개로 영향도 낮음