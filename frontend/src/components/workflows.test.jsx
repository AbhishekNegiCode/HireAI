import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import JobCard from "./JobCard";
import { ToastProvider } from "./UI";
import Auth from "../pages/Auth";
import { api } from "../services/api";
const authenticate = vi.hoisted(() => vi.fn());
vi.mock("../services/api", () => ({
  api: { post: vi.fn(), delete: vi.fn() },
  errorMessage: () => "Request failed",
}));
vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({ authenticate }),
}));
const job = {
  job_id: 1,
  company_id: 1,
  title: "Python Engineer",
  company: { company_name: "Orbit Labs", industry: "Technology" },
  location: "Bengaluru",
  employment_type: "Full-time",
  work_mode: "Remote",
  skills: [{ name: "Python" }],
  salary_min: 600000,
  salary_max: 1200000,
  posted_at: "2026-11-10",
};
function mount(ui) {
  return render(
    <MemoryRouter>
      <ToastProvider>{ui}</ToastProvider>
    </MemoryRouter>,
  );
}
beforeEach(() => vi.clearAllMocks());
describe("Candidate actions", () => {
  it("saves the selected job through the API", async () => {
    api.post.mockResolvedValue({});
    mount(<JobCard job={job} match={80} />);
    fireEvent.click(screen.getByRole("button", { name: "Save job" }));
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith("/candidates/saved-jobs/1"),
    );
    expect(await screen.findByText("Job saved")).toBeInTheDocument();
    expect(screen.getByText("80% match")).toBeInTheDocument();
  });
  it("removes saved jobs and refreshes the list", async () => {
    api.delete.mockResolvedValue({});
    const onSaved = vi.fn();
    mount(<JobCard job={job} saved onSaved={onSaved} />);
    fireEvent.click(screen.getByRole("button", { name: "Unsave job" }));
    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    expect(api.delete).toHaveBeenCalledWith("/candidates/saved-jobs/1");
  });
  it("shows action failures", async () => {
    api.post.mockRejectedValue(new Error());
    mount(<JobCard job={job} />);
    fireEvent.click(screen.getByRole("button", { name: "Save job" }));
    expect(await screen.findByText("Request failed")).toBeInTheDocument();
  });
  it("submits email and password to authentication", async () => {
    authenticate.mockResolvedValue({ role: "candidate" });
    mount(<Auth />);
    fireEvent.change(screen.getByLabelText("Email address"), {
      target: { value: "maya@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "password-long" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Sign in/ }));
    await waitFor(() =>
      expect(authenticate).toHaveBeenCalledWith("login", {
        email: "maya@example.com",
        password: "password-long",
      }),
    );
  });
  it("does not expose admin registration", () => {
    mount(<Auth register />);
    expect(screen.getByRole("combobox").options).toHaveLength(2);
    expect(
      screen.queryByRole("option", { name: /admin/i }),
    ).not.toBeInTheDocument();
  });
});
