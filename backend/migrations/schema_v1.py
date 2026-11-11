# Frozen initial schema. Do not edit; add a new migration instead.
from datetime import datetime, date
from sqlalchemy import (
    String,
    Text,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
    candidate: Mapped["Candidate | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    recruiter: Mapped["Recruiter | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    __table_args__ = (CheckConstraint("role IN ('candidate','recruiter','admin')"),)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), index=True
    )
    csrf: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime]


class Candidate(Base):
    __tablename__ = "candidate_profiles"
    candidate_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), unique=True
    )
    phone: Mapped[str] = mapped_column(String(40), default="")
    location: Mapped[str] = mapped_column(String(160), default="")
    headline: Mapped[str] = mapped_column(String(200), default="")
    professional_summary: Mapped[str] = mapped_column(Text, default="")
    total_experience: Mapped[float] = mapped_column(default=0)
    portfolio_url: Mapped[str] = mapped_column(String(500), default="")
    linkedin_url: Mapped[str] = mapped_column(String(500), default="")
    github_url: Mapped[str] = mapped_column(String(500), default="")
    user: Mapped[User] = relationship(back_populates="candidate")
    skills: Mapped[list["CandidateSkill"]] = relationship(cascade="all, delete-orphan")
    education: Mapped[list["Education"]] = relationship(cascade="all, delete-orphan")
    experience: Mapped[list["Experience"]] = relationship(cascade="all, delete-orphan")
    __table_args__ = (
        CheckConstraint("total_experience >= 0 AND total_experience <= 80"),
    )


class Education(Base):
    __tablename__ = "education"
    education_id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_profiles.candidate_id", ondelete="CASCADE"), index=True
    )
    institution: Mapped[str] = mapped_column(String(200))
    degree: Mapped[str] = mapped_column(String(200))
    start_year: Mapped[int]
    end_year: Mapped[int | None]
    __table_args__ = (CheckConstraint("end_year IS NULL OR end_year >= start_year"),)


class Experience(Base):
    __tablename__ = "experience"
    experience_id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_profiles.candidate_id", ondelete="CASCADE"), index=True
    )
    company: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    start_date: Mapped[date]
    end_date: Mapped[date | None]
    __table_args__ = (CheckConstraint("end_date IS NULL OR end_date >= start_date"),)


class Company(Base):
    __tablename__ = "companies"
    company_id: Mapped[int] = mapped_column(primary_key=True)
    company_name: Mapped[str] = mapped_column(String(160), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    website: Mapped[str] = mapped_column(String(500), default="")
    industry: Mapped[str] = mapped_column(String(100), default="")
    company_size: Mapped[str] = mapped_column(String(50), default="")
    location: Mapped[str] = mapped_column(String(160), default="")
    logo_url: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Recruiter(Base):
    __tablename__ = "recruiter_profiles"
    recruiter_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), unique=True
    )
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.company_id"), index=True
    )
    designation: Mapped[str] = mapped_column(String(120), default="Recruiter")
    user: Mapped[User] = relationship(back_populates="recruiter")
    company: Mapped[Company | None] = relationship()


class Job(Base):
    __tablename__ = "jobs"
    job_id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.company_id"), index=True
    )
    recruiter_id: Mapped[int] = mapped_column(
        ForeignKey("recruiter_profiles.recruiter_id"), index=True
    )
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(Text)
    responsibilities: Mapped[str] = mapped_column(Text, default="")
    employment_type: Mapped[str] = mapped_column(String(40), default="Full-time")
    experience_min: Mapped[float] = mapped_column(default=0)
    experience_max: Mapped[float] = mapped_column(default=10)
    salary_min: Mapped[int] = mapped_column(default=0)
    salary_max: Mapped[int] = mapped_column(default=0)
    location: Mapped[str] = mapped_column(String(160), index=True)
    work_mode: Mapped[str] = mapped_column(String(20), default="Remote")
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    posted_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    application_deadline: Mapped[date | None]
    embedding_status: Mapped[str] = mapped_column(String(30), default="pending")
    company: Mapped[Company] = relationship()
    skills: Mapped[list["JobSkill"]] = relationship(cascade="all, delete-orphan")
    __table_args__ = (
        CheckConstraint("experience_min >= 0 AND experience_max >= experience_min"),
        CheckConstraint("salary_min >= 0 AND salary_max >= salary_min"),
        CheckConstraint("status IN ('active','closed','draft')"),
        CheckConstraint("work_mode IN ('Remote','Hybrid','On-site')"),
        CheckConstraint(
            "employment_type IN ('Full-time','Part-time','Contract','Internship')"
        ),
    )


