from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from app.database.session import get_db
from app.core.security import role, current_user
from app.models import Application, Resume, Job
from app.schemas import ApplicationInput
from app.services.common import application_data, own_job, invalidate
from app.services.job_matcher import available_jobs

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("", status_code=201)
def apply(data: ApplicationInput, user=Depends(role("candidate")), db=Depends(get_db)):
    # Lock the job so a concurrent closing update cannot race application submission.
    job = db.scalar(
        select(Job)
        .where(Job.job_id == data.job_id, *available_jobs())
        .with_for_update()
    )
    if not job:
        raise HTTPException(409, "This job is no longer accepting applications")
    cid = user.candidate.candidate_id
    if db.scalar(
        select(Application).where(
            Application.candidate_id == cid, Application.job_id == data.job_id
        )
    ):
        raise HTTPException(409, "You have already applied to this job")
    resume = db.scalar(
        select(Resume)
        .where(Resume.candidate_id == cid, Resume.is_active)
        .with_for_update()
    )
    if not resume:
        raise HTTPException(422, "Upload a resume before applying")
    row = Application(
        candidate_id=cid,
        job_id=data.job_id,
        resume_id=resume.resume_id,
        cover_letter=data.cover_letter,
    )
    db.add(row)
    db.flush()  # The database trigger inserts history in this same transaction.
    invalidate(db, cid)
    return application_data(row)


@router.get("/me")
def mine(
    page: int = Query(1, ge=1), user=Depends(role("candidate")), db=Depends(get_db)
):
    return [
        application_data(a)
        for a in db.scalars(
            select(Application)
            .where(Application.candidate_id == user.candidate.candidate_id)
            .order_by(Application.applied_at.desc())
            .offset((page - 1) * 50)
            .limit(50)
        )
    ]


def authorized_application(db, aid, user):
    row = db.get(Application, aid)
    if not row:
        raise HTTPException(404, "Application not found")
    if user.role == "candidate":
        if row.candidate_id != user.candidate.candidate_id:
            raise HTTPException(403, "This application is private")
    else:
        own_job(db, row.job_id, user)
    return row


@router.get("/{application_id}")
def detail(application_id: int, user=Depends(current_user), db=Depends(get_db)):
    return application_data(
        authorized_application(db, application_id, user), user.role != "candidate"
    )


@router.patch("/{application_id}/withdraw")
def withdraw(application_id: int, user=Depends(role("candidate")), db=Depends(get_db)):
    row = authorized_application(db, application_id, user)
    db.refresh(row, with_for_update=True)
    if row.status in ("Withdrawn", "Selected", "Rejected"):
        raise HTTPException(409, "This application is already final")
    row.status = "Withdrawn"
    db.flush()
    db.expire(row, ["history"])
    return application_data(row)
