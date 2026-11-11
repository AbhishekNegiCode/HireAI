# Verification report

Tests and browser checks completed on 10 November 2026; local frontend/API/database health rechecked on 11 November 2026.

| Check | Result |
|---|---|
| PostgreSQL connectivity | Passed, isolated loopback cluster on port 55432 |
| pgvector extension | Built/installed v0.8.1 against PostgreSQL 14.17 |
| Alembic migrations | Applied through `0002` in development and test databases |
| Development seed | 10 candidates, 5 recruiters, 5 companies, 20 jobs, 24 skills, 20 applications and 20 saved records created |
| Persisted real vectors | 20 job embeddings and 10 seeded resume embeddings, each 384 dimensions |
| Backend tests | **18 passed**, PostgreSQL/pgvector, latest run 3.05s |
| Frontend tests | **5 passed**, Vitest + React Testing Library, latest run 1.25s |
| Production frontend build | Passed; vendor/chart chunks split; no oversized-chunk warning |
| npm audit | **0 vulnerabilities** at verification time |
| Real BGE encoder | Passed, 384 dimensions, L2 norm 1.0 |
| Semantic sanity check | Related engineering descriptions: 0.8136; unrelated gardening description: 0.4124 |
| Browser desktop | Dashboard and job cards rendered; live API-backed stats; no observed console errors |
| Browser search | Searching Python returned the persisted Python Developer posting |
| Browser mobile | 390px viewport, document scrollWidth=390; navigation collapsed and cards fit |
| SQL demonstrations | Seed counts and EXPLAIN ANALYZE plans captured in docs |

Fresh migration downgrade/upgrade also passed against the disposable test database. An authentication sweep verified every private API route rejects unauthenticated requests.

Tests cover register/login, duplicate email, invalid passwords, public admin rejection,
CSRF/logout revocation, role and ownership checks, job CRUD/search, applications and
uniqueness, recruiter status updates, terminal states, candidate withdrawal, trigger
history, authorized submitted-resume access, PDF/DOCX parsing, malformed/oversized
file rejection, missing Groq credentials, structured output validation/correction,
profile skill import, resume replacement, required/optional skill gaps, pgvector
cosine behavior, cache refresh, FK rejection/rollback, account suspension, company
moderation, report resolution and expired/draft posting restrictions.

AI persistence tests use a mocked structured provider/encoder to be deterministic;
separate real BGE inference and database vector tests establish those integration
boundaries without making paid external requests. `scripts/verify_embeddings.py`
reproduces the local encoder sanity check.

## Verification boundaries

- No Groq API key was supplied, so **live LLM extraction is unverified**. The missing-key
  state, structured schema, persistence and candidate correction flow were tested.
- Docker is not installed on the host. Dockerfiles/Compose are provided, but a Docker
  build/start was **not** run. Native equivalents were migrated, seeded and served.
- The host has Node 23.11; tests/build passed there. Node 22 LTS or 24+ is documented
  because current Vitest declares those supported release lines.
- Recruiter/admin mutation workflows were tested through FastAPI TestClient against
  real PostgreSQL; browser visual QA concentrated on candidate desktop/mobile screens.
- No public deployment, load test, penetration test or cross-browser accessibility
  certification was performed. In-process background tasks and single-process auth
  rate limiting are documented scaling limitations.

The seed verification report may contain additional user-created account counts;
seeding itself created only the fictional baseline. Real user profile data was not
included in these test artifacts.
