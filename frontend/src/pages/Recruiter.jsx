import { useState, useEffect } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { Plus, ArrowUpRight, Trash2, Save, Download } from "lucide-react";
import { useResource } from "../hooks/useResource";
import { api, errorMessage } from "../services/api";
import {
  PageHeader,
  Button,
  Field,
  Loading,
  ErrorState,
  Badge,
  Empty,
  Modal,
  useToast,
} from "../components/UI";
export function CompanyProfile() {
  const r = useResource("/recruiter/company"),
    [data, setData] = useState(null),
    [busy, setBusy] = useState(false),
    notify = useToast();
  useEffect(() => {
    if (!r.loading)
      setData(
        r.data || {
          company_name: "",
          description: "",
          website: "",
          industry: "",
          company_size: "",
          location: "",
          logo_url: "",
        },
      );
  }, [r.data, r.loading]);
  return (
    <>
      <PageHeader
        eyebrow="YOUR COMPANY’S STORY"
        title="Introduce your team."
        description="Show candidates what makes your company a great place to grow."
      />
      {r.error ? (
        <ErrorState message={r.error} retry={r.reload} />
      ) : !data ? (
        <Loading />
      ) : (
        <form
          className="panel"
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            try {
              await api.put("/recruiter/company", data);
              notify("Company profile saved");
            } catch (e) {
              notify(errorMessage(e), "error");
            } finally {
              setBusy(false);
            }
          }}
        >
          <CompanyFields data={data} setData={setData} />
          <Button type="submit" loading={busy}>
            Save company profile
          </Button>
        </form>
      )}
    </>
  );
}
export function CompanyFields({ data, setData }) {
  return (
    <>
      <div className="form-grid">
        {[
          ["company_name", "Company name"],
          ["website", "Website"],
          ["industry", "Industry"],
          ["company_size", "Company size"],
          ["location", "Location"],
          ["logo_url", "Logo URL"],
        ].map(([key, label]) => (
          <Field
            key={key}
            label={label}
            required={key === "company_name"}
            value={data[key]}
            onChange={(e) => setData({ ...data, [key]: e.target.value })}
          />
        ))}
      </div>
      <Field label="Company description">
        <textarea
          rows="5"
          value={data.description}
          onChange={(e) => setData({ ...data, description: e.target.value })}
        />
      </Field>
    </>
  );
}
export function ManageJobs() {
  const { data, loading, error, reload } = useResource("/recruiter/jobs"),
    [remove, setRemove] = useState(null),
    notify = useToast();
  async function toggle(j) {
    try {
      await api.put(`/jobs/${j.job_id}`, {
        ...j,
        status: j.status === "active" ? "closed" : "active",
      });
      notify("Job status updated");
      reload();
    } catch (e) {
      notify(errorMessage(e), "error");
    }
  }
  return (
    <>
      <PageHeader
        eyebrow="BUILD YOUR NEXT GREAT TEAM"
        title="Your opportunities."
        description="Create, manage and find the right people for every opening."
      >
        <Link className="button primary" to="/manage-jobs/new">
          <Plus size={17} /> Post a job
        </Link>
      </PageHeader>
      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorState message={error} retry={reload} />
      ) : data.length ? (
        <div className="panel table-wrap">
          <table>
            <thead>
              <tr>
                <th>Opportunity</th>
                <th>Status</th>
                <th>Deadline</th>
                <th>Manage</th>
              </tr>
            </thead>
            <tbody>
              {data.map((j) => (
                <tr key={j.job_id}>
                  <td>
                    <strong>{j.title}</strong>
                    <small>
                      {j.location} · {j.work_mode}
                    </small>
                  </td>
                  <td>
                    <Badge tone={j.status === "active" ? "green" : ""}>
                      {j.status}
                    </Badge>
                    <small>Embedding: {j.embedding_status}</small>
                  </td>
                  <td>{j.application_deadline || "Open-ended"}</td>
                  <td>
                    <div className="inline-actions">
                      <Link
                        className="button secondary"
                        to={`/applicants/${j.job_id}`}
                      >
                        Applicants
                      </Link>
                      <Link
                        className="button ghost"
                        to={`/manage-jobs/${j.job_id}/edit`}
                      >
                        Edit
                      </Link>
                      <Button variant="ghost" onClick={() => toggle(j)}>
                        {j.status === "active" ? "Close" : "Activate"}
                      </Button>
                      <Button
                        variant="danger"
                        aria-label={`Delete ${j.title}`}
                        onClick={() => setRemove(j)}
                      >
                        <Trash2 size={15} />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Empty
          title="Your next great hire starts here"
          description="Create your company profile, then post your first opportunity."
        />
      )}
      {remove && (
        <Modal title="Delete this job?" onClose={() => setRemove(null)}>
          <p>
            Jobs with applications must be closed instead, preserving candidate
            records.
          </p>
          <Button
            variant="danger"
            onClick={async () => {
              try {
                await api.delete(`/jobs/${remove.job_id}`);
                notify("Job deleted");
                setRemove(null);
                reload();
              } catch (e) {
                notify(errorMessage(e), "error");
              }
            }}
          >
            Delete job
          </Button>
        </Modal>
      )}
    </>
  );
}
const blankJob = {
  title: "",
  description: "",
  responsibilities: "",
  employment_type: "Full-time",
  experience_min: 0,
  experience_max: 5,
  salary_min: 0,
  salary_max: 0,
  location: "",
  work_mode: "Remote",
  status: "active",
  application_deadline: "",
  skills: [],
};
export function JobEditor() {
  const { id } = useParams(),
    navigate = useNavigate(),
    [data, setData] = useState(blankJob),
    [required, setRequired] = useState(""),
    [optional, setOptional] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    notify = useToast();
  useEffect(() => {
    if (id)
      api
        .get(`/jobs/${id}`)
        .then(({ data }) => {
          setData({
            ...data,
            application_deadline: data.application_deadline || "",
          });
          setRequired(
            data.skills
              .filter((s) => s.is_required)
              .map((s) => s.name)
              .join(", "),
          );
          setOptional(
            data.skills
              .filter((s) => !s.is_required)
              .map((s) => s.name)
              .join(", "),
          );
        })
        .catch((e) => setError(errorMessage(e)));
  }, [id]);
  function change(e) {
    setData({ ...data, [e.target.name]: e.target.value });
  }
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      const values = {
        ...data,
        application_deadline: data.application_deadline || null,
        skills: [
          ...required
            .split(",")
            .filter((s) => s.trim())
            .map((s) => ({ name: s.trim(), is_required: true, importance: 5 })),
          ...optional
            .split(",")
            .filter((s) => s.trim())
            .map((s) => ({
              name: s.trim(),
              is_required: false,
              importance: 2,
            })),
        ],
      };
      ["experience_min", "experience_max", "salary_min", "salary_max"].forEach(
        (k) => (values[k] = Number(values[k])),
      );
      await api[id ? "put" : "post"](id ? `/jobs/${id}` : "/jobs", values);
      notify(id ? "Job updated" : "Your opportunity is live");
      navigate("/manage-jobs");
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageHeader
        eyebrow="MAKE ROOM FOR SOMEONE GREAT"
        title={id ? "Refine your opportunity." : "Post a new opportunity."}
        description="Clear expectations make better connections."
      />
      {error && <ErrorState message={error} />}
      <form className="panel" onSubmit={submit}>
        <div className="form-grid">
          <Field
            label="Job title"
            name="title"
            value={data.title}
            onChange={change}
            required
            minLength="3"
          />
          <Field
            label="Location"
            name="location"
            value={data.location}
            onChange={change}
            required
          />
          {[
            [
              "employment_type",
              "Employment type",
              ["Full-time", "Part-time", "Contract", "Internship"],
            ],
            ["work_mode", "Workplace", ["Remote", "Hybrid", "On-site"]],
            ["status", "Posting status", ["active", "closed", "draft"]],
          ].map(([key, label, options]) => (
            <Field label={label} key={key}>
              <select name={key} value={data[key]} onChange={change}>
                {options.map((o) => (
                  <option key={o}>{o}</option>
                ))}
              </select>
            </Field>
          ))}
          <Field
            label="Application deadline"
            name="application_deadline"
            type="date"
            value={data.application_deadline}
            onChange={change}
          />
          {[
            ["experience_min", "Minimum experience (years)"],
            ["experience_max", "Maximum experience (years)"],
            ["salary_min", "Minimum annual salary (₹)"],
            ["salary_max", "Maximum annual salary (₹)"],
          ].map(([key, label]) => (
            <Field
              key={key}
              label={label}
              name={key}
              type="number"
              min="0"
              value={data[key]}
              onChange={change}
            />
          ))}
        </div>
        <Field label="About the role">
          <textarea
            name="description"
            value={data.description}
            onChange={change}
            required
            minLength="30"
            rows="6"
          />
        </Field>
        <Field label="Responsibilities">
          <textarea
            name="responsibilities"
            value={data.responsibilities}
            onChange={change}
            rows="4"
          />
        </Field>
        <div className="form-grid">
          <Field
            label="Required skills (comma-separated)"
            value={required}
            onChange={(e) => setRequired(e.target.value)}
          />
          <Field
            label="Optional skills (comma-separated)"
            value={optional}
            onChange={(e) => setOptional(e.target.value)}
          />
        </div>
        <p className="muted">
          Leave skills blank to extract known skill names from the description.
          Embeddings are generated after saving.
        </p>
        <Button type="submit" loading={busy}>
          <Save size={17} /> {id ? "Save changes" : "Create opportunity"}
        </Button>
      </form>
    </>
  );
}
export function Applicants() {
  const { id } = useParams(),
    [query, setQuery] = useState(""),
    [page, setPage] = useState(1),
    { data, loading, error, reload } = useResource(
      `/recruiter/jobs/${id}/applicants?page=${page}&${query}`,
    ),
    [detail, setDetail] = useState(null),
    notify = useToast();
  async function update(a, status) {
    try {
      await api.patch(`/recruiter/applications/${a.application_id}/status`, {
        status,
      });
      notify("Application status updated");
      reload();
    } catch (e) {
      notify(errorMessage(e), "error");
    }
  }
  return (
    <>
      <PageHeader
        eyebrow="PEOPLE BEHIND THE APPLICATIONS"
        title="Meet your next teammate."
        description="Review experience, find strengths and keep candidates moving."
      />
      <form
        className="search-panel search-row"
        onSubmit={(e) => {
          e.preventDefault();
          setPage(1);
          setQuery(
            new URLSearchParams(new FormData(e.currentTarget)).toString(),
          );
        }}
      >
        <Field label="Skill" name="skill" placeholder="e.g. Python" />
        <Field
          label="Minimum experience"
          name="experience"
          type="number"
          min="0"
          defaultValue="0"
        />
        <Button type="submit">Filter applicants</Button>
      </form>
      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorState message={error} retry={reload} />
      ) : data.length ? (
        <div className="panel table-wrap">
          <table>
            <thead>
              <tr>
                <th>Candidate</th>
                <th>Experience</th>
                <th>Skills</th>
                <th>Applied</th>
                <th>Status</th>
                <th>Profile</th>
              </tr>
            </thead>
            <tbody>
              {data.map((a) => (
                <tr key={a.application_id}>
                  <td>
                    <strong>{a.candidate.full_name}</strong>
                    <small>{a.candidate.headline}</small>
                  </td>
                  <td>{a.candidate.total_experience} years</td>
                  <td>
                    <div className="job-tags">
                      {a.candidate.skills.slice(0, 4).map((s) => (
                        <Badge key={s.name}>{s.name}</Badge>
                      ))}
                    </div>
                  </td>
                  <td>{new Date(a.applied_at).toLocaleDateString()}</td>
                  <td>
                    <select
                      aria-label={`Status for ${a.candidate.full_name}`}
                      value={a.status}
                      disabled={["Selected", "Rejected", "Withdrawn"].includes(
                        a.status,
                      )}
                      onChange={(e) => update(a, e.target.value)}
                    >
                      {[
                        "Applied",
                        "Under Review",
                        "Shortlisted",
                        "Interview Scheduled",
                        "Selected",
                        "Rejected",
                        "Withdrawn",
                      ].map((s) => (
                        <option
                          key={s}
                          disabled={s === "Applied" || s === "Withdrawn"}
                        >
                          {s}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <Button variant="secondary" onClick={() => setDetail(a)}>
                      Review
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Empty
          title="No applicants to show"
          description="Applications matching your filters will appear here."
        />
      )}
      <div className="pagination">
        <Button
          variant="secondary"
          disabled={page === 1}
          onClick={() => setPage(page - 1)}
        >
          Previous
        </Button>
        <span>Page {page}</span>
        <Button
          variant="secondary"
          disabled={(data?.length || 0) < 50}
          onClick={() => setPage(page + 1)}
        >
          Next
        </Button>
      </div>
      {detail && (
        <Modal
          title={detail.candidate.full_name}
          onClose={() => setDetail(null)}
        >
          <p>{detail.candidate.headline}</p>
          <p>
            {detail.candidate.email} · {detail.candidate.location}
          </p>
          <p>{detail.candidate.professional_summary}</p>
          <div className="job-tags">
            {detail.candidate.skills.map((s) => (
              <Badge key={s.name}>{s.name}</Badge>
            ))}
          </div>
          <h3>Education</h3>
          {detail.candidate.education.map((e) => (
            <p key={e.education_id}>
              {e.degree} · {e.institution}
            </p>
          ))}
          <h3>Experience</h3>
          {detail.candidate.experience.map((e) => (
            <p key={e.experience_id}>
              {e.title} at {e.company}: {e.description}
            </p>
          ))}
          <h3>Cover letter</h3>
          <p>{detail.cover_letter || "No cover letter attached."}</p>
          <a
            className="button primary"
            href={`/api/resumes/${detail.resume_id}/download`}
          >
            <Download size={16} /> Download submitted resume
          </a>
          <h3>History</h3>
          {detail.history.map((h) => (
            <p key={h.history_id}>
              {h.new_status} · {new Date(h.changed_at).toLocaleString()}
            </p>
          ))}
        </Modal>
      )}
    </>
  );
}
