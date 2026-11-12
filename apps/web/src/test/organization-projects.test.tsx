import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";

import { OrganizationProjects } from "../components/OrganizationProjects";
import type { Organization } from "../lib/api";
import { ProjectPage } from "../pages/ProjectPage";

const { logoutMock } = vi.hoisted(() => ({
  logoutMock: vi.fn(),
}));

vi.mock("../auth/useAuth", () => ({
  useAuth: () => ({
    session: { accessToken: "test-token" },
    logout: logoutMock,
  }),
}));

const fetchMock = vi.fn<typeof fetch>();

const project = {
  id: 4,
  organization_id: 12,
  name: "Backend API",
  description: "Build the Shipyard API.",
  created_at: "2026-11-12T12:00:00+00:00",
};

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function renderPanel(role: Organization["role"] = "owner") {
  return render(
    <MemoryRouter initialEntries={["/organizations/12"]}>
      <Routes>
        <Route
          path="/organizations/:organizationId"
          element={
            <OrganizationProjects
              organizationId={12}
              currentRole={role}
            />
          }
        />
        <Route
          path="/organizations/:organizationId/projects/:projectId"
          element={<ProjectPage />}
        />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  fetchMock.mockReset();
  logoutMock.mockClear();

  fetchMock.mockRejectedValue(new Error("Unexpected request."));

  vi.stubGlobal("fetch", fetchMock);
});

it("lists projects and hides creation from ordinary members", async () => {
  fetchMock.mockResolvedValueOnce(
    jsonResponse({ data: [project] }),
  );

  renderPanel("member");

  expect(
    await screen.findByRole("link", { name: project.name }),
  ).toHaveAttribute("href", "/organizations/12/projects/4");

  expect(
    screen.queryByRole("form", { name: "Create project" }),
  ).not.toBeInTheDocument();
});

it.each(["owner", "admin"] as const)(
  "allows an %s to create a project and open its detail page",
  async (role) => {
    fetchMock.mockImplementation(async (input, options) => {
      const url = String(input);

      if (url.endsWith("/organizations/12/projects/4")) {
        return jsonResponse({ data: project });
      }

      if (url.endsWith("/organizations/12/projects")) {
        if (options?.method === "POST") {
          return jsonResponse({ data: project }, 201);
        }

        return jsonResponse({ data: [] });
      }

      throw new Error(`Unexpected request: ${url}`);
    });

    renderPanel(role);

    await screen.findByText("No projects yet.");

    const user = userEvent.setup();

    await user.type(
      screen.getByLabelText(/^project name$/i),
      project.name,
    );

    await user.type(
      screen.getByLabelText(/^description$/i),
      project.description,
    );

    await user.click(
      screen.getByRole("button", { name: /^create project$/i }),
    );

    expect(
      await screen.findByRole("heading", { name: project.name }),
    ).toBeInTheDocument();

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/organizations\/12\/projects$/),
      {
        method: "POST",
        headers: {
          Authorization: "Bearer test-token",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: project.name,
          description: project.description,
        }),
      },
    );
  },
);

it("shows a safe message for an inaccessible project", async () => {
  fetchMock.mockResolvedValueOnce(
    jsonResponse(
      {
        error: {
          code: "NOT_FOUND",
          message: "Project not found.",
        },
      },
      404,
    ),
  );

  render(
    <MemoryRouter
      initialEntries={["/organizations/12/projects/4"]}
    >
      <Routes>
        <Route
          path="/organizations/:organizationId/projects/:projectId"
          element={<ProjectPage />}
        />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Project not found or you do not have access.",
  );
});

it("signs out when project loading receives 401", async () => {
  fetchMock.mockResolvedValueOnce(
    jsonResponse(
      {
        error: {
          code: "TOKEN_EXPIRED",
          message: "The access token has expired.",
        },
      },
      401,
    ),
  );

  renderPanel();

  await vi.waitFor(() => {
    expect(logoutMock).toHaveBeenCalledOnce();
  });
});