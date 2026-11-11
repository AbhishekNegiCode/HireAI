# HireAI entity relationships

```mermaid
erDiagram
 USERS ||--o| CANDIDATE_PROFILES : has
 USERS ||--o| RECRUITER_PROFILES : has
 COMPANIES ||--o{ RECRUITER_PROFILES : employs
 COMPANIES ||--o{ JOBS : publishes
 RECRUITER_PROFILES ||--o{ JOBS : owns
 CANDIDATE_PROFILES ||--o{ CANDIDATE_SKILLS : lists
 SKILLS ||--o{ CANDIDATE_SKILLS : identifies
 JOBS ||--o{ JOB_SKILLS : requires
 SKILLS ||--o{ JOB_SKILLS : identifies
 CANDIDATE_PROFILES ||--o{ EDUCATION : has
 CANDIDATE_PROFILES ||--o{ EXPERIENCE : has
 CANDIDATE_PROFILES ||--o{ RESUMES : uploads
 RESUMES ||--o| RESUME_ANALYSES : analyzes
 RESUMES ||--o| RESUME_EMBEDDINGS : embeds
 JOBS ||--o| JOB_EMBEDDINGS : embeds
 CANDIDATE_PROFILES ||--o{ APPLICATIONS : submits
 JOBS ||--o{ APPLICATIONS : receives
 RESUMES ||--o{ APPLICATIONS : submitted_with
 APPLICATIONS ||--|{ APPLICATION_STATUS_HISTORY : audits
 USERS ||--o{ APPLICATION_STATUS_HISTORY : changes
 CANDIDATE_PROFILES ||--o{ SAVED_JOBS : saves
 JOBS ||--o{ SAVED_JOBS : saved
 CANDIDATE_PROFILES ||--o{ JOB_RECOMMENDATIONS : receives
 JOBS ||--o{ JOB_RECOMMENDATIONS : matches
 USERS ||--o{ REPORTS : files
 JOBS ||--o{ REPORTS : concerns
 USERS ||--o{ AUTH_SESSIONS : opens
```

Each entity has an integer surrogate primary key. Profiles are unique per user;
association tables have composite keys. Applications and saved jobs are unique per
candidate/job. Skills are unique by canonical lowercase name. Resume/application
references are retained when a resume is retired; physical removal is refused while
it is evidence for an application. Job deletion is refused after applications;
close the job instead. Cascades remove dependent joins, embeddings and caches.
