import { useState, useEffect } from "react";
import {
  Upload,
  FileText,
  Download,
  Sparkles,
  Trash2,
  RefreshCw,
  Check,
} from "lucide-react";
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
export default function Resume() {
  const resume = useResource("/resumes/me"),
    analysis = useResource("/resumes/me/analysis"),
    [busy, setBusy] = useState(false),
    [edit, setEdit] = useState(null),
    [confirm, setConfirm] = useState(false),
    notify = useToast();
  const refresh = () => {
    resume.reload();
    analysis.reload();
  };
  useEffect(() => {
    if (analysis.data?.status === "pending") {
      const timer = setInterval(() => analysis.reload(), 5000);
      return () => clearInterval(timer);
    }
  }, [analysis.data?.status]);
  async function action(fn) {
    setBusy(true);
    try {
      await fn();
      refresh();
    } catch (e) {
      notify(errorMessage(e), "error");
    } finally {
      setBusy(false);
    }
  }
  const report = analysis.data?.analysis;
  return (
    <>
      <PageHeader
        eyebrow="YOUR EXPERIENCE, UNDERSTOOD"
        title="A clearer picture of your potential."
        description="Upload your resume, discover your strengths, and decide what comes next."
      />
      <section className="panel upload-panel">
        <div className="upload-icon">
          <Upload size={29} />
        </div>
        <h2>
          {resume.data
            ? "Give your resume a refresh"
            : "Let’s start with your story"}
        </h2>
        <p>Upload a text-based PDF or DOCX. Maximum size: 10 MB.</p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const form = new FormData(e.currentTarget);
            action(async () => {
              await api.post("/resumes/upload", form);
              notify("Resume uploaded. Analysis is starting.");
            });
          }}
        >
          <input
            aria-label="Choose resume"
            type="file"
            name="file"
            accept=".pdf,.docx"
            required
          />
          <Button type="submit" loading={busy}>
            <Upload size={16} />
            {resume.data ? "Replace resume" : "Upload resume"}
          </Button>
        </form>
        <small>
          Your resume is private. Recruiters can access only the copy you submit
          to their job.
        </small>
      </section>
      {resume.error && (
        <ErrorState message={resume.error} retry={resume.reload} />
      )}
      {resume.data && (
        <section className="panel resume-file">
          <span className="soft-icon">
            <FileText size={23} />
          </span>
          <div>
            <strong>{resume.data.original_filename}</strong>
            <small>
              Uploaded {new Date(resume.data.uploaded_at).toLocaleDateString()}
            </small>
          </div>
          <Badge>{analysis.data?.status || resume.data.analysis_status}</Badge>
          <a
            className="button secondary"
            href={`/api/resumes/${resume.data.resume_id}/download`}
          >
            <Download size={16} /> Download
          </a>
          <Button variant="danger" onClick={() => setConfirm(true)}>
            <Trash2 size={16} /> Remove
          </Button>
        </section>
      )}
      <section className="panel">
        <div className="section-heading">
          <div>
            <h2>
              <Sparkles size={20} /> Your resume insights
            </h2>
            <p>
              Review AI-extracted information before adding it to your profile.
            </p>
          </div>
          {resume.data && (
            <Button
              variant="secondary"
              loading={busy}
              onClick={() =>
                action(async () => {
                  await api.post("/resumes/me/analyze");
                  notify("Analysis requested");
                })
              }
            >
              <RefreshCw size={15} /> Analyze again
            </Button>
          )}
        </div>
        {analysis.loading ? (
          <Loading />
        ) : analysis.error ? (
          <ErrorState message={analysis.error} retry={analysis.reload} />
        ) : report ? (
          <>
            <div className="notice">
              <Check size={18} />
              <span>
                {analysis.data.semantic_available
                  ? "Semantic embedding is ready."
                  : "Semantic embedding is unavailable; skill-based matching still works."}
              </span>
            </div>
            <p className="prose">{report.professional_summary}</p>
            <div className="form-grid">
              <div>
                <h3>Skills & strengths</h3>
                <div className="job-tags">
                  {[...report.technical_skills, ...report.soft_skills].map(
                    (s) => (
                      <Badge tone="violet" key={s}>
                        {s}
                      </Badge>
                    ),
                  )}
                </div>
              </div>
              <div>
                <h3>Potential directions</h3>
                <div className="job-tags">
                  {report.suggested_roles.map((s) => (
                    <Badge key={s}>{s}</Badge>
                  ))}
                </div>
                <p>{report.total_experience} years of experience</p>
              </div>
            </div>
            <h3>Education</h3>
            {report.education.map((x, i) => (
              <p key={i}>
                {x.degree} · {x.institution} ({x.start_year}–
                {x.end_year || "present"})
              </p>
            ))}
            <h3>Experience</h3>
            {report.work_experience.map((x, i) => (
              <p key={i}>
                {x.title} · {x.company}: {x.description}
              </p>
            ))}
            <h3>Projects</h3>
            {report.projects.map((x, i) => (
              <p key={i}>{x}</p>
            ))}
            <h3>Certifications</h3>
            <p>{report.certifications.join(", ") || "None extracted"}</p>
            <div className="inline-actions">
              <Button
                onClick={() =>
                  action(async () => {
                    const { data } = await api.post(
                      "/resumes/me/analysis/import",
                    );
                    notify(data.message);
                  })
                }
              >
                Add reviewed skills to profile
              </Button>
              <Button
                variant="secondary"
                onClick={() => setEdit(JSON.stringify(report, null, 2))}
              >
                Correct extracted information
              </Button>
            </div>
          </>
        ) : (
          <Empty
            title={
              analysis.data?.status === "pending"
                ? "Your resume is being analyzed"
                : resume.data
                  ? "Your resume is ready to use"
                  : "Your insights start with a resume"
            }
            description={
              analysis.data?.message ||
              "Upload a resume and run analysis to see skills, experience and suggested roles."
            }
          />
        )}
      </section>
      {edit !== null && (
        <Modal title="Correct resume information" onClose={() => setEdit(null)}>
          <p>
            Edit the structured fields below. All changes are validated before
            saving.
          </p>
          <Field label="Resume information (JSON)">
            <textarea
              className="code-editor"
              value={edit}
              onChange={(e) => setEdit(e.target.value)}
              rows="18"
            />
          </Field>
          <Button
            loading={busy}
            onClick={() =>
              action(async () => {
                await api.put("/resumes/me/analysis", JSON.parse(edit));
                notify("Corrections saved");
                setEdit(null);
              })
            }
          >
            Save corrections
          </Button>
        </Modal>
      )}
      {confirm && (
        <Modal title="Remove this resume?" onClose={() => setConfirm(false)}>
          <p>
            It will be removed from your profile. Copies already submitted with
            applications are retained with those applications.
          </p>
          <Button
            variant="danger"
            loading={busy}
            onClick={() =>
              action(async () => {
                const { data } = await api.delete("/resumes/me");
                notify(data.message);
                setConfirm(false);
              })
            }
          >
            Remove resume
          </Button>
        </Modal>
      )}
    </>
  );
}
