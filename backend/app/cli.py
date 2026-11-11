"""Explicit CLI for development fixtures, admin provisioning and embedding refresh."""

import argparse
from datetime import date, timedelta
from getpass import getpass
from pathlib import Path
from sqlalchemy import select, text
from app.database.session import SessionLocal
from app.core.config import settings
from app.core.security import passwords
from app.models import (
    User,
    Candidate,
    Recruiter,
    Company,
    Skill,
    CandidateSkill,
    Job,
    JobSkill,
    Resume,
    Application,
    SavedJob,
    Education,
)


def seed():
    if settings().environment != "development":
        raise SystemExit("Seeding is allowed only with ENVIRONMENT=development")
    with SessionLocal.begin() as db:
        if db.scalar(select(User).where(User.email == "maya@candidate.example")):
            print("Development fixtures already exist; no changes made.")
            return
        names = [
            "Python",
            "SQL",
            "FastAPI",
            "React",
            "JavaScript",
            "TypeScript",
            "PostgreSQL",
            "Docker",
            "AWS",
            "Redis",
            "Git",
            "Java",
            "Node.js",
            "Figma",
            "CSS",
            "HTML",
            "Machine Learning",
            "Pandas",
            "Kubernetes",
            "Go",
            "C++",
            "REST APIs",
            "Testing",
            "Linux",
        ]
        skills = []
        for name in names:
            skill = db.scalar(
                select(Skill).where(Skill.normalized_skill_name == name.casefold())
            )
            if not skill:
                skill = Skill(skill_name=name, normalized_skill_name=name.casefold())
                db.add(skill)
                db.flush()
            skills.append(skill)
        companies = []
        for name, industry, location in [
            ("Orbit Labs", "Developer tools", "Bengaluru"),
            ("Forma Studio", "Design technology", "Mumbai"),
            ("Northstar Cloud", "Cloud infrastructure", "Hyderabad"),
            ("Verdant Systems", "Climate technology", "Pune"),
            ("Helio Analytics", "Data & analytics", "Delhi"),
        ]:
            company = Company(
                company_name=name,
                industry=industry,
                location=location,
                company_size="51–200",
                description=f"{name} is a fictional product team building thoughtful software for a better working world.",
                website="https://example.com",
            )
            db.add(company)
            db.flush()
            companies.append(company)
        recruiters = []
        for i, name in enumerate(
            ["Arjun Mehta", "Nora Shah", "Dev Malhotra", "Rhea Kapoor", "Kabir Rao"]
        ):
            u = User(
                full_name=name,
                email=f"recruiter{i+1}@hireai.example",
                password_hash=passwords.hash("HireAI-demo-2026!"),
                role="recruiter",
            )
            db.add(u)
            db.flush()
            r = Recruiter(
                user_id=u.user_id,
                company_id=companies[i].company_id,
                designation="Talent Partner",
            )
            db.add(r)
            db.flush()
            recruiters.append(r)
        candidates = []
        for i, name in enumerate(
            [
                "Maya Sharma",
                "Aarav Sen",
                "Isha Kapoor",
                "Rohan Das",
                "Anika Rao",
                "Vihaan Shah",
                "Tara Menon",
                "Neil Joshi",
                "Sana Verma",
                "Reyansh Nair",
            ]
        ):
            email = (
                "maya@candidate.example" if i == 0 else f"candidate{i+1}@hireai.example"
            )
            u = User(
                full_name=name,
                email=email,
                password_hash=passwords.hash("HireAI-demo-2026!"),
                role="candidate",
            )
            db.add(u)
            db.flush()
            c = Candidate(
                user_id=u.user_id,
                headline="Software developer · Building useful things",
                location="Bengaluru",
                total_experience=2 + i % 4,
                professional_summary="Software developer interested in reliable APIs, thoughtful interfaces and collaborative product teams.",
                github_url="https://github.com",
                portfolio_url="https://example.com",
            )
            db.add(c)
            db.flush()
            candidates.append(c)
            for s in skills[:7] + skills[10:11]:
                db.add(
                    CandidateSkill(
                        candidate_id=c.candidate_id,
                        skill_id=s.skill_id,
                        years_of_experience=2,
                    )
                )
            db.add(
                Education(
                    candidate_id=c.candidate_id,
                    institution="Fictional Institute of Technology",
                    degree="B.Tech Computer Science",
                    start_year=2019,
                    end_year=2023,
                )
            )
        titles = [
            "Full Stack Developer",
            "Frontend Engineer",
            "Backend Engineer",
            "Product Engineer",
            "Data Engineer",
            "Python Developer",
            "Cloud Engineer",
            "Software Engineer",
            "React Developer",
            "Platform Engineer",
            "Machine Learning Engineer",
            "API Developer",
            "DevOps Engineer",
            "UI Engineer",
            "Graduate Software Engineer",
            "Analytics Engineer",
            "Java Developer",
            "Infrastructure Engineer",
            "Engineering Intern",
            "Senior Backend Engineer",
        ]
        jobs = []
        for i, title in enumerate(titles):
            owner = i % 5
            j = Job(
                company_id=companies[owner].company_id,
                recruiter_id=recruiters[owner].recruiter_id,
                title=title,
                description=f"Join {companies[owner].company_name} as a {title.lower()} and help build products people love. You will collaborate with a small, supportive engineering team to design, implement and ship reliable software. We value curiosity, clear communication and a thoughtful approach to solving problems.",
                responsibilities="Build and maintain production features. Collaborate with design and product teams. Review code, write meaningful tests and improve system performance.",
                employment_type="Internship" if i == 18 else "Full-time",
                experience_min=i % 4,
                experience_max=3 + i % 5,
                salary_min=600000 + i * 50000,
                salary_max=1200000 + i * 75000,
                location=companies[owner].location,
                work_mode=["Remote", "Hybrid", "On-site"][i % 3],
                application_deadline=date.today() + timedelta(days=30 + i),
                embedding_status="pending",
            )
            db.add(j)
            db.flush()
            jobs.append(j)
            indexes = (
                [0, 1, 2, 6, 7, 8]
                if "Backend" in title or "Python" in title or "API" in title
                else (
                    [3, 4, 5, 14, 15, 10]
                    if "Frontend" in title or "React" in title or "UI" in title
                    else [0, 1, 3, 6, 7, 8]
                )
            )
            for n, idx in enumerate(indexes):
                db.add(
                    JobSkill(
                        job_id=j.job_id,
                        skill_id=skills[idx].skill_id,
                        is_required=n < 4,
                        importance=5 if n < 2 else 3,
                    )
                )
        from docx import Document

        directory = Path(settings().storage_dir).resolve()
        directory.mkdir(parents=True, exist_ok=True)
        for i, c in enumerate(candidates):
            doc = Document()
            doc.add_heading(c.user.full_name if c.user else "Sample Candidate", 0)
            doc.add_paragraph(
                "Fictional development resume. Python, SQL, React, FastAPI, PostgreSQL. Built collaborative applications and reliable APIs. Two years of software engineering experience."
            )
            path = directory / f"development-{c.candidate_id}.docx"
            doc.save(path)
            path.chmod(0o600)
            resume = Resume(
                candidate_id=c.candidate_id,
                original_filename="sample-resume.docx",
                storage_path=str(path),
                extracted_text="Fictional candidate. Python SQL React FastAPI PostgreSQL. Software engineering experience.",
                analysis_status="not_analyzed",
            )
            db.add(resume)
            db.flush()
            db.execute(
                text("SELECT set_config('app.user_id', :uid, true)"),
                {"uid": str(c.user_id)},
            )
            for offset in range(2):
                db.add(
                    Application(
                        candidate_id=c.candidate_id,
                        job_id=jobs[(i + offset + 8) % 20].job_id,
                        resume_id=resume.resume_id,
                        status=[
                            "Applied",
                            "Under Review",
                            "Shortlisted",
                            "Interview Scheduled",
                        ][i % 4],
                    )
                )
            for offset in range(2):
                db.add(
                    SavedJob(
                        candidate_id=c.candidate_id,
                        job_id=jobs[(i + offset) % 20].job_id,
                    )
                )
        print(
            "Created 10 candidates, 5 recruiters, 5 companies, 20 jobs and 24 skills with applications and saved jobs."
        )


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("seed")
    admin = sub.add_parser("create-admin")
    admin.add_argument("--email", required=True)
    admin.add_argument("--name", required=True)
    sub.add_parser("embed-jobs")
    sub.add_parser("embed-resumes")
    args = parser.parse_args()
    if args.command == "seed":
        seed()
    elif args.command == "create-admin":
        from pydantic import TypeAdapter, EmailStr

        email = str(TypeAdapter(EmailStr).validate_python(args.email)).lower()
        password = getpass("New admin password (at least 12 characters): ")
        if len(password) < 12:
            raise SystemExit("Password too short")
        with SessionLocal.begin() as db:
            if db.scalar(select(User).where(User.email == email)):
                raise SystemExit("Email already exists")
            db.add(
                User(
                    email=email,
                    full_name=args.name,
                    password_hash=passwords.hash(password),
                    role="admin",
                )
            )
        print("Administrator created.")
    elif args.command == "embed-resumes":
        from app.services.embedding_service import embed
        from app.services.common import invalidate
        from app.models import ResumeEmbedding

        with SessionLocal() as db:
            rows = db.scalars(select(Resume).where(Resume.is_active)).all()
            for resume in rows:
                vector = embed(resume.extracted_text)
                row = db.scalar(
                    select(ResumeEmbedding).where(
                        ResumeEmbedding.resume_id == resume.resume_id
                    )
                )
                if row is None:
                    row = ResumeEmbedding(resume_id=resume.resume_id)
                    db.add(row)
                row.embedding, row.model_name = vector, settings().embedding_model
                invalidate(db, resume.candidate_id)
            db.commit()
            print(
                f"Generated {len(rows)} active resume embeddings locally; no LLM request was made."
            )
    else:
        from app.services.embedding_service import embed_job

        with SessionLocal() as db:
            ids = list(db.scalars(select(Job.job_id)))
        for jid in ids:
            embed_job(jid)
        print("Embedding refresh finished; inspect embedding_status for each job.")


if __name__ == "__main__":
    main()
