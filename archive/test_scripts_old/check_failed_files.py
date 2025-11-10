#!/usr/bin/env python3
"""실패한 5개 파일의 실제 타입 확인"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

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

# 실패한 5개 파일
failed_files = [
    ("R25BK01118382", "2. 연일초-내역서(공란).xlsx"),
    ("R25BK01122934", "설계설명서 및 시방서(2025년 아산시 관내 태풍대비 빗물받이 준설공사)(수정).xlsx"),
    ("R25BK01123356", "2-2. 공사원가계산서(증기트랩 정비) - 공내역서.xlsx"),
    ("R25BK01123710", "설계설명서 및 공종별 내역서.xlsx"),
    ("R25BK01124427", "물량내역서.xlsx"),
]

print("=" * 80)
print("실패한 파일 타입 분석")
print("=" * 80)

for bid_no, filename in failed_files:
    file_path = Path(f"storage/documents/{bid_no}/{filename}")
    
    if not file_path.exists():
        print(f"\n❌ 파일 없음: {filename}")
        continue
    
    print(f"\n📄 {filename}")
    print(f"   경로: {file_path}")
    
    # 파일 타입 감지
    detected_type = processor._detect_file_type(file_path)
    print(f"   감지된 타입: {detected_type}")
    
    # file 명령어로도 확인
    import subprocess
    result = subprocess.run(['file', str(file_path)], capture_output=True, text=True)
    print(f"   file 명령: {result.stdout.strip().split(': ')[1] if ': ' in result.stdout else result.stdout.strip()}")

print("\n" + "=" * 80)
