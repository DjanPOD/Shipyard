import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import { ProtectedRoute } from "./auth/ProtectedRoute";
import { AuthPage } from "./pages/AuthPage";
import { DashboardPage } from "./pages/DashboardPage";
import { OrganizationPage } from "./pages/OrganizationPage";
import { OrganizationsPage } from "./pages/OrganizationsPage";
import { ProjectPage } from "./pages/ProjectPage";

function LoginPage() {
  const location = useLocation();

  const registered =
    (location.state as { registered?: boolean } | null)?.registered === true;

  return (
    <>
      {registered && (
        <p role="status" className="notice">
          Account created. Log in to continue.
        </p>
      )}
      <AuthPage mode="login" />
    </>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/register"
        element={<AuthPage key="register" mode="register" />}
      />

      <Route element={<ProtectedRoute />}>
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/organizations" element={<OrganizationsPage />} />
          <Route path="/organizations/:organizationId" element={<OrganizationPage />} />
          <Route path="/organizations/:organizationId/projects/:projectId" element={<ProjectPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;