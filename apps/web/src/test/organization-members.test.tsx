import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";

import { OrganizationMembers } from "../components/OrganizationMembers";

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

const owner = {
  user_id: 1,
  email: "owner@example.com",
  display_name: "Owner",
  role: "owner",
};

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => {
  fetchMock.mockReset();
  fetchMock.mockRejectedValue(new Error("Unexpected request."));
  vi.stubGlobal("fetch", fetchMock);
});

it("shows members but hides the form from nonowners", async () => {
  fetchMock.mockResolvedValueOnce(
    jsonResponse({ data: [owner] }),
  );

  render(
    <OrganizationMembers organizationId={12} currentRole="member" />,
  );

  expect(
    await screen.findByText("owner@example.com"),
  ).toBeInTheDocument();

  expect(
    screen.queryByRole("form", { name: "Add member" }),
  ).not.toBeInTheDocument();
});

it("lets an owner add an admin and updates the member list", async () => {
  fetchMock.mockResolvedValueOnce(
    jsonResponse({ data: [owner] }),
  );

  fetchMock.mockResolvedValueOnce(
    jsonResponse(
      {
        data: {
          user_id: 2,
          email: "teammate@example.com",
          display_name: "Teammate",
          role: "admin",
        },
      },
      201,
    ),
  );

  render(
    <OrganizationMembers organizationId={12} currentRole="owner" />,
  );

  await screen.findByText("owner@example.com");

  const user = userEvent.setup();

  await user.type(
    screen.getByLabelText(/member email/i),
    "teammate@example.com",
  );

  await user.selectOptions(screen.getByLabelText(/^role$/i), "admin");

  await user.click(
    screen.getByRole("button", { name: /^add member$/i }),
  );

  expect(
    await screen.findByText("teammate@example.com"),
  ).toBeInTheDocument();

  expect(fetchMock).toHaveBeenLastCalledWith(
    expect.stringMatching(/\/organizations\/12\/members$/),
    {
      method: "POST",
      headers: {
        Authorization: "Bearer test-token",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: "teammate@example.com",
        role: "admin",
      }),
    },
  );
});

it("shows duplicate-member errors without removing existing members", async () => {
  fetchMock.mockResolvedValueOnce(
    jsonResponse({ data: [owner] }),
  );

  fetchMock.mockResolvedValueOnce(
    jsonResponse(
      {
        error: {
          code: "CONFLICT",
          message: "This user already belongs to the organization.",
        },
      },
      409,
    ),
  );

  render(
    <OrganizationMembers organizationId={12} currentRole="owner" />,
  );

  await screen.findByText("owner@example.com");

  const user = userEvent.setup();

  await user.type(
    screen.getByLabelText(/member email/i),
    owner.email,
  );

  await user.click(
    screen.getByRole("button", { name: /^add member$/i }),
  );

  expect(await screen.findByRole("alert")).toHaveTextContent(
    "This user already belongs to the organization.",
  );

  expect(screen.getByText(owner.email)).toBeInTheDocument();
});