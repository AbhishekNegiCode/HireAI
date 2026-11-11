import { useEffect, useState } from "react";
import { Plus, Trash2, Save } from "lucide-react";
import { useResource } from "../hooks/useResource";
import { useAuth } from "../context/AuthContext";
import { api, errorMessage } from "../services/api";
import {
  PageHeader,
  Button,
  Field,
  Loading,
  ErrorState,
  useToast,
} from "../components/UI";
export default function Profile() {
  const resource = useResource("/candidates/me"),
    [profile, setProfile] = useState(null),
    [skills, setSkills] = useState(""),
    [busy, setBusy] = useState(false),
    notify = useToast(),
    { user, setUser } = useAuth();
  useEffect(() => {
    if (resource.data) {
      setProfile(resource.data);
      setSkills(resource.data.skills.map((s) => s.name).join(", "));
    }
  }, [resource.data]);
  function change(e) {
    setProfile({ ...profile, [e.target.name]: e.target.value });
  }
  function listChange(list, i, key, value) {
    setProfile({
      ...profile,
      [list]: profile[list].map((item, n) =>
        n === i ? { ...item, [key]: value } : item,
      ),
    });
  }
  async function save(e) {
    e.preventDefault();
    setBusy(true);
    try {
      const clean = {
        ...profile,
        total_experience: Number(profile.total_experience),
        education: profile.education.map((x) => ({
          ...x,
          start_year: Number(x.start_year),
          end_year: x.end_year ? Number(x.end_year) : null,
        })),
        experience: profile.experience.map((x) => ({
          ...x,
          end_date: x.end_date || null,
        })),
      };
      await api.put("/candidates/me", clean);
      await api.put(
        "/candidates/me/skills",
        skills
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean)
          .map(
            (name) =>
              profile.skills.find(
                (s) => s.name.toLowerCase() === name.toLowerCase(),
              ) || { name },
          ),
      );
      setUser({ ...user, full_name: profile.full_name });
      notify("Your profile is up to date");
      resource.reload();
    } catch (e) {
      notify(errorMessage(e), "error");
    } finally {
      setBusy(false);
    }
  }
  if (resource.loading || !profile)
    return resource.error ? (
      <ErrorState message={resource.error} retry={resource.reload} />
    ) : (
      <Loading />
    );
  return (
    <>
      <PageHeader
        eyebrow="TELL YOUR STORY"
        title="More than a resume."
        description="Help the right opportunity find the person behind the skills."
      />
      <form onSubmit={save} className="profile-form">
        <section className="panel">
          <h2>The essentials</h2>
          <div className="form-grid">
            {[
              ["full_name", "Full name"],
              ["headline", "Professional headline"],
              ["phone", "Phone"],
              ["location", "Location"],
              ["total_experience", "Total experience (years)"],
              ["portfolio_url", "Portfolio URL"],
              ["linkedin_url", "LinkedIn URL"],
              ["github_url", "GitHub URL"],
            ].map(([key, label]) => (
              <Field
                key={key}
                label={label}
                name={key}
                value={profile[key]}
                onChange={change}
                type={key === "total_experience" ? "number" : "text"}
                min="0"
                step="0.5"
                required={key === "full_name"}
              />
            ))}
          </div>
          <Field label="Professional summary">
            <textarea
              name="professional_summary"
              rows="4"
              value={profile.professional_summary}
              onChange={change}
            />
          </Field>
          <Field
            label="Your skills (separate with commas)"
            value={skills}
            onChange={(e) => setSkills(e.target.value)}
            placeholder="Python, React, SQL…"
          />
          <small className="muted">
            Skills are stored as individual relational records.
          </small>
        </section>
        {["education", "experience"].map((list) => (
          <section className="panel" key={list}>
            <div className="section-heading">
              <h2>{list === "education" ? "Education" : "Experience"}</h2>
              <Button
                variant="secondary"
                type="button"
                onClick={() =>
                  setProfile({
                    ...profile,
                    [list]: [
                      ...profile[list],
                      list === "education"
                        ? {
                            institution: "",
                            degree: "",
                            start_year: 2020,
                            end_year: "",
                          }
                        : {
                            company: "",
                            title: "",
                            start_date: "",
                            end_date: "",
                            description: "",
                          },
                    ],
                  })
                }
              >
                <Plus size={15} /> Add {list}
              </Button>
            </div>
            {profile[list].map((item, i) => (
              <div className="repeatable-row" key={i}>
                <div className="form-grid">
                  {(list === "education"
                    ? [
                        ["institution", "Institution", "text"],
                        ["degree", "Degree", "text"],
                        ["start_year", "Start year", "number"],
                        ["end_year", "End year (optional)", "number"],
                      ]
                    : [
                        ["company", "Company", "text"],
                        ["title", "Role", "text"],
                        ["start_date", "Start date", "date"],
                        ["end_date", "End date (optional)", "date"],
                        ["description", "Description", "text"],
                      ]
                  ).map(([key, label, type]) => (
                    <Field
                      key={key}
                      label={label}
                      value={item[key] ?? ""}
                      type={type}
                      required={!key.startsWith("end") && key !== "description"}
                      onChange={(e) => listChange(list, i, key, e.target.value)}
                    />
                  ))}
                </div>
                <Button
                  variant="danger"
                  type="button"
                  onClick={() =>
                    setProfile({
                      ...profile,
                      [list]: profile[list].filter((_, n) => n !== i),
                    })
                  }
                >
                  <Trash2 size={15} /> Remove
                </Button>
              </div>
            ))}
          </section>
        ))}
        <Button loading={busy} type="submit">
          <Save size={17} /> Save profile
        </Button>
      </form>
    </>
  );
}
