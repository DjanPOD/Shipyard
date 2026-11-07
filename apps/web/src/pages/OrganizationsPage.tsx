import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/useAuth";
import {
  ApiError,
  createOrganization,
  fetchOrganizations,
  type Organization,
} from "../lib/api";

type ListState =
  | { status: "loading" }
  | { status: "success"; organizations: Organization[] }
  | { status: "error"; message: string };

export function OrganizationsPage() {
  const { session, logout } = useAuth();
  const navigate = useNavigate();
  const token = session?.accessToken;

  const [listState, setListState] = useState<ListState>({
    status: "loading",
  });

  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");

  useEffect(() => {
    if (!token) return;

    let ignore = false;

    async function loadOrganizations(accessToken: string) {
      try {
        const organizations = await fetchOrganizations(accessToken);

        if (!ignore) {
          setListState({ status: "success", organizations });
        }
      } catch (error) {
        if (ignore) return;

        if (error instanceof ApiError && error.status === 401) {
          logout();
          return;
        }

        setListState({
          status: "error",
          message:
            error instanceof Error
              ? error.message
              : "Unable to load organizations.",
        });
      }
    }

    void loadOrganizations(token);

    return () => {
      ignore = true;
    };
  }, [token, logout]);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!token) return;

    setCreating(true);
    setCreateError("");

    try {
      const organization = await createOrganization(token, name.trim());
      navigate(`/organizations/${organization.id}`);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        logout();
        return;
      }

      setCreateError(
        error instanceof Error
          ? error.message
          : "Unable to create organization.",
      );
    } finally {
      setCreating(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="auth-card workspace-card">
        <Link to="/dashboard">Back to dashboard</Link>

        <p className="eyebrow">Your teams</p>
        <h1>Organizations</h1>

        <section aria-labelledby="create-organization-heading">
          <h2 id="create-organization-heading">Create an organization</h2>

          <form onSubmit={handleCreate}>
            <fieldset disabled={creating}>
              <label htmlFor="organization-name">
                Organization name
                <input
                  id="organization-name"
                  name="name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  maxLength={100}
                  required
                />
              </label>

              {createError && (
                <p role="alert" className="error">
                  {createError}
                </p>
              )}

              <button type="submit" disabled={!name.trim()}>
                {creating ? "Creating…" : "Create organization"}
              </button>
            </fieldset>
          </form>
        </section>

        <section aria-labelledby="organizations-heading">
          <h2 id="organizations-heading">Your organizations</h2>

          {listState.status === "loading" && (
            <p role="status">Loading organizations…</p>
          )}

          {listState.status === "error" && (
            <p role="alert" className="error">
              {listState.message}
            </p>
          )}

          {listState.status === "success" &&
            (listState.organizations.length === 0 ? (
              <p>You do not belong to any organizations yet.</p>
            ) : (
              <ul className="organization-list">
                {listState.organizations.map((organization) => (
                  <li key={organization.id}>
                    <Link to={`/organizations/${organization.id}`}>
                      {organization.name}
                    </Link>
                    <span className="role-badge">
                      {organization.role}
                    </span>
                  </li>
                ))}
              </ul>
            ))}
        </section>
      </section>
    </main>
  );
}