#!/usr/bin/env python3
"""
API 응답의 URL 필드 상세 분석
- stdNtceDocUrl: 표준공고문서
- bidNtceDtlUrl: 상세페이지
- ntceSpecDocUrl1~10: 첨부파일들
"""

import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from collections import defaultdict

# 저장된 API 응답 파일 읽기
response_file = Path("api_response_20250922_153534.json")

with open(response_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 80)
print("📊 API URL 필드 상세 분석")
print("=" * 80)
print(f"총 {len(data)}개 공고 분석\n")

# 통계 수집
stats = {
    'stdNtceDocUrl': {'exists': 0, 'file_seqs': [], 'sample_urls': []},
    'bidNtceDtlUrl': {'exists': 0, 'sample_urls': []},
    'ntceSpecDocs': defaultdict(lambda: {'count': 0, 'file_types': set(), 'file_names': []})
}

# 각 공고 분석
for idx, item in enumerate(data, 1):
    print(f"[{idx}] {item.get('bidNtceNm', 'N/A')[:50]}...")
    print(f"    공고번호: {item.get('bidNtceNo')}")

    # 1. stdNtceDocUrl 분석 (표준공고문서)
    std_url = item.get('stdNtceDocUrl', '')
    if std_url:
        stats['stdNtceDocUrl']['exists'] += 1
        parsed = urlparse(std_url)
        params = parse_qs(parsed.query)

        file_seq = params.get('fileSeq', [''])[0]
        stats['stdNtceDocUrl']['file_seqs'].append(file_seq)

        print(f"    📄 표준공고문서 URL:")
        print(f"       - fileSeq: {file_seq}")
        print(f"       - bidPbancNo: {params.get('bidPbancNo', [''])[0]}")

        if len(stats['stdNtceDocUrl']['sample_urls']) < 3:
            stats['stdNtceDocUrl']['sample_urls'].append(std_url)

    # 2. bidNtceDtlUrl 분석 (상세페이지)
    detail_url = item.get('bidNtceDtlUrl', '')
    if detail_url:
        stats['bidNtceDtlUrl']['exists'] += 1
        print(f"    🔗 상세페이지 URL:")
        print(f"       - {detail_url[:80]}...")

        if len(stats['bidNtceDtlUrl']['sample_urls']) < 3:
            stats['bidNtceDtlUrl']['sample_urls'].append(detail_url)

    # 3. ntceSpecDocUrl1~10 분석 (첨부파일)
    attachments = []
    for i in range(1, 11):
        spec_url = item.get(f'ntceSpecDocUrl{i}', '')
        spec_name = item.get(f'ntceSpecFileNm{i}', '')

        if spec_url and spec_name:
            # 파일 확장자 추출
            file_ext = spec_name.split('.')[-1].lower() if '.' in spec_name else 'unknown'

            attachments.append({
                'index': i,
                'url': spec_url,
                'name': spec_name,
                'ext': file_ext
            })

            stats['ntceSpecDocs'][i]['count'] += 1
            stats['ntceSpecDocs'][i]['file_types'].add(file_ext)
            stats['ntceSpecDocs'][i]['file_names'].append(spec_name)

    if attachments:
        print(f"    📎 첨부파일 {len(attachments)}개:")
        for att in attachments[:3]:  # 처음 3개만 출력
            print(f"       [{att['index']}] {att['name']} ({att['ext']})")
        if len(attachments) > 3:
            print(f"       ... 외 {len(attachments)-3}개")

    print()

# 통계 요약
print("=" * 80)
print("📈 통계 요약")
print("=" * 80)

# stdNtceDocUrl 통계
print("\n1️⃣ 표준공고문서 (stdNtceDocUrl):")
print(f"   - 존재율: {stats['stdNtceDocUrl']['exists']}/{len(data)} ({stats['stdNtceDocUrl']['exists']/len(data)*100:.1f}%)")
print(f"   - fileSeq 분포:")
file_seq_counts = {}
for seq in stats['stdNtceDocUrl']['file_seqs']:
    file_seq_counts[seq] = file_seq_counts.get(seq, 0) + 1
for seq, count in sorted(file_seq_counts.items()):
    print(f"      fileSeq={seq}: {count}건")
