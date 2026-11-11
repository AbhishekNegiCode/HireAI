import { Link } from "react-router-dom";
import {
  ArrowRight,
  ArrowUpRight,
  Sparkles,
  BriefcaseBusiness,
  Bookmark,
  CheckCircle2,
  FileText,
  Target,
  Upload,
  TrendingUp,
  Users,
  Building2,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { useAuth } from "../context/AuthContext";
import { useResource } from "../hooks/useResource";
import {
  PageHeader,
  Loading,
  ErrorState,
  Badge,
  Empty,
} from "../components/UI";
import JobCard from "../components/JobCard";
function Stat({ label, value, icon: Icon, note }) {
  return (
    <div className="stat-card">
      <div>
        <span>{label}</span>
        <span className="stat-icon">
          <Icon size={19} />
        </span>
      </div>
      <strong>{value ?? 0}</strong>
      <small>{note}</small>
    </div>
  );
}
export function Chart({ data, dataKey = "applications" }) {
  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data}>
          <CartesianGrid
            strokeDasharray="3 3"
            vertical={false}
            stroke="#eeeef3"
          />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11 }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            allowDecimals={false}
            tick={{ fontSize: 11 }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip />
          <Bar dataKey={dataKey} fill="#7663dc" radius={[5, 5, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
export default function Dashboard() {
  const { user } = useAuth();
  const resource = useResource(
    user.role === "candidate"
      ? "/candidates/dashboard"
      : user.role === "recruiter"
        ? "/recruiter/dashboard"
        : "/admin/dashboard",
  );
  return (
    <>
      <PageHeader
        eyebrow={new Date().toLocaleDateString("en-IN", {
          weekday: "long",
          day: "numeric",
          month: "long",
          year: "numeric",
        })}
        title={`Welcome back, ${user.full_name.split(" ")[0]} 👋`}
        description={
          user.role === "candidate"
            ? "Your next chapter starts here. Let’s make it a great one."
            : user.role === "recruiter"
              ? "A clear view of your hiring pipeline."
              : "A clear view of your recruitment platform."
        }
      >
        {user.role === "candidate" ? (
          <Link className="button secondary" to="/profile">
            View my profile <ArrowUpRight size={16} />
          </Link>
        ) : user.role === "recruiter" ? (
          <Link className="button primary" to="/manage-jobs/new">
            Post a job <ArrowRight size={16} />
          </Link>
        ) : null}
      </PageHeader>
      {resource.loading ? (
        <Loading />
      ) : resource.error ? (
        <ErrorState message={resource.error} retry={resource.reload} />
      ) : user.role === "candidate" ? (
        <CandidateDashboard data={resource.data} />
      ) : user.role === "recruiter" ? (
        <RecruiterDashboard data={resource.data} />
      ) : (
        <AdminDashboard data={resource.data} />
      )}
    </>
  );
}
function CandidateDashboard({ data }) {
  const rec = useResource("/ai/recommendations");
  return (
    <>
      <section className="welcome-banner">
        <div>
          <span className="banner-label">
            <Sparkles size={15} /> BUILT AROUND YOUR POTENTIAL
          </span>
          <h2>Your skills. The right opportunity.</h2>
          <p>
            Discover roles that connect what you do best
            <br className="desktop-break" /> with what you want to do next.
          </p>
          <Link to="/recommendations" className="button dark">
            Explore my matches <ArrowRight size={16} />
          </Link>
        </div>
        <div className="orbital-art" aria-hidden="true">
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />
          <div className="orbit-core">
            <Sparkles size={42} />
          </div>
          <div className="orbit-chip chip-one">
            <CheckCircle2 size={16} /> Skills aligned
          </div>
          <div className="orbit-chip chip-two">
            <Target size={17} /> Your next move
          </div>
          <div className="orbit-dot dot-one" />
          <div className="orbit-dot dot-two" />
        </div>
      </section>
      <div className="stats-grid">
        <Stat
          label="Total applications"
          value={data.total_applications}
          icon={BriefcaseBusiness}
          note="Every step is progress"
        />
        <Stat
          label="Shortlisted"
          value={data.shortlisted}
          icon={CheckCircle2}
          note="You’re on their radar"
        />
        <Stat
          label="Saved opportunities"
          value={data.saved_jobs}
          icon={Bookmark}
          note="Great possibilities, kept close"
        />
        <Stat
          label="Profile strength"
          value={`${data.profile_completion}%`}
          icon={TrendingUp}
          note="A fuller picture of you"
        />
      </div>
      <div className="dashboard-columns">
        <div>
          <section>
            <div className="section-heading">
              <div>
                <h2>
                  <Sparkles size={20} /> Made for your next move{" "}
                  <Badge tone="violet">AI matches</Badge>
                </h2>
                <p>Opportunities aligned with your skills and experience.</p>
              </div>
              <Link to="/recommendations">
                View all <ArrowRight size={15} />
              </Link>
            </div>
            {rec.loading ? (
              <Loading />
            ) : rec.error ? (
              <ErrorState message={rec.error} retry={rec.reload} />
            ) : rec.data.length ? (
              <div className="job-grid">
                {rec.data.slice(0, 4).map((r) => (
                  <JobCard
                    key={r.job.job_id}
                    job={r.job}
                    match={r.overall_score}
                  />
                ))}
              </div>
            ) : (
              <Empty
                title="You’re all caught up"
                description="New matches will appear as jobs are posted."
              />
            )}
          </section>
          <section>
            <div className="section-heading">
              <div>
                <h2>Fresh opportunities</h2>
                <p>New roles worth a closer look.</p>
              </div>
              <Link to="/jobs">
                Browse jobs <ArrowRight size={15} />
              </Link>
            </div>
            <div className="recent-jobs">
              {data.recent_jobs.map((j) => (
                <Link to={`/jobs/${j.job_id}`} key={j.job_id}>
                  <span className={`company-icon color-${j.company_id % 5}`}>
                    {j.company.company_name[0]}
                  </span>
                  <div>
                    <strong>{j.title}</strong>
                    <small>
                      {j.company.company_name} · {j.location}
                    </small>
                  </div>
                  <Badge>{j.work_mode}</Badge>
                  <ArrowUpRight size={18} />
                </Link>
              ))}
            </div>
          </section>
        </div>
        <aside className="dashboard-aside">
          <section className="panel profile-panel">
            <div className="section-heading">
              <h3>Your profile, at a glance</h3>
              <UserIcon />
            </div>
            <div
              className="progress-circle"
              style={{ "--progress": `${data.profile_completion}%` }}
            >
              <div>
                <strong>{data.profile_completion}%</strong>
                <span>complete</span>
              </div>
            </div>
            <h3>Give your story the full picture</h3>
            <p>
              A complete profile helps us find opportunities that feel right for
              you.
            </p>
            <Link className="button secondary" to="/profile">
              Complete my profile <ArrowRight size={15} />
            </Link>
          </section>
          <section className="panel resume-panel">
            <span className="soft-icon">
              <FileText size={22} />
            </span>
            <h3>A resume with more potential</h3>
            <p>
              Turn your experience into insights. Find your strengths and see
              what to learn next.
            </p>
            <div className="resume-state">
              <span
                className={`status-dot ${data.resume_status === "ready" ? "green" : ""}`}
              />
              {data.resume_status.replaceAll("_", " ")}
            </div>
            <Link to="/resume">
              Open resume workspace <ArrowUpRight size={15} />
            </Link>
          </section>
          <div className="quiet-note">
            <span>✧</span>
            <p>
              Your match score is a guide to compatibility, never a measure of
              your potential.
            </p>
          </div>
        </aside>
      </div>
    </>
  );
}
function UserIcon() {
  return <span className="subtle-dot">✦</span>;
}
function RecruiterDashboard({ data }) {
  return (
    <>
      <div className="stats-grid">
        <Stat
          label="Active jobs"
          value={data.active_jobs}
          icon={BriefcaseBusiness}
        />
        <Stat
          label="Applications"
          value={data.total_applications}
          icon={FileText}
        />
        <Stat
          label="Shortlisted"
          value={data.shortlisted}
          icon={CheckCircle2}
        />
        <Stat label="Interviews" value={data.interviews} icon={Users} />
      </div>
      <section className="panel">
        <h2>Applications by opening</h2>
        <Chart data={data.job_statistics} />
      </section>
      <section className="panel">
        <h2>Recent applications</h2>
        {data.recent_applications.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Received</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_applications.map((a) => (
                  <tr key={a.application_id}>
                    <td>
                      <Link to={`/applicants/${a.job_id}`}>
                        {a.candidate.full_name}
                      </Link>
                    </td>
                    <td>{a.job.title}</td>
                    <td>
                      <Badge>{a.status}</Badge>
                    </td>
                    <td>{new Date(a.applied_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty
            title="Your hiring story starts here"
            description="Post a job to start receiving applications."
          />
        )}
      </section>
    </>
  );
}
function AdminDashboard({ data }) {
  return (
    <>
      <div className="stats-grid">
        <Stat
          label="Users"
          value={data.users}
          icon={Users}
          note={`${data.candidate || 0} candidates · ${data.recruiter || 0} recruiters`}
        />
        <Stat label="Companies" value={data.companies} icon={Building2} />
        <Stat
          label="Jobs"
          value={data.jobs}
          icon={BriefcaseBusiness}
          note={`${data.active_jobs} active`}
        />
        <Stat label="Applications" value={data.applications} icon={FileText} />
      </div>
      <section className="panel">
        <h2>Job posting activity</h2>
        <Chart data={data.posting_analytics} dataKey="jobs" />
      </section>
      <section className="panel">
        <h2>Recent registrations</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_registrations.map((u) => (
                <tr key={u.user_id}>
                  <td>{u.full_name}</td>
                  <td>{u.email}</td>
                  <td>
                    <Badge>{u.role}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
