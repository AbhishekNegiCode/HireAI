from datetime import date
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy import select, func, or_, exists, delete, case
from app.database.session import get_db
from app.core.security import current_user, role
from app.models import Job, Company, JobSkill, Skill, Application, JobEmbedding, Report
from app.schemas import JobInput, ReportInput
from app.services.common import job_data, own_job, skill_id, invalidate
from app.services.job_matcher import available_jobs
from app.services.embedding_service import embed_job

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("")
def search(
    q: str = "",
    company: str = "",
    location: str = "",
    work_mode: str = "",
    employment_type: str = "",
    skill: str = "",
    experience: float | None = Query(None, ge=0),
    salary: int | None = Query(None, ge=0),
    sort: str = "newest",
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    user=Depends(current_user),
    db=Depends(get_db),
):
    stmt = select(Job).join(Company).where(*available_jobs())
    if q:
        stmt = stmt.where(
            or_(Job.title.ilike(f"%{q}%"), Company.company_name.ilike(f"%{q}%"))
        )
    for column, value in [(Company.company_name, company), (Job.location, location)]:
        if value:
            stmt = stmt.where(column.ilike(f"%{value}%"))
    if work_mode:
        stmt = stmt.where(Job.work_mode == work_mode)
    if employment_type:
        stmt = stmt.where(Job.employment_type == employment_type)
    if experience is not None:
        stmt = stmt.where(Job.experience_min <= experience)
    if salary is not None:
        stmt = stmt.where(Job.salary_max >= salary)
    if skill:
        stmt = stmt.where(
            exists().where(
                JobSkill.job_id == Job.job_id,
                JobSkill.skill_id == Skill.skill_id,
                Skill.normalized_skill_name.ilike(f"%{skill.casefold()}%"),
            )
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    if sort == "relevance" and q:
        stmt = stmt.order_by(
            case(
                (func.lower(Job.title) == q.lower(), 0),
                (Job.title.ilike(f"{q}%"), 1),
                else_=2,
            ),
            Job.posted_at.desc(),
        )
    else:
        stmt = stmt.order_by(Job.posted_at.desc(), Job.job_id.desc())
    return {
        "items": [
            job_data(j)
            for j in db.scalars(stmt.offset((page - 1) * page_size).limit(page_size))
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def set_skills(db, job, data):
    job.skills.clear()
    db.flush()
    seen = set()
    entries = list(data.skills)
    # Extract exact known skill mentions from the description when no list is supplied.
    if not entries:
        import re
        from app.schemas import JobSkillInput

        content = f"{data.title} {data.description} {data.responsibilities}".casefold()
        entries = [
            JobSkillInput(name=s.skill_name)
            for s in db.scalars(select(Skill))
            if re.search(
                r"(?<!\w)" + re.escape(s.normalized_skill_name) + r"(?!\w)", content
            )
        ]
    for item in entries:
        sid = skill_id(db, item.name)
        if sid not in seen:
            job.skills.append(
                JobSkill(
                    skill_id=sid,
                    importance=item.importance,
                    is_required=item.is_required,
                )
            )
            seen.add(sid)


@router.post("", status_code=201)
def create(
    data: JobInput,
    tasks: BackgroundTasks,
    user=Depends(role("recruiter")),
    db=Depends(get_db),
):
    if not user.recruiter.company_id:
        raise HTTPException(422, "Create your company profile before posting a job")
    job = Job(
        **data.model_dump(exclude={"skills"}),
        recruiter_id=user.recruiter.recruiter_id,
        company_id=user.recruiter.company_id,
    )
    db.add(job)
    db.flush()
    set_skills(db, job, data)
    invalidate(db)
    db.commit()
    tasks.add_task(embed_job, job.job_id)
    return job_data(job)


@router.get("/{job_id}")
def detail(job_id: int, user=Depends(current_user), db=Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status == "draft":
        own_job(db, job_id, user)
    return job_data(job)


@router.put("/{job_id}")
def update(
    job_id: int,
    data: JobInput,
    tasks: BackgroundTasks,
    user=Depends(role("recruiter", "admin")),
    db=Depends(get_db),
):
    job = own_job(db, job_id, user)
    for key, value in data.model_dump(exclude={"skills"}).items():
        setattr(job, key, value)
    set_skills(db, job, data)
    db.execute(delete(JobEmbedding).where(JobEmbedding.job_id == job_id))
    job.embedding_status = "pending"
    invalidate(db)
    db.commit()
    tasks.add_task(embed_job, job_id)
    return job_data(job)


@router.delete("/{job_id}")
def remove(job_id: int, user=Depends(role("recruiter", "admin")), db=Depends(get_db)):
    job = own_job(db, job_id, user)
    if db.scalar(
        select(Application.application_id).where(Application.job_id == job_id).limit(1)
    ):
        raise HTTPException(
            409, "This job has applications. Close it to preserve application records."
        )
    db.delete(job)
    invalidate(db)
    return {"message": "Job deleted"}


@router.post("/{job_id}/report", status_code=201)
def report(
    job_id: int, data: ReportInput, user=Depends(current_user), db=Depends(get_db)
):
    if not db.get(Job, job_id):
        raise HTTPException(404, "Job not found")
    db.add(Report(user_id=user.user_id, job_id=job_id, reason=data.reason))
    return {"message": "Report submitted for review"}
