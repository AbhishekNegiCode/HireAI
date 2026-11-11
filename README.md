# HireAI — Your next chapter

A working AI-assisted recruitment portal built for a university DBMS project:
React/Vite, FastAPI, PostgreSQL and pgvector, with local BGE embeddings and a
LangChain/Groq structured resume-analysis integration.

## Features

- **Candidates:** secure sign-up/sign-in; profile, education, experience and normalized
  skills; private PDF/DOCX resumes; editable extraction reports; job search/filtering;
  saved jobs; applications with timestamped status history; hybrid recommendations
  and deterministic skill-gap roadmaps.
- **Recruiters:** company profiles; create/edit/activate/close/delete postings; authorized
  applicant and submitted-resume review; skill/experience filters; status updates;
  live recruitment counts and Recharts analytics.
- **Admins:** secure CLI provisioning, platform statistics, account suspension,
  company/job moderation, application monitoring and content-report resolution.
- **Database:** normalized role profiles and skill joins, constraints, transactions,
  audit triggers, analytics view, stored skill-match function, vector HNSW index,
  Alembic migrations and guarded fictional seed data.

All dashboard numbers and matches are generated from persisted database records.
Missing AI credentials never substitute a fake analysis or invented score.

## Set up on a new device

Start with the [complete new-device guide](docs/new-device-setup.md). It includes
Windows PowerShell and macOS/Linux commands, cloning, secrets, PostgreSQL/pgvector,
migrations, seed accounts, AI setup, tests and troubleshooting.

**Recommended: Docker** (Git and Docker must be installed and Docker running):

```sh
git clone <YOUR-REPOSITORY-URL> HireAI
cd HireAI
cp .env.example .env
# Set independent random POSTGRES_PASSWORD and SECRET_KEY values in .env.
# Optionally add your own GROQ_API_KEY.
docker compose up --build -d
# Wait for the backend to finish starting; inspect: docker compose logs -f backend
docker compose exec backend python -m app.cli seed
docker compose exec backend python -m app.cli embed-jobs
docker compose exec backend python -m app.cli embed-resumes
```

Copy the clone URL from this repository's **Code** button. On Windows PowerShell,
use `Copy-Item .env.example .env` instead of `cp`. The guide also covers native
installation without Docker.

Open **http://localhost:5173**. API docs: **http://localhost:8000/docs**.
Migrations run on backend startup. The first embedding run downloads BGE weights.
A fresh clone does not include secrets, uploaded files, a database or model weights.
Named Docker volumes retain your local data between container restarts.

To start/stop an existing installation, see the [operation guide](docs/setup.md).
The original developer workstation's database on port 55432 is not required on a
new device; the Docker configuration uses its own database service.

## Development accounts

Run `python -m app.cli seed` from `backend` with `ENVIRONMENT=development`.
The seed is repeat-safe and creates 10 candidates, 5 recruiters, 5 companies,
20 openings, 24 skills, 20 applications and 20 saved-job records.

| Role | Email | Development-only password |
|---|---|---|
| Candidate | `maya@candidate.example` | `HireAI-demo-2026!` |
| Recruiter | `recruiter1@hireai.example` | `HireAI-demo-2026!` |
| Other recruiters | `recruiter2@hireai.example` through `recruiter5@hireai.example` | `HireAI-demo-2026!` |
| Other candidates | `candidate2@hireai.example` through `candidate10@hireai.example` | `HireAI-demo-2026!` |

No default admin exists. Create one using an interactive password prompt:

```sh
cd backend
../.venv/bin/python -m app.cli create-admin --email admin@example.com --name 'Platform Administrator'
```

## Configuration

`backend/.env.example` documents native settings; root `.env.example` documents
Compose settings. Required: `DATABASE_URL`, random `SECRET_KEY`. Optional:
`GROQ_API_KEY`, `GROQ_MODEL`, `EMBEDDINGS_ENABLED`, `EMBEDDING_CACHE_DIR` and four
matching weights. `FRONTEND_ORIGIN` must match the browser origin. Use HTTPS and
`COOKIE_SECURE=true` with `ENVIRONMENT=production`.

No Groq key was supplied during implementation. LLM extraction is implemented and
tested with a controlled provider fixture, but live Groq inference is not verified.
The real BGE model was downloaded and its 384-dimensional normalized output verified.

