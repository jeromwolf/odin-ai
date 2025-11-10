#!/usr/bin/env python3
"""PDF 파일 테스트"""

from pathlib import Path
import PyPDF2

file_path = Path("storage/documents/R25BK01124427/물량내역서.xlsx")

print(f"파일 존재: {file_path.exists()}")
print(f"파일 크기: {file_path.stat().st_size if file_path.exists() else 0} bytes")

# file 명령어로 확인
import subprocess
result = subprocess.run(['file', str(file_path)], capture_output=True, text=True)
print(f"file 명령: {result.stdout.strip()}")

# PyPDF2로 읽기 테스트
try:
    with open(file_path, 'rb') as f:
        pdf_reader = PyPDF2.PdfReader(f)
        print(f"PDF 페이지 수: {len(pdf_reader.pages)}")
        
        # 첫 페이지 텍스트 추출
        if len(pdf_reader.pages) > 0:
            first_page_text = pdf_reader.pages[0].extract_text()
            print(f"첫 페이지 텍스트 길이: {len(first_page_text)}")
            print(f"첫 100자: {first_page_text[:100]}")
except Exception as e:
    print(f"PDF 읽기 실패: {e}")
