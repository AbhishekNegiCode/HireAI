CREATE OR REPLACE FUNCTION audit_application_status() RETURNS trigger AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO application_status_history(application_id, old_status, new_status, changed_by)
    VALUES (NEW.application_id, NULL, NEW.status, NULLIF(current_setting('app.user_id', true), '')::integer);
  ELSIF OLD.status IS DISTINCT FROM NEW.status THEN
    INSERT INTO application_status_history(application_id, old_status, new_status, changed_by)
    VALUES (NEW.application_id, OLD.status, NEW.status, NULLIF(current_setting('app.user_id', true), '')::integer);
    UPDATE applications SET updated_at = CURRENT_TIMESTAMP WHERE application_id = NEW.application_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER application_status_audit AFTER INSERT OR UPDATE OF status ON applications
FOR EACH ROW EXECUTE FUNCTION audit_application_status();

CREATE VIEW job_application_counts AS
SELECT j.job_id, j.title, j.recruiter_id, COUNT(a.application_id) AS applicant_count,
       COUNT(a.application_id) FILTER (WHERE a.status = 'Shortlisted') AS shortlisted_count
FROM jobs j LEFT JOIN applications a ON a.job_id = j.job_id
GROUP BY j.job_id;

CREATE OR REPLACE FUNCTION required_skill_match(candidate integer, target_job integer)
RETURNS numeric AS $$
 SELECT CASE WHEN COUNT(*) = 0 THEN 100
 ELSE 100.0 * COUNT(cs.skill_id) / COUNT(*) END
 FROM job_skills js LEFT JOIN candidate_skills cs
 ON cs.skill_id = js.skill_id AND cs.candidate_id = candidate
 WHERE js.job_id = target_job AND js.is_required;
$$ LANGUAGE SQL STABLE;
