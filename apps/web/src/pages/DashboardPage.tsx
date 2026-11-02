import { useState } from "react";

import { useAuth } from "../auth/useAuth";
import { ApiError, fetchCurrentUser } from "../lib/api";

export function DashboardPage() {
  const { session, logout } = useAuth();
  const [message, setMessage] = useState("");
  const [checking, setChecking] = useState(false);

  if (!session) {
    return null;
  }

  const currentSession = session;

  async function verifySession() {
    setChecking(true);
    setMessage("");

    try {
      const user = await fetchCurrentUser(currentSession.accessToken);
      setMessage(`Authenticated as ${user.email}.`);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        logout();
        return;
      }

      setMessage(
        error instanceof Error ? error.message : "Verification failed.",
      );
    } finally {
      setChecking(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="auth-card">
        <p className="eyebrow">Shipyard dashboard</p>
        <h1>Hello, {session.user.display_name}</h1>
        <p className="muted">{session.user.email}</p>

        <p>Your account is ready. Projects and organizations come next.</p>

        <div className="actions">
          <button
            type="button"
            onClick={() => void verifySession()}
            disabled={checking}
          >
            {checking ? "Checking…" : "Verify API session"}
          </button>

          <button type="button" className="secondary" onClick={logout}>
            Log out
          </button>
        </div>

        <p role="status">{message}</p>
      </section>
    </main>
  );
}