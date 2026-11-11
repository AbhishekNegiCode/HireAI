import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.core.config import settings
from app.database.session import engine
from app.routes import (
    auth,
    candidates,
    jobs,
    applications,
    recruiter,
    resumes,
    ai,
    admin,
)

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="HireAI API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings().frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    origin = request.headers.get("origin")
    if (
        request.method not in ("GET", "HEAD", "OPTIONS")
        and origin
        and origin != settings().frontend_origin
    ):
        return JSONResponse(
            status_code=403, content={"error": {"message": "Untrusted request origin"}}
        )
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(HTTPException)
async def http_error(request, exc):
    return JSONResponse(
        status_code=exc.status_code, content={"error": {"message": exc.detail}}
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    details = [
        {"field": ".".join(map(str, e["loc"])), "message": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"error": {"message": "Please check your input", "details": details}},
    )


@app.exception_handler(IntegrityError)
async def conflict(request, exc):
    logging.getLogger(__name__).warning(
        "Database constraint rejected request: %s", type(exc.orig).__name__
    )
    return JSONResponse(
        status_code=409,
        content={
            "error": {
                "message": "This conflicts with an existing record or a database constraint"
            }
        },
    )


@app.get("/api/health")
def health():
    with engine.connect() as db:
        db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "database": "connected",
        "ai_configured": bool(settings().groq_api_key),
        "embeddings_enabled": settings().embeddings_enabled,
    }


for router in (
    auth.router,
    candidates.router,
    jobs.router,
    applications.router,
    recruiter.router,
    resumes.router,
    ai.router,
    admin.router,
):
    app.include_router(router, prefix="/api")
