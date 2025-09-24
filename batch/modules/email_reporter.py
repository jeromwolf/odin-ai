#!/usr/bin/env python
"""
이메일 보고서 모듈
배치 실행 결과를 이메일로 발송
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from loguru import logger
import os
import json
from pathlib import Path


class EmailReporter:
    """이메일 보고서 발송기"""

    def __init__(self, db_url=None):
        """초기화

        Args:
            db_url: 데이터베이스 URL. None이면 환경변수에서 읽음
        """
        # 이메일 설정
        self.enabled = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
        self.host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        self.port = int(os.getenv('EMAIL_PORT', '587'))
        self.username = os.getenv('EMAIL_USERNAME', '')
        self.password = os.getenv('EMAIL_PASSWORD', '')
        self.from_email = os.getenv('EMAIL_FROM', '')
        self.to_emails = os.getenv('EMAIL_TO', '').split(',')
        self.use_tls = os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true'

        # DB 설정 (통계 조회용)
        self.db_url = db_url or os.getenv('DATABASE_URL', 'postgresql://blockmeta@localhost:5432/odin_db')

    def send_batch_report(self, stats):
        """배치 실행 보고서 발송

        Args:
            stats: 실행 통계 딕셔너리

        Returns:
            bool: 발송 성공 여부
        """
        if not self.enabled:
            logger.info("📧 이메일 발송이 비활성화되어 있습니다")
            return False

        if not self.username or not self.password:
            logger.warning("📧 이메일 계정 정보가 설정되지 않았습니다")
            return False

        try:
            # 상세 통계 수집
            detailed_stats = self._collect_detailed_stats()
            stats.update(detailed_stats)

            # HTML 보고서 생성
            html_content = self._create_html_report(stats)

            # 텍스트 버전
            text_content = self._create_text_report(stats)

            # 메시지 생성
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[ODIN-AI] 배치 실행 보고서 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Date'] = formatdate(localtime=True)

            # 컨텐츠 추가
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            # 이메일 발송
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

    def _collect_detailed_stats(self):
        """상세 통계 수집

        Returns:
            dict: 상세 통계 정보
        """
        engine = create_engine(self.db_url)
        Session = sessionmaker(bind=engine)
        session = Session()

        stats = {
            'db_stats': {},
            'file_types': {},
            'processing_stats': {},
            'extracted_info': {},
            'tags': []
        }

        try:
            # 전체 데이터베이스 통계
            result = session.execute(text("""
                SELECT
                    (SELECT COUNT(*) FROM bid_announcements) as announcements,
                    (SELECT COUNT(*) FROM bid_documents) as documents,
                    (SELECT COUNT(*) FROM bid_documents WHERE download_status = 'completed') as downloaded,
                    (SELECT COUNT(*) FROM bid_documents WHERE processing_status = 'completed') as processed,
                    (SELECT COUNT(*) FROM bid_extracted_info) as extracted,
                    (SELECT COUNT(*) FROM bid_tags) as tags
            """)).first()

            stats['db_stats'] = {
                'announcements': result[0],
                'documents': result[1],
                'downloaded': result[2],
                'processed': result[3],
                'extracted_info': result[4],
                'tags': result[5]
            }

            # 파일 타입별 통계
            result = session.execute(text("""
                SELECT file_extension, COUNT(*) as cnt
                FROM bid_documents
                WHERE file_extension IS NOT NULL
                GROUP BY file_extension
                ORDER BY cnt DESC
            """))

            for row in result:
                stats['file_types'][row[0]] = row[1]

            # 처리 상태별 통계
            result = session.execute(text("""
                SELECT processing_status, COUNT(*) as cnt
                FROM bid_documents
                GROUP BY processing_status
            """))

            for row in result:
                stats['processing_stats'][row[0] or 'unknown'] = row[1]

            # 추출 정보 카테고리별 통계
            result = session.execute(text("""
                SELECT info_category, COUNT(*) as cnt
                FROM bid_extracted_info
                GROUP BY info_category
            """))

            for row in result:
                stats['extracted_info'][row[0]] = row[1]

            # 인기 태그 TOP 10
            result = session.execute(text("""
                SELECT t.tag_name, COUNT(r.bid_notice_no) as cnt
                FROM bid_tags t
                LEFT JOIN bid_tag_relations r ON t.tag_id = r.tag_id
                GROUP BY t.tag_id, t.tag_name
                ORDER BY cnt DESC
                LIMIT 10
            """))

            for row in result:
                stats['tags'].append({'name': row[0], 'count': row[1]})

        except Exception as e:
            logger.error(f"통계 수집 실패: {e}")
        finally:
            session.close()

        return stats

    def _create_html_report(self, stats):
        """HTML 형식의 보고서 생성

        Args:
            stats: 통계 정보

        Returns:
            str: HTML 컨텐츠
        """
        execution_time = stats.get('execution_time', 0)
        db_stats = stats.get('db_stats', {})
        file_types = stats.get('file_types', {})
        processing_stats = stats.get('processing_stats', {})
        extracted_info = stats.get('extracted_info', {})
        tags = stats.get('tags', [])

        # 파일 타입 테이블 생성
        file_type_rows = ""
        for ext, count in file_types.items():
            file_type_rows += f"<tr><td>{ext.upper()}</td><td>{count:,}</td></tr>"

        # 처리 상태 테이블 생성
        processing_rows = ""
        for status, count in processing_stats.items():
            icon = "✅" if status == "completed" else "❌" if status == "failed" else "⏳"
            processing_rows += f"<tr><td>{icon} {status}</td><td>{count:,}</td></tr>"

        # 추출된 정보 테이블 생성
        extracted_rows = ""
        for category, count in extracted_info.items():
            category_name = {
                'requirements': '자격요건',
                'prices': '가격정보',
                'schedule': '일정정보',
                'contract_details': '계약상세'
            }.get(category, category)
            extracted_rows += f"<tr><td>{category_name}</td><td>{count:,}</td></tr>"

        # 태그 테이블 생성
        tag_rows = ""
        for tag in tags[:10]:  # 상위 10개만 표시
            tag_rows += f"<tr><td>{tag['name']}</td><td>{tag['count']:,}</td></tr>"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 900px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    border-radius: 10px;
                    padding: 30px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #34495e;
                    margin-top: 30px;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }}
                .stat-card {{
                    background: #ecf0f1;
                    padding: 15px;
                    border-radius: 8px;
                    text-align: center;
                }}
                .stat-card .number {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #2c3e50;
                }}
                .stat-card .label {{
                    font-size: 12px;
                    color: #7f8c8d;
                    text-transform: uppercase;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th, td {{
                    padding: 10px;
                    text-align: left;
                    border-bottom: 1px solid #ecf0f1;
                }}
                th {{
                    background: #34495e;
                    color: white;
                }}
                .success {{ color: #27ae60; font-weight: bold; }}
                .warning {{ color: #f39c12; font-weight: bold; }}
                .error {{ color: #e74c3c; font-weight: bold; }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #ecf0f1;
                    text-align: center;
                    color: #95a5a6;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 ODIN-AI 배치 실행 보고서</h1>

                <p><strong>실행 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>소요 시간:</strong> {execution_time:.1f}초</p>

                <h2>📊 전체 데이터베이스 현황</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="number">{db_stats.get('announcements', 0):,}</div>
                        <div class="label">공고</div>
                    </div>
                    <div class="stat-card">
                        <div class="number">{db_stats.get('documents', 0):,}</div>
                        <div class="label">문서</div>
                    </div>
                    <div class="stat-card">
                        <div class="number">{db_stats.get('downloaded', 0):,}</div>
                        <div class="label">다운로드</div>
                    </div>
                    <div class="stat-card">
                        <div class="number">{db_stats.get('processed', 0):,}</div>
                        <div class="label">처리완료</div>
                    </div>
                </div>

                <h2>📄 오늘 실행 결과</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="number">{stats.get('collected', 0):,}</div>
                        <div class="label">수집</div>
                    </div>
                    <div class="stat-card">
                        <div class="number">{stats.get('downloaded', 0):,}</div>
                        <div class="label">다운로드</div>
                    </div>
                    <div class="stat-card">
                        <div class="number">{stats.get('processed', 0):,}</div>
                        <div class="label">처리</div>
                    </div>
                    <div class="stat-card">
                        <div class="number">{stats.get('failed', 0):,}</div>
                        <div class="label">실패</div>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
                    <div>
                        <h2>📁 파일 타입별 분포</h2>
                        <table>
                            <thead>
                                <tr><th>확장자</th><th>개수</th></tr>
                            </thead>
                            <tbody>
                                {file_type_rows if file_type_rows else '<tr><td colspan="2">데이터 없음</td></tr>'}
                            </tbody>
                        </table>
                    </div>

                    <div>
                        <h2>⚙️ 처리 상태</h2>
                        <table>
                            <thead>
                                <tr><th>상태</th><th>개수</th></tr>
                            </thead>
                            <tbody>
                                {processing_rows if processing_rows else '<tr><td colspan="2">데이터 없음</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 30px;">
                    <div>
                        <h2>📋 추출된 정보</h2>
                        <table>
                            <thead>
                                <tr><th>정보 유형</th><th>건수</th></tr>
                            </thead>
                            <tbody>
                                {extracted_rows if extracted_rows else '<tr><td colspan="2">데이터 없음</td></tr>'}
                            </tbody>
                        </table>
                    </div>

                    <div>
                        <h2>🏷️ 자동 생성 태그</h2>
                        <table>
                            <thead>
                                <tr><th>태그명</th><th>사용 횟수</th></tr>
                            </thead>
                            <tbody>
                                {tag_rows if tag_rows else '<tr><td colspan="2">데이터 없음</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div style="margin-top: 30px; padding: 20px; background: #e8f4fd; border-left: 4px solid #3498db; border-radius: 4px;">
                    <h3 style="color: #2c3e50; margin-top: 0;">📊 DB 작업 내역</h3>
                    <ul style="margin: 10px 0;">
                        <li><strong>INSERT:</strong>
                            공고 {stats.get('collected', 0)}건,
                            문서 {stats.get('collected', 0)}건,
                            추출정보 {stats.get('extracted_info_count', 0)}건,
                            태그관계 {stats.get('tags_created', 0)}건
                        </li>
                        <li><strong>UPDATE:</strong>
                            문서 처리상태 {stats.get('processed', 0)}건 (pending → completed)
                        </li>
                        <li><strong>자격요건 추출:</strong> {extracted_info.get('requirements', 0)}건 성공</li>
                        <li><strong>태그 자동 분류:</strong> {len(tags)}개 태그로 {stats.get('tags_created', 0)}개 관계 생성</li>
                    </ul>
                </div>

                <div class="footer">
                    <p>ODIN-AI Batch System v1.0 | 이 보고서는 자동으로 생성되었습니다.</p>
                    <p>문의: support@odin-ai.kr</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _create_text_report(self, stats):
        """텍스트 형식의 보고서 생성

        Args:
            stats: 통계 정보

        Returns:
            str: 텍스트 컨텐츠
        """
        text = f"""
