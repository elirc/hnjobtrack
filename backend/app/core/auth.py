from fastapi import Depends, HTTPException, Header
from app.core.supabase import get_supabase_admin
from app.core.config import settings


async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.split(" ", 1)[1]
    sb = get_supabase_admin()

    try:
        user_response = sb.auth.get_user(token)
        return user_response.user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def get_optional_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    sb = get_supabase_admin()
    try:
        user_response = sb.auth.get_user(token)
        return user_response.user
    except Exception:
        return None


async def require_admin(x_api_key: str = Header(None)):
    if not x_api_key or x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Admin access required")
    return True
