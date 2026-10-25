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

const testBusinessAnalyst = {
  id: "analyst-1",
  record_number: "USR-002",
  email: "analyst@example.test",
  full_name: "Test Analyst",
  role: "business_analyst",
  is_active: true,
};
const testRequirement = {
  id: "requirement-1",
  record_number: "REQ-001",
  created_by: null,
  project_id: testProject.id,
  title: "Account access",
  description: "A synthetic requirement.",
  priority: "high",
  status: "draft",
  created_at: "2026-10-01T00:00:00Z",
  updated_at: "2026-10-01T00:00:00Z",
};
const testSavedStory = {
  id: "story-1",
  record_number: "STY-001",
  created_by: null,
  requirement_id: testRequirement.id,
  title: "Reviewable synthetic story",
  description: "A saved synthetic story.",
  acceptance_criteria: ["Given a reviewer, when reviewing, then decide."],
  status: "in_review",
  created_at: "2026-10-01T00:00:00Z",
  updated_at: "2026-10-01T00:00:00Z",
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
  currentUser: Record<string, unknown> = {
    id: "admin-1",
    record_number: "USR-001",
    email: "admin@example.test",
    full_name: "Test Admin",
    role: "admin",
    is_active: true,
  },
) {
  fetchMock.mockImplementation(async (input) => {
    const url = String(input);
    if (url.endsWith("/api/v1/auth/login")) {
      return jsonResponse({ access_token: "test-token", token_type: "bearer" });
    }
    if (url.endsWith("/api/v1/auth/me")) {
      return jsonResponse(currentUser);
    }
    if (url.includes("/api/v1/projects")) return projectsResponse(url);
    return paginatedResponse();
  });
}

