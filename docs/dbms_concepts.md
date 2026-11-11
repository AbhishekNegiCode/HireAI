# DBMS concepts implemented in HireAI

Run the examples against the development database after seeding. IDs shown below
refer to fictional fixture records. Mutation examples are rolled back deliberately.

## ER model, keys and cardinality

[ER diagram](../database/er_diagram.md), [exported schema](../database/schema.sql),
and [ORM models](../backend/app/models/__init__.py) describe the actual implementation.

- One-to-one: `users.user_id → candidate_profiles.user_id`, enforced by UNIQUE FK.
- One-to-many: company→jobs, candidate→resumes, application→history.
- Many-to-many: candidate↔skills and job↔skills through composite-key join tables.
- Surrogate primary keys identify independent entities. Join-table primary keys
  prevent duplicate assignments. Application and saved-job candidate/job pairs are unique.
- FK restrictions preserve jobs/resumes referenced by applications. Cascades remove
  dependent joins, embeddings and cache entries where deletion is safe.
- CHECK constraints validate role, work mode, application status, nonnegative years,
  salary/experience ranges and skill importance. Active resume uniqueness is a partial index.

```sql
SELECT conrelid::regclass AS table_name, conname, pg_get_constraintdef(oid)
FROM pg_constraint WHERE connamespace = 'public'::regnamespace ORDER BY 1,2;
```

## Functional dependencies and normalization

`user_id → full_name, email, password_hash, role, timestamps, is_active`; email is
also a candidate key. `company_id → company_name, industry, website, …`.
`job_id → company_id, recruiter_id, title, description, requirements, …`.
`skill_id → skill_name, normalized_skill_name`; normalized name is another candidate key.
`(candidate_id,skill_id) → proficiency_level, years_of_experience`.
`(job_id,skill_id) → importance,is_required`.
`application_id → candidate_id,job_id,resume_id,status, …`; candidate/job is an alternate key.

**1NF:** skills and education/experience records are separate rows, not comma-separated
columns. Commas in form inputs are just an input affordance, converted into rows.
**2NF:** join-table attributes depend on the whole composite key. A candidate's name
is not repeated in candidate_skills; a skill's name is not repeated in job_skills.
**3NF:** company attributes, user identity and skill names live in their own tables,
so they are not transitively dependent on a job/application key.

A job stores company_id as the posting's company and recruiter_id as its owning
account, rather than deriving historical company ownership from a recruiter's
potentially changeable affiliation. The API verifies both. `resume_analyses.analysis_json`
is a document extraction snapshot; education/project JSON is model output for review,
not the authoritative relational profile. Recommendation rows are an explicitly
denormalized, invalidatable cache. Embeddings are derived search data.

## INNER JOIN: recruiter applicant list

```sql
SELECT u.full_name, j.title, a.status, a.applied_at
FROM applications a
JOIN candidate_profiles c ON c.candidate_id = a.candidate_id
JOIN users u ON u.user_id = c.user_id
JOIN jobs j ON j.job_id = a.job_id
WHERE j.recruiter_id = 1 ORDER BY a.applied_at DESC;
```

## LEFT JOIN and aggregates: jobs with zero applications

This query is installed as the `job_application_counts` view.

```sql
SELECT j.job_id, j.title, COUNT(a.application_id) AS applicants
FROM jobs j LEFT JOIN applications a ON a.job_id = j.job_id
GROUP BY j.job_id ORDER BY applicants DESC;
SELECT * FROM job_application_counts WHERE recruiter_id = 1;
```

## RIGHT JOIN: preserve every company in a coverage report

```sql
SELECT c.company_name, COUNT(j.job_id) AS posted_jobs
FROM jobs j RIGHT JOIN companies c ON c.company_id = j.company_id
GROUP BY c.company_id ORDER BY posted_jobs;
```

LEFT JOIN with reversed operands would be equivalent; RIGHT JOIN is useful here
when extending an existing jobs-first report to retain companies with no postings.

