# 🏗️ 향상된 데이터 추출 및 DB 저장 아키텍처

## 📊 현재 문제점
- 마크다운에서 핵심 정보 누락 (금액, 정확한 일정)
- 단순 텍스트 추출로 구조화된 데이터 미확보
- DB 검색 최적화를 위한 정규화된 데이터 부족

## 🎯 목표
중요 정보를 DB에 구조화하여 저장하고 빠른 검색/필터링 지원

## 🗄️ 개선된 DB 스키마

### 1. bid_announcements 테이블 확장
```sql
ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS
    estimated_price BIGINT,                    -- 추정가격
    budget_price BIGINT,                       -- 예가
    vat_amount BIGINT,                         -- 부가세
    price_method VARCHAR(100),                 -- 예가방법
    registration_start_date TIMESTAMP,         -- 참가자격등록 시작
    registration_end_date TIMESTAMP,           -- 참가자격등록 마감
    submission_start_date TIMESTAMP,           -- 입찰서 제출 시작
    submission_end_date TIMESTAMP,             -- 입찰서 제출 마감
    opening_date TIMESTAMP,                    -- 개찰일시
    contract_type VARCHAR(50),                 -- 계약방식 (경쟁입찰/수의계약)
    qualification_requirements TEXT,           -- 자격요건
    region_restriction VARCHAR(100),           -- 지역제한
    joint_venture_allowed BOOLEAN,             -- 공동수급 허용여부
    tax_exemption BOOLEAN;                     -- 면세여부
```

### 2. bid_details 테이블 (신규)
```sql
CREATE TABLE bid_details (
    detail_id SERIAL PRIMARY KEY,
    bid_notice_no VARCHAR(100) REFERENCES bid_announcements(bid_notice_no),
    detail_type VARCHAR(50),                   -- 'price', 'schedule', 'qualification'
    field_name VARCHAR(100),                   -- 필드명
    field_value TEXT,                          -- 값
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extraction_confidence FLOAT,              -- AI 추출 신뢰도
    verified BOOLEAN DEFAULT FALSE            -- 수동 검증 여부
);
```

### 3. bid_schedule 테이블 (신규)
```sql
CREATE TABLE bid_schedule (
    schedule_id SERIAL PRIMARY KEY,
    bid_notice_no VARCHAR(100) REFERENCES bid_announcements(bid_notice_no),
    event_type VARCHAR(50),                    -- 'announcement', 'registration', 'submission', 'opening'
    event_date TIMESTAMP,
    event_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🤖 AI 기반 정보 추출 시스템

### 1. 구조화된 정보 추출기
```python
class EnhancedInfoExtractor:
    def extract_structured_data(self, text):
        """HWP 텍스트에서 구조화된 데이터 추출"""

        # 1. 금액 정보 추출
        price_info = self.extract_price_info(text)

        # 2. 일정 정보 추출
        schedule_info = self.extract_schedule_info(text)

        # 3. 자격요건 추출
        qualification_info = self.extract_qualification_info(text)

        # 4. 기타 메타데이터
        metadata = self.extract_metadata(text)

        return {
            'prices': price_info,
            'schedules': schedule_info,
            'qualifications': qualification_info,
            'metadata': metadata
        }

    def extract_price_info(self, text):
        """금액 관련 정보 추출"""
        patterns = {
            'estimated_price': [
                r'추정가격[:\s]*([0-9,]+)\s*원',
                r'공사추정금액[:\s]*([0-9,]+)\s*원',
                r'추정금액[:\s]*([0-9,]+)\s*원'
            ],
            'budget_price': [
                r'예가[:\s]*([0-9,]+)\s*원',
                r'예정가격[:\s]*([0-9,]+)\s*원'
            ],
            'vat_amount': [
                r'부가가치세[:\s]*([0-9,]+)\s*원',
                r'부가세[:\s]*([0-9,]+)\s*원'
            ]
        }

        results = {}
        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text)
                if match:
                    amount_str = match.group(1).replace(',', '')
                    results[field] = int(amount_str)
                    break

        return results

    def extract_schedule_info(self, text):
        """일정 정보 추출"""
        patterns = {
            'registration_period': r'입찰참가자격등록[:\s]*([0-9/\s\-:.~]+)',
            'submission_period': r'입찰서\s*제출[:\s]*([0-9/\s\-:.~]+)',
            'opening_date': r'개찰[:\s]*([0-9/\s\-:.]+)',
            'announcement_date': r'공고일[:\s]*([0-9/\s\-:.]+)'
        }

        results = {}
        for event_type, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                results[event_type] = self.parse_date_range(date_str)

        return results
