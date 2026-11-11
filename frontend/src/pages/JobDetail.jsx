import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  MapPin,
  BriefcaseBusiness,
  Clock3,
  Sparkles,
  Bookmark,
  Flag,
} from "lucide-react";
import { useResource } from "../hooks/useResource";
import { useAuth } from "../context/AuthContext";
import { api, errorMessage } from "../services/api";
import {
  PageHeader,
  Button,
  Field,
  Loading,
  ErrorState,
  Badge,
  Modal,
  useToast,
} from "../components/UI";
import { salary } from "../components/JobCard";
export default function JobDetail() {
  const { id } = useParams(),
    { user } = useAuth(),
    { data: job, loading, error, reload } = useResource(`/jobs/${id}`),
    [apply, setApply] = useState(false),
    [report, setReport] = useState(false),
    [gap, setGap] = useState(null),
    [busy, setBusy] = useState(false),
    notify = useToast();
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post("/applications", {
        job_id: Number(id),
        cover_letter: new FormData(e.currentTarget).get("cover_letter"),
      });
      notify("Application submitted. Your next chapter is underway.");
      setApply(false);
    } catch (e) {
      notify(errorMessage(e), "error");
    } finally {
      setBusy(false);
    }
  }
  async function action(fn) {
    try {
      await fn();
    } catch (e) {
      notify(errorMessage(e), "error");
    }
  }
  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} retry={reload} />;
  return (
    <>
      <Link className="back-link" to="/jobs">
        <ArrowLeft size={16} /> Back to opportunities
      </Link>
      <div className="job-detail-header">
        <span className={`company-icon large color-${job.company_id % 5}`}>
          {job.company.company_name[0]}
        </span>
        <PageHeader
          eyebrow={job.company.company_name}
          title={job.title}
          description={`${job.location} · ${job.work_mode} · ${job.employment_type}`}
        >
          <Badge tone={job.status === "active" ? "green" : ""}>
            {job.status}
          </Badge>
        </PageHeader>
      </div>
      <div className="detail-columns">
        <div>
          <section className="panel">
            <h2>About the opportunity</h2>
            <p className="prose">{job.description}</p>
            <h2>What you’ll do</h2>
            <p className="prose">
              {job.responsibilities || "See the role description for details."}
            </p>
            <h2>Skills you’ll bring</h2>
            <div className="job-tags">
              {job.skills.map((s) => (
                <Badge key={s.name}>
                  {s.name} {!s.is_required && "· optional"}
                </Badge>
              ))}
            </div>
          </section>
          <section className="panel">
            <h2>Meet {job.company.company_name}</h2>
            <p className="prose">{job.company.description}</p>
            <div className="job-meta">
              <span>{job.company.industry}</span>
              <span>{job.company.company_size} people</span>
            </div>
            {job.company.website && (
              <a
                className="text-link"
                href={job.company.website}
                target="_blank"
                rel="noreferrer"
              >
                Visit company website ↗
              </a>
            )}
          </section>
          {gap && (
            <section className="panel">
              <h2>
                <Sparkles size={20} /> Your skill roadmap
              </h2>
              <p>{gap.explanation.text}</p>
              {gap.explanation.missing_skills.length ? (
                gap.explanation.missing_skills.map((s) => (
                  <div className="roadmap-item" key={s.name}>
                    <div>
                      <strong>{s.name}</strong>
                      <Badge tone={s.required ? "violet" : ""}>
                        {s.required ? "Required" : "Optional"} · priority{" "}
                        {s.importance}/5
                      </Badge>
                    </div>
                    <p>{s.reason}</p>
                    <p>{s.roadmap}</p>
                  </div>
                ))
              ) : (
                <p className="notice">
                  Your profile includes every skill listed in this posting.
                </p>
              )}
            </section>
          )}
        </div>
        <aside>
          <section className="panel job-summary">
            <h3>The essentials</h3>
            <dl>
              <dt>Annual salary</dt>
              <dd>
                {salary(job.salary_min)} – {salary(job.salary_max)}
              </dd>
              <dt>Experience</dt>
              <dd>
                {job.experience_min}–{job.experience_max} years
              </dd>
              <dt>Workplace</dt>
              <dd>
                {job.work_mode} · {job.location}
              </dd>
              <dt>Apply before</dt>
              <dd>{job.application_deadline || "Open until filled"}</dd>
            </dl>
            {user.role === "candidate" && (
              <>
                <Button
                  disabled={
                    job.status !== "active" ||
                    (job.application_deadline &&
                      job.application_deadline <
                        new Date().toISOString().slice(0, 10))
                  }
                  onClick={() => setApply(true)}
                >
                  Apply for this role
                </Button>
                <Button
                  variant="secondary"
                  onClick={() =>
                    action(async () => {
                      await api.post(`/candidates/saved-jobs/${id}`);
                      notify("Job saved");
                    })
                  }
                >
                  <Bookmark size={16} /> Save for later
                </Button>
                <Button
                  variant="soft"
                  onClick={() =>
                    action(async () => {
                      const { data } = await api.post(`/ai/skill-gap/${id}`);
                      setGap(data);
                    })
                  }
                >
                  <Sparkles size={16} /> Explore my skill gap
                </Button>
              </>
            )}
          </section>
          <button className="report-button" onClick={() => setReport(true)}>
            <Flag size={14} /> Report this posting
          </button>
        </aside>
      </div>
      {apply && (
        <Modal title="Make your next move" onClose={() => setApply(false)}>
          <form onSubmit={submit}>
            <p>
              Your current resume will be attached to this application. Review
              it in your resume workspace before submitting.
            </p>
            <Field label="Cover letter (optional)">
              <textarea
                name="cover_letter"
                rows="6"
                maxLength="10000"
                placeholder="Tell them why this opportunity speaks to you…"
              />
            </Field>
            <Button loading={busy} type="submit">
              Submit application
            </Button>
          </form>
        </Modal>
      )}
      {report && (
        <Modal title="Report a posting" onClose={() => setReport(false)}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const reason = new FormData(e.currentTarget).get("reason");
              action(async () => {
                await api.post(`/jobs/${id}/report`, { reason });
                notify("Report sent to the moderation team");
                setReport(false);
              });
            }}
          >
            <Field label="What should our team review?">
              <textarea name="reason" required minLength="10" rows="4" />
            </Field>
            <Button type="submit">Send report</Button>
          </form>
        </Modal>
      )}
    </>
  );
}
