from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, exists
from app.database.session import get_db
from app.core.security import role
from app.models import Job, Company, Application, CandidateSkill, Skill, Candidate
from app.schemas import CompanyInput, StatusInput
from app.services.common import columns, own_job, job_data, application_data

router = APIRouter(prefix="/recruiter", tags=["Recruiters"])
recruiter_user = role("recruiter")


@router.get("/company")
def company(user=Depends(recruiter_user)):
    return columns(user.recruiter.company) if user.recruiter.company else None


@router.put("/company")
def update_company(
    data: CompanyInput, user=Depends(recruiter_user), db=Depends(get_db)
):
    company = user.recruiter.company
    if not company:
        company = Company(**data.model_dump())
        db.add(company)
        db.flush()
        user.recruiter.company = company
    else:
        for key, value in data.model_dump().items():
            setattr(company, key, value)
    return columns(company)


@router.get("/jobs")
def jobs(user=Depends(recruiter_user), db=Depends(get_db)):
    return [
        job_data(j)
        for j in db.scalars(
            select(Job)
            .where(Job.recruiter_id == user.recruiter.recruiter_id)
            .order_by(Job.posted_at.desc())
        )
    ]


@router.get("/dashboard")
def dashboard(user=Depends(recruiter_user), db=Depends(get_db)):
    rid = user.recruiter.recruiter_id
    counts = dict(
        db.execute(
            select(Application.status, func.count())
            .join(Job)
            .where(Job.recruiter_id == rid)
            .group_by(Application.status)
        ).all()
    )
    per_job = db.execute(
        select(Job.title, func.count(Application.application_id))
        .outerjoin(Application)
        .where(Job.recruiter_id == rid)
        .group_by(Job.job_id)
    ).all()
    return {
        "active_jobs": db.scalar(
            select(func.count())
            .select_from(Job)
            .where(Job.recruiter_id == rid, Job.status == "active")
        ),
        "total_applications": sum(counts.values()),
        "shortlisted": counts.get("Shortlisted", 0),
        "interviews": counts.get("Interview Scheduled", 0),
        "job_statistics": [
            {"name": title, "applications": count} for title, count in per_job
        ],
        "recent_applications": [
            application_data(a, True)
            for a in db.scalars(
                select(Application)
                .join(Job)
                .where(Job.recruiter_id == rid)
                .order_by(Application.applied_at.desc())
                .limit(8)
            )
        ],
    }


@router.get("/jobs/{job_id}/applicants")
def applicants(
    job_id: int,
    skill: str = "",
    experience: float = Query(0, ge=0),
    page: int = Query(1, ge=1),
    user=Depends(recruiter_user),
    db=Depends(get_db),
):
    own_job(db, job_id, user)
    stmt = (
        select(Application)
        .join(Candidate)
        .where(Application.job_id == job_id, Candidate.total_experience >= experience)
    )
    if skill:
        stmt = stmt.where(
            exists().where(
                CandidateSkill.candidate_id == Candidate.candidate_id,
                CandidateSkill.skill_id == Skill.skill_id,
                Skill.normalized_skill_name.ilike(f"%{skill.casefold()}%"),
            )
        )
    return [
        application_data(a, True)
        for a in db.scalars(
            stmt.order_by(Application.applied_at.desc())
            .offset((page - 1) * 50)
            .limit(50)
        )
    ]


@router.patch("/applications/{application_id}/status")
def status(
    application_id: int,
    data: StatusInput,
    user=Depends(recruiter_user),
    db=Depends(get_db),
):
    row = db.scalar(
        select(Application)
        .where(Application.application_id == application_id)
        .with_for_update()
    )
    if not row:
        raise HTTPException(404, "Application not found")
    own_job(db, row.job_id, user)
    if row.status in ("Withdrawn", "Selected", "Rejected"):
        raise HTTPException(409, "Final applications cannot be changed")
    row.status = data.status
    db.flush()
    db.expire(row, ["history"])
    return application_data(row, True)
