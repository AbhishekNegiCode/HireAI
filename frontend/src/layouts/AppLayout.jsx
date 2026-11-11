import { useState } from "react";
import { NavLink, Outlet, Link, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  BriefcaseBusiness,
  FileText,
  Bookmark,
  UserRound,
  Sparkles,
  Building2,
  Users,
  ShieldCheck,
  LogOut,
  Menu,
  ChevronRight,
  ArrowUpRight,
  Search,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../components/UI";
import { errorMessage } from "../services/api";
const menus = {
  candidate: [
    ["/", "Overview", LayoutDashboard],
    ["/jobs", "Find jobs", BriefcaseBusiness],
    ["/recommendations", "AI matches", Sparkles],
    ["/applications", "Applications", FileText],
    ["/saved", "Saved jobs", Bookmark],
    ["/resume", "My resume", FileText],
    ["/profile", "My profile", UserRound],
  ],
  recruiter: [
    ["/", "Overview", LayoutDashboard],
    ["/manage-jobs", "Job postings", BriefcaseBusiness],
    ["/company", "Company profile", Building2],
  ],
  admin: [
    ["/", "Overview", LayoutDashboard],
    ["/admin/users", "Users", Users],
    ["/admin/jobs", "Job moderation", BriefcaseBusiness],
    ["/admin/companies", "Companies", Building2],
    ["/admin/applications", "Applications", FileText],
    ["/admin/reports", "Content reports", ShieldCheck],
  ],
};
export default function AppLayout() {
  const { user, logout } = useAuth(),
    [open, setOpen] = useState(false),
    notify = useToast(),
    navigate = useNavigate();
  return (
    <div className="app-shell">
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <Link className="brand" to="/">
          <span className="brand-mark">
            h<span>✦</span>
          </span>
          hire<span className="brand-ai">AI</span>
        </Link>
        <div className="workspace-label">
          {user.role === "candidate"
            ? "YOUR WORKSPACE"
            : user.role === "recruiter"
              ? "RECRUITER WORKSPACE"
              : "ADMINISTRATION"}
        </div>
        <nav>
          {menus[user.role].map(([to, label, Icon]) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                isActive ? "nav-item active" : "nav-item"
              }
            >
              <Icon size={19} />
              {label}
              {label === "AI matches" && <span className="tiny-label">AI</span>}
            </NavLink>
          ))}
        </nav>
        {user.role === "candidate" && (
          <div className="sidebar-tip">
            <span className="tip-icon">
              <Sparkles size={18} />
            </span>
            <h4>
              A little insight.
              <br />A bigger opportunity.
            </h4>
            <p>Let your experience guide your next move.</p>
            <Link to="/resume">
              Analyze your resume <ArrowUpRight size={15} />
            </Link>
          </div>
        )}
        <div className="sidebar-bottom">
          <span className="avatar">
            {user.full_name
              .split(" ")
              .map((s) => s[0])
              .slice(0, 2)
              .join("")}
          </span>
          <div>
            <strong>{user.full_name}</strong>
            <small>{user.role} account</small>
          </div>
          <button
            title="Sign out"
            aria-label="Sign out"
            onClick={async () => {
              try {
                await logout();
                navigate("/login");
              } catch (e) {
                notify(errorMessage(e), "error");
              }
            }}
          >
            <LogOut size={17} />
          </button>
        </div>
      </aside>
      {open && (
        <div className="sidebar-overlay" onClick={() => setOpen(false)} />
      )}
      <div className="workspace">
        <header className="topbar">
          <div>
            <button
              className="mobile-menu"
              aria-label="Open menu"
              onClick={() => setOpen(!open)}
            >
              <Menu size={22} />
            </button>
            <span className="breadcrumb">
              Workspace <ChevronRight size={14} />{" "}
              <span>
                {user.role === "candidate"
                  ? "Your career, in motion"
                  : user.role === "recruiter"
                    ? "Find your next great hire"
                    : "Platform management"}
              </span>
            </span>
          </div>
          <div className="topbar-right">
            {user.role === "candidate" && (
              <Link to="/jobs">
                <Search size={16} />
                <span>Explore opportunities</span>
              </Link>
            )}
            <span className="live-dot" /> <span>HireAI workspace</span>
          </div>
        </header>
        <main>
          <Outlet />
        </main>
        <footer>
          Thoughtful matches. Meaningful careers.
          <span>HireAI · Recruitment, reimagined</span>
        </footer>
      </div>
    </div>
  );
}