ODIN-AI 배치 실행 보고서
{'='*50}

실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
소요 시간: {stats.get('execution_time', 0):.1f}초

오늘 실행 결과:
- 수집: {stats.get('collected', 0)}건
- 다운로드: {stats.get('downloaded', 0)}건
- 처리: {stats.get('processed', 0)}건
- 실패: {stats.get('failed', 0)}건

전체 DB 현황:
- 공고: {stats.get('db_stats', {}).get('announcements', 0)}건
- 문서: {stats.get('db_stats', {}).get('documents', 0)}건
- 다운로드: {stats.get('db_stats', {}).get('downloaded', 0)}건
- 처리완료: {stats.get('db_stats', {}).get('processed', 0)}건

{'='*50}
ODIN-AI Batch System
        """

        return text

    def save_json_report(self, stats, report_dir="reports"):
        """JSON 형식으로 보고서 저장

        Args:
            stats: 통계 정보
            report_dir: 보고서 저장 디렉토리

        Returns:
            str: 저장된 파일 경로
        """
        # 디렉토리 생성
        report_path = Path(report_dir)
        report_path.mkdir(parents=True, exist_ok=True)

        # 파일명 생성
        filename = f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = report_path / filename

        # JSON 저장
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"📄 JSON 보고서 저장: {filepath}")
        return str(filepath)


# 독립 실행 가능
if __name__ == "__main__":
    reporter = EmailReporter()

    # 테스트 통계
    test_stats = {
        'execution_time': 123.4,
        'collected': 100,
        'downloaded': 50,
        'processed': 45,
        'failed': 5
    }

    # 이메일 발송
    success = reporter.send_batch_report(test_stats)
    print(f"이메일 발송: {'성공' if success else '실패'}")

    # JSON 저장
    json_path = reporter.save_json_report(test_stats)
    print(f"JSON 저장: {json_path}")