from functools import lru_cache
import logging
from sqlalchemy import select
from app.core.config import settings
from app.database.session import SessionLocal
from app.models import Job, JobEmbedding
from app.services.common import invalidate

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(
        settings().embedding_model, cache_folder=settings().embedding_cache_dir
    )


def embed(text):
    if not settings().embeddings_enabled:
        raise RuntimeError(
            "Semantic matching is disabled. Set EMBEDDINGS_ENABLED=true."
        )
    import numpy as np

    # Pool short overlapping chunks so a long resume is not silently truncated.
    words = text.split()
    chunks = [" ".join(words[i : i + 250]) for i in range(0, max(len(words), 1), 220)]
    vectors = model().encode(chunks, normalize_embeddings=True)
    pooled = np.mean(vectors, axis=0)
    vector = (pooled / max(float(np.linalg.norm(pooled)), 1e-12)).tolist()
    if len(vector) != 384:
        raise RuntimeError("Embedding model must produce 384 dimensions")
    return vector


def embed_job(job_id):
    with SessionLocal() as db:
        job = db.get(Job, job_id)
        if not job:
            return
        try:
            vector = embed(f"{job.title}\n{job.description}\n{job.responsibilities}")
            row = db.scalar(select(JobEmbedding).where(JobEmbedding.job_id == job_id))
            if row is None:
                row = JobEmbedding(job_id=job_id)
                db.add(row)
            row.embedding, row.model_name = vector, settings().embedding_model
            job.embedding_status = "ready"
            invalidate(db)
        except Exception as exc:
            logger.warning(
                "Job embedding unavailable for %s (%s)", job_id, type(exc).__name__
            )
            job.embedding_status = "unavailable"
        db.commit()
