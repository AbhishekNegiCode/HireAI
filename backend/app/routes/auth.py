from collections import defaultdict, deque
from time import monotonic
import jwt
from fastapi import APIRouter, Depends, Response, Request, HTTPException
from sqlalchemy import select, delete
from app.database.session import get_db
from app.models import User, Candidate, Recruiter, AuthSession
from app.schemas import Register, Login
from app.core.security import (
    passwords,
    DUMMY_HASH,
    create_session,
    current_user,
    user_data,
)
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
attempts = defaultdict(deque)


def limit(request):
    key = request.client.host if request.client else "unknown"
    now = monotonic()
    queue = attempts[key]
    while queue and queue[0] < now - 60:
        queue.popleft()
    if len(queue) >= 20:
        raise HTTPException(429, "Too many attempts. Try again in a minute.")
    queue.append(now)


@router.post("/register", status_code=201)
def register(data: Register, request: Request, response: Response, db=Depends(get_db)):
    limit(request)
    email = str(data.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Email is already registered")
    user = User(
        full_name=data.full_name,
        email=email,
        password_hash=passwords.hash(data.password),
        role=data.role,
    )
    db.add(user)
    db.flush()
    db.add(
        Candidate(user_id=user.user_id)
        if data.role == "candidate"
        else Recruiter(user_id=user.user_id)
    )
    return create_session(user, db, response)


@router.post("/login")
def login(data: Login, request: Request, response: Response, db=Depends(get_db)):
    limit(request)
    user = db.scalar(select(User).where(User.email == str(data.email).lower()))
    valid = passwords.verify(data.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid or not user.is_active:
        raise HTTPException(401, "Invalid email or password")
    return create_session(user, db, response)


@router.get("/me")
def me(request: Request, user=Depends(current_user), db=Depends(get_db)):
    payload = jwt.decode(
        request.cookies["hireai_session"], settings().secret_key, algorithms=["HS256"]
    )
    return {
        "user": user_data(user),
        "csrf_token": db.get(AuthSession, payload["sid"]).csrf,
    }


@router.post("/logout")
def logout(
    request: Request, response: Response, user=Depends(current_user), db=Depends(get_db)
):
    payload = jwt.decode(
        request.cookies["hireai_session"], settings().secret_key, algorithms=["HS256"]
    )
    db.execute(delete(AuthSession).where(AuthSession.session_id == payload["sid"]))
    response.delete_cookie("hireai_session", path="/")
    return {"message": "Signed out"}
