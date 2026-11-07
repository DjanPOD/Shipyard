import { useEffect, useState, type FormEvent } from "react";

import { useAuth } from "../auth/useAuth";
import {
  ApiError,
  addOrganizationMember,
  fetchOrganizationMembers,
  type Organization,
  type OrganizationMember,
} from "../lib/api";

type Props = {
  organizationId: number;
  currentRole: Organization["role"];
};

type MemberState =
  | { status: "loading" }
  | { status: "success"; members: OrganizationMember[] }
  | { status: "error"; message: string };

export function OrganizationMembers({
  organizationId,
  currentRole,
}: Props) {
  const { session, logout } = useAuth();
  const token = session?.accessToken;

  const [state, setState] = useState<MemberState>({
    status: "loading",
  });
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"member" | "admin">("member");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    if (!token) return;

    let ignore = false;

    async function loadMembers(accessToken: string) {
      try {
        const members = await fetchOrganizationMembers(
          accessToken,
          organizationId,
        );

        if (!ignore) {
          setState({ status: "success", members });
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
              : "Unable to load members.",
        });
      }
    }

    void loadMembers(token);

    return () => {
      ignore = true;
    };
  }, [token, organizationId, logout]);

  async function handleAdd(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!token || state.status !== "success") return;

    setSubmitting(true);
    setFormError("");
    setNotice("");

    try {
      const member = await addOrganizationMember(
        token,
        organizationId,
        {
          email: email.trim(),
          role,
        },
      );

      setState((previous) => {
        if (previous.status !== "success") return previous;

        return {
          status: "success",
          members: [...previous.members, member],
        };
      });

      setEmail("");
      setRole("member");
      setNotice(`${member.display_name} was added to the organization.`);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        logout();
        return;
      }

      setFormError(
        error instanceof Error ? error.message : "Unable to add member.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section aria-labelledby="members-heading">
      <h2 id="members-heading">Members</h2>

      {state.status === "loading" && (
        <p role="status">Loading members…</p>
      )}

      {state.status === "error" && (
        <p role="alert" className="error">
          {state.message}
        </p>
      )}

      {state.status === "success" && (
        <ul className="organization-list">
          {state.members.map((member) => (
            <li key={member.user_id}>
              <div>
                <strong>{member.display_name}</strong>
                <div className="muted">{member.email}</div>
              </div>
              <span className="role-badge">{member.role}</span>
            </li>
          ))}
        </ul>
      )}

      {currentRole === "owner" && (
        <form onSubmit={handleAdd} aria-label="Add member">
          <h3>Add an existing user</h3>
          <p className="muted">
            The user must already have a Shipyard account. This adds
            them immediately; it does not send an invitation.
          </p>

          <fieldset
            disabled={submitting || state.status !== "success"}
          >
            <label htmlFor="member-email">
              Member email
              <input
                id="member-email"
                type="email"
                autoComplete="off"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                maxLength={255}
                required
              />
            </label>

            <label htmlFor="member-role">
              Role
              <select
                id="member-role"
                value={role}
                onChange={(event) => {
                  const value = event.target.value;

                  if (value === "member" || value === "admin") {
                    setRole(value);
                  }
                }}
              >
                <option value="member">Member</option>
                <option value="admin">Admin</option>
              </select>
            </label>

            <button type="submit" disabled={!email.trim()}>
              {submitting ? "Adding…" : "Add member"}
            </button>
          </fieldset>

          {formError && (
            <p role="alert" className="error">
              {formError}
            </p>
          )}

          <p role="status">{notice}</p>
        </form>
      )}
    </section>
  );
}