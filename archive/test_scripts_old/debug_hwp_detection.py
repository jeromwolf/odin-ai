#!/usr/bin/env python3
from pathlib import Path

file_path = Path("storage/documents/R25BK01122306/공(내역서).xlsx")

with open(file_path, 'rb') as f:
    content = f.read(8192)

print("=== 파일 헤더 확인 ===")
print(f"OLE2 헤더: {content[:8] == b'\\xd0\\xcf\\x11\\xe0\\xa1\\xb1\\x1a\\xe1'}")
print(f"'HWP Document File' 존재: {b'HWP Document File' in content}")
print(f"'HwpDoc' 존재: {b'HwpDoc' in content}")
print(f"'HwpSummaryInformation' 존재: {b'HwpSummaryInformation' in content}")
print(f"'FileHeader' 존재: {b'FileHeader' in content}")
print(f"'Hwp' 존재: {b'Hwp' in content}")

# UTF-16LE로 인코딩된 'HwpSummaryInformation' 찾기
hwp_utf16 = b'H\x00w\x00p\x00S\x00u\x00m\x00m\x00a\x00r\x00y\x00I\x00n\x00f\x00o\x00r\x00m\x00a\x00t\x00i\x00o\x00n\x00'
print(f"'HwpSummaryInformation' (UTF-16LE) 존재: {hwp_utf16 in content}")

# FileHeader UTF-16LE
file_header_utf16 = b'F\x00i\x00l\x00e\x00H\x00e\x00a\x00d\x00e\x00r\x00'
print(f"'FileHeader' (UTF-16LE) 존재: {file_header_utf16 in content}")

