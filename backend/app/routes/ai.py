from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from app.database.session import get_db
from app.core.security import role
from app.models import Job
from app.services.job_matcher import recommend, match_data, available_jobs

router = APIRouter(prefix="/ai", tags=["AI matching"])


@router.get("/recommendations")
@router.post("/recommendations/refresh")
def recommendations(
    request: Request, user=Depends(role("candidate")), db=Depends(get_db)
):
    return recommend(db, user.candidate, refresh=request.method == "POST")


@router.post("/skill-gap/{job_id}")
def gap(job_id: int, user=Depends(role("candidate")), db=Depends(get_db)):
    job = db.scalar(select(Job).where(Job.job_id == job_id, *available_jobs()))
    if not job:
        raise HTTPException(404, "Available job not found")
    return match_data(user.candidate, job)
