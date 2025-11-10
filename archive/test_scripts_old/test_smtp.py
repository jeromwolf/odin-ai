#!/usr/bin/env python
"""
SMTP 이메일 발송 테스트 스크립트
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env 파일 로드 완료")
except ImportError:
    print("⚠️ python-dotenv 없음 - 환경변수만 사용")

def test_smtp():
    """SMTP 설정 테스트"""

    # 환경변수에서 SMTP 설정 읽기
    smtp_host = os.getenv("SMTP_HOST") or os.getenv("EMAIL_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT") or os.getenv("EMAIL_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER") or os.getenv("EMAIL_USERNAME", "")
    smtp_password = os.getenv("SMTP_PASSWORD") or os.getenv("EMAIL_PASSWORD", "")

    print("\n📧 SMTP 설정 확인:")
    print(f"  Host: {smtp_host}")
    print(f"  Port: {smtp_port}")
    print(f"  User: {smtp_user}")
    print(f"  Password: {'*' * len(smtp_password) if smtp_password else '(없음)'}")

    if not smtp_user or not smtp_password:
        print("\n❌ SMTP 사용자 또는 비밀번호가 설정되지 않았습니다")
        print("\n💡 .env 파일에 다음 내용을 추가하세요:")
        print("SMTP_HOST=smtp.gmail.com")
        print("SMTP_PORT=587")
        print("SMTP_USER=your-email@gmail.com")
        print("SMTP_PASSWORD=your-app-password")
        return False

    try:
        # 테스트 이메일 생성
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "🎯 ODIN-AI SMTP 테스트"
        msg['From'] = smtp_user
        msg['To'] = smtp_user  # 자신에게 발송

        # HTML 본문
        html_content = f"""
        <html>
        <head>
            <style>
                .container {{ max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }}
                .header {{ background: #1976d2; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f5f5f5; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🎯 ODIN-AI SMTP 테스트</h2>
                </div>
                <div class="content">
                    <h3>✅ 이메일 발송 테스트 성공!</h3>
                    <p>SMTP 설정이 올바르게 구성되었습니다.</p>
                    <p><strong>설정 정보:</strong></p>
                    <ul>
                        <li>Host: {smtp_host}</li>
                        <li>Port: {smtp_port}</li>
                        <li>User: {smtp_user}</li>
                    </ul>
                    <p>이제 ODIN-AI 알림 시스템을 사용할 수 있습니다! 🎉</p>
                </div>
            </div>
        </body>
        </html>
        """

        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        # SMTP 서버 연결 및 발송
        print("\n📤 이메일 발송 중...")
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.set_debuglevel(0)  # 디버그 끄기
            server.starttls()
            print("  ✅ TLS 연결 성공")

            server.login(smtp_user, smtp_password)
            print("  ✅ 로그인 성공")

            server.send_message(msg)
            print("  ✅ 이메일 발송 성공")

        print(f"\n🎉 성공! {smtp_user} 메일함을 확인하세요!")
        print(f"   제목: 🎯 ODIN-AI SMTP 테스트")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ 인증 실패: {e}")
        print("\n💡 확인사항:")
        print("  1. Gmail 앱 비밀번호를 정확히 입력했는지 확인")
        print("  2. 공백을 제거했는지 확인")
        print("  3. 2단계 인증이 활성화되어 있는지 확인")
        return False

    except smtplib.SMTPException as e:
        print(f"\n❌ SMTP 오류: {e}")
        return False

    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("="*60)
    print("🔔 ODIN-AI SMTP 이메일 발송 테스트")
    print("="*60)

    success = test_smtp()

    print("\n" + "="*60)
    if success:
        print("✅ 테스트 완료 - SMTP 설정이 정상입니다")
        print("\n다음 단계:")
        print("  1. 알림 규칙 생성 (/notifications 페이지)")
        print("  2. 배치 프로그램 실행")
        print("  3. 이메일 수신 확인")
    else:
        print("❌ 테스트 실패 - SMTP 설정을 확인하세요")
    print("="*60)
