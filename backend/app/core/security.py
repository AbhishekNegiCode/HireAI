from datetime import datetime, timedelta, timezone
import secrets
import jwt
from pwdlib import PasswordHash
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database.session import get_db
from app.models import User, AuthSession

passwords = PasswordHash.recommended()
DUMMY_HASH = passwords.hash("dummy-password-for-timing")


def current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("hireai_session")
    try:
        payload = jwt.decode(token or "", settings().secret_key, algorithms=["HS256"])
        session = db.get(AuthSession, payload["sid"])
        if not session or session.expires_at.replace(
            tzinfo=timezone.utc
        ) <= datetime.now(timezone.utc):
            raise ValueError()
        user = db.get(User, int(payload["sub"]))
        if not user or not user.is_active or session.user_id != user.user_id:
            raise ValueError()
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(401, "Please sign in again")
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        if not secrets.compare_digest(
            request.headers.get("X-CSRF-Token", ""), session.csrf
        ):
            raise HTTPException(403, "Invalid CSRF token")
    db.execute(
        text("SELECT set_config('app.user_id', :uid, true)"), {"uid": str(user.user_id)}
    )
    return user


def role(*allowed):
    def dependency(user: User = Depends(current_user)):
        if user.role not in allowed:
            raise HTTPException(403, "This action is not available for your role")
        return user

    return dependency


def create_session(user, db, response):
    config = settings()
    sid, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(minutes=config.token_minutes)
    db.add(
        AuthSession(
            session_id=sid,
            user_id=user.user_id,
            csrf=csrf,
            expires_at=expires.replace(tzinfo=None),
        )
    )
    token = jwt.encode(
        {"sub": str(user.user_id), "sid": sid, "exp": expires},
        config.secret_key,
        algorithm="HS256",
    )
    response.set_cookie(
        "hireai_session",
        token,
        httponly=True,
        secure=config.cookie_secure,
        samesite="lax",
        max_age=config.token_minutes * 60,
        path="/",
    )
    return {"user": user_data(user), "csrf_token": csrf}


def user_data(user):
    return {
        k: getattr(user, k)
        for k in ("user_id", "full_name", "email", "role", "is_active")
    }