function mockUserStorySession(
  fetchMock: ReturnType<typeof vi.fn>,
  currentUser: Record<string, unknown>,
  generatedResponse?: Response,
) {
  mockAuthenticatedSession(
    fetchMock,
    (url) =>
      url.includes("/api/v1/projects/")
        ? jsonResponse(testProject)
        : paginatedResponse([testProject]),
    currentUser,
  );
  const authenticatedFetch = fetchMock.getMockImplementation() as unknown as (
    input: RequestInfo | URL,
    init?: RequestInit,
  ) => Promise<Response>;
  fetchMock.mockImplementation(async (input, init) => {
    const url = String(input);
    if (url.includes("/api/v1/requirements?")) {
      return paginatedResponse([testRequirement]);
    }
    if (
      url.endsWith("/api/v1/user-stories") &&
      init?.method === "POST"
    ) {
      return jsonResponse({});
    }
    if (url.includes("/api/v1/user-stories/generate") && generatedResponse) {
      return generatedResponse;
    }
    if (url.includes("/api/v1/user-stories?")) {
      return paginatedResponse([testSavedStory]);
    }
    return authenticatedFetch(input as RequestInfo | URL, init);
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

async function signInAsTestBusinessAnalyst() {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Email address"), testBusinessAnalyst.email);
  await user.type(screen.getByLabelText("Password"), "synthetic-test-password");
  await user.click(screen.getByRole("button", { name: /sign in/i }));
  expect(await screen.findByText(/Test Analyst.*USR-002.*Business Analyst/)).toBeVisible();
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

  it("allows business analysts to edit active projects but hides admin-only archive actions", async () => {
    const fetchMock = vi.mocked(fetch);
    mockAuthenticatedSession(
      fetchMock,
      (url) =>
        url.includes("archived=true")
          ? paginatedResponse([archivedTestProject])
          : paginatedResponse([testProject]),
      testBusinessAnalyst,
    );
    render(<App />);

    const user = await signInAsTestBusinessAnalyst();
    await user.click(screen.getByRole("button", { name: /projects/i }));

    expect(
      screen.getByRole("heading", { name: "All Projects" }),
    ).toBeVisible();
    expect(screen.getByLabelText("Show")).toBeVisible();
    expect(await screen.findByText("Customer Portal")).toBeVisible();
    expect(screen.getByRole("button", { name: "Edit Customer Portal" })).toBeVisible();
    expect(screen.queryByRole("button", { name: "Archive Customer Portal" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Restore Customer Portal" })).not.toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Show"), "archived");

    expect(await screen.findByText("Archived Portal")).toBeVisible();
    expect(screen.queryByRole("button", { name: "Edit Archived Portal" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Archive Archived Portal" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Restore Archived Portal" })).not.toBeInTheDocument();
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
    expect(
      screen.getByRole("heading", { name: "All Projects" }),
    ).toBeVisible();
    expect(screen.getByLabelText("Show")).toBeVisible();
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

  it("disables live AI generation for the public demo analyst but keeps manual stories available", async () => {
    const fetchMock = vi.mocked(fetch);
    const publicAnalyst = {
      ...testBusinessAnalyst,
      email: "  Banlyst@Example.com ",
    };
    mockUserStorySession(fetchMock, publicAnalyst);
    render(<App />);

    const user = await signInAsTestBusinessAnalyst();
    await user.click(screen.getByRole("button", { name: /user stories/i }));
    await user.selectOptions(screen.getByLabelText("Project"), testProject.id);
    await user.selectOptions(
      await screen.findByLabelText("Requirement"),
      testRequirement.id,
    );

    const generateButton = await screen.findByRole("button", {
      name: /generate ai draft/i,
    });
    expect(generateButton).toBeDisabled();
    expect(
      screen.getByRole("note"),
    ).toHaveTextContent("Live AI generation is unavailable for public demo accounts.");
    expect(await screen.findByText("Reviewable synthetic story")).toBeVisible();
    await user.click(screen.getByRole("button", { name: /new user story/i }));
    await user.type(screen.getByLabelText("Title", { selector: "input" }), "Manual demo story");
    await user.type(
      screen.getByLabelText("Description", { selector: "textarea" }),
      "Manually entered synthetic content.",
    );
    await user.click(screen.getByRole("button", { name: "Save as Draft" }));

    expect(await screen.findByRole("status")).toHaveTextContent(
      "User story saved as Draft.",
    );
    expect(
      fetchMock.mock.calls.some(
        ([input, init]) =>
          String(input).endsWith("/api/v1/user-stories") &&
          init?.method === "POST",
      ),
    ).toBe(true);

    expect(
      fetchMock.mock.calls.some(([input]) =>
        String(input).endsWith("/api/v1/user-stories/generate"),
      ),
    ).toBe(false);
  });

  it("keeps saved stories and reviewer decisions available without an AI action", async () => {
    const fetchMock = vi.mocked(fetch);
    const publicReviewer = {
      id: "reviewer-1",
      record_number: "USR-003",
      email: "reviwer@example.com",
      full_name: "Demo Reviewer",
      role: "reviewer",
      is_active: true,
    };
    mockUserStorySession(fetchMock, publicReviewer);
    render(<App />);
    const user = userEvent.setup();
    await user.type(screen.getByLabelText("Email address"), publicReviewer.email);
    await user.type(screen.getByLabelText("Password"), "synthetic-test-password");
    await user.click(screen.getByRole("button", { name: /sign in/i }));
    await screen.findByText(/Demo Reviewer.*USR-003.*Reviewer/);
    await user.click(screen.getByRole("button", { name: /user stories/i }));
    await user.selectOptions(screen.getByLabelText("Project"), testProject.id);
    await user.selectOptions(
      await screen.findByLabelText("Requirement"),
      testRequirement.id,
    );

    expect(await screen.findByText("Reviewable synthetic story")).toBeVisible();
    expect(screen.getByRole("button", { name: "Approve" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Reject" })).toBeEnabled();
    expect(
      screen.queryByRole("button", { name: /generate ai draft/i }),
    ).not.toBeInTheDocument();
    expect(
      fetchMock.mock.calls.some(([input]) =>
        String(input).endsWith("/api/v1/user-stories/generate"),
      ),
    ).toBe(false);
  });

  it("preserves AI generation for a non-demo Business Analyst", async () => {
    const fetchMock = vi.mocked(fetch);
    mockUserStorySession(
      fetchMock,
      testBusinessAnalyst,
      jsonResponse({
          requirement_id: testRequirement.id,
          title: "Mocked AI draft",
          description: "A synthetic generated draft.",
          acceptance_criteria: ["Given a request, when processed, then respond."],
          requires_human_review: true,
          saved_to_database: false,
        }),
    );
    render(<App />);

    const user = await signInAsTestBusinessAnalyst();
    await user.click(screen.getByRole("button", { name: /user stories/i }));
    await user.selectOptions(screen.getByLabelText("Project"), testProject.id);
    await user.selectOptions(
      await screen.findByLabelText("Requirement"),
      testRequirement.id,
    );
    await user.click(
      await screen.findByRole("button", { name: /generate ai draft/i }),
    );

    expect(await screen.findByText(/AI draft generated/)).toBeVisible();
    expect(
      fetchMock.mock.calls.filter(([input]) =>
        String(input).endsWith("/api/v1/user-stories/generate"),
      ),
    ).toHaveLength(1);
  });
});
