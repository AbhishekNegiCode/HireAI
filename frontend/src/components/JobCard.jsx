import { Link } from "react-router-dom";
import { MapPin, Clock3, Bookmark, ArrowUpRight } from "lucide-react";
import { Badge, useToast } from "./UI";
import { api, errorMessage } from "../services/api";
export const salary = (value) =>
  value
    ? `₹${(value / 100000).toLocaleString("en-IN", { maximumFractionDigits: 1 })}L`
    : "Not disclosed";
export default function JobCard({ job, match, onSaved, saved = false }) {
  const notify = useToast();
  return (
    <article className="job-card">
      <div className="job-card-top">
        <div className={`company-icon color-${job.company_id % 5}`}>
          {job.company.company_name
            .split(" ")
            .map((s) => s[0])
            .slice(0, 2)
            .join("")}
        </div>
        <div>
          <span className="company-name">{job.company.company_name}</span>
          <small>{job.company.industry}</small>
        </div>
        <button
          className={`save-button ${saved ? "saved" : ""}`}
          aria-label={saved ? "Unsave job" : "Save job"}
          onClick={async () => {
            try {
              await api[saved ? "delete" : "post"](
                `/candidates/saved-jobs/${job.job_id}`,
              );
              notify(saved ? "Job removed" : "Job saved");
              onSaved?.();
            } catch (e) {
              notify(errorMessage(e), "error");
            }
          }}
        >
          <Bookmark size={19} fill={saved ? "currentColor" : "none"} />
        </button>
      </div>
      <Link className="job-title" to={`/jobs/${job.job_id}`}>
        {job.title}
        <ArrowUpRight size={18} />
      </Link>
      <div className="job-meta">
        <span>
          <MapPin size={14} />
          {job.location}
        </span>
        <span>
          <Clock3 size={14} />
          {job.employment_type}
        </span>
      </div>
      <div className="job-tags">
        <Badge>{job.work_mode}</Badge>
        {job.skills.slice(0, 3).map((s) => (
          <Badge key={s.name}>{s.name}</Badge>
        ))}
      </div>
      <div className="job-card-footer">
        <strong>
          {salary(job.salary_min)}
          {job.salary_max > 0 && ` – ${salary(job.salary_max)}`}{" "}
          <small>/ year</small>
        </strong>
        {match !== undefined ? (
          <span className="match-badge">
            <span>✧</span> {Math.round(match)}% match
          </span>
        ) : (
          <span className="posted-date">
            {new Date(job.posted_at).toLocaleDateString("en-IN", {
              day: "numeric",
              month: "short",
            })}
          </span>
        )}
      </div>
    </article>
  );
}
