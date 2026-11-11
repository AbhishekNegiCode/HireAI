import os
from pathlib import Path
import pytest

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://localhost:55432/hireai_test"
)
os.environ["SECRET_KEY"] = "test-only-secret-key-at-least-thirty-two-characters"
os.environ["EMBEDDINGS_ENABLED"] = "false"
os.environ["GROQ_API_KEY"] = ""
os.environ["STORAGE_DIR"] = "/tmp/hireai-test-resumes"

from fastapi.testclient import TestClient
from sqlalchemy import text
from app.main import app
from app.database.session import engine, SessionLocal, Base
from app.models import User
from app.core.security import passwords
from app.routes.auth import attempts


@pytest.fixture(scope="session", autouse=True)
def schema():
    if not engine.url.database.endswith("_test"):
        raise RuntimeError("Tests require a dedicated database ending in _test")
    from alembic.config import Config
    from alembic import command

    command.upgrade(Config("alembic.ini"), "head")
    yield


@pytest.fixture(autouse=True)
def clean(schema):
    with engine.begin() as conn:
        names = ", ".join(
            '"' + table.name + '"' for table in Base.metadata.sorted_tables
        )
        conn.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))
    attempts.clear()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def register(client, role="candidate", email="person@example.com"):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Test Person",
            "email": email,
            "password": "testing-password-123",
            "confirm_password": "testing-password-123",
            "role": role,
        },
    )
    assert response.status_code == 201, response.text
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    return response.json()["user"]


@pytest.fixture
def candidate(client):
    register(client)
    return client


@pytest.fixture
def recruiter(client):
    register(client, "recruiter")
    assert (
        client.put(
            "/api/recruiter/company",
            json={"company_name": "Test Company", "location": "Bengaluru"},
        ).status_code
        == 200
    )
    return client


@pytest.fixture
def admin(client):
    with SessionLocal.begin() as db:
        db.add(
            User(
                full_name="Admin",
                email="admin@example.com",
                password_hash=passwords.hash("testing-password-123"),
                role="admin",
            )
        )
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "testing-password-123"},
    )
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    return client
