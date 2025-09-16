# 공공데이터포털 API 키 설정 가이드

## 1. 공공데이터포털 회원가입 및 API 키 발급

### 1.1 회원가입
1. **공공데이터포털** 접속: https://www.data.go.kr/
2. 우상단 **"회원가입"** 클릭
3. **개인회원 가입** 선택
4. 필수 정보 입력:
   - 아이디/비밀번호
   - 이름/이메일
   - 휴대폰 인증
5. 이메일 인증 완료

### 1.2 데이터 활용 신청
1. **로그인** 후 **"데이터"** 메뉴 이동
2. **"조달정보"** 또는 **"계약정보"** 검색
3. 주요 API 서비스:
   - **나라장터 입찰정보 조회 서비스**
   - **국가계약시스템 계약정보 조회 서비스**
   - **조달청 입찰공고 정보 서비스**

### 1.3 API 키 발급 과정

#### Step 1: 5개 API 모두 신청 (필수)

**Odin-AI 완전 기능을 위해서는 다음 5개 API를 모두 신청해야 합니다**:

```
✅ 필수 API 목록 (2025-09-16 확인):

1. "조달청 나라장터 입찰공고정보서비스"
   - 입찰공고 목록 및 상세 정보
   - 키워드: 나라장터, 입찰, 입찰공고, 물품, 공사, 의자

2. "조달청 나라장터 낙찰정보서비스"
   - 낙찰업체 및 계약 정보
   - 키워드: 나라장터, 낙찰, 정보, 순위, 예가기법

3. "조달청 나라장터 계약정보서비스"
   - 계약 체결 상세 정보
   - 키워드: 나라장터, 계약, 정보, 물품, 용역, 공사

4. "조달청 나라장터 사전규격정보서비스"
   - 사전규격서 정보 조회
   - 키워드: 사전규격, 정보, 물품, 용역, 의자, 공사

5. "조달청 나라장터 사용자정보 서비스"
   - 조달업체 및 수요기관 정보
   - 키워드: 나라장터, 사용자, 정보, 기관, 업체, 업종
```

**중요**: 각 API마다 별도의 활용신청이 필요합니다!

#### Step 2: 활용신청
1. API 상세페이지에서 **"활용신청"** 버튼 클릭
2. **신청 정보 입력**:
   ```
   신청구분: 상업적 이용 (또는 비상업적 이용)
   활용목적: 공공조달 정보 분석 플랫폼 개발
   서비스명: Odin-AI (공공조달 AI 분석 서비스)
   활용분야: IT/소프트웨어
   예상 트래픽: 일일 1,000건 (초기), 월 30,000건
   활용기간: 1년 (갱신 가능)
   ```

3. **추가 정보**:
   ```
   개발언어: Python
   서비스 개요:
   - 나라장터 입찰정보를 AI로 분석
   - 기업별 맞춤 입찰 정보 추천
   - 입찰 성공률 예측 서비스
   ```

#### Step 3: 승인 대기
- **승인 시간**: 보통 1-3 영업일
- **승인 알림**: 이메일 및 문자로 통지
- **승인 확인**: 마이페이지 > 나의 신청현황

#### Step 4: API 키 확인
1. **승인 후** 마이페이지 > **"나의 신청현황"**
2. **"인증키 확인"** 버튼 클릭
3. **중요**: **Decoding된 인증키**를 사용하세요!

```
❌ Encoding 인증키: 사용하면 안됨 (암호화된 상태)
✅ Decoding 인증키: 실제 API 호출에 사용하는 키

예시:
- Encoding: %2BxyzAbc123%3D%2F (URL 인코딩된 상태)
- Decoding: +xyzAbc123=/ (실제 사용할 키)
```

**반드시 Decoding된 인증키를 복사하여 사용하세요!**

---

## 2. API 키 설정 방법

### 2.1 환경변수 설정
```bash
# .env 파일에 실제 API 키 입력
cp .env.example .env

# .env 파일 편집
vi .env
```

### 2.2 .env 파일 수정
```bash
# 실제 발급받은 API 키로 변경
PUBLIC_DATA_API_KEY=your-actual-api-key-here

# 예시 (실제 키는 더 길고 복잡함)
PUBLIC_DATA_API_KEY=1234567890abcdef1234567890abcdef
```

