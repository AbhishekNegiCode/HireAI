from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert
from fastapi import HTTPException
from app.models import Skill, Recommendation, Job


def skill_id(db, name):
    name = " ".join(name.split())[:100]
    if not name:
        raise HTTPException(422, "Skill name cannot be blank")
    normalized = name.casefold()
    db.execute(
        insert(Skill)
        .values(skill_name=name, normalized_skill_name=normalized)
        .on_conflict_do_nothing(index_elements=["normalized_skill_name"])
    )
    return db.scalar(
        select(Skill.skill_id).where(Skill.normalized_skill_name == normalized)
    )


def invalidate(db, candidate_id=None):
    query = delete(Recommendation)
    if candidate_id is not None:
        query = query.where(Recommendation.candidate_id == candidate_id)
    db.execute(query)


def own_job(db, job_id, user):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if user.role != "admin" and (
        not user.recruiter
        or job.recruiter_id != user.recruiter.recruiter_id
        or job.company_id != user.recruiter.company_id
    ):
        raise HTTPException(403, "You do not own this job")
    return job


def columns(obj, exclude=()):
    return {
        column.name: getattr(obj, column.name)
        for column in obj.__table__.columns
        if column.name not in exclude
    }


def job_data(job):
    return {
        **columns(job),
        "company": columns(job.company),
        "skills": [
            {
                "name": s.skill.skill_name,
                "importance": s.importance,
                "is_required": s.is_required,
            }
            for s in job.skills
        ],
    }


def profile_data(candidate):
    return {
        **columns(candidate),
        "full_name": candidate.user.full_name,
        "email": candidate.user.email,
        "skills": [
            {
                "name": s.skill.skill_name,
                "proficiency_level": s.proficiency_level,
                "years_of_experience": s.years_of_experience,
            }
            for s in candidate.skills
        ],
        "education": [columns(e) for e in candidate.education],
        "experience": [columns(e) for e in candidate.experience],
    }


def application_data(app, include_candidate=False):
    result = {
        **columns(app),
        "job": job_data(app.job),
        "history": [columns(h) for h in app.history],
    }
    if include_candidate:
        result["candidate"] = profile_data(app.candidate)
    return result
