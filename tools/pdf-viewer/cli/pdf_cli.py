#!/usr/bin/env python
"""
PDF Viewer CLI 도구
"""

import click
import sys
from pathlib import Path
import json

# 상위 디렉토리의 pdf_viewer 모듈 임포트
sys.path.append(str(Path(__file__).parent.parent))

from pdf_viewer import PDFParser
from pdf_viewer.markdown_formatter import PDFMarkdownFormatter


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """PDF Viewer - PDF 파일 처리 도구"""
    pass


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('-o', '--output', help='출력 파일 경로')
@click.option('--format', type=click.Choice(['txt', 'md', 'markdown']), default='txt', help='출력 형식')
@click.option('--method', type=click.Choice(['auto', 'pypdf2', 'pdfplumber', 'pymupdf']), default='auto', help='파싱 방법')
@click.option('--emoji', is_flag=True, help='이모지 포함 (기본: 미포함)')
def extract(file_path, output, format, method, emoji):
    """PDF 파일에서 텍스트 추출

    사용 예시:
        python cli/pdf_cli.py extract document.pdf                        # 화면 출력
        python cli/pdf_cli.py extract document.pdf -o output.txt          # 텍스트 파일로 저장
        python cli/pdf_cli.py extract document.pdf -o output.md --format md  # 마크다운으로 저장
        python cli/pdf_cli.py extract document.pdf --method pdfplumber    # 특정 파서 사용
    """
    try:
        # PDF 파서 초기화
        parser = PDFParser(method=method)

        # PDF 파일 파싱
        doc = parser.parse(file_path)

        # 출력 형식에 따라 텍스트 생성
        if format in ['md', 'markdown'] or (output and output.endswith('.md')):
            # 마크다운 형식으로 생성
            formatter = PDFMarkdownFormatter(use_emoji=emoji)

            # 메타데이터 준비
            metadata = {}
            if doc.metadata.title:
                metadata['제목'] = doc.metadata.title
            if doc.metadata.author:
                metadata['작성자'] = doc.metadata.author
            if doc.metadata.creator:
                metadata['생성도구'] = doc.metadata.creator
            if doc.metadata.pages:
                metadata['총 페이지'] = f"{doc.metadata.pages}페이지"

            metadata['원본 파일'] = Path(file_path).name

            from datetime import datetime
            metadata['추출 일시'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 페이지 정보 준비
            pages_info = []
            for page in doc.pages:
                pages_info.append({
                    'page_num': page.page_num,
                    'text': page.text,
                    'tables': page.tables
                })

            # 마크다운 포맷터로 문서 생성
            text = formatter.format_document(
                title=Path(file_path).stem,
                content=doc.raw_text,
                metadata=metadata,
                pages=pages_info
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
            if doc.pages:
                click.echo(f"   - 페이지: {len(doc.pages)}페이지")
                total_tables = sum(len(page.tables) for page in doc.pages)
                if total_tables > 0:
                    click.echo(f"   - 테이블: {total_tables}개")
        else:
            click.echo(text)

    except Exception as e:
        click.echo(f"❌ 오류: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--json', 'as_json', is_flag=True, help='JSON 형식으로 출력')
@click.option('--method', type=click.Choice(['auto', 'pypdf2', 'pdfplumber', 'pymupdf']), default='auto', help='파싱 방법')
def info(file_path, as_json, method):
    """PDF 파일 정보 표시"""
    try:
        parser = PDFParser(method=method)
        doc = parser.parse(file_path)

        if as_json:
            click.echo(json.dumps(doc.to_dict(), ensure_ascii=False, indent=2))
        else:
            click.echo(f"📄 PDF 파일 정보")
            click.echo(f"파일명: {Path(file_path).name}")
            click.echo(f"제목: {doc.metadata.title or 'N/A'}")
            click.echo(f"작성자: {doc.metadata.author or 'N/A'}")
            click.echo(f"생성도구: {doc.metadata.creator or 'N/A'}")
            click.echo(f"페이지 수: {doc.metadata.pages}")

            total_tables = sum(len(page.tables) for page in doc.pages)
            click.echo(f"테이블 수: {total_tables}")
            click.echo(f"텍스트 길이: {len(doc.raw_text):,} 자")

            if doc.metadata.creation_date:
                click.echo(f"생성 일시: {doc.metadata.creation_date}")

    except Exception as e:
        click.echo(f"❌ 오류: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.argument('search_text')
@click.option('--method', type=click.Choice(['auto', 'pypdf2', 'pdfplumber', 'pymupdf']), default='auto', help='파싱 방법')
def search(file_path, search_text, method):
    """PDF 파일 내 텍스트 검색"""
    try:
        parser = PDFParser(method=method)
        doc = parser.parse(file_path)

        found = False
        for page in doc.pages:
            if search_text.lower() in page.text.lower():
                click.echo(f"[페이지 {page.page_num}] {page.text[:200]}...")
                found = True

        if not found:
            click.echo(f"'{search_text}'를 찾을 수 없습니다.")

    except Exception as e:
        click.echo(f"❌ 오류: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('-o', '--output', help='출력 디렉토리')
@click.option('--method', type=click.Choice(['auto', 'pypdf2', 'pdfplumber', 'pymupdf']), default='auto', help='파싱 방법')
def tables(file_path, output, method):
    """PDF에서 테이블 추출"""
    try:
        parser = PDFParser(method=method)
        doc = parser.parse(file_path)

        total_tables = 0
        for page in doc.pages:
            for i, table in enumerate(page.tables):
                total_tables += 1
                table_name = f"table_page{page.page_num}_{i+1}.csv"

                if output:
                    output_path = Path(output) / table_name
                    output_path.parent.mkdir(parents=True, exist_ok=True)

                    with open(output_path, 'w', encoding='utf-8') as f:
                        for row in table.cells:
                            f.write(','.join([f'"{cell}"' if cell else '""' for cell in row]) + '\\n')

                    click.echo(f"✅ {table_name} 저장됨 ({table.rows}행 x {table.cols}열)")
                else:
                    click.echo(f"\\n📊 페이지 {page.page_num} - 테이블 {i+1} ({table.rows}행 x {table.cols}열)")
                    for j, row in enumerate(table.cells[:3]):  # 처음 3행만 표시
                        click.echo(f"   {j+1}: {' | '.join(row)}")
                    if table.rows > 3:
                        click.echo(f"   ... {table.rows-3}행 더 있음")

        if total_tables == 0:
            click.echo("테이블을 찾을 수 없습니다.")
        else:
            click.echo(f"\\n총 {total_tables}개의 테이블 발견")

    except Exception as e:
        click.echo(f"❌ 오류: {e}", err=True)
        sys.exit(1)


def main():
    """메인 진입점"""
    cli()


if __name__ == '__main__':
    main()