print(f"   - 용도: 공고문 원본 다운로드 (HWP/PDF)")
print(f"   - 샘플 URL: {stats['stdNtceDocUrl']['sample_urls'][0] if stats['stdNtceDocUrl']['sample_urls'] else 'N/A'}")

# bidNtceDtlUrl 통계
print("\n2️⃣ 상세페이지 (bidNtceDtlUrl):")
print(f"   - 존재율: {stats['bidNtceDtlUrl']['exists']}/{len(data)} ({stats['bidNtceDtlUrl']['exists']/len(data)*100:.1f}%)")
print(f"   - 용도: 웹페이지에서 추가 정보 확인")
print(f"   - 샘플 URL: {stats['bidNtceDtlUrl']['sample_urls'][0] if stats['bidNtceDtlUrl']['sample_urls'] else 'N/A'}")

# ntceSpecDocUrl 통계
print("\n3️⃣ 첨부파일 (ntceSpecDocUrl1~10):")
total_attachments = sum(stats['ntceSpecDocs'][i]['count'] for i in range(1, 11))
print(f"   - 총 첨부파일 수: {total_attachments}개")

for i in range(1, 11):
    if stats['ntceSpecDocs'][i]['count'] > 0:
        doc_stat = stats['ntceSpecDocs'][i]
        print(f"\n   📎 ntceSpecDocUrl{i}:")
        print(f"      - 사용 빈도: {doc_stat['count']}건")
        print(f"      - 파일 형식: {', '.join(sorted(doc_stat['file_types']))}")

        # 대표 파일명 예시
        sample_names = doc_stat['file_names'][:2]
        for name in sample_names:
            print(f"      - 예시: {name}")

# 파일 형식별 통계
print("\n4️⃣ 파일 형식 분포:")
all_file_types = defaultdict(int)
for i in range(1, 11):
    for file_type in stats['ntceSpecDocs'][i]['file_types']:
        all_file_types[file_type] += stats['ntceSpecDocs'][i]['count']

for file_type, count in sorted(all_file_types.items(), key=lambda x: x[1], reverse=True):
    print(f"   - .{file_type}: {count}개")

print("\n" + "=" * 80)
print("💡 활용 전략 제안")
print("=" * 80)

print("""
1. **우선순위 전략**:
   - 1순위: stdNtceDocUrl (표준공고문서) - 핵심 정보 포함
   - 2순위: ntceSpecDocUrl1 (주로 공고문 HWP)
   - 3순위: ntceSpecDocUrl2~3 (시방서, 내역서)
   - 4순위: bidNtceDtlUrl (웹 크롤링 필요시)

2. **파일 처리 전략**:
   - HWP: hwp5txt 또는 pyhwp로 텍스트 추출
   - DOCX: python-docx로 처리
   - XLSX: pandas로 데이터 추출
   - ZIP: 압축 해제 후 내부 파일 처리
   - PDF: PyPDF2로 텍스트 추출

3. **저장 전략**:
   - 공고별 폴더 생성 (bidNtceNo 기준)
   - 표준문서와 첨부파일 구분 저장
   - 메타데이터 JSON으로 관리

4. **검색 최적화**:
   - 표준문서 내용을 우선 인덱싱
   - 첨부파일은 파일명과 주요 키워드만 인덱싱
   - 상세페이지는 필요시에만 크롤링
""")

# 결과를 JSON으로 저장
analysis_result = {
    'total_items': len(data),
    'stdNtceDocUrl_stats': {
        'exists_count': stats['stdNtceDocUrl']['exists'],
        'exists_rate': f"{stats['stdNtceDocUrl']['exists']/len(data)*100:.1f}%",
        'file_seq_distribution': file_seq_counts
    },
    'bidNtceDtlUrl_stats': {
        'exists_count': stats['bidNtceDtlUrl']['exists'],
        'exists_rate': f"{stats['bidNtceDtlUrl']['exists']/len(data)*100:.1f}%"
    },
    'attachment_stats': {
        'total_count': total_attachments,
        'file_types': dict(all_file_types)
    }
}

with open('url_analysis_result.json', 'w', encoding='utf-8') as f:
    json.dump(analysis_result, f, indent=2, ensure_ascii=False)

print(f"\n📊 분석 결과 저장: url_analysis_result.json")