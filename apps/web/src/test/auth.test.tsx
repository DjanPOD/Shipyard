import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "../App";
import { AuthProvider } from "../auth/AuthProvider";

const account = {
  id: 1,
  email: "peter@example.com",
  display_name: "Peter",
  created_at: "2026-10-28T12:00:00+00:00",
  updated: "2026-10-28T12:00:00+00:00",
};

const password = "Shipyard learning password!";
const accessToken = "test-access-token";

const fetchMock = vi.fn<typeof fetch>();

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
    },
  });
}

function renderApp(path = "/login") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </MemoryRouter>,
  );
}

async function submitLogin() {
  const user = userEvent.setup();

  await user.type(screen.getByLabelText(/^email$/i), account.email);
  await user.type(screen.getByLabelText(/^password$/i), password);
  await user.click(screen.getByRole("button", { name: /^log in$/i }));

  return user;
}

function mockSuccessfulLogin() {
  fetchMock.mockResolvedValueOnce(
    jsonResponse({
      data: {
        access_token: accessToken,
        token_type: "Bearer",
        user: account,
      },
    }),
  );
}

beforeEach(() => {
  fetchMock.mockReset();

  // Fail unexpected requests rather than silently contacting a real server.
  fetchMock.mockRejectedValue(new Error("Unexpected network request."));

  vi.stubGlobal("fetch", fetchMock);
});

describe("authentication flow", () => {
  it("redirects signed-out visitors away from the dashboard", async () => {
    renderApp("/dashboard");

    expect(
      await screen.findByRole("heading", { name: /welcome back/i }),
    ).toBeInTheDocument();

    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("registers an account and redirects to login", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ data: account }, 201),
    );

    renderApp("/register");

    const user = userEvent.setup();

    await user.type(
      screen.getByLabelText(/display name/i),
      account.display_name,
    );
    await user.type(screen.getByLabelText(/^email$/i), account.email);
    await user.type(screen.getByLabelText(/^password$/i), password);

    await user.click(
      screen.getByRole("button", { name: /^create account$/i }),
    );

    expect(
      await screen.findByRole("heading", { name: /welcome back/i }),
    ).toBeInTheDocument();

    expect(
      screen.getByText(/account created\. log in to continue/i),
    ).toBeInTheDocument();

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/v1\/auth\/register$/),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          email: account.email,
          display_name: account.display_name,
          password,
        }),
      }),
    );
  });

  it("logs in and displays the dashboard", async () => {
    mockSuccessfulLogin();
    renderApp();

    await submitLogin();

    expect(
      await screen.findByRole("heading", { name: /hello, peter/i }),
    ).toBeInTheDocument();

    expect(screen.getByText(account.email)).toBeInTheDocument();
  });

  it("displays invalid-credential errors", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse(
        {
          error: {
            code: "INVALID_CREDENTIALS",
            message: "Invalid email or password.",
          },
        },
        401,
      ),
    );

    renderApp();
    await submitLogin();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Invalid email or password.",
    );

    expect(
      screen.getByRole("heading", { name: /welcome back/i }),
    ).toBeInTheDocument();
  });

  it("displays network errors without crashing", async () => {
    fetchMock.mockRejectedValueOnce(new TypeError("Failed to fetch"));

    renderApp();
    await submitLogin();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Failed to fetch",
    );
  });

  it("sends the access token to the protected account endpoint", async () => {
    mockSuccessfulLogin();

    fetchMock.mockResolvedValueOnce(
      jsonResponse({ data: account }),
    );

    renderApp();
    const user = await submitLogin();

    await user.click(
      await screen.findByRole("button", {
        name: /verify api session/i,
      }),
    );

    expect(await screen.findByRole("status")).toHaveTextContent(
      `Authenticated as ${account.email}.`,
    );

    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.stringMatching(/\/api\/v1\/auth\/me$/),
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      },
    );
  });

  it("returns to login when the API rejects an expired token", async () => {
    mockSuccessfulLogin();

    fetchMock.mockResolvedValueOnce(
      jsonResponse(
        {
          error: {
            code: "TOKEN_EXPIRED",
            message: "The access token has expired. Log in again.",
          },
        },
        401,
      ),
    );

    renderApp();
    const user = await submitLogin();

    await user.click(
      await screen.findByRole("button", {
        name: /verify api session/i,
      }),
    );

    expect(
      await screen.findByRole("heading", { name: /welcome back/i }),
    ).toBeInTheDocument();
  });

  it("logs out and removes access to the dashboard", async () => {
    mockSuccessfulLogin();
    renderApp();

    const user = await submitLogin();

    await user.click(
      await screen.findByRole("button", { name: /^log out$/i }),
    );

    expect(
      await screen.findByRole("heading", { name: /welcome back/i }),
    ).toBeInTheDocument();
  });
});