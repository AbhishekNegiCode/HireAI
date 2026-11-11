# Architecture

HireAI is a single-repository React SPA and FastAPI API backed by PostgreSQL.
All displayed counters, job listings and compatibility scores come from the API.
The application does not substitute fixture data when a request fails.

```text
Browser → Vite proxy (development) / Nginx (Docker) → FastAPI routers
                                                        ↓
                                              SQLAlchemy session/transaction
                                                        ↓
                                              PostgreSQL + pgvector
                                                        ↑
Private resume → PDF/DOCX text → LangChain/Groq → Pydantic structured output
                         ↘ local BGE encoder → 384-dimensional pgvector rows
```

## Components and trust boundaries

- `frontend/src/pages`: role-specific workflows. Shared cards, forms, notifications,
  loading/error/empty states live in `components`. Auth state and CSRF tokens are
  held in memory. Browser credentials are HTTP-only cookies, not localStorage.
- `backend/app/routes`: HTTP validation, authorization and ownership checks.
- `backend/app/services`: parsing, provider calls, embeddings, matching and serializers.
- `backend/app/models`: normalized domain schema and navigable ORM relationships.
- `backend/migrations`: versioned PostgreSQL schema, initial frozen model snapshot,
  application audit trigger and timestamps. `database/schema.sql` is an exported
  inspection artifact; Alembic is the authoritative installation path.
- Private files are UUID-named and never mounted under a public static route.
  Downloads require the resume owner, the specific receiving recruiter, or admin.

Every request uses one SQLAlchemy session. On success it commits; on errors it
rolls back. Application submission locks the target job and current resume, checks
availability and uniqueness, inserts the application, and lets PostgreSQL create
its history record in the same transaction. Status transitions lock the application.
Withdrawn, selected and rejected states are terminal in this version.

## Authentication

Argon2 hashes passwords. Public registration admits candidate/recruiter roles only.
A JWT contains the user ID, opaque session ID and expiry. The server also checks a
revocable `auth_sessions` row and the user's active status on every request.
Logout deletes the session; suspension deletes all of the user's sessions.

Unsafe authenticated requests require a session-bound `X-CSRF-Token`. Browser
Origin must match `FRONTEND_ORIGIN`; cookies use SameSite=Lax. Production requires
secure cookies and HTTPS. Login/register have a per-process 20-attempt/minute IP
limit. A shared rate limiter is needed before running multiple public workers.

## Resume processing

1. Accept a nonempty PDF/DOCX up to 10 MB; validate extension, magic bytes and parser.
2. Reject unreadable scans, encrypted PDFs, >100-page PDFs and oversized DOCX expansion.
3. Store private bytes and at most 60,000 extracted characters; retire the previous resume.
4. Queue an in-process FastAPI background task after the upload transaction commits.
5. LangChain ChatGroq invokes structured extraction with a Pydantic schema. The system
   message treats document text as untrusted data; no tool execution is available.
6. Validate ranges, dates, list bounds and duplicate values; persist the analysis.
7. Generate local embeddings independently of Groq, so semantics can work without a key.
8. Candidate reviews/corrects structured data and explicitly imports skills into normalized
   skill records. Education and experience can be edited on the profile page.

The structured-output integration follows the [ChatGroq API](https://reference.langchain.com/python/langchain-groq/chat_models/ChatGroq/with_structured_output).
Pydantic shape validation reduces malformed output; it cannot establish that the
model's claims are true. Candidate review is therefore part of the workflow.
Resume text and provider exception content are not logged.

## Semantic and hybrid matching

`BAAI/bge-small-en-v1.5` runs locally through SentenceTransformers. Text is broken
into overlapping 250-word chunks, encoded, mean-pooled and L2-normalized. Stored
vectors have 384 dimensions and a model identifier. Both job and resume embeddings
use the same process. See [SentenceTransformer encoding](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html).

Required skill matches are calculated using an SQL LEFT JOIN and filtered aggregate.
Optional skills are displayed separately and do not count as mandatory matches.
Cosine distance is computed in PostgreSQL with pgvector and converted to a clamped
0–100 score. The HNSW cosine index supports nearest-neighbor lookup; the current
small-dataset hybrid scorer evaluates all eligible jobs to avoid losing strong
skill matches during vector preselection.

Default score = 0.50 × required skills + 0.30 × semantic + 0.10 × experience +
0.10 × location. Experience receives 100 once the minimum is met, otherwise a
proportion of the minimum. Remote jobs receive full location compatibility;
nonremote jobs require a case-insensitive exact location match. No maximum-experience
penalty is imposed. Missing semantic data is represented as `null`, and remaining
weights are renormalized, with that limitation shown to candidates.

Scores are compatibility heuristics, not hiring probabilities or eligibility rulings.
Explanations and roadmaps use posting requirements, never invented LLM compatibility
claims. Optional gaps are explicitly labeled. Closed, expired and already-applied
jobs are excluded. Cache rows expire after five minutes and are invalidated by profile,
skill, resume, job, embedding and application changes. Explicit refresh bypasses cache.
Concurrent refreshes for one candidate are serialized by a database row lock.

## Operational boundaries

This is a working university-scale application, not a claim of audited production
readiness. Background tasks are in-process and need manual retry after interruption.
Use a durable worker/outbox for production. Resume parsing is bounded but not sandboxed;
add malware scanning, isolated workers, a retention policy and protected backups before
accepting public uploads. There is no email verification, password reset, MFA, SSO,
calendar integration or outbound email. Matching is an explainable initial heuristic;
there is no empirical hiring-outcome calibration. Admin creation is interactive CLI only.