## Subquery / NOT EXISTS: never recommend already-applied jobs

```sql
SELECT j.job_id, j.title FROM jobs j
WHERE j.status = 'active'
AND (j.application_deadline IS NULL OR j.application_deadline >= CURRENT_DATE)
AND NOT EXISTS (SELECT 1 FROM applications a
                WHERE a.job_id = j.job_id AND a.candidate_id = 1);
```

## GROUP BY / HAVING: active hiring teams

```sql
SELECT c.company_name, COUNT(j.job_id) AS active_openings,
       AVG(j.salary_min) AS average_starting_salary
FROM companies c JOIN jobs j ON j.company_id = c.company_id
WHERE j.status = 'active'
GROUP BY c.company_id HAVING COUNT(j.job_id) >= 2;
```

## SQL skill matching and stored function

`required_skill_match` is a stable SQL function installed by the migration. The
API's vectorized aggregate computes the same formula for all jobs in one query.

```sql
SELECT required_skill_match(1, 1);
SELECT js.job_id,
       COUNT(*) FILTER (WHERE js.is_required) AS required_count,
       COUNT(*) FILTER (WHERE js.is_required AND cs.skill_id IS NOT NULL) AS matched_count
FROM job_skills js LEFT JOIN candidate_skills cs
ON cs.skill_id = js.skill_id AND cs.candidate_id = 1
GROUP BY js.job_id;
```

No required skills yields 100% required-skill coverage, not a guarantee of fit.
Optional skill gaps remain visible and do not dilute required-skill coverage.

## Trigger, transactions and ACID

`application_status_audit` records the initial state and every changed status. The
session-scoped actor is set with transaction-local `set_config` by authentication.
Direct maintenance SQL should also set the actor; otherwise it is explicitly NULL.
The audit function updates `updated_at` for direct SQL transitions as well.

```sql
BEGIN;
SELECT set_config('app.user_id', '11', true);
SELECT application_id FROM applications WHERE application_id = 1 FOR UPDATE;
UPDATE applications SET status = 'Under Review' WHERE application_id = 1;
SELECT * FROM application_status_history WHERE application_id = 1 ORDER BY changed_at;
ROLLBACK;
```

**Atomicity:** application/status and history either both commit or both roll back.
**Consistency:** unique, foreign key and check constraints remain enforced even if
application validation is bypassed.
**Isolation:** PostgreSQL READ COMMITTED plus explicit row locks serializes conflicting
job submission/status changes. The unique pair constraint catches duplicate races.
**Durability:** committed WAL-backed PostgreSQL data survives application restarts;
Compose uses named volumes. Backups remain an operational responsibility.

Tests demonstrate FK rejection and rollback leaving neither application nor history.

## Indexing and query optimization

Indexes cover job title, company/location/status/posted_at, common foreign keys,
user email, canonical skills and application status. Partial unique indexing permits
many historical resumes but only one active resume per candidate. A vector HNSW
index uses `vector_cosine_ops`; embeddings are 384-dimensional.

```sql
SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'public';
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM applications WHERE candidate_id = 1 ORDER BY applied_at DESC LIMIT 50;
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM jobs WHERE status = 'active' ORDER BY posted_at DESC LIMIT 12;
EXPLAIN (ANALYZE, BUFFERS)
SELECT job_id FROM job_embeddings
ORDER BY embedding <=> (SELECT embedding FROM resume_embeddings LIMIT 1) LIMIT 10;
```

A sequential scan is often optimal for 20 seeded jobs. Do not disable sequential
scans just to obtain an impressive plan. Compare actual buffers/time on representative
data. `%substring%` ILIKE filters do not benefit from ordinary B-tree indexes; add
pg_trgm GIN indexes if the dataset grows. Search is paginated; associations are
batch-loaded with SQLAlchemy select-in loading to avoid per-card relationship queries.
