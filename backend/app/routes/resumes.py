from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy import select, update, delete
from app.database.session import get_db
from app.core.config import settings
from app.core.security import role, current_user
from app.models import (
    Resume,
    ResumeAnalysis,
    ResumeEmbedding,
    Application,
    Candidate,
    CandidateSkill,
)
from app.schemas import ResumeOutput
from app.services.resume_parser import extract, MAX_BYTES
from app.services.resume_analyzer import analyze_resume
from app.services.common import columns, invalidate, own_job, skill_id

router = APIRouter(prefix="/resumes", tags=["Resumes"])
candidate_user = role("candidate")


def active_resume(db, cid):
    return db.scalar(select(Resume).where(Resume.candidate_id == cid, Resume.is_active))


def public_resume(row):
    return columns(row, ("storage_path", "extracted_text"))


@router.post("/upload", status_code=201)
def upload(
    tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user=Depends(candidate_user),
    db=Depends(get_db),
):
    data = file.file.read(MAX_BYTES + 1)
    filename = Path(file.filename or "resume").name[:255]
    try:
        text = extract(data, filename)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    cid = user.candidate.candidate_id
    db.scalar(select(Candidate).where(Candidate.candidate_id == cid).with_for_update())
    db.execute(
        update(Resume)
        .where(Resume.candidate_id == cid, Resume.is_active)
        .values(is_active=False)
    )
    directory = Path(settings().storage_dir).resolve()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = directory / f'{uuid4().hex}.{filename.rsplit(".",1)[-1].lower()}'
    path.write_bytes(data)
    path.chmod(0o600)
    row = Resume(
        candidate_id=cid,
        original_filename=filename,
        storage_path=str(path),
        extracted_text=text,
    )
    try:
        db.add(row)
        invalidate(db, cid)
        db.commit()
    except Exception:
        path.unlink(missing_ok=True)
        raise
    tasks.add_task(analyze_resume, row.resume_id)
    return public_resume(row)


@router.get("/me")
def mine(user=Depends(candidate_user), db=Depends(get_db)):
    row = active_resume(db, user.candidate.candidate_id)
    return public_resume(row) if row else None


@router.get("/me/analysis")
def analysis(user=Depends(candidate_user), db=Depends(get_db)):
    row = active_resume(db, user.candidate.candidate_id)
    if not row:
        return {"status": "not_uploaded", "analysis": None}
    analysis = db.scalar(
        select(ResumeAnalysis).where(ResumeAnalysis.resume_id == row.resume_id)
    )
    vector = db.scalar(
        select(ResumeEmbedding.embedding_id).where(
            ResumeEmbedding.resume_id == row.resume_id
        )
    )
    return {
        "status": row.analysis_status,
        "message": row.analysis_error,
        "analysis": analysis.analysis_json if analysis else None,
        "semantic_available": bool(vector),
    }


@router.post("/me/analyze")
def retry(tasks: BackgroundTasks, user=Depends(candidate_user), db=Depends(get_db)):
    row = active_resume(db, user.candidate.candidate_id)
    if not row:
        raise HTTPException(404, "Upload a resume first")
    row.analysis_status = "pending"
    db.commit()
    tasks.add_task(analyze_resume, row.resume_id)
    return {"message": "Analysis started"}


@router.put("/me/analysis")
def correct(data: ResumeOutput, user=Depends(candidate_user), db=Depends(get_db)):
    row = active_resume(db, user.candidate.candidate_id)
    if not row:
        raise HTTPException(404, "Upload a resume first")
    analysis = db.scalar(
        select(ResumeAnalysis).where(ResumeAnalysis.resume_id == row.resume_id)
    )
    if not analysis:
        analysis = ResumeAnalysis(resume_id=row.resume_id)
        db.add(analysis)
    analysis.analysis_json = data.model_dump(mode="json")
    analysis.education = [e.model_dump(mode="json") for e in data.education]
    analysis.experience_years = data.total_experience
    analysis.professional_summary = data.professional_summary
    analysis.extracted_projects = data.projects
    analysis.suggested_roles = data.suggested_roles
    row.analysis_status = "ready"
    row.analysis_error = ""
    invalidate(db, user.candidate.candidate_id)
    return {"message": "Analysis corrections saved"}


@router.post("/me/analysis/import")
def import_skills(user=Depends(candidate_user), db=Depends(get_db)):
    row = active_resume(db, user.candidate.candidate_id)
    analysis = (
        db.scalar(
            select(ResumeAnalysis).where(ResumeAnalysis.resume_id == row.resume_id)
        )
        if row
        else None
    )
    if not analysis:
        raise HTTPException(422, "No analysis available to import")
    existing = {s.skill_id for s in user.candidate.skills}
    output = ResumeOutput.model_validate(analysis.analysis_json)
    for name in output.technical_skills + output.soft_skills:
        sid = skill_id(db, name)
        if sid not in existing:
            user.candidate.skills.append(CandidateSkill(skill_id=sid))
            existing.add(sid)
    invalidate(db, user.candidate.candidate_id)
    return {
        "message": "Reviewed skills added to your profile; edit experience and education on the profile page."
    }


@router.delete("/me")
def remove(user=Depends(candidate_user), db=Depends(get_db)):
    row = active_resume(db, user.candidate.candidate_id)
    if not row:
        raise HTTPException(404, "No active resume")
    if db.scalar(
        select(Application.application_id)
        .where(Application.resume_id == row.resume_id)
        .limit(1)
    ):
        row.is_active = False
        message = "Resume removed from your profile. Submitted copies are retained with your applications."
    else:
        path = Path(row.storage_path)
        db.delete(row)
        db.flush()
        db.commit()
        path.unlink(missing_ok=True)
        message = "Resume deleted"
    invalidate(db, user.candidate.candidate_id)
    return {"message": message}


@router.get("/{resume_id}/download")
def download(resume_id: int, user=Depends(current_user), db=Depends(get_db)):
    row = db.get(Resume, resume_id)
    if not row:
        raise HTTPException(404, "Resume not found")
    if user.role == "candidate":
        if row.candidate_id != user.candidate.candidate_id:
            raise HTTPException(403, "This resume is private")
    elif user.role == "recruiter":
        apps = db.scalars(
            select(Application).where(Application.resume_id == resume_id)
        ).all()
        if not any(
            a.job.recruiter_id == user.recruiter.recruiter_id
            and a.job.company_id == user.recruiter.company_id
            for a in apps
        ):
            raise HTTPException(
                403, "Only resumes submitted to your jobs are available"
            )
    if not Path(row.storage_path).is_file():
        raise HTTPException(404, "Resume file is unavailable")
    return FileResponse(
        row.storage_path,
        filename=row.original_filename,
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
