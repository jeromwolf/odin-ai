#!/usr/bin/env python3
"""MD → PDF 변환 (이미지 포함)"""
import os
import markdown
from weasyprint import HTML

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MD_PATH = os.path.join(BASE_DIR, "ODIN_AI_PROPOSAL.md")
PDF_PATH = os.path.join(BASE_DIR, "ODIN_AI_PROPOSAL.pdf")

with open(MD_PATH, "r", encoding="utf-8") as f:
    md_text = f.read()

html_body = markdown.markdown(md_text, extensions=["tables", "fenced_code"])

html_full = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page {{
    size: A4;
    margin: 2cm 2.5cm;
    @bottom-center {{
      content: counter(page);
      font-size: 9pt;
      color: #999;
    }}
  }}
  body {{
    font-family: -apple-system, "Malgun Gothic", "Apple SD Gothic Neo", sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
  }}
  h1 {{
    color: #1565C0;
    font-size: 22pt;
    border-bottom: 2px solid #1565C0;
    padding-bottom: 6px;
    margin-top: 30px;
    page-break-before: always;
  }}
  h1:first-of-type {{
    page-break-before: avoid;
  }}
  h2 {{
    color: #1976D2;
    font-size: 16pt;
    margin-top: 20px;
  }}
  h3 {{
    color: #1E88E5;
    font-size: 13pt;
    margin-top: 16px;
  }}
  table {{
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
    font-size: 9.5pt;
  }}
  th {{
    background-color: #1565C0;
    color: white;
    padding: 8px 10px;
    text-align: left;
    font-weight: bold;
  }}
  td {{
    border: 1px solid #ddd;
    padding: 6px 10px;
  }}
  tr:nth-child(even) {{
    background-color: #f5f5f5;
  }}
  img {{
    max-width: 100%;
    display: block;
    margin: 10px auto;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
  }}
  blockquote {{
    border-left: 4px solid #1976D2;
    margin: 12px 0;
    padding: 8px 16px;
    background: #E3F2FD;
    color: #333;
    font-style: italic;
  }}
  code {{
    background: #f5f5f5;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 9.5pt;
  }}
  hr {{
    border: none;
    border-top: 2px solid #1565C0;
    margin: 20px 0;
  }}
  em {{
    color: #666;
  }}
  strong {{
    color: #1565C0;
  }}
  p {{
    margin: 6px 0;
  }}
  ul, ol {{
    margin: 6px 0;
    padding-left: 24px;
  }}
  li {{
    margin: 3px 0;
  }}
</style>
</head>
<body>
{html_body}
</body>
</html>
"""

HTML(string=html_full, base_url=BASE_DIR).write_pdf(PDF_PATH)
size_kb = os.path.getsize(PDF_PATH) / 1024
print(f"✅ PDF 생성 완료: {PDF_PATH}")
print(f"   파일 크기: {size_kb:.0f} KB")
