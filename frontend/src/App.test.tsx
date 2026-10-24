import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "./App";

const testProject = {
  id: "project-1",
  record_number: "PRJ-001",
  created_by: null,
  archived_at: null,
  archived_by: null,
  name: "Customer Portal",
  description: "A synthetic test project.",
  status: "active",
  created_at: "2026-10-01T00:00:00Z",
  updated_at: "2026-10-01T00:00:00Z",
};

const archivedTestProject = {
  ...testProject,
  id: "project-archived",
  record_number: "PRJ-002",
  name: "Archived Portal",
  archived_at: "2026-10-02T00:00:00Z",
  archived_by: {
    id: "admin-1",
    record_number: "USR-001",
    full_name: "Test Admin",
  },
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function paginatedResponse(items: unknown[] = []) {
  return jsonResponse({ items, total: items.length, limit: 20, offset: 0 });
}

function mockAuthenticatedSession(
  fetchMock: ReturnType<typeof vi.fn>,
  projectsResponse: (url: string) => Response | Promise<Response> = () =>
    paginatedResponse(),
) {
  fetchMock.mockImplementation(async (input) => {
    const url = String(input);
    if (url.endsWith("/api/v1/auth/login")) {
      return jsonResponse({ access_token: "test-token", token_type: "bearer" });
    }
    if (url.endsWith("/api/v1/auth/me")) {
      return jsonResponse({
        id: "admin-1",
        record_number: "USR-001",
        email: "admin@example.test",
        full_name: "Test Admin",
        role: "admin",
        is_active: true,
      });
    }
    if (url.includes("/api/v1/projects")) return projectsResponse(url);
    return paginatedResponse();
  });
}

async function signInAsTestAdmin() {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Email address"), "admin@example.test");
  await user.type(screen.getByLabelText("Password"), "synthetic-test-password");
  await user.click(screen.getByRole("button", { name: /sign in/i }));
  expect(await screen.findByText(/Test Admin.*USR-001.*Admin/)).toBeVisible();
  return user;
}

describe("AI BAP authentication and workspace", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("renders an accessible unauthenticated sign-in form", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "Sign in to your account" })).toBeVisible();
    expect(screen.getByLabelText("Email address")).toHaveAttribute("type", "email");
    expect(screen.getByLabelText("Password")).toHaveAttribute("type", "password");
    expect(screen.getByRole("button", { name: /sign in/i })).toBeEnabled();
    expect(screen.queryByRole("button", { name: /sign out/i })).not.toBeInTheDocument();
  });

  it("uses browser form validation before attempting a login request", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(fetch);
    render(<App />);

    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(fetchMock).not.toHaveBeenCalled();
    expect(screen.getByLabelText("Email address")).toBeInvalid();
    expect(screen.getByLabelText("Password")).toBeInvalid();
  });

  it("shows the server-safe login failure message", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: "Invalid credentials" }, 401));
    render(<App />);

    await user.type(screen.getByLabelText("Email address"), "reviewer@example.test");
    await user.type(screen.getByLabelText("Password"), "not-a-real-password");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid email or password.");
    expect(screen.getByRole("button", { name: /sign in/i })).toBeEnabled();
  });

  it("signs in with mocked API responses and renders the protected projects", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/api/v1/auth/login")) {
        return jsonResponse({ access_token: "test-token", token_type: "bearer" });
      }
      if (url.endsWith("/api/v1/auth/me")) {
        return jsonResponse({
          id: "user-1",
          record_number: "USR-001",
          email: "reviewer@example.test",
          full_name: "Test Reviewer",
          role: "reviewer",
          is_active: true,
        });
      }
      if (url.includes("/api/v1/projects")) return paginatedResponse([testProject]);
      return paginatedResponse();
    });
    render(<App />);

    await user.type(screen.getByLabelText("Email address"), "reviewer@example.test");
    await user.type(screen.getByLabelText("Password"), "not-a-real-password");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByText(/Test Reviewer.*USR-001.*Reviewer/)).toBeVisible();
    await user.click(screen.getByRole("button", { name: /projects/i }));
    await waitFor(() => expect(screen.getByText("Customer Portal")).toBeVisible());
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/projects"),
      expect.objectContaining({ headers: expect.any(Headers) }),
    );
  });

  it("filters active and archived projects and exposes only applicable actions", async () => {
    const fetchMock = vi.mocked(fetch);
    mockAuthenticatedSession(fetchMock, (url) =>
      url.includes("archived=true")
        ? paginatedResponse([archivedTestProject])
        : paginatedResponse([testProject]),
    );
    render(<App />);

    const user = await signInAsTestAdmin();
    await user.click(screen.getByRole("button", { name: /projects/i }));

    expect(await screen.findByText("Customer Portal")).toBeVisible();
    expect(screen.getByRole("button", { name: "Edit Customer Portal" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Archive Customer Portal" })).toBeVisible();

    await user.selectOptions(screen.getByLabelText("Show"), "archived");

    expect(await screen.findByText("Archived Portal")).toBeVisible();
    expect(screen.queryByText("Customer Portal")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Restore Archived Portal" })).toBeVisible();
    expect(screen.queryByRole("button", { name: "Edit Archived Portal" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Archive Archived Portal" })).not.toBeInTheDocument();
  });

  it("shows project-list loading feedback until the pending request resolves", async () => {
    const fetchMock = vi.mocked(fetch);
    let resolveProjects!: (response: Response) => void;
    const pendingProjects = new Promise<Response>((resolve) => {
      resolveProjects = resolve;
    });
    mockAuthenticatedSession(fetchMock, (url) =>
      url.includes("limit=10") ? pendingProjects : paginatedResponse(),
    );
    render(<App />);

    const user = await signInAsTestAdmin();
    await user.click(screen.getByRole("button", { name: /projects/i }));
    expect(screen.getByText("Loading projects...")).toBeVisible();

    await act(async () => {
      resolveProjects(paginatedResponse([testProject]));
      await pendingProjects;
    });

    expect(await screen.findByText("Customer Portal")).toBeVisible();
    expect(screen.queryByText("Loading projects...")).not.toBeInTheDocument();
  });

  it("shows accessible feedback when the project-list request fails", async () => {
    const fetchMock = vi.mocked(fetch);
    mockAuthenticatedSession(fetchMock, (url) =>
      url.includes("limit=10")
        ? jsonResponse({ detail: "Project list is temporarily unavailable." }, 503)
        : paginatedResponse(),
    );
    render(<App />);

    await signInAsTestAdmin();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Project list is temporarily unavailable.",
    );
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/projects?archived=false&limit=10"),
      expect.objectContaining({ headers: expect.any(Headers) }),
    );
  });
});
