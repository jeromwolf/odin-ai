#!/usr/bin/env python3
"""
테스트용 샘플 Excel 파일 생성
"""

import pandas as pd
from datetime import datetime, timedelta

# 샘플 데이터 생성
data = {
    '공고번호-차수': [
        '20259999-00',
        '20259998-00',
        '20259997-00',
    ],
    '공고명': [
        '[테스트] 샘플 건설공사',
        '[테스트] 샘플 시스템 구축',
        '[테스트] 샘플 용역',
    ],
    '공고기관': [
        '테스트기관A',
        '테스트기관B',
        '테스트기관C',
    ],
    '공고일시': [
        '2025-10-15',
        '2025-10-14',
        '2025-10-13',
    ],
    '입찰마감일시': [
        '2025-10-25',
        '2025-10-24',
        '2025-10-23',
    ],
    '추정가격': [
        '1500000000',
        '200000000',
        '50000000',
    ],
    '입찰방법': [
        '일반경쟁',
        '제한경쟁',
        '일반경쟁',
    ],
}

df = pd.DataFrame(data)

# Excel 파일로 저장
output_file = '/tmp/test_sample_bids.xlsx'
df.to_excel(output_file, index=False, sheet_name='입찰공고')

print(f"✅ 샘플 Excel 파일 생성 완료: {output_file}")
print(f"📊 총 {len(df)}개 행")
print("\n샘플 데이터:")
print(df.to_string(index=False))
