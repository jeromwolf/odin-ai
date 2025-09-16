#!/bin/bash
# HWP → Markdown 검색 예제 스크립트

echo "🔍 HWP 검색 다양한 방법"
echo "================================="

# 1. 기본 grep 검색
echo -e "\n1. 키워드 검색:"
echo "   grep -i \"IoT\" 1.md"
grep -i "IoT" 1.md | head -3

# 2. 줄 번호와 함께 검색
echo -e "\n2. 줄 번호 포함 검색:"
echo "   grep -n -i \"데이터\" 1.md"
grep -n -i "데이터" 1.md | head -3

# 3. 컨텍스트 검색 (앞뒤 줄 포함)
echo -e "\n3. 컨텍스트 검색 (앞뒤 2줄):"
echo "   grep -C 2 \"과업수행기간\" 1.md"
grep -C 2 "과업수행기간" 1.md

# 4. 정규표현식 검색
echo -e "\n4. 패턴 검색:"
echo "   grep -E \"202[0-9]년\" 1.md"
grep -E "202[0-9]년" 1.md | head -3

# 5. 여러 키워드 검색
echo -e "\n5. 여러 키워드 (OR 조건):"
echo "   grep -E \"IoT|데이터|시스템\" 1.md | head -3"
grep -E "IoT|데이터|시스템" 1.md | head -3

# 6. 대소문자 구분하지 않는 검색
echo -e "\n6. 영어 검색 (대소문자 무관):"
echo "   grep -i \"iot\" 1.md | wc -l"
echo "   총 $(grep -i "iot" 1.md | wc -l)개의 IoT 관련 항목 발견"

# 7. ripgrep이 있다면 더 강력한 검색
if command -v rg &> /dev/null; then
    echo -e "\n7. ripgrep 검색 (더 빠르고 강력):"
    echo "   rg -i \"모니터링\" 1.md"
    rg -i "모니터링" 1.md
fi

echo -e "\n✅ 마크다운으로 변환하면 다양한 검색 도구 활용 가능!"
echo "   - grep: 기본 텍스트 검색"
echo "   - rg (ripgrep): 더 빠른 검색"
echo "   - VS Code: 파일 내 검색"
echo "   - 웹 브라우저: 페이지 내 검색 (Ctrl+F)"