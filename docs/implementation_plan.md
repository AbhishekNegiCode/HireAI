# HireAI implementation plan

1. Model the relational domain before implementation: users, role profiles, companies, skills, jobs, resumes, analyses, embeddings, applications, history, saved jobs, recommendations and reports. Record relationships and deletion rules.
2. Build typed SQLAlchemy models, PostgreSQL/pgvector migration, audit trigger, analytics view and seed/admin CLIs.
3. Implement cookie JWT sessions with CSRF, password hashing, role/ownership dependencies and validated API inputs.
4. Implement candidate profiles, private resume storage, job search, applications and recruiter/company workflows; expose live aggregates and admin moderation.
5. Integrate validated LangChain/Groq extraction and BGE embeddings; implement SQL/pgvector hybrid scoring and deterministic skill-gap explanations. Expose missing-service states.
6. Build a responsive React application with shared navigation, forms, cards, tables, analytics, notifications and functional workflows for each role.
7. Add PostgreSQL integration tests and frontend behavior tests; run migrations, seed, build, servers and browser checks as environment permits.
8. Finish DBMS examples, API and architecture documentation, Docker deployment and reproducible setup instructions. Record verification limits honestly.
