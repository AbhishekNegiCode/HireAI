from io import BytesIO
from datetime import date, timedelta
import pytest
from docx import Document
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from app.main import app
from app.database.session import SessionLocal
from app.models import (
    Application,
    StatusHistory,
    Job,
    User,
    Resume,
    Skill,
    JobEmbedding,
    ResumeEmbedding,
)
from app.schemas import ResumeOutput
from app.services.resume_parser import extract
from app.services.job_matcher import weighted_score
from conftest import register

JOB = {
    "title": "Python Engineer",
    "description": "Build reliable Python APIs with SQL and FastAPI in a collaborative team.",
    "location": "Bengaluru",
    "experience_min": 1,
    "experience_max": 5,
    "salary_min": 500000,
    "salary_max": 1000000,
    "skills": [
        {"name": "Python"},
        {"name": "SQL"},
        {"name": "Docker", "is_required": False},
    ],
}


def document():
    doc = Document()
    doc.add_paragraph(
        "Test Person. Python SQL FastAPI developer. Built a production recruitment platform with two years of experience."
    )
    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def pdf():
    writer = PdfWriter()
    page = writer.add_blank_page(612, 792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject(
                {NameObject("/F1"): writer._add_object(font)}
            )
        }
    )
    stream = DecodedStreamObject()
    stream.set_data(
        b"BT /F1 12 Tf 50 700 Td (Test Person Python SQL FastAPI developer with two years of software experience.) Tj ET"
    )
    page[NameObject("/Contents")] = writer._add_object(stream)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def create_job(client, **overrides):
    response = client.post("/api/jobs", json={**JOB, **overrides})
    assert response.status_code == 201, response.text
    return response.json()


def upload(client, data=None, name="resume.docx"):
    return client.post(
        "/api/resumes/upload", files={"file": (name, data or document())}
    )


def test_registration_auth_and_csrf(client):
    register(client)
    assert client.get("/api/auth/me").json()["user"]["role"] == "candidate"
    assert client.get("/api/admin/dashboard").status_code == 403
    assert client.get("/api/recruiter/jobs").status_code == 403
    assert (
        client.post(
            "/api/auth/register",
            json={
                "full_name": "Test",
                "email": "person@example.com",
                "password": "testing-password-123",
                "confirm_password": "testing-password-123",
                "role": "candidate",
            },
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/auth/login", json={"email": "person@example.com", "password": "wrong"}
        ).status_code
        == 401
    )
    csrf = client.headers.pop("X-CSRF-Token")
    assert client.post("/api/auth/logout").status_code == 403
    client.headers["X-CSRF-Token"] = csrf
    saved_cookie = client.cookies.get("hireai_session")
    assert client.post("/api/auth/logout").status_code == 200
    client.cookies.set("hireai_session", saved_cookie)
    assert client.get("/api/auth/me").status_code == 401


def test_no_admin_registration(client):
    assert (
        client.post(
            "/api/auth/register",
            json={
                "full_name": "Admin",
                "email": "a@example.com",
                "password": "password-long",
                "confirm_password": "password-long",
                "role": "admin",
            },
        ).status_code
        == 422
    )


def test_bad_password_confirmation(client):
    assert (
        client.post(
            "/api/auth/register",
            json={
                "full_name": "Person",
                "email": "a@example.com",
                "password": "short",
                "confirm_password": "different",
                "role": "candidate",
            },
        ).status_code
        == 422
    )


def test_job_crud_and_filters(recruiter):
    job = create_job(recruiter)
    assert (
        recruiter.get(
            "/api/jobs?q=Python&skill=sql&work_mode=Remote&experience=2&salary=600000"
        ).json()["total"]
        == 1
    )
    assert recruiter.get("/api/jobs?skill=java").json()["total"] == 0
    assert (
        recruiter.put(
            f"/api/jobs/{job['job_id']}",
            json={**JOB, "title": "Senior Python Engineer"},
        ).status_code
        == 200
    )
    with TestClient(app) as other:
        register(other, "recruiter", "other@example.com")
        assert other.put(f"/api/jobs/{job['job_id']}", json=JOB).status_code == 403
        assert (
            other.get(f"/api/recruiter/jobs/{job['job_id']}/applicants").status_code
            == 403
        )
    assert recruiter.delete(f"/api/jobs/{job['job_id']}").status_code == 200


