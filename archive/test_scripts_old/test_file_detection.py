#!/usr/bin/env python3
"""파일 타입 감지 기능 테스트"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

# DocumentProcessor import
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.services.document_processor import DocumentProcessor

# DB 연결
db_url = "postgresql://blockmeta@localhost:5432/odin_db"
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

# DocumentProcessor 인스턴스 생성
processor = DocumentProcessor(session, Path("./storage"))

# 테스트 파일 목록
test_files = [
    "storage/documents/R25BK01122306/공(내역서).xlsx",
    "storage/documents/R25BK01122272/공(내역서).xlsx",
    "storage/documents/R25BK01123356/2-2. 공사원가계산서(증기트랩 정비) - 공내역서.xlsx",
]

print("=" * 80)
print("파일 타입 감지 테스트")
print("=" * 80)

for file_path_str in test_files:
    file_path = Path(file_path_str)
    if not file_path.exists():
        print(f"\n❌ 파일 없음: {file_path_str}")
        continue
    
    print(f"\n📄 파일: {file_path.name}")
    print(f"   경로: {file_path_str}")
    print(f"   확장자: {file_path.suffix}")
    
    # 파일 타입 감지
    detected_type = processor._detect_file_type(file_path)
    print(f"   감지된 타입: {detected_type}")
    
    expected_type = file_path.suffix[1:] if file_path.suffix else 'unknown'
    if detected_type != expected_type:
        print(f"   ⚠️ 불일치! 확장자({expected_type}) ≠ 실제({detected_type})")
    else:
        print(f"   ✅ 일치")

print("\n" + "=" * 80)
