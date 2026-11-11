import { useState } from "react";
import {
  Search,
  SlidersHorizontal,
  ArrowLeft,
  ArrowRight,
  Sparkles,
  RefreshCw,
} from "lucide-react";
import { useResource } from "../hooks/useResource";
import {
  PageHeader,
  Button,
  Field,
  Loading,
  ErrorState,
  Empty,
  Badge,
  useToast,
} from "../components/UI";
import JobCard from "../components/JobCard";
import { api, errorMessage } from "../services/api";
export default function Jobs() {
  const [params, setParams] = useState({ page: 1 }),
    [filters, setFilters] = useState(false);
  const query = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== ""),
  );
  const { data, loading, error, reload } = useResource(`/jobs?${query}`);
  function search(e) {
    e.preventDefault();
    setParams({
      ...Object.fromEntries(new FormData(e.currentTarget)),
      page: 1,
    });
  }
  return (
    <>
      <PageHeader
        eyebrow="THE NEXT CHAPTER"
        title="Find your kind of work."
        description="Good opportunities begin with a little exploration."
      />
      <form className="search-panel" onSubmit={search}>
        <div className="search-row">
          <div className="search-input">
            <Search size={20} />
            <input
              aria-label="Search jobs"
              name="q"
              placeholder="Job title or company"
            />
          </div>
          <Button
            type="button"
            variant="secondary"
            onClick={() => setFilters(!filters)}
          >
            <SlidersHorizontal size={17} /> Filters
          </Button>
          <Button type="submit">
            Find jobs <ArrowRight size={16} />
          </Button>
        </div>
        <div className={`filter-grid ${filters ? "expanded" : ""}`}>
          <Field
            label="Location"
            name="location"
            placeholder="e.g. Bengaluru"
          />
          <Field label="Company" name="company" placeholder="Company name" />
          <Field
            label="Required skill"
            name="skill"
            placeholder="e.g. Python"
          />
          <Field label="Workplace">
            <select name="work_mode">
              <option value="">All workplaces</option>
              {["Remote", "Hybrid", "On-site"].map((v) => (
                <option key={v}>{v}</option>
              ))}
            </select>
          </Field>
          <Field label="Job type">
            <select name="employment_type">
              <option value="">All types</option>
              {["Full-time", "Part-time", "Contract", "Internship"].map((v) => (
                <option key={v}>{v}</option>
              ))}
            </select>
          </Field>
          <Field
            label="Your experience (years)"
            name="experience"
            type="number"
            min="0"
            step="0.5"
          />
          <Field
            label="Minimum annual salary (₹)"
            name="salary"
            type="number"
            min="0"
          />
          <Field label="Sort by">
            <select name="sort">
              <option value="newest">Newest first</option>
              <option value="relevance">Search relevance</option>
            </select>
          </Field>
        </div>
      </form>
      <div className="section-heading">
        <h2>
          {data?.total ?? "…"}{" "}
          {data?.total === 1 ? "opportunity" : "opportunities"} to explore
        </h2>
        <span className="muted">A role for your next move</span>
      </div>
      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorState message={error} retry={reload} />
      ) : data.items.length ? (
        <div className="job-grid three">
          {data.items.map((j) => (
            <JobCard key={j.job_id} job={j} />
          ))}
        </div>
      ) : (
        <Empty
          title="No matches for these filters"
          description="Try another title, location or skill."
        />
      )}
      {data && (
        <div className="pagination">
          <Button
            variant="secondary"
            disabled={params.page <= 1}
            onClick={() => setParams({ ...params, page: params.page - 1 })}
          >
            <ArrowLeft size={15} /> Previous
          </Button>
          <span>
            Page {params.page} of{" "}
            {Math.max(1, Math.ceil(data.total / data.page_size))}
          </span>
          <Button
            variant="secondary"
            disabled={params.page * data.page_size >= data.total}
            onClick={() => setParams({ ...params, page: params.page + 1 })}
          >
            Next <ArrowRight size={15} />
          </Button>
        </div>
      )}
    </>
  );
}
export function Saved() {
  const { data, loading, error, reload } = useResource(
    "/candidates/saved-jobs",
  );
  return (
    <>
      <PageHeader
        eyebrow="KEEP YOUR OPTIONS OPEN"
        title="Good possibilities, saved."
        description="A little collection of what could come next."
      />
      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorState message={error} retry={reload} />
      ) : data.length ? (
        <div className="job-grid three">
          {data.map((j) => (
            <JobCard key={j.job_id} job={j} saved onSaved={reload} />
          ))}
        </div>
      ) : (
        <Empty
          title="Start your shortlist"
          description="Save roles while exploring jobs to come back to them later."
        />
      )}
    </>
  );
}
export function Recommendations() {
  const { data, loading, error, reload } = useResource("/ai/recommendations"),
    notify = useToast();
  return (
    <>
      <PageHeader
        eyebrow="A LITTLE INTELLIGENCE, A LOT OF POSSIBILITY"
        title="Opportunities that connect."
        description="Skill alignment, experience and semantic similarity—all in one thoughtful match."
      >
        <Button variant="secondary" onClick={reload}>
          <RefreshCw size={16} /> Refresh matches
        </Button>
      </PageHeader>
      <div className="notice">
        <Sparkles size={20} />
        <span>
          Compatibility is a starting point, not a hiring prediction.{" "}
          {data?.some((r) => !r.explanation.semantic_available) &&
            "Semantic matching is unavailable for some roles; those scores use skills, experience and location with adjusted weights."}
        </span>
      </div>
      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorState message={error} retry={reload} />
      ) : data.length ? (
        <div className="job-grid three">
          {data.map((r) => (
            <div className="recommendation-wrap" key={r.job.job_id}>
              <JobCard job={r.job} match={r.overall_score} />
              <div className="match-detail">
                <p>{r.explanation.text}</p>
                <div className="score-bars">
                  {[
                    ["Skills", r.skill_match_score],
                    ["Meaning", r.semantic_match_score],
                    ["Experience", r.experience_score],
                    ["Location", r.location_score],
                  ].map(([label, value]) => (
                    <div key={label}>
                      <span>{label}</span>
                      <div>
                        <i style={{ width: `${value ?? 0}%` }} />
                      </div>
                      <strong>
                        {value === null ? "N/A" : `${Math.round(value)}%`}
                      </strong>
                    </div>
                  ))}
                </div>
                <div className="job-tags">
                  {r.explanation.matching_skills.map((s) => (
                    <Badge tone="green" key={s}>
                      {s}
                    </Badge>
                  ))}
                </div>
                {r.explanation.missing_skills.length > 0 && (
                  <p className="muted">
                    To explore:{" "}
                    {r.explanation.missing_skills
                      .map((s) => `${s.name}${s.required ? "" : " (optional)"}`)
                      .join(", ")}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <Empty
          title="No new matches right now"
          description="Update your skills or check back as new opportunities arrive."
        />
      )}
    </>
  );
}
