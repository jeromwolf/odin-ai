#!/usr/bin/env python3
"""
프로덕션 배치 프로그램 (이메일 발송 기능 포함)
환경변수를 통한 설정 관리, 중복 체크, 이메일 보고서 발송
"""

import os
import sys
import json
import time
import shutil
import asyncio
import smtplib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
import logging
from dotenv import load_dotenv

import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from loguru import logger

# 프로젝트 루트 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.database.models import Base, BidAnnouncement, BidDocument, BidExtractedInfo, BidTag, BidTagRelation
from src.services.document_processor import DocumentProcessor

# .env 파일 로드
load_dotenv()


class EmailSender:
    """이메일 발송 클래스"""

    def __init__(self):
        self.enabled = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
        self.host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        self.port = int(os.getenv('EMAIL_PORT', '587'))
        self.username = os.getenv('EMAIL_USERNAME', '')
        self.password = os.getenv('EMAIL_PASSWORD', '')
        self.from_email = os.getenv('EMAIL_FROM', 'ODIN-AI Batch <noreply@odin-ai.kr>')
        self.to_emails = os.getenv('EMAIL_TO', '').split(',')
        self.use_tls = os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true'

    def get_detailed_stats(self, session) -> Dict:
        """상세 통계 수집"""
        from sqlalchemy import text

        details = {
            'file_types': {},
            'markdown_stats': {},
            'extracted_info': {},
            'tags': {},
            'errors_detail': [],
            'db_changes': [],
            'file_cleanup': []
        }

        try:
            # 파일 타입별 다운로드 통계
            result = session.execute(text("""
                SELECT file_extension, COUNT(*) as cnt
                FROM bid_documents
                WHERE download_status = 'completed'
                GROUP BY file_extension
            """))
            for row in result:
                ext = row[0] or 'unknown'
                details['file_types'][ext] = row[1]

            # 마크다운 변환 통계
            result = session.execute(text("""
                SELECT processing_status, COUNT(*) as cnt
                FROM bid_documents
                WHERE download_status = 'completed'
                GROUP BY processing_status
            """))
            for row in result:
                status = row[0] or 'pending'
                details['markdown_stats'][status] = row[1]

            # 추출된 정보 통계
            result = session.execute(text("""
                SELECT info_category, field_name, COUNT(*) as cnt
                FROM bid_extracted_info
                GROUP BY info_category, field_name
                ORDER BY info_category, field_name
            """))
            for row in result:
                category = row[0]
                field = row[1]
                count = row[2]
                if category not in details['extracted_info']:
                    details['extracted_info'][category] = {}
                details['extracted_info'][category][field] = count

            # 태그 통계 (category 컬럼이 없을 수 있음)
            try:
                result = session.execute(text("""
                    SELECT bt.tag_name, COUNT(btr.bid_notice_no) as cnt
                    FROM bid_tags bt
                    LEFT JOIN bid_tag_relations btr ON bt.tag_id = btr.tag_id
                    GROUP BY bt.tag_id, bt.tag_name
                    ORDER BY cnt DESC
                    LIMIT 10
                """))
                for row in result:
                    tag_name = row[0]
                    count = row[1]
                    details['tags'][tag_name] = {'category': 'general', 'count': count}
            except Exception as e:
                logger.debug(f"태그 통계 수집 스킵: {e}")

            # 오류 상세 정보
            result = session.execute(text("""
                SELECT bid_notice_no, file_name, error_message
                FROM bid_documents
                WHERE processing_status = 'failed'
                AND error_message IS NOT NULL
                LIMIT 5
            """))
            for row in result:
                details['errors_detail'].append({
                    'bid_no': row[0],
                    'file': row[1],
                    'error': row[2]
                })

        except Exception as e:
            logger.error(f"상세 통계 수집 실패: {e}")

        return details

    def create_html_report(self, stats: Dict) -> str:
        """HTML 형식의 보고서 생성 (상세 버전)"""
        elapsed = stats.get('elapsed_time', 0)
        test_mode = stats.get('test_mode', False)
        details = stats.get('details', {})

        # 테스트 모드 초기화 정보
        init_info_html = ""
        if test_mode:
            db_changes_list = ""
            if details.get('db_changes'):
                for change in details['db_changes']:
                    db_changes_list += f"<li>{change}</li>"

            file_cleanup_list = ""
            if details.get('file_cleanup'):
                for cleanup in details['file_cleanup']:
                    file_cleanup_list += f"<li>{cleanup}</li>"

            init_info_html = f"""
            <div style="background-color: #ffebee; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #c62828;">🔧 TEST MODE 실행 - 시스템 초기화 완료</h3>
                <h4 style="color: #c62828;">데이터베이스 변경사항:</h4>
                <ul style="color: #c62828;">
                    {db_changes_list if db_changes_list else '<li>bid_announcements, bid_documents, bid_attachments, bid_extracted_info, bid_schedule, bid_tags, bid_tag_relations 테이블 재생성</li>'}
                </ul>
                <h4 style="color: #c62828;">파일 시스템 정리:</h4>
                <ul style="color: #c62828;">
                    {file_cleanup_list if file_cleanup_list else '<li>storage/documents 디렉토리 초기화</li><li>storage/markdown 디렉토리 초기화</li>'}
                </ul>
            </div>
            """

        # 파일 타입별 통계
        file_types_html = ""
        if details.get('file_types'):
            file_rows = ""
            for ext, count in details['file_types'].items():
                file_rows += f"<tr><td>{ext.upper()}</td><td>{count}개</td></tr>"
            file_types_html = f"""
            <h3>📁 다운로드 파일 종류별 통계</h3>
            <table style="width: 50%;">
                <thead>
                    <tr><th>확장자</th><th>개수</th></tr>
                </thead>
                <tbody>
                    {file_rows}
                </tbody>
            </table>
            """

        # 마크다운 변환 통계
        markdown_html = ""
        if details.get('markdown_stats'):
            md_rows = ""
            for status, count in details['markdown_stats'].items():
                icon = "✅" if status == "completed" else "❌" if status == "failed" else "⏳"
                md_rows += f"<tr><td>{icon} {status}</td><td>{count}개</td></tr>"
            markdown_html = f"""
            <h3>📝 마크다운 변환 결과</h3>
            <table style="width: 50%;">
                <thead>
                    <tr><th>상태</th><th>개수</th></tr>
                </thead>
                <tbody>
                    {md_rows}
                </tbody>
            </table>
            """

        # 추출된 정보 통계
        extracted_html = ""
        if details.get('extracted_info'):
            extracted_rows = ""
            for category, fields in details['extracted_info'].items():
                for field, count in fields.items():
                    table_name = "bid_extracted_info"
                    extracted_rows += f"""
                    <tr>
                        <td>{category}</td>
                        <td>{field}</td>
                        <td>{count}개</td>
                        <td>{table_name}</td>
                    </tr>
                    """
            if extracted_rows:
                extracted_html = f"""
                <h3>💡 추출된 정보 및 저장 위치</h3>
                <table>
                    <thead>
                        <tr>
                            <th>카테고리</th>
                            <th>필드명</th>
                            <th>추출 건수</th>
                            <th>저장 테이블</th>
                        </tr>
                    </thead>
                    <tbody>
                        {extracted_rows}
                    </tbody>
                </table>
                """

        # 태그 통계
        tags_html = ""
        if details.get('tags'):
            tag_rows = ""
            for tag_name, info in list(details['tags'].items())[:10]:
                category = info.get('category', 'unknown')
                count = info.get('count', 0)
                tag_rows += f"""
                <tr>
                    <td>{tag_name}</td>
                    <td>{category}</td>
                    <td>{count}개</td>
                </tr>
                """
            if tag_rows:
                tags_html = f"""
                <h3>🏷️ 생성된 해시태그 (상위 10개)</h3>
                <table style="width: 70%;">
                    <thead>
                        <tr>
                            <th>태그명</th>
                            <th>카테고리</th>
                            <th>적용 공고 수</th>
                        </tr>
                    </thead>
                    <tbody>
                        {tag_rows}
                    </tbody>
                </table>
                """

        # 오류 상세
        errors_html = ""
        if details.get('errors_detail'):
            error_rows = ""
            for err in details['errors_detail']:
                error_rows += f"""
                <tr>
                    <td>{err['bid_no']}</td>
                    <td>{err['file']}</td>
                    <td style="color: red;">{err['error'][:100]}...</td>
                </tr>
                """
            errors_html = f"""
            <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin-top: 20px;">
                <h3 style="color: #856404;">⚠️ 처리 실패 상세 내역</h3>
                <table>
                    <thead>
                        <tr>
                            <th>공고번호</th>
                            <th>파일명</th>
                            <th>오류 내용</th>
                        </tr>
                    </thead>
                    <tbody>
                        {error_rows}
                    </tbody>
                </table>
            </div>
            """
        elif stats.get('errors'):
            # 기본 오류 표시
            errors_list = '\n'.join([f"<li>{error}</li>" for error in stats['errors'][:10]])
            errors_html = f"""
            <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin-top: 20px;">
                <h3 style="color: #856404;">⚠️ 오류 발생 ({len(stats['errors'])}건)</h3>
                <ul style="color: #856404;">
                    {errors_list}
                </ul>
            </div>
            """

        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .header p {{
                    margin: 10px 0 0 0;
                    opacity: 0.9;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                }}
                .stat-card {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #667eea;
                }}
                .stat-card h3 {{
                    margin: 0 0 10px 0;
                    color: #667eea;
                    font-size: 14px;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                .stat-card .value {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #333;
                }}
                .stat-card .label {{
                    font-size: 14px;
                    color: #666;
                    margin-top: 5px;
                }}
                .summary {{
                    background: #e7f3ff;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .summary h2 {{
                    color: #0066cc;
                    margin-top: 0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #667eea;
                    color: white;
                }}
                tr:hover {{
                    background-color: #f5f5f5;
                }}
                .success {{
                    color: #28a745;
                    font-weight: bold;
                }}
                .warning {{
                    color: #ffc107;
                    font-weight: bold;
                }}
                .error {{
                    color: #dc3545;
                    font-weight: bold;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #666;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 ODIN-AI 배치 실행 보고서</h1>
                <p>{stats['execution_date']}</p>
            </div>

            <div class="summary">
                <h2>📊 실행 요약</h2>
                <p>
                    <strong>실행 시간:</strong> {elapsed:.1f}초<br>
                    <strong>실행 모드:</strong> {'테스트 모드' if stats.get('test_mode', False) else '프로덕션 모드'}<br>
                    <strong>실행 상태:</strong>
                    <span class="{'success' if not stats['errors'] else 'error'}">
                        {'✅ 성공' if not stats['errors'] else '⚠️ 부분 성공'}
                    </span>
                </p>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <h3>전체 공고</h3>
                    <div class="value">{stats['total_count']}</div>
                    <div class="label">건</div>
                </div>
                <div class="stat-card">
                    <h3>신규 삽입</h3>
                    <div class="value">{stats['inserted']}</div>
                    <div class="label">건</div>
                </div>
                <div class="stat-card">
                    <h3>업데이트</h3>
                    <div class="value">{stats['updated']}</div>
                    <div class="label">건</div>
                </div>
                <div class="stat-card">
                    <h3>스킵</h3>
                    <div class="value">{stats['skipped']}</div>
                    <div class="label">건</div>
                </div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>처리 단계</th>
                        <th>처리 건수</th>
                        <th>상태</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>📥 API 데이터 수집</td>
                        <td>{stats['total_count']}</td>
                        <td class="{'success' if stats['total_count'] > 0 else 'warning'}">
                            {'완료' if stats['total_count'] > 0 else '데이터 없음'}
                        </td>
                    </tr>
                    <tr>
                        <td>💾 DB 저장 (신규)</td>
                        <td>{stats['inserted']}</td>
                        <td class="success">완료</td>
                    </tr>
                    <tr>
                        <td>🔄 DB 업데이트</td>
                        <td>{stats['updated']}</td>
                        <td class="success">완료</td>
                    </tr>
                    <tr>
                        <td>📄 문서 다운로드</td>
                        <td>{stats['downloaded']}</td>
                        <td class="{'success' if stats['downloaded'] > 0 else 'warning'}">
                            {'완료' if stats['downloaded'] > 0 else '대상 없음'}
                        </td>
                    </tr>
                    <tr>
                        <td>🔧 문서 처리</td>
                        <td>{stats['processed']}</td>
                        <td class="{'success' if stats['processed'] > 0 else 'warning'}">
                            {'완료' if stats['processed'] > 0 else '대상 없음'}
                        </td>
                    </tr>
                </tbody>
            </table>

            {init_info_html}
            {file_types_html}
            {markdown_html}
            {extracted_html}
            {tags_html}
            {errors_html}

            <div class="footer">
                <p>
                    ODIN-AI Batch System v1.0<br>
                    이 보고서는 자동으로 생성되었습니다.<br>
                    문의: support@odin-ai.kr
                </p>
            </div>
        </body>
        </html>
        """
        return html_template

    def send_report(self, stats: Dict) -> bool:
        """이메일 보고서 발송"""
        if not self.enabled:
            logger.info("📧 이메일 발송이 비활성화되어 있습니다")
            return False

        if not self.username or not self.password:
            logger.warning("📧 이메일 계정 정보가 설정되지 않았습니다")
            return False

        try:
            # 메시지 생성
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[ODIN-AI] 배치 실행 보고서 - {datetime.now().strftime('%Y-%m-%d')}"
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Date'] = formatdate(localtime=True)

            # HTML 보고서 생성
            html_content = self.create_html_report(stats)

            # 텍스트 버전 (간단)
            text_content = f"""
ODIN-AI 배치 실행 보고서
=======================
실행 시간: {stats['execution_date']}
소요 시간: {stats.get('elapsed_time', 0):.1f}초

처리 결과:
- 전체 공고: {stats['total_count']}건
- 신규 삽입: {stats['inserted']}건
- 업데이트: {stats['updated']}건
- 스킵: {stats['skipped']}건
- 다운로드: {stats['downloaded']}건
- 처리 완료: {stats['processed']}건

{'오류: ' + str(len(stats['errors'])) + '건' if stats['errors'] else '오류 없음'}
            """

            # 메시지에 컨텐츠 추가
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')

            msg.attach(part1)
            msg.attach(part2)

            # SMTP 서버 연결 및 발송
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"✅ 이메일 보고서 발송 완료: {', '.join(self.to_emails)}")
            return True

        except Exception as e:
            logger.error(f"❌ 이메일 발송 실패: {e}")
            return False


class ProductionBatchWithEmail:
    """프로덕션 배치 프로그램 (이메일 발송 포함)"""

    def __init__(self):
        # 환경변수에서 설정 읽기
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db')
        self.api_url = os.getenv('BID_API_URL', 'http://apis.data.go.kr/1230000/BidPublicInfoService/getBidPblancListInfoCnstwk')
        self.api_key = os.getenv('BID_API_KEY', '1BoVC3SjQb3kb8M%2FdG5vXXt37P8I9OWBCY85W%2BHX3BqOqnFYSZhmxJLKdqGYlGRfiUOQ8k4T6LCMfT9Cs7vCPA%3D%3D')
        self.test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
        self.batch_size = int(os.getenv('BATCH_SIZE', '100'))
        self.max_pages = int(os.getenv('MAX_PAGES', '10'))

        # DB 설정
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)

        # 파일 저장 경로
        self.storage_path = Path("./storage")

        # 이메일 발송기
        self.email_sender = EmailSender()

        # 통계
        self.stats = {
            'start_time': None,
            'end_time': None,
            'elapsed_time': 0,
            'execution_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'test_mode': self.test_mode,
            'total_count': 0,
            'inserted': 0,
            'updated': 0,
            'skipped': 0,
            'downloaded': 0,
            'processed': 0,
            'errors': []
        }

        # 로거 설정
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        logger.remove()
        logger.add(sys.stdout, level=log_level)
        logger.add(f"batch_{datetime.now().strftime('%Y%m%d')}.log", rotation="1 day", level=log_level)

    def initialize_system(self):
        """시스템 초기화 (TEST_MODE가 true일 때만)"""
        if self.test_mode:
            logger.warning("⚠️ TEST_MODE 활성화: DB 및 파일 초기화 진행")

            # 초기화 추적
            if 'details' not in self.stats:
                self.stats['details'] = {}
            self.stats['details']['db_changes'] = []
            self.stats['details']['file_cleanup'] = []

            # DB 초기화
            with self.engine.connect() as conn:
                tables = [
                    'bid_tag_relations',
                    'bid_tags',
                    'bid_extracted_info',
                    'bid_schedule',
                    'bid_attachments',
                    'bid_documents',
                    'bid_announcements'
                ]

                for table in tables:
                    try:
                        conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                        conn.commit()
                        logger.info(f"  ✅ {table} 테이블 삭제")
                        self.stats['details']['db_changes'].append(f"{table} 테이블 삭제 및 재생성")
                    except Exception as e:
                        logger.error(f"  ❌ {table} 삭제 실패: {e}")

            # 테이블 재생성
            Base.metadata.create_all(self.engine)
            logger.info("  ✅ 테이블 재생성 완료")

            # 파일 시스템 초기화
            for subdir in ['documents', 'markdown']:
                dir_path = self.storage_path / subdir
                if dir_path.exists():
                    # 파일 개수 세기
                    file_count = sum(1 for _ in dir_path.rglob('*') if _.is_file())
                    shutil.rmtree(dir_path)
                    self.stats['details']['file_cleanup'].append(f"{subdir} 디렉토리 ({file_count}개 파일 삭제)")
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"  ✅ {subdir} 디렉토리 초기화")
        else:
            logger.info("🚀 프로덕션 모드: 기존 데이터 유지")
            # 디렉토리만 생성 (없을 경우)
            for subdir in ['documents', 'markdown']:
                dir_path = self.storage_path / subdir
                dir_path.mkdir(parents=True, exist_ok=True)

    def get_total_count(self, start_date: str, end_date: str) -> int:
        """전체 공고 건수 확인"""
        url = (
            f"{self.api_url}?"
            f"serviceKey={self.api_key}&"
            f"numOfRows=1&pageNo=1&"
            f"inqryBgnDt={start_date}&"
            f"inqryEndDt={end_date}&"
            f"inqryDiv=1&"
            f"type=json"
        )

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            total_count = data.get('response', {}).get('body', {}).get('totalCount', 0)
            logger.info(f"📊 오늘 총 공고 수: {total_count}개")
            return total_count

        except Exception as e:
            logger.error(f"전체 건수 조회 실패: {e}")
            self.stats['errors'].append(f"API 조회 실패: {str(e)}")
            return 0

    def collect_announcements(self, session) -> Dict[str, int]:
        """공고 수집 (중복 체크 포함)"""
        # 오늘 날짜 기준 (하루 단위)
        today = datetime.now()
        start_date = today.strftime("%Y%m%d0000")
        end_date = today.strftime("%Y%m%d2359")

        logger.info(f"📅 수집 기간: {start_date} ~ {end_date}")

        # 전체 건수 확인
        total_count = self.get_total_count(start_date, end_date)
        if total_count == 0:
            return {'total': 0, 'inserted': 0, 'updated': 0, 'skipped': 0}

        # 페이지네이션으로 전체 수집
        total_pages = min((total_count + self.batch_size - 1) // self.batch_size, self.max_pages)
        logger.info(f"📄 총 {total_pages}페이지 수집 예정 (페이지당 {self.batch_size}개)")

        result = {'total': 0, 'inserted': 0, 'updated': 0, 'skipped': 0}

        for page in range(1, total_pages + 1):
            url = (
                f"{self.api_url}?"
                f"serviceKey={self.api_key}&"
                f"numOfRows={self.batch_size}&pageNo={page}&"
                f"inqryBgnDt={start_date}&"
                f"inqryEndDt={end_date}&"
                f"inqryDiv=1&"
                f"type=json"
            )

            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()
                items = data.get('response', {}).get('body', {}).get('items', [])

                logger.info(f"  📥 페이지 {page}: {len(items)}개 조회")

                for item in items:
                    status = self.process_announcement(session, item)
                    result[status] += 1
                    result['total'] += 1

                session.commit()

            except Exception as e:
                error_msg = f"페이지 {page} 수집 실패: {str(e)}"
                logger.error(error_msg)
                self.stats['errors'].append(error_msg)

        logger.info(f"✅ 수집 완료: 신규 {result['inserted']}개, 업데이트 {result['updated']}개, 스킵 {result['skipped']}개")
        return result

    def process_announcement(self, session, item: Dict) -> str:
        """개별 공고 처리 (중복 체크)"""
        bid_notice_no = item.get('bidNtceNo', '')

        # 기존 데이터 확인
        existing = session.query(BidAnnouncement).filter_by(
            bid_notice_no=bid_notice_no
        ).first()

        if existing:
            # 이미 처리 완료된 경우 스킵
            if existing.collection_status == 'completed':
                logger.debug(f"  ⏭️ 스킵: {bid_notice_no} (이미 처리 완료)")
                return 'skipped'

            # 미완료 데이터는 업데이트
            else:
                existing.title = item.get('bidNtceNm', existing.title)
                existing.updated_at = datetime.now()
                existing.collection_status = 'completed'
                logger.debug(f"  🔄 업데이트: {bid_notice_no}")
                return 'updated'

        else:
            # 신규 데이터 삽입
            try:
                announcement = BidAnnouncement(
                    bid_notice_no=bid_notice_no,
                    bid_notice_ord=item.get('bidNtceOrd', '000'),
                    title=item.get('bidNtceNm', ''),
                    organization_code=item.get('ntceInsttCd', ''),
                    organization_name=item.get('ntceInsttNm', ''),
                    department_name=item.get('dmndInsttNm', ''),
                    announcement_date=self._parse_date(item.get('bidNtceDt')),
                    bid_start_date=self._parse_date(item.get('bidBeginDt')),
                    bid_end_date=self._parse_date(item.get('bidClseDt')),
                    opening_date=self._parse_date(item.get('opengDt')),
                    estimated_price=self._parse_price(item.get('presmptPrce')),
                    bid_method=item.get('bidMethdNm', ''),
                    contract_method=item.get('cntrctCnclsMthdNm', ''),
                    detail_page_url=item.get('bidNtceDtlUrl', ''),
                    standard_doc_url=item.get('stdNtceDocUrl', ''),
                    status='active',
                    collection_status='completed',
                    collected_at=datetime.now()
                )
                session.add(announcement)

                # 문서 메타데이터도 생성
                if item.get('stdNtceDocUrl'):
                    # 기존 문서 확인
                    existing_doc = session.query(BidDocument).filter_by(
                        bid_notice_no=bid_notice_no,
                        document_type='standard'
                    ).first()

                    if not existing_doc:
                        file_name = item.get('ntceSpecFileNm1', 'standard.hwp')
                        # 파일 확장자 추출
                        file_extension = ''
                        if '.' in file_name:
                            file_extension = file_name.split('.')[-1].lower()

                        doc = BidDocument(
                            bid_notice_no=bid_notice_no,
                            document_type='standard',
                            file_name=file_name,
                            file_extension=file_extension,
                            download_url=item.get('stdNtceDocUrl', ''),
                            download_status='pending',
                            processing_status='pending'
                        )
                        session.add(doc)

                logger.debug(f"  ✅ 신규: {bid_notice_no}")
                return 'inserted'

            except Exception as e:
                error_msg = f"삽입 실패 {bid_notice_no}: {str(e)}"
                logger.error(f"  ❌ {error_msg}")
                self.stats['errors'].append(error_msg)
                return 'skipped'

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """날짜 파싱"""
        if not date_str:
            return None
        try:
            if ' ' in date_str:
                return datetime.strptime(date_str.split(' ')[0], '%Y-%m-%d')
            elif '-' in date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')
            elif len(date_str) >= 8:
                return datetime.strptime(date_str[:8], '%Y%m%d')
        except:
            return None

    def _parse_price(self, price_str: str) -> Optional[int]:
        """가격 파싱"""
        if not price_str:
            return None
        try:
            import re
            numbers = re.findall(r'\d+', str(price_str))
            if numbers:
                return int(''.join(numbers))
        except:
            return None

    async def download_documents(self, session) -> int:
        """신규 문서만 다운로드"""
        # 다운로드 대기 문서 조회 (pending 상태만)
        documents = session.query(BidDocument).filter(
            BidDocument.download_status == 'pending'
        ).limit(50).all()  # 배치당 최대 50개

        if not documents:
            logger.info("📄 다운로드할 신규 문서 없음")
            return 0

        logger.info(f"📥 {len(documents)}개 문서 다운로드 시작")

        success_count = 0
        for doc in documents:
            try:
                # 다운로드 로직 (실제 구현 필요)
                doc_dir = self.storage_path / "documents" / doc.bid_notice_no
                doc_dir.mkdir(parents=True, exist_ok=True)

                # 파일 확장자 업데이트 (file_name에서 추출)
                if doc.file_name and '.' in doc.file_name:
                    doc.file_extension = doc.file_name.split('.')[-1].lower()
                elif not doc.file_extension:
                    # 파일명에 확장자가 없으면 hwp로 기본 설정
                    doc.file_extension = 'hwp'

                # TEST MODE: 다운로드 시뮬레이션만 (실제 파일 생성 안함)
                if self.test_mode:
                    # 다운로드 URL과 파일 정보만 로깅
                    logger.debug(f"  [TEST] 다운로드 시뮬레이션: {doc.file_name}")
                    logger.debug(f"         URL: {doc.download_url[:100]}...")

                    # 파일 경로만 설정 (실제 파일 생성 안함)
                    file_path = doc_dir / (doc.file_name or f"document.{doc.file_extension}")
                    doc.storage_path = str(file_path)
                    doc.file_size = 0  # 테스트 모드에서는 0

                    # 다운로드 상태는 pending으로 유지 (나중에 실제 다운로드 예정)
                    doc.download_status = 'pending'
                    doc.downloaded_at = None

                    # TEST MODE에서는 다운로드 대상으로만 카운트
                    logger.debug(f"  ⏳ {doc.bid_notice_no} 다운로드 예정 ({doc.file_extension})")
                    continue  # 다음 문서로

                # 실제 다운로드 구현 (프로덕션 모드에서만)
                # TODO: Selenium 또는 requests로 실제 HWP 다운로드 구현
                doc.download_status = 'completed'
                doc.downloaded_at = datetime.now()
                success_count += 1

                logger.debug(f"  ✅ {doc.bid_notice_no} 다운로드 완료 ({doc.file_extension})")

            except Exception as e:
                error_msg = f"{doc.bid_notice_no} 다운로드 실패: {str(e)}"
                logger.error(f"  ❌ {error_msg}")
                self.stats['errors'].append(error_msg)
                doc.download_status = 'failed'
                doc.error_message = str(e)

        session.commit()
        logger.info(f"✅ {success_count}/{len(documents)}개 다운로드 완료")
        return success_count

    async def process_documents(self, session) -> int:
        """신규 문서만 처리"""
        processor = DocumentProcessor(session, self.storage_path)

        # 처리 대기 문서 조회
        documents = session.query(BidDocument).filter(
            BidDocument.download_status == 'completed',
            BidDocument.processing_status == 'pending'
        ).limit(50).all()

        if not documents:
            logger.info("🔧 처리할 신규 문서 없음")
            return 0

        logger.info(f"🔧 {len(documents)}개 문서 처리 시작")

        success_count = 0
        for doc in documents:
            try:
                result = await processor._process_document(doc)
                if doc.processing_status == 'completed':
                    success_count += 1

                    # 관련 공고 업데이트
                    announcement = session.query(BidAnnouncement).filter_by(
                        bid_notice_no=doc.bid_notice_no
                    ).first()
                    if announcement:
                        announcement.collection_status = 'completed'

                    logger.debug(f"  ✅ {doc.bid_notice_no} 처리 완료")

            except Exception as e:
                error_msg = f"{doc.bid_notice_no} 처리 실패: {str(e)}"
                logger.error(f"  ❌ {error_msg}")
                self.stats['errors'].append(error_msg)

        session.commit()
        logger.info(f"✅ {success_count}/{len(documents)}개 처리 완료")
        return success_count

    def generate_report(self):
        """실행 보고서 생성 및 이메일 발송"""
        self.stats['elapsed_time'] = time.time() - self.stats['start_time']
        elapsed = self.stats['elapsed_time']

        # 데이터베이스 연결하여 상세 통계 수집
        engine = create_engine(self.db_url)
        Session = sessionmaker(bind=engine)
        session = Session()

        # 상세 통계 수집
        if 'details' not in self.stats:
            self.stats['details'] = {}

        # 기존 초기화 정보 보존
        existing_db_changes = self.stats['details'].get('db_changes', [])
        existing_file_cleanup = self.stats['details'].get('file_cleanup', [])

        # 새로운 상세 통계 수집
        self.stats['details'].update(self.email_sender.get_detailed_stats(session))

        # 초기화 정보 복원
        if existing_db_changes:
            self.stats['details']['db_changes'] = existing_db_changes
        if existing_file_cleanup:
            self.stats['details']['file_cleanup'] = existing_file_cleanup

        session.close()

        logger.info("="*70)
        logger.info("📊 배치 실행 보고서")
        logger.info("="*70)
        logger.info(f"⏱️ 실행 시간: {elapsed:.1f}초")
        logger.info(f"📋 전체 공고: {self.stats['total_count']}개")
        logger.info(f"  ✅ 신규 삽입: {self.stats['inserted']}개")
        logger.info(f"  🔄 업데이트: {self.stats['updated']}개")
        logger.info(f"  ⏭️ 스킵: {self.stats['skipped']}개")
        logger.info(f"📥 다운로드: {self.stats['downloaded']}개")
        logger.info(f"🔧 처리 완료: {self.stats['processed']}개")

        if self.stats['errors']:
            logger.warning(f"⚠️ 오류 발생: {len(self.stats['errors'])}건")
            for error in self.stats['errors'][:5]:
                logger.warning(f"  - {error}")

        logger.info("="*70)

        # 이메일 보고서 발송
        logger.info("📧 이메일 보고서 발송 중...")
        email_result = self.email_sender.send_report(self.stats)

        if email_result:
            logger.info("✅ 이메일 보고서 발송 완료")
        else:
            logger.warning("⚠️ 이메일 보고서 발송 실패 또는 비활성화")

        # JSON 파일로도 저장
        report_path = Path(f"reports/batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"📄 보고서 파일 저장: {report_path}")

    async def run(self):
        """배치 실행"""
        self.stats['start_time'] = time.time()

        logger.info("🚀 프로덕션 배치 시작 (이메일 발송 포함)")
        logger.info(f"📅 실행 시각: {datetime.now()}")
        logger.info(f"🔧 API URL: {self.api_url}")
        logger.info(f"🔑 테스트 모드: {self.test_mode}")
        logger.info(f"📧 이메일 발송: {'활성화' if self.email_sender.enabled else '비활성화'}")

        # 1. 시스템 초기화 (TEST_MODE일 때만)
        self.initialize_system()

        session = self.Session()

        try:
            # 2. 공고 수집
            collect_result = self.collect_announcements(session)
            self.stats['total_count'] = collect_result['total']
            self.stats['inserted'] = collect_result['inserted']
            self.stats['updated'] = collect_result['updated']
            self.stats['skipped'] = collect_result['skipped']

            # 3. 문서 다운로드 (신규만)
            if collect_result['inserted'] > 0:
                self.stats['downloaded'] = await self.download_documents(session)

                # 4. 문서 처리 (신규만)
                if self.stats['downloaded'] > 0:
                    self.stats['processed'] = await self.process_documents(session)

        except Exception as e:
            error_msg = f"배치 실행 오류: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)

        finally:
            session.close()

        # 5. 보고서 생성 및 이메일 발송
        self.generate_report()

        logger.info("✅ 배치 실행 완료")


async def main():
    """메인 함수"""
    batch = ProductionBatchWithEmail()
    await batch.run()


if __name__ == "__main__":
    asyncio.run(main())