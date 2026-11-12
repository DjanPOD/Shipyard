import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/useAuth";
import {
  ApiError,
  createProject,
  fetchProjects,
  type Organization,
  type Project,
} from "../lib/api";

type Props = {
  organizationId: number;
  currentRole: Organization["role"];
};

type ProjectState =
  | { status: "loading" }
  | { status: "success"; projects: Project[] }
  | { status: "error"; message: string };

export function OrganizationProjects({
  organizationId,
  currentRole,
}: Props) {
  const { session, logout } = useAuth();
  const token = session?.accessToken;
  const navigate = useNavigate();

  const [state, setState] = useState<ProjectState>({
    status: "loading",
  });
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const canCreate = currentRole === "owner" || currentRole === "admin";

  useEffect(() => {
    if (!token) return;

    let ignore = false;

    async function loadProjects(accessToken: string) {
      try {
        const projects = await fetchProjects(
          accessToken,
          organizationId,
        );

        if (!ignore) {
          setState({ status: "success", projects });
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
            error instanceof Error
              ? error.message
              : "Unable to load projects.",
        });
      }
    }

    void loadProjects(token);

    return () => {
      ignore = true;
    };
  }, [token, organizationId, logout]);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!token || !canCreate) return;

    setSubmitting(true);
    setFormError("");

    try {
      const project = await createProject(token, organizationId, {
        name: name.trim(),
        description: description.trim(),
      });

      navigate(
        `/organizations/${organizationId}/projects/${project.id}`,
      );
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        logout();
        return;
      }

      setFormError(
        error instanceof Error
          ? error.message
          : "Unable to create project.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section aria-labelledby="projects-heading">
      <h2 id="projects-heading">Projects</h2>

      {state.status === "loading" && (
        <p role="status">Loading projects…</p>
      )}

      {state.status === "error" && (
        <p role="alert" className="error">
          {state.message}
        </p>
      )}

      {state.status === "success" &&
        (state.projects.length === 0 ? (
          <p>No projects yet.</p>
        ) : (
          <ul className="organization-list">
            {state.projects.map((project) => (
              <li key={project.id}>
                <div>
                  <Link
                    to={`/organizations/${organizationId}/projects/${project.id}`}
                  >
                    {project.name}
                  </Link>

                  {project.description && (
                    <p className="muted project-description">
                      {project.description}
                    </p>
                  )}
                </div>
              </li>
            ))}
          </ul>
        ))}

      {canCreate && (
        <form onSubmit={handleCreate} aria-label="Create project">
          <h3>Create a project</h3>

          <fieldset disabled={submitting}>
            <label htmlFor="project-name">
              Project name
              <input
                id="project-name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                maxLength={100}
                required
              />
            </label>

            <label htmlFor="project-description">
              Description
              <textarea
                id="project-description"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                maxLength={5000}
                rows={4}
              />
            </label>

            <button type="submit" disabled={!name.trim()}>
              {submitting ? "Creating…" : "Create project"}
            </button>
          </fieldset>

          {formError && (
            <p role="alert" className="error">
              {formError}
            </p>
          )}
        </form>
      )}
    </section>
  );
}