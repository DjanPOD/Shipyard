import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { useAuth } from "../auth/useAuth";
import {
  ApiError,
  fetchOrganization,
  type Organization,
} from "../lib/api";

type OrganizationState =
  | { status: "loading" }
  | { status: "success"; organization: Organization }
  | { status: "error"; message: string };

export function OrganizationPage() {
  const { organizationId } = useParams();

  const id = Number(organizationId);

  if (!Number.isSafeInteger(id) || id <= 0) {
    return (
      <main className="app-shell">
        <section className="auth-card">
          <h1>Invalid organization</h1>
          <Link to="/organizations">Back to organizations</Link>
        </section>
      </main>
    );
  }

  return <OrganizationWorkspace key={id} id={id} />;
}

function OrganizationWorkspace({ id }: { id: number }) {
  const { session, logout } = useAuth();
  const token = session?.accessToken;

  const [state, setState] = useState<OrganizationState>({
    status: "loading",
  });

  useEffect(() => {
    if (!token) return;

    let ignore = false;

    async function loadOrganization(accessToken: string) {
      try {
        const organization = await fetchOrganization(accessToken, id);

        if (!ignore) {
          setState({ status: "success", organization });
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
              ? "Organization not found or you do not have access."
              : error instanceof Error
                ? error.message
                : "Unable to load organization.",
        });
      }
    }

    void loadOrganization(token);

    return () => {
      ignore = true;
    };
  }, [id, token, logout]);

  return (
    <main className="app-shell">
      <section className="auth-card workspace-card">
        <Link to="/organizations">Back to organizations</Link>

        {state.status === "loading" && (
          <p role="status">Loading workspace…</p>
        )}

        {state.status === "error" && (
          <>
            <h1>Workspace unavailable</h1>
            <p role="alert" className="error">
              {state.message}
            </p>
          </>
        )}

        {state.status === "success" && (
          <>
            <p className="eyebrow">Organization workspace</p>
            <h1>{state.organization.name}</h1>

            <p>
              Your role:{" "}
              <span className="role-badge">
                {state.organization.role}
              </span>
            </p>

            <p className="muted">
              Created{" "}
              {new Date(
                state.organization.created_at,
              ).toLocaleDateString()}
            </p>

            <section aria-labelledby="projects-heading">
              <h2 id="projects-heading">Projects</h2>
              <p>Project management is coming in the next feature.</p>
            </section>
          </>
        )}
      </section>
    </main>
  );
}