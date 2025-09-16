#!/usr/bin/env python
"""
HWP Viewer CLI 도구
"""

import click
import sys
from pathlib import Path
import json

# 상위 디렉토리의 hwp_viewer 모듈 임포트
sys.path.append(str(Path(__file__).parent.parent))

from hwp_viewer import HWPParser


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """HWP Viewer - 한글 파일 처리 도구"""
    pass


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('-o', '--output', help='출력 파일 경로')
@click.option('--format', type=click.Choice(['txt', 'md', 'markdown']), default='txt', help='출력 형식')
@click.option('--emoji', is_flag=True, help='이모지 포함 (기본: 미포함)')
def extract(file_path, output, format, emoji):
    """HWP 파일에서 텍스트 추출

    사용 예시:
        hwp_cli.py extract document.hwp                    # 화면 출력
        hwp_cli.py extract document.hwp -o output.txt      # 텍스트 파일로 저장
        hwp_cli.py extract document.hwp -o output.md       # 마크다운으로 저장
        hwp_cli.py extract document.hwp --format md        # 마크다운 형식으로 화면 출력
    """
    try:
        # 파서 선택 (개선된 파서 우선 사용)
        try:
            from hwp_viewer.parser_improved import ImprovedHWPParser
            parser = ImprovedHWPParser()
        except ImportError:
            parser = HWPParser()

        # HWP 파일 파싱
        doc = parser.parse(file_path)

        # 출력 형식에 따라 텍스트 생성
        if format in ['md', 'markdown'] or (output and output.endswith('.md')):
            # 마크다운 포맷터 사용
            from hwp_viewer.markdown_formatter import MarkdownFormatter

            formatter = MarkdownFormatter(use_emoji=emoji)

            # 메타데이터 준비
            metadata = {}
            if doc.metadata.title:
                metadata['제목'] = doc.metadata.title
            if doc.metadata.author:
                metadata['작성자'] = doc.metadata.author
            if doc.metadata.keywords:
                metadata['키워드'] = doc.metadata.keywords
            metadata['원본 파일'] = Path(file_path).name

            from datetime import datetime
            metadata['추출 일시'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 본문 텍스트 준비
            if doc.paragraphs:
                content = '\n'.join([para.text for para in doc.paragraphs if para.text])
            else:
                content = doc.raw_text

            # 마크다운 포맷터로 문서 생성
            text = formatter.format_document(
                title=Path(file_path).stem,
                content=content,
                metadata=metadata
            )
        else:
            # 일반 텍스트
            text = doc.raw_text

        # 출력 처리
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(text)
            file_type = "마크다운" if output.endswith('.md') else "텍스트"
            click.echo(f"✅ {file_type}를 {output}에 저장했습니다.")
            click.echo(f"   - 크기: {len(text):,} 자")
            click.echo(f"   - 줄 수: {text.count(chr(10)):,} 줄")
        else:
            click.echo(text)

    except Exception as e:
        click.echo(f"❌ 오류: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--json', 'as_json', is_flag=True, help='JSON 형식으로 출력')
def info(file_path, as_json):
    """HWP 파일 정보 표시"""
    try:
        parser = HWPParser()
        doc = parser.parse(file_path)

        if as_json:
            click.echo(json.dumps(doc.to_dict(), ensure_ascii=False, indent=2))
        else:
            click.echo(f"제목: {doc.metadata.title}")
            click.echo(f"작성자: {doc.metadata.author}")
            click.echo(f"단락 수: {len(doc.paragraphs)}")
            click.echo(f"테이블 수: {len(doc.tables)}")
            click.echo(f"텍스트 길이: {len(doc.raw_text)} 자")

    except Exception as e:
        click.echo(f"오류: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--format', type=click.Choice(['pdf', 'html', 'txt']), default='pdf')
@click.option('-o', '--output', help='출력 파일 경로')
def convert(file_path, format, output):
    """HWP 파일을 다른 형식으로 변환"""
    click.echo(f"변환 기능은 현재 개발 중입니다.")
    # TODO: LibreOffice 또는 다른 변환 도구 연동


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.argument('search_text')
def search(file_path, search_text):
    """HWP 파일 내 텍스트 검색"""
    try:
        parser = HWPParser()
        doc = parser.parse(file_path)

        found = False
        for i, para in enumerate(doc.paragraphs, 1):
            if search_text.lower() in para.text.lower():
                click.echo(f"[단락 {i}] {para.text[:100]}...")
                found = True

        if not found:
            click.echo(f"'{search_text}'를 찾을 수 없습니다.")

    except Exception as e:
        click.echo(f"오류: {e}", err=True)
        sys.exit(1)


def main():
    """메인 진입점"""
    cli()


if __name__ == '__main__':
    main()