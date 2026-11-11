import { useState } from "react";
import { useParams } from "react-router-dom";
import { useResource } from "../hooks/useResource";
import { api, errorMessage } from "../services/api";
import {
  PageHeader,
  Button,
  Loading,
  ErrorState,
  Badge,
  Empty,
  Modal,
  useToast,
} from "../components/UI";
import { CompanyFields } from "./Recruiter";
export default function Admin() {
  const { section } = useParams(),
    [page, setPage] = useState(1),
    [company, setCompany] = useState(null),
    r = useResource(`/admin/${section}?page=${page}`),
    notify = useToast();
  async function action(fn) {
    try {
      await fn();
      notify("Changes saved");
      r.reload();
    } catch (e) {
      notify(errorMessage(e), "error");
    }
  }
  return (
    <>
      <PageHeader
        eyebrow="PLATFORM MANAGEMENT"
        title={`${section[0].toUpperCase() + section.slice(1)}.`}
        description="Keep HireAI useful, trustworthy and welcoming."
      />
      {r.loading ? (
        <Loading />
      ) : r.error ? (
        <ErrorState message={r.error} retry={r.reload} />
      ) : !r.data.length ? (
        <Empty title="No records to review" />
      ) : (
        <div className="panel table-wrap">
          <table>
            <thead>
              <tr>
                {(section === "users"
                  ? ["Name", "Email", "Role", "Access"]
                  : section === "jobs"
                    ? ["Job", "Company", "Status", "Moderation"]
                    : section === "companies"
                      ? ["Company", "Industry", "Location", "Manage"]
                      : section === "applications"
                        ? ["Candidate", "Job", "Status", "Applied"]
                        : ["Report", "Job ID", "Reason", "Status", "Review"]
                ).map((t) => (
                  <th key={t}>{t}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {r.data.map((row) =>
                section === "users" ? (
                  <tr key={row.user_id}>
                    <td>{row.full_name}</td>
                    <td>{row.email}</td>
                    <td>
                      <Badge>{row.role}</Badge>
                    </td>
                    <td>
                      <Button
                        disabled={row.role === "admin"}
                        variant={row.is_active ? "danger" : "secondary"}
                        onClick={() =>
                          action(() =>
                            api.patch(`/admin/users/${row.user_id}/status`, {
                              is_active: !row.is_active,
                            }),
                          )
                        }
                      >
                        {row.is_active ? "Suspend" : "Activate"}
                      </Button>
                    </td>
                  </tr>
                ) : section === "jobs" ? (
                  <tr key={row.job_id}>
                    <td>{row.title}</td>
                    <td>{row.company.company_name}</td>
                    <td>
                      <Badge>{row.status}</Badge>
                    </td>
                    <td>
                      <Button
                        variant="secondary"
                        onClick={() =>
                          action(() =>
                            api.put(`/jobs/${row.job_id}`, {
                              ...row,
                              status:
                                row.status === "active" ? "closed" : "active",
                            }),
                          )
                        }
                      >
                        {row.status === "active" ? "Close posting" : "Activate"}
                      </Button>
                    </td>
                  </tr>
                ) : section === "companies" ? (
                  <tr key={row.company_id}>
                    <td>{row.company_name}</td>
                    <td>{row.industry}</td>
                    <td>{row.location}</td>
                    <td>
                      <Button
                        variant="secondary"
                        onClick={() => setCompany(row)}
                      >
                        Edit
                      </Button>
                    </td>
                  </tr>
                ) : section === "applications" ? (
                  <tr key={row.application_id}>
                    <td>{row.candidate.full_name}</td>
                    <td>{row.job.title}</td>
                    <td>
                      <Badge>{row.status}</Badge>
                    </td>
                    <td>{new Date(row.applied_at).toLocaleDateString()}</td>
                  </tr>
                ) : (
                  <tr key={row.report_id}>
                    <td>#{row.report_id}</td>
                    <td>{row.job_id}</td>
                    <td>{row.reason}</td>
                    <td>
                      <Badge>{row.status}</Badge>
                    </td>
                    <td>
                      {row.status === "open" && (
                        <div className="inline-actions">
                          <Button
                            variant="secondary"
                            onClick={() =>
                              action(() =>
                                api.patch(`/admin/reports/${row.report_id}`, {
                                  status: "resolved",
                                }),
                              )
                            }
                          >
                            Resolve
                          </Button>
                          <Button
                            variant="ghost"
                            onClick={() =>
                              action(() =>
                                api.patch(`/admin/reports/${row.report_id}`, {
                                  status: "dismissed",
                                }),
                              )
                            }
                          >
                            Dismiss
                          </Button>
                        </div>
                      )}
                    </td>
                  </tr>
                ),
              )}
            </tbody>
          </table>
        </div>
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
          disabled={(r.data?.length || 0) < 50}
          onClick={() => setPage(page + 1)}
        >
          Next
        </Button>
      </div>
      {company && (
        <Modal title="Edit company" onClose={() => setCompany(null)}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              action(async () => {
                await api.put(
                  `/admin/companies/${company.company_id}`,
                  company,
                );
                setCompany(null);
              });
            }}
          >
            <CompanyFields data={company} setData={setCompany} />
            <Button type="submit">Save company</Button>
          </form>
        </Modal>
      )}
    </>
  );
}
