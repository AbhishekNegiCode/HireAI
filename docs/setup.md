# Setup and operation

## Docker (portable, recommended)

Install Docker Engine/Desktop and Compose. From the repository root:

```sh
cp .env.example .env
# Edit POSTGRES_PASSWORD and SECRET_KEY; use long random URL-safe values.
# Optional: add GROQ_API_KEY. Do not commit .env.
docker compose up --build -d
docker compose exec backend python -m app.cli seed
docker compose exec backend python -m app.cli embed-jobs
docker compose exec backend python -m app.cli embed-resumes
```

Open http://localhost:5173 . The API is at http://localhost:8000 and documentation
at http://localhost:8000/docs . Migrations run before the backend starts. The first
embedding invocation downloads BGE weights; the named model cache prevents repeated
downloads. The CPU model also consumes memory, so allow several GB for the stack.

Seed is explicitly development-only. It creates fictional users and documents,
never a default administrator. To provision an administrator:

```sh
docker compose exec backend python -m app.cli create-admin --email admin@example.com --name 'Platform Administrator'
```

The password is entered securely at the terminal prompt, not in shell history.
Set `ENVIRONMENT=production`, `COOKIE_SECURE=true`, and the HTTPS `FRONTEND_ORIGIN`
for public deployment. Put the frontend behind HTTPS and keep PostgreSQL private.
Docker build/configuration is provided but was not executed on the development host
because Docker was not installed; the same services were verified natively.

## Native development

Requirements: Python 3.11+ (verified with 3.13), Node 22 LTS or 24+, PostgreSQL 14+
with the pgvector extension installed for that PostgreSQL version.

```sh
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
npm ci --prefix frontend
cp backend/.env.example backend/.env
```

Configure `backend/.env`: a reachable SQLAlchemy psycopg PostgreSQL URL, a random
32+-character `SECRET_KEY`, `FRONTEND_ORIGIN=http://localhost:5173`, and optionally
`GROQ_API_KEY`. Generate a secret with `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`.
Create a database, then run:

```sh
cd backend
../.venv/bin/alembic upgrade head
../.venv/bin/python -m app.cli seed
../.venv/bin/python -m app.cli embed-jobs
../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```sh
cd frontend
npm run dev
```

Use **http://localhost:5173**, matching `FRONTEND_ORIGIN`. The Vite proxy routes `/api`
to port 8000. If using `http://127.0.0.1:5173` instead, update FRONTEND_ORIGIN to match
and restart the backend. Origin matching intentionally distinguishes these hostnames.

### This workspace's prepared native database

An isolated PostgreSQL cluster was created in `.pgdata`, listening on loopback port
**55432**, with `hireai` and `hireai_test` databases. The ignored `backend/.env` contains
a generated secret and this database URL. It does not contain a Groq key.

Restart the database if needed, from the repository root:

```sh
pg_ctl -D .pgdata -l /tmp/hireai-postgres.log -o '-p 55432 -h 127.0.0.1 -k /tmp' start
```

Stop it only when you are finished using the app:

```sh
pg_ctl -D .pgdata stop
```

This local-only cluster uses trust authentication for development. It is bound to
loopback, and is not a public deployment configuration. Compose uses a separate
password-protected database and persistent named volumes.

## Configuration reference

| Variable | Purpose |
|---|---|
| DATABASE_URL | `postgresql+psycopg://user:password@host:port/hireai` |
| SECRET_KEY | Required random signing secret, 32+ characters |
| GROQ_API_KEY | Optional key for structured LLM resume extraction |
| GROQ_MODEL | Configurable Groq model; default `openai/gpt-oss-120b` |
| EMBEDDINGS_ENABLED | `true` for local BGE inference, `false` for explicit skill-only fallback |
| EMBEDDING_MODEL | `BAAI/bge-small-en-v1.5`; must produce 384 dimensions |
| EMBEDDING_CACHE_DIR | Persistent local model cache; default `storage/model-cache/hub` |
| STORAGE_DIR | Private resume directory; default `storage/resumes` |
| FRONTEND_ORIGIN | Exact allowed browser origin |
| COOKIE_SECURE | `true` for HTTPS production |
| ENVIRONMENT | `development` permits explicit fixture seeding; `production` forbids it |
| TOKEN_MINUTES | Session expiry; default 60 |
| SKILL_WEIGHT / SEMANTIC_WEIGHT / EXPERIENCE_WEIGHT / LOCATION_WEIGHT | Relative scoring weights, defaults .50/.30/.10/.10 |
| TEST_DATABASE_URL | Dedicated test DB URL ending in `_test` |

Settings are loaded at backend startup. Restart after changing environment values.
No API key is sent to the frontend. The backend can start and serve all non-LLM
features without a Groq key. In that state the resume page explains configuration.
When a key is added, use **Analyze again** on the resume page. Confirm the configured
model remains available in the Groq account; the model name is not hardcoded in calls.

## Tests

Create a separate database ending in `_test`; never point tests at production.
Tests migrate and truncate only that database between test cases.

```sh
createdb -h localhost -p 55432 hireai_test   # only if it does not already exist
cd backend
TEST_DATABASE_URL=postgresql+psycopg://localhost:55432/hireai_test ../.venv/bin/python -m pytest -q
cd ../frontend
npm test
npm run build
npm audit
```

Provider extraction and embedding persistence are mocked in deterministic tests.
Real local model inference was checked separately; live Groq inference requires a key.
The test database guard refuses a URL whose database name does not end in `_test`.

## Common problems

- `vector extension is not available`: install pgvector for the exact PostgreSQL
  major version, or use the provided pgvector Docker image. The Python package alone
  does not install the PostgreSQL extension.
- Connection refused: start PostgreSQL and verify host/port against DATABASE_URL.
- `Untrusted request origin`: use the configured frontend hostname and restart after edits.
- AI unavailable: add GROQ_API_KEY; for semantic failures check model download access,
  cache permissions and available memory. Skills and applications remain functional.
- Old job embeddings: run `python -m app.cli embed-jobs`. Resume embeddings are produced
  after upload/reanalysis. Recommendation refresh uses current profile skills.
- Job deletion returns 409: it has applications; close the posting instead.
- Scanned PDF rejected: provide a text-based PDF/DOCX; OCR is not implemented.
- Stale `pending` after backend restart: click Analyze again. Tasks are not durable yet.