### 2.3 API 키 테스트
```python
# 간단한 테스트 스크립트
from backend.core.config import settings
import httpx

async def test_api_key():
    url = "http://apis.data.go.kr/1230000/BidPublicInfoService/getBidPblancListInfoServc01"
    params = {
        "serviceKey": settings.PUBLIC_DATA_API_KEY,
        "numOfRows": 1,
        "pageNo": 1,
        "type": "json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")

# 실행 방법
# python -c "import asyncio; from test_api import test_api_key; asyncio.run(test_api_key())"
```

---

## 3. 주요 API 서비스 정보

### 3.1 나라장터 입찰정보 조회 서비스
```
서비스 ID: 1230000
API URL: http://apis.data.go.kr/1230000/BidPublicInfoService/getBidPblancListInfoServc01

주요 매개변수:
- bidNtceNo: 입찰공고번호
- bidNtceOrd: 입찰공고차수
- ntceInsttCd: 공고기관코드
- dminsttCd: 수요기관코드
- bidClsfcNo: 입찰분류번호

응답 데이터:
- 입찰공고명
- 공고기관
- 입찰방법
- 개찰일시
- 예정가격
- 첨부파일 정보
```

### 3.2 국가계약시스템 계약정보 조회 서비스
```
서비스 ID: 1230000
API URL: http://apis.data.go.kr/1230000/CntrctInfoService/getCntrctInfoListServc01

주요 정보:
- 계약체결 정보
- 낙찰업체 정보
- 계약금액
- 계약기간
```

### 3.3 조달청 조달계획 정보 서비스
```
서비스 ID: 1230000
API URL: http://apis.data.go.kr/1230000/PrcrmntPlanInfoService/getPrcrmntPlanInfoListServc01

주요 정보:
- 연간 조달계획
- 조달 예정 물품/서비스
- 예상 입찰시기
```

---

## 4. 보안 및 주의사항

### 4.1 API 키 보안
```bash
# .env 파일을 .gitignore에 포함시켜 Git에 업로드 방지
echo ".env" >> .gitignore

# 환경변수 확인 (키가 로드되었는지 확인)
python -c "from backend.core.config import settings; print('API Key loaded:', len(settings.PUBLIC_DATA_API_KEY) > 0)"
```

### 4.2 사용량 제한
```
일반적인 제한:
- 시간당 1,000건
- 일일 10,000건
- 월간 300,000건

초과 시:
- API 호출 실패 (429 Too Many Requests)
- 일시적 서비스 중단 가능
```

### 4.3 오류 처리
```python
# API 키 관련 주요 오류 코드
ERROR_CODES = {
    "00": "정상",
    "01": "APPLICATION_ERROR",
    "02": "DB_ERROR",
    "03": "NODATA_ERROR",
    "04": "HTTP_ERROR",
    "05": "SERVICETIMEOUT_ERROR",
    "10": "INVALID_REQUEST_PARAMETER_ERROR",  # API 키 오류
    "11": "NO_MANDATORY_REQUEST_PARAMETERS_ERROR",
    "12": "NO_OPENAPI_SERVICE_ERROR",
    "13": "SERVICE_ACCESS_DENIED_ERROR",  # 승인되지 않은 서비스
    "99": "UNKNOWN_ERROR"
}
```

---

## 5. 트러블슈팅

### 5.1 API 키 오류
```
문제: "SERVICE_ACCESS_DENIED_ERROR"
해결:
1. API 키 정확성 확인
2. 해당 서비스 활용신청 승인 상태 확인
3. 인코딩/디코딩 키 확인 (일반키 사용)
```

### 5.2 승인 지연
```
문제: 승인이 3일 이상 지연
해결:
1. 마이페이지에서 신청 상태 확인
2. 공공데이터포털 고객센터 문의 (1588-3570)
3. help@data.go.kr 이메일 문의
```

### 5.3 사용량 초과
```
문제: 429 Too Many Requests
해결:
1. Rate Limiting 구현 (시간당 최대 800건으로 제한)
2. 요청 간격 조정 (최소 3.6초)
3. 캐싱 시스템 도입
```

---

## 6. 다음 단계

API 키 설정 완료 후:
1. ✅ **API 클라이언트 클래스 구현**
2. ✅ **Rate Limiting 및 재시도 로직**
3. ✅ **데이터 파싱 및 정규화**
4. ✅ **실제 데이터 수집 테스트**

**완료 체크**: API 키가 정상적으로 작동하면 컨펌 요청!