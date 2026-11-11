-- Development fixture verification. Passwords and DOCX artifacts are generated
-- by the guarded Python CLI, not embedded as plaintext SQL literals.
-- Run from backend: python -m app.cli seed
SELECT role, COUNT(*) FROM users GROUP BY role;
SELECT COUNT(*) AS companies FROM companies;
SELECT COUNT(*) AS jobs FROM jobs;
SELECT COUNT(*) AS skills FROM skills;
SELECT COUNT(*) AS applications FROM applications;
