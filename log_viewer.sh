#!/bin/bash

echo "=========================================="
echo "📊 ODIN-AI 로그 뷰어"
echo "=========================================="
echo ""
echo "사용 가능한 명령어:"
echo ""
echo "1. 최신 테스트 결과 요약:"
echo "   grep -E 'Phase|완료|성공|실패' today_batch_test.log | tail -30"
echo ""
echo "2. 오늘 수집된 데이터 확인:"
echo "   grep '신규 저장' today_batch_test.log | wc -l"
echo ""
echo "3. 다운로드된 파일 목록:"
echo "   grep '다운로드 성공' today_batch_test.log | tail -20"
echo ""
echo "4. 실시간 로그 모니터링:"
echo "   tail -f logs/batch_*.log"
echo ""
echo "5. 에러 메시지 확인:"
echo "   grep -E 'ERROR|❌' today_batch_test.log"
echo ""
echo "6. DB 현재 상태 확인:"
echo "   python -c \"
from sqlalchemy import create_engine, text
engine = create_engine('postgresql://blockmeta@localhost:5432/odin_db')
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM bid_announcements'))
    print(f'공고: {result.scalar()}개')
    result = conn.execute(text('SELECT COUNT(*) FROM bid_documents'))
    print(f'문서: {result.scalar()}개')
\""
echo ""
echo "=========================================="
echo "현재 로그 파일들:"
ls -lh *.log 2>/dev/null | awk '{print "  📄", $9, "(" $5 ")"}'
echo ""
echo "=========================================="
echo "최근 실행 결과 (today_batch_test.log):"
echo ""
grep -E "수집 완료|다운로드 완료|처리 완료|최종" today_batch_test.log | tail -5