def test_candidate_application_recruiter_flow(recruiter):
    job = create_job(recruiter)
    with TestClient(app) as candidate:
        register(candidate, email="candidate@example.com")
        assert (
            candidate.post(
                "/api/applications", json={"job_id": job["job_id"]}
            ).status_code
            == 422
        )
        uploaded = upload(candidate)
        assert uploaded.status_code == 201, uploaded.text
        rid = uploaded.json()["resume_id"]
        response = candidate.post(
            "/api/applications",
            json={
                "job_id": job["job_id"],
                "cover_letter": "Interested in building great APIs.",
            },
        )
        assert response.status_code == 201, response.text
        aid = response.json()["application_id"]
        assert len(response.json()["history"]) == 1
        assert (
            candidate.post(
                "/api/applications", json={"job_id": job["job_id"]}
            ).status_code
            == 409
        )
        assert (
            candidate.get("/api/candidates/dashboard").json()["total_applications"] == 1
        )
        assert recruiter.get(f"/api/resumes/{rid}/download").status_code == 200
        changed = recruiter.patch(
            f"/api/recruiter/applications/{aid}/status", json={"status": "Shortlisted"}
        )
        assert changed.status_code == 200, changed.text
        assert len(changed.json()["history"]) == 2
        assert changed.json()["history"][-1]["changed_by"] is not None
        assert recruiter.delete(f"/api/jobs/{job['job_id']}").status_code == 409
        assert candidate.patch(f"/api/applications/{aid}/withdraw").status_code == 200
        assert (
            recruiter.patch(
                f"/api/recruiter/applications/{aid}/status", json={"status": "Selected"}
            ).status_code
            == 409
        )
        assert candidate.delete("/api/resumes/me").status_code == 200
        assert candidate.get("/api/resumes/me").json() is None
        assert candidate.get(f"/api/resumes/{rid}/download").status_code == 200
    with TestClient(app) as other:
        register(other, email="outsider@example.com")
        assert other.get(f"/api/applications/{aid}").status_code == 403
        assert other.get(f"/api/resumes/{rid}/download").status_code == 403


@pytest.mark.parametrize(
    "data,name", [(document(), "resume.docx"), (pdf(), "resume.pdf")]
)
def test_resume_upload_and_missing_key(candidate, data, name):
    response = upload(candidate, data, name)
    assert response.status_code == 201, response.text
    result = candidate.get("/api/resumes/me/analysis").json()
    assert result["status"] == "unavailable"
    assert "GROQ_API_KEY" in result["message"]
    assert extract(data, name)
    assert candidate.delete("/api/resumes/me").status_code == 200


def test_invalid_resume(candidate):
    assert upload(candidate, b"not a document", "evil.pdf").status_code == 422
    assert upload(candidate, b"not a document", "resume.exe").status_code == 422
    assert (
        upload(candidate, b"a" * (10 * 1024 * 1024 + 1), "large.pdf").status_code == 422
    )


def test_skills_recommendations_and_gaps(recruiter):
    job = create_job(recruiter)
    create_job(recruiter, title="Closed opportunity", status="closed")
    create_job(
        recruiter,
        title="Expired opportunity",
        application_deadline=str(date.today() - timedelta(days=1)),
    )
    with TestClient(app) as candidate:
        register(candidate, email="candidate@example.com")
        assert (
            candidate.put(
                "/api/candidates/me/skills",
                json=[{"name": "Python"}, {"name": "python"}],
            ).status_code
            == 200
        )
        assert len(candidate.get("/api/candidates/me/skills").json()) == 1
        response = candidate.get("/api/ai/recommendations")
        assert response.status_code == 200, response.text
        assert len(response.json()) == 1
        row = response.json()[0]
        assert row["skill_match_score"] == 50
        assert row["semantic_match_score"] is None
        gap = candidate.post(f"/api/ai/skill-gap/{job['job_id']}").json()
        assert [x["name"] for x in gap["explanation"]["missing_skills"]] == [
            "SQL",
            "Docker",
        ]
        assert gap["explanation"]["missing_skills"][1]["required"] is False
        assert (
            candidate.post(f"/api/candidates/saved-jobs/{job['job_id']}").status_code
            == 201
        )
        assert (
            candidate.post(f"/api/candidates/saved-jobs/{job['job_id']}").status_code
            == 201
        )
        assert len(candidate.get("/api/candidates/saved-jobs").json()) == 1
        assert (
            candidate.delete(f"/api/candidates/saved-jobs/{job['job_id']}").status_code
            == 200
        )