class Skill(Base):
    __tablename__ = "skills"
    skill_id: Mapped[int] = mapped_column(primary_key=True)
    skill_name: Mapped[str] = mapped_column(String(100))
    normalized_skill_name: Mapped[str] = mapped_column(String(100), unique=True)


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_profiles.candidate_id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.skill_id"), primary_key=True, index=True
    )
    proficiency_level: Mapped[str] = mapped_column(String(20), default="Intermediate")
    years_of_experience: Mapped[float] = mapped_column(default=0)
    skill: Mapped[Skill] = relationship()
    __table_args__ = (CheckConstraint("years_of_experience >= 0"),)


class JobSkill(Base):
    __tablename__ = "job_skills"
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.job_id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.skill_id"), primary_key=True, index=True
    )
    importance: Mapped[int] = mapped_column(default=3)
    is_required: Mapped[bool] = mapped_column(default=True)
    skill: Mapped[Skill] = relationship()
    __table_args__ = (CheckConstraint("importance BETWEEN 1 AND 5"),)


class Resume(Base):
    __tablename__ = "resumes"
    resume_id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_profiles.candidate_id", ondelete="CASCADE"), index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(500))
    extracted_text: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)
    uploaded_at: Mapped[datetime] = mapped_column(server_default=func.now())
    analysis_status: Mapped[str] = mapped_column(String(30), default="pending")
    analysis_error: Mapped[str] = mapped_column(Text, default="")
    __table_args__ = (
        Index(
            "uq_active_resume",
            "candidate_id",
            unique=True,
            postgresql_where=(is_active == True),
        ),
    )


class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"
    analysis_id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.resume_id", ondelete="CASCADE"), unique=True
    )
    education: Mapped[list] = mapped_column(JSONB)
    experience_years: Mapped[float]
    professional_summary: Mapped[str] = mapped_column(Text)
    extracted_projects: Mapped[list] = mapped_column(JSONB)
    suggested_roles: Mapped[list] = mapped_column(JSONB)
    analysis_json: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Application(Base):
    __tablename__ = "applications"
    application_id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_profiles.candidate_id"), index=True
    )
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.job_id"), index=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.resume_id"), index=True)
    cover_letter: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="Applied", index=True)
    applied_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
    candidate: Mapped[Candidate] = relationship()
    job: Mapped[Job] = relationship()
    history: Mapped[list["StatusHistory"]] = relationship(
        order_by="StatusHistory.changed_at", cascade="all, delete-orphan"
    )
    __table_args__ = (
        UniqueConstraint("candidate_id", "job_id"),
        CheckConstraint(
            "status IN ('Applied','Under Review','Shortlisted','Interview Scheduled','Selected','Rejected','Withdrawn')"
        ),
    )


class StatusHistory(Base):
    __tablename__ = "application_status_history"
    history_id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.application_id", ondelete="CASCADE"), index=True
    )
    old_status: Mapped[str | None] = mapped_column(String(30))
    new_status: Mapped[str] = mapped_column(String(30))
    changed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id"), index=True
    )
    changed_at: Mapped[datetime] = mapped_column(server_default=func.now())


class SavedJob(Base):
    __tablename__ = "saved_jobs"
    saved_job_id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_profiles.candidate_id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.job_id", ondelete="CASCADE"), index=True
    )
    saved_at: Mapped[datetime] = mapped_column(server_default=func.now())
    job: Mapped[Job] = relationship()
    __table_args__ = (UniqueConstraint("candidate_id", "job_id"),)


class Recommendation(Base):
    __tablename__ = "job_recommendations"
    recommendation_id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_profiles.candidate_id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.job_id", ondelete="CASCADE"), index=True
    )
    skill_match_score: Mapped[float]
    semantic_match_score: Mapped[float | None]
    experience_score: Mapped[float]
    location_score: Mapped[float]
    overall_score: Mapped[float]
    explanation: Mapped[dict] = mapped_column(JSONB)
    generated_at: Mapped[datetime] = mapped_column(server_default=func.now())
    __table_args__ = (
        UniqueConstraint("candidate_id", "job_id"),
        CheckConstraint("overall_score BETWEEN 0 AND 100"),
    )


class ResumeEmbedding(Base):
    __tablename__ = "resume_embeddings"
    embedding_id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.resume_id", ondelete="CASCADE"), unique=True
    )
    embedding: Mapped[list] = mapped_column(Vector(384))
    model_name: Mapped[str] = mapped_column(String(100))


class JobEmbedding(Base):
    __tablename__ = "job_embeddings"
    embedding_id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.job_id", ondelete="CASCADE"), unique=True
    )
    embedding: Mapped[list] = mapped_column(Vector(384))
    model_name: Mapped[str] = mapped_column(String(100))
    __table_args__ = (
        Index(
            "ix_job_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


class Report(Base):
    __tablename__ = "reports"
    report_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.job_id", ondelete="CASCADE"), index=True
    )
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="open")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    __table_args__ = (CheckConstraint("status IN ('open','resolved','dismissed')"),)
