from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, delete
from app.database.session import get_db
from app.core.security import role, user_data
from app.models import User, Company, Job, Application, Report, AuthSession
from app.schemas import ActiveInput, ReportStatus, CompanyInput
from app.services.common import columns, job_data, application_data, invalidate

router = APIRouter(
    prefix="/admin", tags=["Administration"], dependencies=[Depends(role("admin"))]
)


@router.get("/dashboard")
def dashboard(db=Depends(get_db)):
    result = {
        name: db.scalar(select(func.count()).select_from(model))
        for name, model in [
            ("users", User),
            ("companies", Company),
            ("jobs", Job),
            ("applications", Application),
        ]
    }
    result.update(
        {
            r: c
            for r, c in db.execute(select(User.role, func.count()).group_by(User.role))
        }
    )
    result["active_jobs"] = db.scalar(
        select(func.count()).select_from(Job).where(Job.status == "active")
    )
    result["recent_registrations"] = [
        user_data(u)
        for u in db.scalars(select(User).order_by(User.created_at.desc()).limit(10))
    ]
    result["posting_analytics"] = [
        {"name": str(day), "jobs": count}
        for day, count in db.execute(
            select(func.date(Job.posted_at), func.count())
            .group_by(func.date(Job.posted_at))
            .order_by(func.date(Job.posted_at))
        )
    ]
    return result


@router.get("/users")
def users(page: int = Query(1, ge=1), q: str = "", db=Depends(get_db)):
    return [
        user_data(u)
        for u in db.scalars(
            select(User)
            .where(User.email.ilike(f"%{q}%"))
            .order_by(User.user_id)
            .offset((page - 1) * 50)
            .limit(50)
        )
    ]


@router.patch("/users/{user_id}/status")
def status(
    user_id: int, data: ActiveInput, admin=Depends(role("admin")), db=Depends(get_db)
):
    row = db.get(User, user_id)
    if not row:
        raise HTTPException(404, "User not found")
    if row.role == "admin":
        raise HTTPException(409, "Administrator accounts cannot be suspended here")
    row.is_active = data.is_active
    if not data.is_active:
        db.execute(delete(AuthSession).where(AuthSession.user_id == user_id))
    return user_data(row)


@router.get("/jobs")
def jobs(page: int = Query(1, ge=1), db=Depends(get_db)):
    return [
        job_data(j)
        for j in db.scalars(
            select(Job).order_by(Job.posted_at.desc()).offset((page - 1) * 50).limit(50)
        )
    ]


@router.get("/companies")
def companies(page: int = Query(1, ge=1), db=Depends(get_db)):
    return [
        columns(c)
        for c in db.scalars(
            select(Company)
            .order_by(Company.company_id)
            .offset((page - 1) * 50)
            .limit(50)
        )
    ]


@router.put("/companies/{company_id}")
def company(company_id: int, data: CompanyInput, db=Depends(get_db)):
    row = db.get(Company, company_id)
    if not row:
        raise HTTPException(404, "Company not found")
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    return columns(row)


@router.get("/applications")
def applications(page: int = Query(1, ge=1), db=Depends(get_db)):
    return [
        application_data(a, True)
        for a in db.scalars(
            select(Application)
            .order_by(Application.applied_at.desc())
            .offset((page - 1) * 50)
            .limit(50)
        )
    ]


@router.get("/reports")
def reports(page: int = Query(1, ge=1), db=Depends(get_db)):
    return [
        columns(r)
        for r in db.scalars(
            select(Report)
            .order_by(Report.created_at.desc())
            .offset((page - 1) * 50)
            .limit(50)
        )
    ]


@router.patch("/reports/{report_id}")
def resolve(report_id: int, data: ReportStatus, db=Depends(get_db)):
    row = db.get(Report, report_id)
    if not row:
        raise HTTPException(404, "Report not found")
    row.status = data.status
    return columns(row)
