#!/usr/bin/env python
"""
HWPX 파일 내용 분석 - XML 구조 확인
"""

import zipfile
from pathlib import Path

# HWPX 파일 찾기
storage_path = Path("./storage/downloads")
hwpx_files = list(storage_path.glob("**/*.hwpx"))

if hwpx_files:
    test_file = hwpx_files[0]
    print(f"📄 분석 파일: {test_file}")

    try:
        with zipfile.ZipFile(test_file, 'r') as z:
            print(f"📁 ZIP 파일 내용:")
            for filename in z.namelist():
                print(f"  - {filename}")

            print("\n" + "="*60)

            # content 관련 파일 분석
            for filename in z.namelist():
                if 'content' in filename.lower():
                    print(f"\n📄 파일: {filename}")

                    with z.open(filename) as f:
                        content = f.read().decode('utf-8', errors='ignore')

                        print(f"📊 크기: {len(content):,} bytes")
                        print(f"📖 처음 500자:")
                        print(content[:500])
                        print("\n" + "-"*40)

                        # XML 태그 분석
                        import re
                        tags = re.findall(r'<([^>]+)>', content[:5000])  # 처음 5000자에서 태그 추출
                        unique_tags = list(set([tag.split()[0] for tag in tags]))[:10]  # 처음 10개 태그
                        print(f"🏷️ 주요 XML 태그: {unique_tags}")

    except Exception as e:
        print(f"❌ 분석 실패: {e}")
else:
    print("📄 HWPX 파일을 찾을 수 없습니다")