def test_pgvector_similarity(recruiter):
    job = create_job(recruiter)
    with TestClient(app) as candidate:
        register(candidate, email="candidate@example.com")
        rid = upload(candidate).json()["resume_id"]
        with SessionLocal.begin() as db:
            db.add(
                JobEmbedding(
                    job_id=job["job_id"],
                    embedding=[1.0] + [0.0] * 383,
                    model_name="BAAI/bge-small-en-v1.5",
                )
            )
            db.add(
                ResumeEmbedding(
                    resume_id=rid,
                    embedding=[1.0] + [0.0] * 383,
                    model_name="BAAI/bge-small-en-v1.5",
                )
            )
        result = candidate.get("/api/ai/recommendations").json()[0]
        assert result["semantic_match_score"] == 100
        with SessionLocal.begin() as db:
            db.scalar(select(JobEmbedding)).embedding = [0.0, 1.0] + [0.0] * 382
        assert (
            candidate.post("/api/ai/recommendations/refresh").json()[0][
                "semantic_match_score"
            ]
            == 0
        )


def test_fk_and_transaction_rollback(candidate):
    with SessionLocal() as db:
        with pytest.raises(IntegrityError):
            db.add(Application(candidate_id=999, job_id=999, resume_id=999))
            db.commit()
        db.rollback()
        assert db.scalar(select(Application.application_id)) is None
        assert db.scalar(select(StatusHistory.history_id)) is None
    with SessionLocal() as db:
        db.add(Skill(skill_name="SQL", normalized_skill_name="sql"))
        db.flush()
        db.rollback()
    with SessionLocal() as db:
        assert db.scalar(select(Skill.skill_id)) is None


def test_admin_suspension(admin):
    with TestClient(app) as candidate:
        user = register(candidate, email="candidate@example.com")
        assert (
            admin.patch(
                f"/api/admin/users/{user['user_id']}/status", json={"is_active": False}
            ).status_code
            == 200
        )
        assert candidate.get("/api/auth/me").status_code == 401
    assert admin.get("/api/admin/dashboard").json()["users"] == 2
    for path in ("users", "companies", "jobs", "applications", "reports"):
        assert admin.get(f"/api/admin/{path}").status_code == 200


def test_structured_output_validation():
    result = ResumeOutput(technical_skills=[" Python ", "python", "SQL"])
    assert result.technical_skills == ["Python", "SQL"]
    with pytest.raises(ValueError):
        ResumeOutput(total_experience=-1)
    assert weighted_score(100, 100, 100, 100) == 100
    assert weighted_score(100, None, 100, 100) == 100


def test_real_pipeline_with_mocked_provider(candidate, monkeypatch):
    from app.services import resume_analyzer

    monkeypatch.setattr(
        resume_analyzer,
        "analyze_text",
        lambda _: ResumeOutput(
            technical_skills=["Python"],
            total_experience=2,
            professional_summary="API engineer",
            suggested_roles=["Backend Engineer"],
        ),
    )
    monkeypatch.setattr(resume_analyzer, "embed", lambda _: [1.0] + [0.0] * 383)
    response = upload(candidate)
    assert response.status_code == 201
    analysis = candidate.get("/api/resumes/me/analysis").json()
    assert analysis["status"] == "ready"
    assert analysis["semantic_available"] is True
    assert candidate.post("/api/resumes/me/analysis/import").status_code == 200
    assert candidate.get("/api/candidates/me/skills").json()[0]["name"] == "Python"
    corrected = {**analysis["analysis"], "total_experience": 3}
    assert candidate.put("/api/resumes/me/analysis", json=corrected).status_code == 200
    assert (
        candidate.get("/api/resumes/me/analysis").json()["analysis"]["total_experience"]
        == 3
    )


