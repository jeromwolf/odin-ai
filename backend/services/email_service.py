"""
이메일 발송 서비스
인증 이메일 등 트랜잭션 이메일 발송
"""

import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate

logger = logging.getLogger(__name__)


def _get_smtp_config() -> dict:
    """환경변수에서 SMTP 설정 읽기"""
    return {
        "enabled": os.getenv("EMAIL_ENABLED", "false").lower() == "true",
        "host": os.getenv("EMAIL_HOST", "smtp.gmail.com"),
        "port": int(os.getenv("EMAIL_PORT", "587")),
        "username": os.getenv("EMAIL_USERNAME", ""),
        "password": os.getenv("EMAIL_PASSWORD", ""),
        "from_email": os.getenv("EMAIL_FROM", ""),
        "use_tls": os.getenv("EMAIL_USE_TLS", "true").lower() == "true",
    }


def send_verification_email(to_email: str, token: str, username: str) -> bool:
    """이메일 인증 메일 발송

    Args:
        to_email: 수신자 이메일
        token: 이메일 인증 토큰
        username: 사용자명 (이메일 본문에 표시)

    Returns:
        bool: 발송 성공 여부
    """
    config = _get_smtp_config()

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    verify_link = f"{frontend_url}/verify-email?token={token}"

    if not config["enabled"]:
        logger.info(
            f"이메일 발송 비활성화 - 인증 링크 (개발용): {verify_link}"
        )
        return False

    if not config["username"] or not config["password"]:
        logger.warning("이메일 계정 정보가 설정되지 않아 인증 메일을 발송하지 않습니다")
        return False

    from_email = config["from_email"] or config["username"]

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: Arial, sans-serif; color: #333; background: #f5f5f5; margin: 0; padding: 0; }}
    .container {{ max-width: 600px; margin: 40px auto; background: #fff; border-radius: 8px;
                  padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
    h1 {{ color: #2c3e50; font-size: 24px; }}
    p {{ line-height: 1.6; }}
    .btn {{ display: inline-block; margin: 20px 0; padding: 14px 28px;
            background: #3498db; color: #fff; text-decoration: none;
            border-radius: 5px; font-size: 16px; font-weight: bold; }}
    .link-text {{ word-break: break-all; color: #7f8c8d; font-size: 13px; }}
    .footer {{ margin-top: 30px; font-size: 12px; color: #95a5a6; border-top: 1px solid #eee; padding-top: 20px; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>ODIN-AI 이메일 인증</h1>
    <p>안녕하세요, <strong>{username}</strong>님!</p>
    <p>ODIN-AI에 가입해 주셔서 감사합니다.<br>
       아래 버튼을 클릭하여 이메일 인증을 완료해 주세요.</p>
    <a href="{verify_link}" class="btn">이메일 인증하기</a>
    <p>버튼이 작동하지 않으면 아래 링크를 브라우저에 직접 복사하세요:</p>
    <p class="link-text">{verify_link}</p>
    <p><strong>이 링크는 24시간 후 만료됩니다.</strong></p>
    <div class="footer">
      <p>본인이 가입하지 않았다면 이 이메일을 무시하세요.</p>
      <p>ODIN-AI | 공공입찰 정보 분석 플랫폼</p>
    </div>
  </div>
</body>
</html>
"""

    text_content = (
        f"안녕하세요, {username}님!\n\n"
        f"ODIN-AI 이메일 인증을 완료하려면 아래 링크를 방문해 주세요:\n\n"
        f"{verify_link}\n\n"
        f"이 링크는 24시간 후 만료됩니다.\n\n"
        f"본인이 가입하지 않았다면 이 이메일을 무시하세요.\n\n"
        f"ODIN-AI"
    )

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "[ODIN-AI] 이메일 인증을 완료해 주세요"
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Date"] = formatdate(localtime=True)

        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        with smtplib.SMTP(config["host"], config["port"]) as server:
            if config["use_tls"]:
                server.starttls()
            server.login(config["username"], config["password"])
            server.send_message(msg)

        logger.info(f"이메일 인증 메일 발송 완료: {to_email}")
        return True

    except Exception as e:
        logger.error(f"이메일 인증 메일 발송 실패 ({to_email}): {e}")
        return False
