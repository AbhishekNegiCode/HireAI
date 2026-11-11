import { useState } from "react";
import { Link } from "react-router-dom";
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
export default function Applications() {
  const [page, setPage] = useState(1),
    { data, loading, error, reload } = useResource(
      `/applications/me?page=${page}`,
    ),
    [detail, setDetail] = useState(null),
    [withdraw, setWithdraw] = useState(null),
    notify = useToast();
  return (
    <>
      <PageHeader
        eyebrow="EVERY STEP COUNTS"
        title="Your career, in motion."
        description="Follow your applications from the first hello to the next chapter."
      />
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
                <th>Applied</th>
                <th>Status</th>
                <th>Next steps</th>
              </tr>
            </thead>
            <tbody>
              {data.map((a) => (
                <tr key={a.application_id}>
                  <td>
                    <Link to={`/jobs/${a.job_id}`}>
                      <strong>{a.job.title}</strong>
                    </Link>
                    <small>{a.job.company.company_name}</small>
                  </td>
                  <td>{new Date(a.applied_at).toLocaleDateString()}</td>
                  <td>
                    <Badge
                      tone={
                        ["Shortlisted", "Selected"].includes(a.status)
                          ? "green"
                          : ""
                      }
                    >
                      {a.status}
                    </Badge>
                  </td>
                  <td>
                    <div className="inline-actions">
                      <Button variant="secondary" onClick={() => setDetail(a)}>
                        History
                      </Button>
                      {!["Selected", "Rejected", "Withdrawn"].includes(
                        a.status,
                      ) && (
                        <Button variant="ghost" onClick={() => setWithdraw(a)}>
                          Withdraw
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Empty
          title="Your next move is waiting"
          description="Explore opportunities and submit your first application."
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
        <Modal title="Your application journey" onClose={() => setDetail(null)}>
          <h3>{detail.job.title}</h3>
          <div className="timeline">
            {detail.history.map((h) => (
              <div key={h.history_id}>
                <span />
                <div>
                  <strong>{h.new_status}</strong>
                  <small>{new Date(h.changed_at).toLocaleString()}</small>
                </div>
              </div>
            ))}
          </div>
          <a
            className="button secondary"
            href={`/api/resumes/${detail.resume_id}/download`}
          >
            Download submitted resume
          </a>
        </Modal>
      )}
      {withdraw && (
        <Modal
          title="Withdraw your application?"
          onClose={() => setWithdraw(null)}
        >
          <p>
            This will close your application to {withdraw.job.title}. You cannot
            apply to the same posting again.
          </p>
          <Button
            variant="danger"
            onClick={async () => {
              try {
                await api.patch(
                  `/applications/${withdraw.application_id}/withdraw`,
                );
                notify("Application withdrawn");
                setWithdraw(null);
                reload();
              } catch (e) {
                notify(errorMessage(e), "error");
              }
            }}
          >
            Withdraw application
          </Button>
        </Modal>
      )}
    </>
  );
}
