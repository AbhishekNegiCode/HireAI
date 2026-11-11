from datetime import date, timedelta
from sqlalchemy import select, func, case, exists
from app.models import (
    Job,
    JobSkill,
    Candidate,
    CandidateSkill,
    Application,
    Resume,
    ResumeEmbedding,
    JobEmbedding,
    Recommendation,
)
from app.core.config import settings
from app.services.common import invalidate, job_data


def available_jobs():
    return (
        Job.status == "active",
        (
            Job.application_deadline.is_(None)
            | (Job.application_deadline >= date.today())
        ),
    )


def weighted_score(skill, semantic, experience, location):
    config = settings()
    pairs = [
        (skill, config.skill_weight),
        (semantic, config.semantic_weight),
        (experience, config.experience_weight),
        (location, config.location_weight),
    ]
    available = [(value, weight) for value, weight in pairs if value is not None]
    total = sum(weight for _, weight in available)
    return (
        round(sum(value * weight for value, weight in available) / total, 1)
        if total
        else 0
    )


def match_data(candidate, job, semantic=None, sql_skill_score=None):
    names = {s.skill.normalized_skill_name for s in candidate.skills}
    required = [s for s in job.skills if s.is_required]
    matching = [
        s.skill.skill_name for s in job.skills if s.skill.normalized_skill_name in names
    ]
    missing = [
        {
            "name": s.skill.skill_name,
            "importance": s.importance,
            "required": s.is_required,
            "reason": f'This is a {"required" if s.is_required else "optional"} skill in the employer’s posting.',
            "roadmap": f"Learn the fundamentals of {s.skill.skill_name}, build a small project, then document it in your portfolio.",
        }
        for s in job.skills
        if s.skill.normalized_skill_name not in names
    ]
    # Optional skills are shown separately; they never count as mandatory skill matches.
    skill = (
        sql_skill_score
        if sql_skill_score is not None
        else (
            100
            * sum(s.skill.normalized_skill_name in names for s in required)
            / len(required)
            if required
            else 100
        )
    )
    exp = (
        100
        if candidate.total_experience >= job.experience_min
        else 100 * candidate.total_experience / max(job.experience_min, 1)
    )
    loc = (
        100
        if job.work_mode == "Remote"
        or candidate.location.casefold() == job.location.casefold()
        else 0
    )
    return {
        "skill_match_score": round(skill, 1),
        "semantic_match_score": round(semantic, 1) if semantic is not None else None,
        "experience_score": round(exp, 1),
        "location_score": loc,
        "overall_score": weighted_score(skill, semantic, exp, loc),
        "explanation": {
            "matching_skills": matching,
            "missing_skills": sorted(
                missing, key=lambda x: (not x["required"], -x["importance"])
            ),
            "text": f"Matches {sum(s.skill.normalized_skill_name in names for s in required)} of {len(required)} required skills. "
            + (
                "Meets the minimum experience requirement."
                if exp == 100
                else "Experience is below the stated minimum."
            ),
            "semantic_available": semantic is not None,
            "scoring_note": "Compatibility heuristic, not a hiring probability. If semantic matching is unavailable, other weights are renormalized.",
        },
    }


def recommend(db, candidate, refresh=False):
    # Serialize concurrent refreshes for this candidate to preserve the unique cache key.
    db.scalar(
        select(Candidate)
        .where(Candidate.candidate_id == candidate.candidate_id)
        .with_for_update()
    )
    if not refresh:
        cached = db.execute(
            select(Recommendation, Job)
            .join(Job)
            .where(
                Recommendation.candidate_id == candidate.candidate_id,
                Recommendation.generated_at >= func.now() - timedelta(minutes=5),
                *available_jobs(),
                ~exists().where(
                    Application.job_id == Job.job_id,
                    Application.candidate_id == candidate.candidate_id,
                ),
            )
            .order_by(Recommendation.overall_score.desc())
        ).all()
        if cached:
            return [
                {
                    "job": job_data(job),
                    **{
                        key: getattr(row, key)
                        for key in (
                            "skill_match_score",
                            "semantic_match_score",
                            "experience_score",
                            "location_score",
                            "overall_score",
                            "explanation",
                        )
                    },
                }
                for row, job in cached
            ]
    # Required skill numerator/denominator are aggregated in SQL, not inferred by the LLM.
    aggregate = (
        select(
            JobSkill.job_id,
            func.count().filter(JobSkill.is_required).label("required"),
            func.count()
            .filter(JobSkill.is_required & CandidateSkill.skill_id.is_not(None))
            .label("matched"),
        )
        .outerjoin(
            CandidateSkill,
            (CandidateSkill.skill_id == JobSkill.skill_id)
            & (CandidateSkill.candidate_id == candidate.candidate_id),
        )
        .group_by(JobSkill.job_id)
    )
    scores = {
        row.job_id: 100 * row.matched / row.required if row.required else 100
        for row in db.execute(aggregate)
    }
    resume_vector = db.scalar(
        select(ResumeEmbedding)
        .join(Resume)
        .where(
            Resume.candidate_id == candidate.candidate_id,
            Resume.is_active,
            ResumeEmbedding.model_name == settings().embedding_model,
        )
    )
    semantics = {}
    if resume_vector:
        distance = JobEmbedding.embedding.cosine_distance(resume_vector.embedding)
        rows = db.execute(
            select(JobEmbedding.job_id, distance.label("distance"))
            .join(Job)
            .where(
                *available_jobs(), JobEmbedding.model_name == resume_vector.model_name
            )
            .order_by(distance)
        )
        semantics = {r.job_id: max(0, min(100, (1 - r.distance) * 100)) for r in rows}
    jobs = db.scalars(
        select(Job).where(
            *available_jobs(),
            ~exists().where(
                Application.job_id == Job.job_id,
                Application.candidate_id == candidate.candidate_id,
            ),
        )
    ).all()
    invalidate(db, candidate.candidate_id)
    result = []
    for job in jobs:
        data = match_data(
            candidate, job, semantics.get(job.job_id), scores.get(job.job_id, 100)
        )
        db.add(
            Recommendation(
                candidate_id=candidate.candidate_id, job_id=job.job_id, **data
            )
        )
        result.append({"job": job_data(job), **data})
    return sorted(result, key=lambda row: row["overall_score"], reverse=True)
