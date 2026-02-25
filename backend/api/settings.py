"""
사용자 설정 API
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging
import json
from psycopg2.extras import RealDictCursor
from database import get_db_connection
from auth.dependencies import get_current_user, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["Settings"])


class UserSettings(BaseModel):
    dark_mode: Optional[bool] = None
    language: Optional[str] = None
    auto_save: Optional[bool] = None
    data_sync: Optional[bool] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    sound_enabled: Optional[bool] = None
    public_profile: Optional[bool] = None
    analytics_enabled: Optional[bool] = None


_DEFAULT_SETTINGS = {
    "dark_mode": False,
    "language": "ko",
    "auto_save": True,
    "data_sync": True,
    "email_notifications": True,
    "push_notifications": True,
    "sound_enabled": False,
    "public_profile": False,
    "analytics_enabled": True,
}


@router.get("")
async def get_settings(current_user: User = Depends(get_current_user)):
    """사용자 설정 조회"""
    user_id = current_user.id

    try:
        with get_db_connection() as conn:

            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT settings FROM user_settings WHERE user_id = %s
            """, (user_id,))

            row = cur.fetchone()
            if row and row['settings']:
                return row['settings']

            return _DEFAULT_SETTINGS.copy()

    except Exception as e:
        logger.error(f"설정 조회 에러: {e}")
        return _DEFAULT_SETTINGS.copy()


@router.put("")
async def update_settings(settings: UserSettings, current_user: User = Depends(get_current_user)):
    """사용자 설정 업데이트"""
    user_id = current_user.id

    try:
        with get_db_connection() as conn:

            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT settings FROM user_settings WHERE user_id = %s
            """, (user_id,))

            row = cur.fetchone()
            current_settings = dict(row['settings']) if row and row['settings'] else _DEFAULT_SETTINGS.copy()

            # 변경된 필드만 덮어씀 (exclude_unset=True 로 미전송 필드 무시)
            for field, value in settings.dict(exclude_unset=True).items():
                if value is not None:
                    current_settings[field] = value

            settings_json = json.dumps(current_settings)

            if row:
                cur.execute("""
                    UPDATE user_settings
                    SET settings = %s::jsonb, updated_at = NOW()
                    WHERE user_id = %s
                """, (settings_json, user_id))
            else:
                cur.execute("""
                    INSERT INTO user_settings (user_id, settings, created_at, updated_at)
                    VALUES (%s, %s::jsonb, NOW(), NOW())
                """, (user_id, settings_json))

            conn.commit()

            return {"success": True, "settings": current_settings}

    except Exception as e:
        logger.error(f"설정 업데이트 에러: {e}")
        raise HTTPException(status_code=500, detail="설정 저장에 실패했습니다")


@router.get("/export")
async def export_data(current_user: User = Depends(get_current_user)):
    """사용자 데이터 내보내기"""
    user_id = current_user.id

    try:
        with get_db_connection() as conn:

            cur = conn.cursor(cursor_factory=RealDictCursor)

            data: dict = {
                "exported_at": datetime.now().isoformat(),
                "user_id": str(user_id),
            }

            # 북마크
            cur.execute("""
                SELECT bid_notice_no, note, created_at
                FROM user_bookmarks WHERE user_id = %s
            """, (user_id,))
            bookmarks = cur.fetchall()
            data["bookmarks"] = [
                {
                    "bid_notice_no": b['bid_notice_no'],
                    "note": b.get('note', ''),
                    "created_at": b['created_at'].isoformat() if b.get('created_at') else None,
                }
                for b in bookmarks
            ]

            # 알림 규칙
            cur.execute("""
                SELECT rule_name, conditions, is_active, created_at
                FROM alert_rules WHERE user_id = %s
            """, (user_id,))
            rules = cur.fetchall()
            data["notification_rules"] = [
                {
                    "rule_name": r['rule_name'],
                    "conditions": r['conditions'],
                    "is_active": r['is_active'],
                    "created_at": r['created_at'].isoformat() if r.get('created_at') else None,
                }
                for r in rules
            ]

            # 설정
            cur.execute("""
                SELECT settings FROM user_settings WHERE user_id = %s
            """, (user_id,))
            settings_row = cur.fetchone()
            data["settings"] = (
                dict(settings_row['settings'])
                if settings_row and settings_row.get('settings')
                else _DEFAULT_SETTINGS.copy()
            )

            filename = f"odin_export_{datetime.now().strftime('%Y%m%d')}.json"
            return JSONResponse(
                content=data,
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

    except Exception as e:
        logger.error(f"데이터 내보내기 에러: {e}")
        raise HTTPException(status_code=500, detail="데이터 내보내기에 실패했습니다")


@router.delete("/account")
async def delete_account(current_user: User = Depends(get_current_user)):
    """계정 삭제 (소프트 삭제 - 30일 유예)"""
    user_id = current_user.id

    try:
        with get_db_connection() as conn:
            cur = conn.cursor()

            cur.execute("""
                UPDATE users
                SET is_active = false, updated_at = NOW()
                WHERE id = %s
            """, (user_id,))

            conn.commit()

            return {
                "success": True,
                "message": "계정 삭제가 예약되었습니다. 30일 후 완전히 삭제됩니다.",
            }

    except Exception as e:
        logger.error(f"계정 삭제 에러: {e}")
        raise HTTPException(status_code=500, detail="계정 삭제에 실패했습니다")