## Project structure

```text
DBMS_Project/
├── frontend/                 React SPA, reusable UI, role-specific pages
│   ├── src/{components,pages,layouts,hooks,context,services}
│   ├── Dockerfile
│   └── nginx.conf
├── backend/
│   ├── app/{core,database,models,schemas,routes,services,utils}
│   ├── migrations/           Versioned schema, frozen v1 snapshot, audit function
│   ├── tests/                PostgreSQL-backed API and AI pipeline tests
│   ├── requirements.txt
│   └── Dockerfile
├── database/                 schema.sql, audit.sql, seed.sql, init.sh, ER diagram
├── docs/                     Architecture, API, setup, DBMS concepts, verification
├── docker-compose.yml
└── README.md
```

## Architecture and AI workflows

The browser calls FastAPI through a same-origin proxy. HTTP-only JWT cookies plus
session-bound CSRF tokens protect requests. SQLAlchemy commits related changes in
one transaction; PostgreSQL enforces identity, ownership references and uniqueness.

Resume → validated private file → extracted text → LangChain/Groq → Pydantic report
→ candidate review/correction → normalized profile skills. Independently, local BGE
embeddings are stored in pgvector. No external vector database is used.

Recommendations combine **50% required skills + 30% semantic similarity + 10%
experience + 10% location**. Optional skills are separate from mandatory coverage.
When vectors are missing, semantic score is null and remaining weights are adjusted,
with an explicit UI notice. Closed, expired and already-applied jobs are excluded.
A match score is a compatibility heuristic, not a probability of being hired.

[Architecture and tradeoffs](docs/architecture.md) · [API reference](docs/api_documentation.md)

## Database schema and ER diagram

The Mermaid ER diagram is in [database/er_diagram.md](database/er_diagram.md).
The full verified SQL schema is in [database/schema.sql](database/schema.sql).
The [DBMS guide](docs/dbms_concepts.md) explains functional dependencies, 3NF,
keys, joins, subqueries, views, aggregates, indexes, stored functions, audit triggers,
transactions, ACID and EXPLAIN ANALYZE using the actual application tables.

Core entities: users, candidate_profiles, recruiter_profiles, companies, jobs,
skills, candidate_skills, job_skills, education, experience, resumes, resume_analyses,
applications, application_status_history, saved_jobs, job_recommendations,
resume_embeddings, job_embeddings, reports and auth_sessions.

## Testing

```sh
cd backend
TEST_DATABASE_URL=postgresql+psycopg://localhost:55432/hireai_test ../.venv/bin/python -m pytest -q
cd ../frontend
npm test
npm run build
```

Backend tests use a dedicated PostgreSQL/pgvector database and cover authentication,
CSRF, authorization, search/CRUD, application status/history, private resumes,
PDF/DOCX parsing, rollback/foreign keys, matching, vector similarity and moderation.
Frontend tests exercise sign-in and save/unsave/failure behavior. See the detailed
[verification report](docs/verification.md) for results and verification boundaries.

## Screenshots and UI review

The running desktop dashboard and job search were visually inspected in the browser.
Job search was also checked at a 390px mobile viewport with no horizontal overflow.
To capture presentation screenshots, sign into the fictional candidate account and
capture Overview, AI matches, My resume and Applications; sign into a recruiter
account for recruitment analytics and applicant management. Do not include real
candidate data in shared screenshots.

## Remaining limitations and future work

- Live Groq extraction requires your API key and a currently available model.
- Docker files are supplied; Docker execution was not verified on this host.
- Background AI tasks run inside FastAPI. Add a durable queue/outbox for recovery
  across worker restarts and heavier workloads.
- Add email verification, password recovery/MFA, shared rate limiting, isolated
  document scanning and an explicit privacy/retention policy before public deployment.
- Resume corrections currently use a validated structured JSON editor; profile fields
  have conventional forms. Skill-gap learning guidance is a deterministic generic roadmap.
- Search uses ILIKE and simple title relevance; large deployments should add pg_trgm
  indexes, keyset pagination and vector candidate preselection with measured recall.
- Add OCR for scanned resumes, notification delivery and interview calendar scheduling.
