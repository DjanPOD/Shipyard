import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { useAuth } from "../auth/useAuth";
import { ApiError, fetchProject, type Project } from "../lib/api";

type ProjectState =
  | { status: "loading" }
  | { status: "success"; project: Project }
  | { status: "error"; message: string };

export function ProjectPage() {
  const params = useParams();

  const organizationId = Number(params.organizationId);
  const projectId = Number(params.projectId);

  if (
    !Number.isSafeInteger(organizationId) ||
    organizationId <= 0 ||
    !Number.isSafeInteger(projectId) ||
    projectId <= 0
  ) {
    return (
      <main className="app-shell">
        <section className="auth-card">
          <h1>Invalid project URL</h1>
          <Link to="/organizations">Back to organizations</Link>
        </section>
      </main>
    );
  }

  return (
    <ProjectWorkspace
      key={`${organizationId}:${projectId}`}
      organizationId={organizationId}
      projectId={projectId}
    />
  );
}

function ProjectWorkspace({
  organizationId,
  projectId,
}: {
  organizationId: number;
  projectId: number;
}) {
  const { session, logout } = useAuth();
  const token = session?.accessToken;

  const [state, setState] = useState<ProjectState>({
    status: "loading",
  });

  useEffect(() => {
    if (!token) return;

    let ignore = false;

    async function loadProject(accessToken: string) {
      try {
        const project = await fetchProject(
          accessToken,
          organizationId,
          projectId,
        );

        if (!ignore) {
          setState({ status: "success", project });
        }
      } catch (error) {
        if (ignore) return;

        if (error instanceof ApiError && error.status === 401) {
          logout();
          return;
        }

        setState({
          status: "error",
          message:
            error instanceof ApiError && error.status === 404
              ? "Project not found or you do not have access."
              : error instanceof Error
                ? error.message
                : "Unable to load project.",
        });
      }
    }

    void loadProject(token);

    return () => {
      ignore = true;
    };
  }, [token, organizationId, projectId, logout]);

  return (
    <main className="app-shell">
      <section className="auth-card workspace-card">
        <Link to={`/organizations/${organizationId}`}>
          Back to organization
        </Link>

        {state.status === "loading" && (
          <p role="status">Loading project…</p>
        )}

        {state.status === "error" && (
          <>
            <h1>Project unavailable</h1>
            <p role="alert" className="error">
              {state.message}
            </p>
          </>
        )}

        {state.status === "success" && (
          <>
            <p className="eyebrow">Project workspace</p>
            <h1>{state.project.name}</h1>

            <p className="project-description">
              {state.project.description || "No description provided."}
            </p>

            <p className="muted">
              Created{" "}
              {new Date(state.project.created_at).toLocaleDateString()}
            </p>

            <section aria-labelledby="issues-heading">
              <h2 id="issues-heading">Issues</h2>
              <p>Issue tracking and the Kanban board come next.</p>
            </section>
          </>
        )}
      </section>
    </main>
  );
}