```

### 2. GPT-4 기반 스마트 추출
```python
class GPTInfoExtractor:
    def extract_with_gpt(self, text):
        """GPT-4를 사용한 고도화된 정보 추출"""

        prompt = f"""
        다음 입찰 공고문에서 핵심 정보를 JSON 형태로 추출해주세요:

        {text[:3000]}  # 토큰 제한 고려

        추출할 정보:
        1. 금액정보: 추정가격, 예가, 부가세
        2. 일정정보: 공고일, 참가등록기간, 입찰제출기간, 개찰일시
        3. 자격요건: 업종, 지역제한, 면허/등록 요구사항
        4. 계약정보: 계약방식, 공동수급 허용여부

        JSON 형식:
        {{
            "prices": {{
                "estimated_price": 숫자,
                "budget_price": 숫자,
                "vat_amount": 숫자
            }},
            "schedules": {{
                "announcement_date": "YYYY-MM-DD HH:MM:SS",
                "registration_start": "YYYY-MM-DD HH:MM:SS",
                "registration_end": "YYYY-MM-DD HH:MM:SS",
                "submission_start": "YYYY-MM-DD HH:MM:SS",
                "submission_end": "YYYY-MM-DD HH:MM:SS",
                "opening_date": "YYYY-MM-DD HH:MM:SS"
            }},
            "qualifications": {{
                "industry": "업종명",
                "region_restriction": "지역제한",
                "license_required": "필요 면허/등록"
            }},
            "contract_info": {{
                "contract_type": "계약방식",
                "joint_venture_allowed": true/false
            }}
        }}
        """

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )

        return json.loads(response.choices[0].message.content)
```

## 📊 개선된 데이터 플로우

```
1. HWP 파일 다운로드
   ↓
2. hwp5txt로 텍스트 추출
   ↓
3. 향상된 정보 추출
   ├── 정규식 기반 추출
   ├── GPT-4 기반 추출
   └── 신뢰도 검증
   ↓
4. 구조화된 DB 저장
   ├── bid_announcements (기본정보)
   ├── bid_details (상세정보)
   └── bid_schedule (일정정보)
   ↓
5. 마크다운 생성 (보완)
   ├── 추출된 구조화 데이터 포함
   └── 검색 최적화된 포맷
```

## 🔍 검색 최적화

### 1. 금액 범위 검색
```sql
-- 예산 범위로 입찰 검색
SELECT * FROM bid_announcements
WHERE estimated_price BETWEEN 50000000 AND 100000000;
```

### 2. 일정 기반 검색
```sql
-- 이번 주 마감 입찰
SELECT * FROM bid_announcements
WHERE submission_end_date BETWEEN NOW() AND NOW() + INTERVAL '7 days';
```

### 3. 자격요건 검색
```sql
-- 특정 업종 입찰
SELECT * FROM bid_announcements
WHERE qualification_requirements LIKE '%전기공사%';
```

## 📈 예상 효과

1. **정확한 정보 제공**: 91.3% → 95%+ 정확도 향상
2. **빠른 검색**: 금액/일정 기반 즉시 필터링
3. **사용자 경험**: 구조화된 데이터로 대시보드 최적화
4. **AI 분석**: 입찰 성공률 예측 모델 학습 데이터 확보

## 🚀 구현 단계

1. **Phase 1**: DB 스키마 확장
2. **Phase 2**: 정보 추출기 개발
3. **Phase 3**: GPT-4 통합
4. **Phase 4**: 검색 API 개선
5. **Phase 5**: 대시보드 업데이트