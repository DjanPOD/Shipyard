import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/useAuth";
import { registerAccount } from "../lib/api";

type AuthPageProps = {
  mode: "login" | "register";
};

export function AuthPage({ mode }: AuthPageProps) {
  const isRegister = mode === "register";
  const navigate = useNavigate();
  const { session, login } = useAuth();

  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (session) {
    return <Navigate to="/dashboard" replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      if (isRegister) {
        await registerAccount({
          email,
          display_name: displayName,
          password,
        });

        // Registration creates an account; login issues the token.
        setPassword("");
        navigate("/login", {
          replace: true,
          state: { registered: true },
        });
      } else {
        await login(email, password);
        setPassword("");
        navigate("/dashboard", { replace: true });
      }
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Something went wrong.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="auth-card">
        <p className="eyebrow">Shipyard</p>
        <h1>{isRegister ? "Create your account" : "Welcome back"}</h1>

        <form onSubmit={handleSubmit}>
          <fieldset disabled={submitting}>
            {isRegister && (
              <label htmlFor="display-name">
                Display name
                <input
                  id="display-name"
                  name="display_name"
                  autoComplete="name"
                  value={displayName}
                  onChange={(event) => setDisplayName(event.target.value)}
                  maxLength={100}
                  required
                />
              </label>
            )}

            <label htmlFor="email">
              Email
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                maxLength={255}
                required
              />
            </label>

            <label htmlFor="password">
              Password
              <input
                id="password"
                name="password"
                type="password"
                autoComplete={
                  isRegister ? "new-password" : "current-password"
                }
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                minLength={isRegister ? 15 : undefined}
                maxLength={128}
                required
              />
            </label>

            {isRegister && (
              <p className="muted">Use between 15 and 128 characters.</p>
            )}

            {error && <p role="alert" className="error">{error}</p>}

            <button type="submit">
              {submitting
                ? "Please wait…"
                : isRegister
                  ? "Create account"
                  : "Log in"}
            </button>
          </fieldset>
        </form>

        <p>
          {isRegister ? "Already have an account? " : "Need an account? "}
          <Link to={isRegister ? "/login" : "/register"}>
            {isRegister ? "Log in" : "Register"}
          </Link>
        </p>
      </section>
    </main>
  );
}