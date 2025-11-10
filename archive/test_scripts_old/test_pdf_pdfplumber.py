#!/usr/bin/env python3
"""pdfplumber로 PDF 파일 테스트"""

from pathlib import Path
import pdfplumber

file_path = Path("storage/documents/R25BK01124427/물량내역서.xlsx")

try:
    with pdfplumber.open(file_path) as pdf:
        print(f"PDF 페이지 수: {len(pdf.pages)}")
        
        # 모든 페이지에서 텍스트 추출
        total_text = ""
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            print(f"페이지 {i+1} 텍스트 길이: {len(page_text) if page_text else 0}")
            if page_text:
                total_text += page_text + "\n"
        
        print(f"\n총 텍스트 길이: {len(total_text)}")
        if total_text:
            print(f"첫 200자:\n{total_text[:200]}")
except Exception as e:
    print(f"pdfplumber 읽기 실패: {e}")
