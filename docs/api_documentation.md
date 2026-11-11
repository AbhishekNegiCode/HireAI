# API reference

Interactive Swagger: http://localhost:8000/docs . Machine schema:
http://localhost:8000/openapi.json . API prefix: `/api`.

Responses use JSON. Errors use `{"error":{"message":"…","details":[…]}}` with
validation details when applicable. 401 = sign-in required; 403 = role/ownership/CSRF
failure; 404 = missing resource; 409 = duplicate/conflict/final state; 422 = invalid
input; 429 = auth rate limit. Lists use bounded `page` and, for job search, `page_size`.

Authentication returns `{user,csrf_token}` and sets HTTP-only `hireai_session`.
Send cookies on every request and `X-CSRF-Token` on authenticated POST/PUT/PATCH/DELETE.
`GET /auth/me` restores user/CSRF state after reload. Tokens expire after 60 minutes
by default. Public registration is limited to candidate/recruiter.

| Module | Endpoints | Access |
|---|---|---|
| Auth | POST `/auth/register`, `/auth/login`; POST `/auth/logout`; GET `/auth/me` | Public registration/login, authenticated remainder |
| Candidate | GET/PUT `/candidates/me`; GET/PUT `/candidates/me/skills`; GET `/candidates/dashboard` | Candidate |
| Saved | GET `/candidates/saved-jobs`; POST/DELETE `/candidates/saved-jobs/{job_id}` | Candidate |
| Resume | POST `/resumes/upload`; GET/DELETE `/resumes/me`; GET/PUT `/resumes/me/analysis`; POST `/resumes/me/analyze`; POST `/resumes/me/analysis/import` | Candidate |
| Download | GET `/resumes/{resume_id}/download` | Owner, receiving recruiter, admin |
| Jobs | GET `/jobs`, `/jobs/{job_id}`; POST `/jobs/{job_id}/report` | Authenticated; drafts restricted |
| Job editing | POST `/jobs`; PUT/DELETE `/jobs/{job_id}` | Recruiter owner; admin can edit/delete |
| Applications | POST `/applications`; GET `/applications/me`; GET `/applications/{id}`; PATCH `/applications/{id}/withdraw` | Candidate; detail also receiving recruiter/admin |
| Recruiter | GET `/recruiter/dashboard`, `/recruiter/jobs`; GET/PUT `/recruiter/company` | Recruiter |
| Applicants | GET `/recruiter/jobs/{id}/applicants`; PATCH `/recruiter/applications/{id}/status` | Owning recruiter |
| Matching | GET `/ai/recommendations`; POST `/ai/recommendations/refresh`; POST `/ai/skill-gap/{job_id}` | Candidate |
| Admin | GET `/admin/dashboard`, `/admin/users`, `/admin/jobs`, `/admin/companies`, `/admin/applications`, `/admin/reports` | Admin |
| Moderation | PATCH `/admin/users/{id}/status`; PUT `/admin/companies/{id}`; PATCH `/admin/reports/{id}` | Admin |
| Health | GET `/health` | Public, no secrets |

Job search supports `q` (title/company), `company`, `location`, `skill`, `work_mode`,
`employment_type`, `experience` (candidate years), `salary` (minimum desired annual
INR), `sort=newest|relevance`, `page`, and `page_size` (1–100). Relevance prioritizes
exact/prefix title matches; personalized hybrid ranking is the separate AI endpoint.

Applicant search supports `skill`, `experience` (minimum years), `page`. Admin lists
and application history lists use 50 rows per page. Recruiter job management returns
that recruiter's own postings. Dashboard recent lists are deliberately bounded.

## Examples

Registration:
```json
{"full_name":"Example Person","email":"person@example.com","password":"a-long-unique-password","confirm_password":"a-long-unique-password","role":"candidate"}
```

Skills are supplied as individual records:
```json
[{"name":"Python","proficiency_level":"Advanced","years_of_experience":3}]
```

An application uses the current active resume server-side; a caller cannot submit
another candidate's resume ID:
```json
{"job_id":1,"cover_letter":"I would love to contribute to your API team."}
```

Status updates:
```json
{"status":"Interview Scheduled"}
```

Allowed recruiter transitions target Under Review, Shortlisted, Interview Scheduled,
Selected or Rejected. Withdrawn/Selected/Rejected are terminal. Candidates can withdraw
nonfinal applications. History includes old/new status, actor and timestamp.

Job edit uses the complete validated job payload, including a `skills` list of
`{name,importance,is_required}`. No company/recruiter owner IDs are accepted from clients.
Deletion with existing applications returns 409; set status to `closed` instead.

Resume analysis corrections use the exact `ResumeOutput` schema in OpenAPI. Uploads
are multipart field `file`. Upload success can precede AI completion; poll analysis
while status is pending. A missing Groq key returns a readable `unavailable` analysis
state without disabling resume download, application submission or job search.