def test_profile_resume_replacement_and_read_routes(candidate):
    data = {
        "full_name": "Updated Candidate",
        "headline": "API Engineer",
        "location": "Bengaluru",
        "total_experience": 2,
        "education": [
            {
                "institution": "Test University",
                "degree": "BSc",
                "start_year": 2020,
                "end_year": 2023,
            }
        ],
        "experience": [
            {
                "company": "Test Co",
                "title": "Engineer",
                "start_date": "2023-01-01",
                "description": "Built APIs",
            }
        ],
    }
    result = candidate.put("/api/candidates/me", json=data)
    assert result.status_code == 200, result.text
    assert result.json()["education"][0]["degree"] == "BSc"
    assert (
        candidate.get("/api/candidates/me").json()["full_name"] == "Updated Candidate"
    )
    first = upload(candidate).json()["resume_id"]
    second = upload(candidate).json()["resume_id"]
    assert first != second
    assert candidate.get("/api/resumes/me").json()["resume_id"] == second
    assert candidate.post("/api/resumes/me/analyze").status_code == 200
    assert candidate.get("/api/applications/me").status_code == 200
    assert candidate.get("/api/candidates/saved-jobs").status_code == 200
    assert candidate.get("/api/health").status_code == 200
    assert (
        candidate.put(
            "/api/candidates/me", json={**data, "github_url": "javascript:alert(1)"}
        ).status_code
        == 422
    )


def test_recruiter_admin_moderation_routes(recruiter):
    job = create_job(recruiter)
    assert recruiter.get("/api/recruiter/dashboard").json()["active_jobs"] == 1
    assert len(recruiter.get("/api/recruiter/jobs").json()) == 1
    assert (
        recruiter.get("/api/recruiter/company").json()["company_name"] == "Test Company"
    )
    assert recruiter.get(f"/api/jobs/{job['job_id']}").status_code == 200
    assert (
        recruiter.post(
            f"/api/jobs/{job['job_id']}/report",
            json={"reason": "This is a fictional moderation test report."},
        ).status_code
        == 201
    )
    from app.core.security import passwords

    with SessionLocal.begin() as db:
        db.add(
            User(
                full_name="Admin",
                email="moderator@example.com",
                password_hash=passwords.hash("testing-password-123"),
                role="admin",
            )
        )
    with TestClient(app) as moderator:
        response = moderator.post(
            "/api/auth/login",
            json={"email": "moderator@example.com", "password": "testing-password-123"},
        )
        moderator.headers["X-CSRF-Token"] = response.json()["csrf_token"]
        report = moderator.get("/api/admin/reports").json()[0]
        assert (
            moderator.patch(
                f"/api/admin/reports/{report['report_id']}", json={"status": "resolved"}
            ).status_code
            == 200
        )
        company = moderator.get("/api/admin/companies").json()[0]
        assert (
            moderator.put(
                f"/api/admin/companies/{company['company_id']}",
                json={"company_name": "Reviewed Company"},
            ).status_code
            == 200
        )
        assert (
            moderator.put(
                f"/api/jobs/{job['job_id']}", json={**JOB, "status": "closed"}
            ).status_code
            == 200
        )
        assert moderator.get("/api/admin/jobs").json()[0]["status"] == "closed"


def test_expired_and_draft_jobs_block_applications(recruiter):
    expired = create_job(
        recruiter, application_deadline=str(date.today() - timedelta(days=1))
    )
    draft = create_job(recruiter, status="draft")
    with TestClient(app) as candidate:
        register(candidate, email="candidate@example.com")
        upload(candidate)
        assert (
            candidate.post(
                "/api/applications", json={"job_id": expired["job_id"]}
            ).status_code
            == 409
        )
        assert (
            candidate.post(
                "/api/applications", json={"job_id": draft["job_id"]}
            ).status_code
            == 409
        )
        assert candidate.get(f"/api/jobs/{draft['job_id']}").status_code == 403


def test_every_private_api_route_requires_authentication(client):
    import re

    public = {"/api/auth/register", "/api/auth/login", "/api/health"}
    checked = 0
    for path, operations in app.openapi()["paths"].items():
        if not path.startswith("/api/") or path in public:
            continue
        url = re.sub(r"\{[^}]+\}", "1", path)
        for method in operations:
            if method.upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                continue
            response = client.request(method.upper(), url, json={})
            assert response.status_code == 401, (method, path, response.text)
            checked += 1
    assert checked >= 40
