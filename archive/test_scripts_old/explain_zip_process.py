#!/usr/bin/env python3
"""ZIP 파일 처리 과정 시각화"""

import zipfile
from pathlib import Path

# 실제 HWPX 파일 경로
hwpx_file = Path("storage/documents/R25BK01118382/2. 연일초-내역서(공란).xlsx")

if hwpx_file.exists():
    print("=" * 80)
    print("HWPX 파일 구조 분석 (압축 풀지 않고 내부 확인)")
    print("=" * 80)
    
    # 1단계: ZIP 파일 열기 (메모리에서만)
    with zipfile.ZipFile(hwpx_file, 'r') as zf:
        print(f"\n📦 파일명: {hwpx_file.name}")
        print(f"📊 파일 크기: {hwpx_file.stat().st_size:,} bytes")
        print(f"\n🗂️  ZIP 내부 파일 목록 ({len(zf.namelist())}개):")
        
        for i, filename in enumerate(zf.namelist()[:15], 1):
            info = zf.getinfo(filename)
            print(f"   {i:2d}. {filename:50s} ({info.file_size:,} bytes)")
        
        if len(zf.namelist()) > 15:
            print(f"   ... (총 {len(zf.namelist())}개 파일)")
        
        # 2단계: section*.xml 파일 찾기
        section_files = [f for f in zf.namelist() 
                        if 'section' in f.lower() and f.endswith('.xml')]
        
        print(f"\n📝 텍스트가 있는 section 파일: {len(section_files)}개")
        for section_file in section_files[:5]:
            print(f"   - {section_file}")
        
        # 3단계: 첫 번째 section 파일을 메모리에서 읽기
        if section_files:
            first_section = section_files[0]
            print(f"\n🔍 첫 번째 섹션 파일 읽기 (디스크에 풀지 않고):")
            print(f"   파일: {first_section}")
            
            with zf.open(first_section) as f:
                content = f.read()
                print(f"   압축 전 크기: {zf.getinfo(first_section).compress_size:,} bytes")
                print(f"   압축 후 크기: {len(content):,} bytes")
                print(f"   처음 100자: {content[:100]}")

else:
    print(f"❌ 파일 없음: {hwpx_file}")
