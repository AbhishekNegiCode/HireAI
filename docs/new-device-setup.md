# Set up HireAI on a new device

A Git clone includes source code, migrations and fictional seed scripts. It does
**not** include passwords/API keys, uploaded resumes, the previous device's database,
Python virtual environment, node_modules or downloaded AI models.

## Option A — Docker (Windows, macOS or Linux)

This is the simplest way to start the same PostgreSQL + pgvector, API and frontend
stack without installing Python, Node or PostgreSQL separately.

### 1. Install prerequisites and clone

Install Git and Docker Desktop (Windows/macOS) or Docker Engine with the Compose
plugin (Linux). Start Docker. On GitHub, copy this repository's HTTPS URL from
**Code**, then run:

```sh
git clone https://github.com/AbhishekNegiCode/HireAI.git HireAI
cd HireAI
```

The command above uses this project’s HTTPS clone URL.
For this private repository, sign into an account with repository access using your normal Git credential helper.
Do not put a password or access token in the clone URL.

### 2. Create configuration

macOS/Linux terminal:

```sh
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Open `.env` in a text editor. Set:

```dotenv
POSTGRES_PASSWORD=your-long-random-url-safe-database-password
SECRET_KEY=your-random-signing-secret-at-least-32-characters-long
GROQ_API_KEY=
FRONTEND_ORIGIN=http://localhost:5173
ENVIRONMENT=development
COOKIE_SECURE=false
EMBEDDINGS_ENABLED=true
```

Generate independent random values for the database password and signing secret.
Avoid URL-reserved characters in POSTGRES_PASSWORD because Compose embeds it in the
database URL. Use `COOKIE_SECURE=false` only for this localhost HTTP setup.

Add your own Groq key if you want LLM resume extraction. Leaving it blank is supported:
authentication, job search, uploads, applications and local embedding-based matching
still work. The resume page explains that LLM analysis is not configured.

### 3. Build, migrate and seed

```sh
docker compose up --build -d
docker compose logs -f backend
```

Wait for `Application startup complete`, then press Ctrl+C to stop following logs
(the containers keep running). The API startup command applies Alembic migrations.
Create fictional demonstration records and real local vectors:

```sh
docker compose exec backend python -m app.cli seed
docker compose exec backend python -m app.cli embed-jobs
docker compose exec backend python -m app.cli embed-resumes
```

The first embedding run downloads BGE model weights and can take several minutes.
Internet access is needed for the first build and model download. Subsequent runs
reuse Docker's dependency layers and persistent model cache.

### 4. Open the application

- App: http://localhost:5173
- API documentation: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

Use `localhost`, matching FRONTEND_ORIGIN, rather than switching to `127.0.0.1`.

| Demo role | Email | Development-only password |
|---|---|---|
| Candidate | maya@candidate.example | HireAI-demo-2026! |
| Recruiter | recruiter1@hireai.example | HireAI-demo-2026! |

Create an administrator separately; none is seeded:

```sh
docker compose exec backend python -m app.cli create-admin --email admin@example.com --name "Platform Administrator"
```

Enter a unique password at the hidden terminal prompt. Never reuse demonstration
passwords in a public deployment.

### 5. Stop, restart and update

```sh
docker compose stop
# Later:
docker compose start
# After pulling source updates:
git pull
docker compose up --build -d
```

Named volumes retain PostgreSQL records, private resumes and model weights across
container recreation. `docker compose down` removes containers but retains those
volumes. **Do not add `--volumes` / `-v` unless you intend to erase that local data.**
Do not seed an existing production database. Changing POSTGRES_PASSWORD after a
volume has been initialized does not automatically change the existing DB user's
password; preserve the original setting or perform an explicit database password rotation.

## Option B — Native development

Install Git, Python 3.11+, Node 22 LTS or 24+, and PostgreSQL 14+ with the **server-side
pgvector extension for that exact PostgreSQL version**. The Python `pgvector` package
alone is not enough. On Windows, Docker is the easier database option if pgvector
is not available in your native PostgreSQL installation.

Clone as above. Create the database using your PostgreSQL administration tool or:

```sh
createdb -U postgres hireai
```

Your migration database user needs permission to create the vector extension. An
administrator can install it in advance with `CREATE EXTENSION IF NOT EXISTS vector;`.

### macOS/Linux

From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
npm ci --prefix frontend
cp backend/.env.example backend/.env
```

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
npm ci --prefix frontend
Copy-Item backend\.env.example backend\.env
```

No virtual-environment activation or PowerShell execution-policy change is required.

Edit `backend/.env`:

```dotenv
DATABASE_URL=postgresql+psycopg://postgres:YOUR_DATABASE_PASSWORD@localhost:5432/hireai
SECRET_KEY=YOUR_RANDOM_SECRET_AT_LEAST_32_CHARACTERS_LONG
GROQ_API_KEY=
FRONTEND_ORIGIN=http://localhost:5173
EMBEDDINGS_ENABLED=true
```

Use your actual database username, password and port. URL-encode reserved characters
in the password portion of DATABASE_URL. You can generate a signing secret using
`python -c "import secrets; print(secrets.token_urlsafe(48))"` (or `py -c` on Windows).

Run migrations, seed and start the API from `backend`:

macOS/Linux:

```sh
cd backend
../.venv/bin/python -m alembic upgrade head
../.venv/bin/python -m app.cli seed
../.venv/bin/python -m app.cli embed-jobs
../.venv/bin/python -m app.cli embed-resumes
../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Windows PowerShell:

```powershell
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m app.cli seed
..\.venv\Scripts\python.exe -m app.cli embed-jobs
..\.venv\Scripts\python.exe -m app.cli embed-resumes
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal, from the cloned repository root:

```sh
cd frontend
npm run dev
```

Open http://localhost:5173. Restart the API after changing `backend/.env`.
The original development machine's `.pgdata` cluster and port 55432 are **not**
prerequisites for a new device; use the database you configured above.

## Verify the installation

1. `/api/health` should report `status: ok` and `database: connected`.
2. Sign into the seeded candidate account and check that jobs appear.
3. Sign into the seeded recruiter account and check its own job postings.
4. Upload a fictional PDF/DOCX and check analysis status. Live extraction needs Groq;
   local semantic matching needs the model download and stored job/resume vectors.

Frontend checks, from `frontend`:

```sh
npm test
npm run build
```

For backend tests, create a **separate** database named `hireai_test` and set
TEST_DATABASE_URL. Tests truncate its tables; never supply your application database.

macOS/Linux, from `backend`:

```sh
TEST_DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/hireai_test ../.venv/bin/python -m pytest -q
```

Windows PowerShell, from `backend`:

```powershell
$env:TEST_DATABASE_URL = "postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/hireai_test"
..\.venv\Scripts\python.exe -m pytest -q
Remove-Item Env:TEST_DATABASE_URL
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| Docker daemon unavailable | Start Docker Desktop/Engine before Compose. |
| Port 5432 already allocated | Stop the conflicting local PostgreSQL service or change only the Compose host port mapping; containers still use `db:5432`. |
| Port 8000 or 5173 occupied | Stop the conflicting app or consistently update the ports, Vite proxy and FRONTEND_ORIGIN. |
| Vector extension missing | Use the provided pgvector image or install the matching PostgreSQL server extension. |
| Connection refused/password rejected | Check database service, username, password and configured port. |
| Untrusted request origin | Open the exact FRONTEND_ORIGIN URL; restart the API after edits. |
| AI analysis unavailable | Add GROQ_API_KEY and an available GROQ_MODEL, restart, then choose Analyze again. |
| Semantic matching unavailable | Enable embeddings, permit the initial model download and run both embedding CLI commands. |
| Model download is slow | Let the first run finish; cached weights are reused. |
| Blank or scanned resume rejected | Use a text-based PDF/DOCX; OCR is not implemented. |

For architecture, testing boundaries and deployment considerations, see
[architecture.md](architecture.md), [verification.md](verification.md) and [setup.md](setup.md).
