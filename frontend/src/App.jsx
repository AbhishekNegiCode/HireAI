import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ToastProvider, Loading, Empty } from "./components/UI";
import AppLayout from "./layouts/AppLayout";
import Auth from "./pages/Auth";
import Dashboard from "./pages/Dashboard";
import Jobs, { Saved, Recommendations } from "./pages/Jobs";
import JobDetail from "./pages/JobDetail";
import Profile from "./pages/Profile";
import Resume from "./pages/Resume";
import Applications from "./pages/Applications";
import {
  CompanyProfile,
  ManageJobs,
  JobEditor,
  Applicants,
} from "./pages/Recruiter";
import Admin from "./pages/Admin";
function Guard({ roles, children }) {
  const { user, loading } = useAuth();
  if (loading) return <Loading />;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;
  return children;
}
function PublicAuth({ register }) {
  const { user } = useAuth();
  return user ? <Navigate to="/" replace /> : <Auth register={register} />;
}
export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            <Route path="/login" element={<PublicAuth />} />
            <Route path="/register" element={<PublicAuth register />} />
            <Route
              element={
                <Guard>
                  <AppLayout />
                </Guard>
              }
            >
              <Route index element={<Dashboard />} />
              <Route
                path="jobs"
                element={
                  <Guard roles={["candidate"]}>
                    <Jobs />
                  </Guard>
                }
              />
              <Route path="jobs/:id" element={<JobDetail />} />
              {[
                ["profile", Profile],
                ["resume", Resume],
                ["applications", Applications],
                ["saved", Saved],
                ["recommendations", Recommendations],
              ].map(([path, Component]) => (
                <Route
                  key={path}
                  path={path}
                  element={
                    <Guard roles={["candidate"]}>
                      <Component />
                    </Guard>
                  }
                />
              ))}
              {[
                ["company", CompanyProfile],
                ["manage-jobs", ManageJobs],
                ["manage-jobs/new", JobEditor],
                ["manage-jobs/:id/edit", JobEditor],
                ["applicants/:id", Applicants],
              ].map(([path, Component]) => (
                <Route
                  key={path}
                  path={path}
                  element={
                    <Guard roles={["recruiter"]}>
                      <Component />
                    </Guard>
                  }
                />
              ))}
              <Route
                path="admin/:section"
                element={
                  <Guard roles={["admin"]}>
                    <Admin />
                  </Guard>
                }
              />
              <Route
                path="*"
                element={
                  <Empty
                    title="This page doesn’t exist"
                    description="Use the navigation to return to your workspace."
                  />
                }
              />
            </Route>
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
