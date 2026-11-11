from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, delete
from app.core.security import role
from app.database.session import get_db
from app.models import (
    CandidateSkill,
    Education,
    Experience,
    Application,
    SavedJob,
    Resume,
    Job,
    ResumeEmbedding,
)
from app.schemas import ProfileInput, SkillInput
from app.services.common import profile_data, skill_id, invalidate, job_data
from app.services.job_matcher import available_jobs

router = APIRouter(prefix="/candidates", tags=["Candidates"])
candidate_user = role("candidate")


@router.get("/me")
def profile(user=Depends(candidate_user)):
    return profile_data(user.candidate)


@router.put("/me")
def update_profile(
    data: ProfileInput, user=Depends(candidate_user), db=Depends(get_db)
):
    candidate = user.candidate
    values = data.model_dump(exclude={"full_name", "education", "experience"})
    for key, value in values.items():
        setattr(candidate, key, value)
    user.full_name = data.full_name
    candidate.education = [Education(**row.model_dump()) for row in data.education]
    candidate.experience = [Experience(**row.model_dump()) for row in data.experience]
    invalidate(db, candidate.candidate_id)
    db.flush()
    return profile_data(candidate)


@router.get("/me/skills")
def skills(user=Depends(candidate_user)):
    return profile_data(user.candidate)["skills"]


@router.put("/me/skills")
def update_skills(
    data: list[SkillInput], user=Depends(candidate_user), db=Depends(get_db)
):
    if len(data) > 100:
        raise HTTPException(422, "Maximum 100 skills")
    candidate = user.candidate
    candidate.skills.clear()
    db.flush()
    seen = set()
    for item in data:
        sid = skill_id(db, item.name)
        if sid not in seen:
            candidate.skills.append(
                CandidateSkill(skill_id=sid, **item.model_dump(exclude={"name"}))
            )
            seen.add(sid)
    db.flush()
    invalidate(db, candidate.candidate_id)
    return profile_data(candidate)["skills"]


@router.get("/dashboard")
def dashboard(user=Depends(candidate_user), db=Depends(get_db)):
    cid = user.candidate.candidate_id
    counts = dict(
        db.execute(
            select(Application.status, func.count())
            .where(Application.candidate_id == cid)
            .group_by(Application.status)
        ).all()
    )
    resume = db.scalar(
        select(Resume).where(Resume.candidate_id == cid, Resume.is_active)
    )
    fields = [
        user.candidate.headline,
        user.candidate.location,
        user.candidate.professional_summary,
        user.candidate.skills,
        user.candidate.education,
        user.candidate.experience,
        resume,
    ]
    return {
        "total_applications": sum(counts.values()),
        "shortlisted": counts.get("Shortlisted", 0),
        "saved_jobs": db.scalar(
            select(func.count())
            .select_from(SavedJob)
            .where(SavedJob.candidate_id == cid)
        ),
        "profile_completion": round(100 * sum(bool(f) for f in fields) / len(fields)),
        "resume_status": resume.analysis_status if resume else "not_uploaded",
        "status_counts": counts,
        "recent_jobs": [
            job_data(j)
            for j in db.scalars(
                select(Job)
                .where(*available_jobs())
                .order_by(Job.posted_at.desc())
                .limit(4)
            )
        ],
    }


@router.get("/saved-jobs")
def saved(user=Depends(candidate_user), db=Depends(get_db)):
    return [
        job_data(s.job)
        for s in db.scalars(
            select(SavedJob)
            .where(SavedJob.candidate_id == user.candidate.candidate_id)
            .order_by(SavedJob.saved_at.desc())
        )
    ]


@router.post("/saved-jobs/{job_id}", status_code=201)
def save(job_id: int, user=Depends(candidate_user), db=Depends(get_db)):
    job = db.scalar(select(Job).where(Job.job_id == job_id, *available_jobs()))
    if not job:
        raise HTTPException(404, "Available job not found")
    row = db.scalar(
        select(SavedJob).where(
            SavedJob.candidate_id == user.candidate.candidate_id,
            SavedJob.job_id == job_id,
        )
    )
    if not row:
        db.add(SavedJob(candidate_id=user.candidate.candidate_id, job_id=job_id))
    return {"message": "Job saved"}


@router.delete("/saved-jobs/{job_id}")
def unsave(job_id: int, user=Depends(candidate_user), db=Depends(get_db)):
    db.execute(
        delete(SavedJob).where(
            SavedJob.candidate_id == user.candidate.candidate_id,
            SavedJob.job_id == job_id,
        )
    )
    return {"message": "Job removed from saved jobs"}
