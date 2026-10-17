import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import "./App.css";

type ProjectStatus = "planned" | "active" | "on_hold" | "completed";
type RequirementPriority = "low" | "medium" | "high" | "critical";
type RequirementStatus = "draft" | "in_review" | "approved" | "rejected";
type Page = "dashboard" | "projects" | "requirements" | "user-stories";
type StoryStatus = "draft" | "in_review" | "approved" | "rejected";

type RecordCreator = {
  record_number: string;
  full_name: string;
};

type Project = {
  id: string;
  record_number: string;
  created_by: RecordCreator | null;
  name: string;
  description: string | null;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
};
type Requirement = {
  id: string;
  record_number: string;
  created_by: RecordCreator | null;
  project_id: string;
  title: string;
  description: string;
  priority: RequirementPriority;
  status: RequirementStatus;
  created_at: string;
  updated_at: string;
};
type UserStory = {
  id: string;
  record_number: string;
  created_by: RecordCreator | null;
  requirement_id: string;
  title: string;
  description: string;
  acceptance_criteria: string[];
  status: StoryStatus;
  created_at: string;
  updated_at: string;
};
type AIDraft = {
  requirement_id: string;
  title: string;
  description: string;
  acceptance_criteria: string[];
  requires_human_review: boolean;
  saved_to_database: boolean;
};
type Paginated<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};
type TokenResponse = { access_token: string; token_type: string };

type UserRole = "admin" | "business_analyst" | "reviewer";

type CurrentUser = {
  id: string;
  record_number: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
};

type AuditEvent = {
  id: string;
  user_story_id: string | null;
  actor_id: string | null;
  user_story_id_snapshot: string | null;
  actor_id_snapshot: string | null;
  action: string;
  previous_status: string;
  new_status: string;
  created_at: string;
};

type AuditResponse = {
  items: AuditEvent[];
  total: number;
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const PAGE_SIZE = 10;
const PROJECT_STATUS: Record<ProjectStatus, string> = {
  planned: "Planned",
  active: "Active",
  on_hold: "On Hold",
  completed: "Completed",
};
const PRIORITY: Record<RequirementPriority, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  critical: "Critical",
};
const REQUIREMENT_STATUS: Record<RequirementStatus, string> = {
  draft: "Draft",
  in_review: "In Review",
  approved: "Approved",
  rejected: "Rejected",
};

function App() {
  // I keep AI drafts separate from persisted user stories.
  const [storyProjectId, setStoryProjectId] = useState("");
  const [storyRequirementId, setStoryRequirementId] = useState("");
  const [storyRequirements, setStoryRequirements] = useState<Requirement[]>([]);
  const [stories, setStories] = useState<UserStory[]>([]);
  const [totalStories, setTotalStories] = useState(0);
  const [storyOffset, setStoryOffset] = useState(0);
  const [storyTitle, setStoryTitle] = useState("");
  const [storyDescription, setStoryDescription] = useState("");
  const [criteriaText, setCriteriaText] = useState("");
  const [aiDraft, setAiDraft] = useState<AIDraft | null>(null);
  const [reviewed, setReviewed] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [showStoryForm, setShowStoryForm] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  // I keep the selected user story's audit history in memory.
  const [selectedAuditStoryId, setSelectedAuditStoryId] = useState<
    string | null
  >(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [isLoadingAudit, setIsLoadingAudit] = useState(false);
  const [auditError, setAuditError] = useState("");
  const auditRequestGeneration = useRef(0);
  const [page, setPage] = useState<Page>("dashboard");
  const [projects, setProjects] = useState<Project[]>([]);
  const [totalProjects, setTotalProjects] = useState(0);
  const [projectOffset, setProjectOffset] = useState(0);
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [totalRequirements, setTotalRequirements] = useState(0);
  const [requirementOffset, setRequirementOffset] = useState(0);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showProjectForm, setShowProjectForm] = useState(false);
  const [showRequirementForm, setShowRequirementForm] = useState(false);
  const [projectName, setProjectName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");
  const [projectStatus, setProjectStatus] = useState<ProjectStatus>("planned");
  const [requirementTitle, setRequirementTitle] = useState("");
  const [requirementDescription, setRequirementDescription] = useState("");
  const [requirementPriority, setRequirementPriority] =
    useState<RequirementPriority>("medium");
  const [requirementStatus, setRequirementStatus] =
    useState<RequirementStatus>("draft");
  const canCreateContent =
    currentUser?.role === "admin" || currentUser?.role === "business_analyst";

  const clearAuditHistory = useCallback(() => {
    auditRequestGeneration.current += 1;
    setSelectedAuditStoryId(null);
    setAuditEvents([]);
    setIsLoadingAudit(false);
    setAuditError("");
  }, []);

  const logout = useCallback(() => {
    // I clear the in-memory token and all protected workspace data.
    setAccessToken(null);
    setCurrentUser(null);
    setPassword("");
    setProjects([]);
    setRequirements([]);
    setStories([]);
    setStoryRequirements([]);
    setStoryProjectId("");
    setStoryRequirementId("");
    setAiDraft(null);
    setReviewed(false);
    clearAuditHistory();
    setTotalStories(0);
    setStoryOffset(0);
    setTotalProjects(0);
    setTotalRequirements(0);
    setSelectedProjectId("");
    setProjectOffset(0);
    setRequirementOffset(0);
    setPage("dashboard");
    setError("");
    setSuccess("");
  }, [clearAuditHistory]);

  const request = useCallback(
    async (path: string, options: RequestInit = {}) => {
      // I attach the JWT to every protected API request.
      if (!accessToken) throw new Error("Please sign in again.");
      const headers = new Headers(options.headers);
      headers.set("Authorization", `Bearer ${accessToken}`);
      if (options.body) headers.set("Content-Type", "application/json");
      const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers,
      });
      if (response.status === 401) {
        logout();
        throw new Error("Your session has expired. Please sign in again.");
      }
      if (!response.ok) {
        const body: unknown = await response.json().catch(() => null);
        const detail =
          body && typeof body === "object" && "detail" in body
            ? (body as { detail: unknown }).detail
            : null;
        throw new Error(
          typeof detail === "string"
            ? detail
            : `Request failed (${response.status}).`,
        );
      }
      return response;
    },
    [accessToken, logout],
  );

  const loadProjects = useCallback(
    async (offset: number) => {
      setIsLoading(true);
      setError("");
      try {
        const response = await request(
          `/api/v1/projects?limit=${PAGE_SIZE}&offset=${offset}`,
        );
        const data: Paginated<Project> = await response.json();
        setProjects(data.items);
        setTotalProjects(data.total);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Unable to load projects.",
        );
      } finally {
        setIsLoading(false);
      }
    },
    [request],
  );

  const loadRequirements = useCallback(
    async (projectId: string, offset: number) => {
      if (!projectId) {
        setRequirements([]);
        setTotalRequirements(0);
        return;
      }
      setIsLoading(true);
      setError("");
      try {
        const params = new URLSearchParams({
          project_id: projectId,
          limit: String(PAGE_SIZE),
          offset: String(offset),
        });
        const response = await request(
          `/api/v1/requirements?${params.toString()}`,
        );
        const data: Paginated<Requirement> = await response.json();
        setRequirements(data.items);
        setTotalRequirements(data.total);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Unable to load requirements.",
        );
      } finally {
        setIsLoading(false);
      }
    },
    [request],
  );

  const loadStoryRequirements = useCallback(
    async (projectId: string) => {
      if (!projectId) {
        setStoryRequirements([]);
        return;
      }
      setIsLoading(true);
      setError("");
      try {
        // I load up to 100 requirements for the selected project.
        const response = await request(
          `/api/v1/requirements?${new URLSearchParams({ project_id: projectId, limit: "100", offset: "0" })}`,
        );
        const data: Paginated<Requirement> = await response.json();
        setStoryRequirements(data.items);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Unable to load requirements.",
        );
      } finally {
        setIsLoading(false);
      }
    },
    [request],
  );

  const loadStories = useCallback(
    async (requirementId: string, offset: number) => {
      if (!requirementId) {
        setStories([]);
        setTotalStories(0);
        return;
      }
      setIsLoading(true);
      setError("");
      try {
        const params = new URLSearchParams({
          requirement_id: requirementId,
          limit: String(PAGE_SIZE),
          offset: String(offset),
        });
        const response = await request(`/api/v1/user-stories?${params}`);
        const data: Paginated<UserStory> = await response.json();
        setStories(data.items);
        setTotalStories(data.total);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Unable to load user stories.",
        );
      } finally {
        setIsLoading(false);
      }
    },
    [request],
  );

  async function handleViewAuditHistory(storyId: string) {
    const requestGeneration = auditRequestGeneration.current + 1;
    auditRequestGeneration.current = requestGeneration;
    setSelectedAuditStoryId(storyId);
    setAuditEvents([]);
    setIsLoadingAudit(true);
    setAuditError("");

    try {
      const response = await request(`/api/v1/user-stories/${storyId}/audit`);
      const data: AuditResponse = await response.json();

      if (!Array.isArray(data.items) || typeof data.total !== "number") {
        throw new Error("Unexpected audit history response.");
      }

      if (auditRequestGeneration.current !== requestGeneration) return;
      setAuditEvents(data.items);
    } catch (err) {
      if (auditRequestGeneration.current !== requestGeneration) return;
      setAuditError(
        err instanceof Error ? err.message : "Unable to load audit history.",
      );
    } finally {
      if (auditRequestGeneration.current !== requestGeneration) return;
      setIsLoadingAudit(false);
    }
  }

  useEffect(() => {
    if (accessToken && page === "user-stories")
      void loadStoryRequirements(storyProjectId);
  }, [accessToken, page, storyProjectId, loadStoryRequirements]);

  useEffect(() => {
    if (accessToken && page === "user-stories")
      void loadStories(storyRequirementId, storyOffset);
  }, [accessToken, page, storyRequirementId, storyOffset, loadStories]);

  function clearStoryEditor() {
    setStoryTitle("");
    setStoryDescription("");
    setCriteriaText("");
    setAiDraft(null);
    setReviewed(false);
  }

  async function handleGenerateStory() {
    if (!storyRequirementId) return;
    setIsGenerating(true);
    setError("");
    setSuccess("");
    setAiDraft(null);
    setReviewed(false);
    try {
      // I request an AI draft without persisting it to PostgreSQL.
      const response = await request("/api/v1/user-stories/generate", {
        method: "POST",
        body: JSON.stringify({ requirement_id: storyRequirementId }),
      });
      const draft: AIDraft = await response.json();
      if (
        draft.requirement_id !== storyRequirementId ||
        draft.saved_to_database !== false ||
        draft.requires_human_review !== true ||
        !Array.isArray(draft.acceptance_criteria)
      ) {
        throw new Error("Unexpected AI draft response. Nothing was saved.");
      }
      setAiDraft(draft);
      setStoryTitle(draft.title);
      setStoryDescription(draft.description);
      setCriteriaText(draft.acceptance_criteria.join("\n"));
      setShowStoryForm(true);
      setSuccess("AI draft generated. Review and edit it before saving.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "AI generation failed.");
    } finally {
      setIsGenerating(false);
    }
  }

  async function handleCreateStory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!storyRequirementId) return;
    if (aiDraft && !reviewed) {
      setError("Please confirm that you reviewed the AI draft.");
      return;
    }
    const criteria = criteriaText
      .split("\n")
      .map((item) => item.trim())
      .filter(Boolean);
    if (criteria.length > 30 || criteria.some((item) => item.length > 1000)) {
      setError(
        "Provide at most 30 acceptance criteria, each at most 1000 characters.",
      );
      return;
    }
    setIsSaving(true);
    setError("");
    setSuccess("");
    try {
      // I save only a human-reviewed draft through the standard endpoint.
      await request("/api/v1/user-stories", {
        method: "POST",
        body: JSON.stringify({
          requirement_id: storyRequirementId,
          title: storyTitle.trim(),
          description: storyDescription.trim(),
          acceptance_criteria: criteria,
          status: "draft",
        }),
      });
      clearStoryEditor();
      setShowStoryForm(false);
      setStoryOffset(0);
      await loadStories(storyRequirementId, 0);
      setSuccess("User story saved as Draft.");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to save user story.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function handleSubmitStoryForReview(storyId: string) {
    if (
      !currentUser ||
      !["business_analyst", "admin"].includes(currentUser.role)
    ) {
      setError("You do not have permission to submit user stories.");
      return;
    }

    if (!window.confirm("Submit this user story for review?")) {
      return;
    }

    setIsSaving(true);
    setError("");
    setSuccess("");

    try {
      // I submit the draft for formal human review.
      await request(`/api/v1/user-stories/${storyId}`, {
        method: "PATCH",
        body: JSON.stringify({ status: "in_review" }),
      });

      await loadStories(storyRequirementId, storyOffset);
      setSuccess("User story submitted for review successfully.");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to submit user story for review.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function handleReviewStory(
    storyId: string,
    decision: "approve" | "reject",
  ) {
    if (currentUser?.role !== "reviewer" && currentUser?.role !== "admin") {
      setError("You do not have permission to review user stories.");
      return;
    }

    const actionLabel = decision === "approve" ? "approve" : "reject";

    if (
      !window.confirm(
        `Are you sure you want to ${actionLabel} this user story?`,
      )
    ) {
      return;
    }

    setIsSaving(true);
    setError("");
    setSuccess("");

    try {
      // I record the review decision through the protected backend endpoint.
      await request(`/api/v1/user-stories/${storyId}/${decision}`, {
        method: "POST",
      });

      await loadStories(storyRequirementId, storyOffset);

      setSuccess(
        decision === "approve"
          ? "User story approved successfully."
          : "User story rejected successfully.",
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to complete the review decision.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  useEffect(() => {
    if (accessToken) void loadProjects(projectOffset);
  }, [accessToken, projectOffset, loadProjects]);

  useEffect(() => {
    if (accessToken && page === "requirements") {
      void loadRequirements(selectedProjectId, requirementOffset);
    }
  }, [
    accessToken,
    page,
    selectedProjectId,
    requirementOffset,
    loadRequirements,
  ]);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });
      if (!response.ok)
        throw new Error(
          response.status === 401
            ? "Invalid email or password."
            : "Login failed.",
        );
      const data: TokenResponse = await response.json();
      if (!data.access_token || data.token_type.toLowerCase() !== "bearer") {
        throw new Error("Invalid authentication response.");
      }
      // I retrieve my verified profile before completing sign-in.
      const profileResponse = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
        headers: {
          Authorization: `Bearer ${data.access_token}`,
        },
      });

      if (!profileResponse.ok) {
        throw new Error("Unable to verify your user profile.");
      }

      const profile: CurrentUser = await profileResponse.json();

      if (
        !profile.is_active ||
        !["admin", "business_analyst", "reviewer"].includes(profile.role)
      ) {
        throw new Error(
          "Your account is not authorized to access this workspace.",
        );
      }

      setCurrentUser(profile);
      setAccessToken(data.access_token);
      setPassword("");
      setProjectOffset(0);
      setPage("dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleCreateProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setError("");
    setSuccess("");
    try {
      await request("/api/v1/projects", {
        method: "POST",
        body: JSON.stringify({
          name: projectName.trim(),
          description: projectDescription.trim() || null,
          status: projectStatus,
        }),
      });
      setProjectName("");
      setProjectDescription("");
      setProjectStatus("planned");
      setShowProjectForm(false);
      setProjectOffset(0);
      await loadProjects(0);
      setSuccess("Project created successfully.");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to create project.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function handleCreateRequirement(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedProjectId) return;
    setIsSaving(true);
    setError("");
    setSuccess("");
    try {
      await request("/api/v1/requirements", {
        method: "POST",
        body: JSON.stringify({
          project_id: selectedProjectId,
          title: requirementTitle.trim(),
          description: requirementDescription.trim(),
          priority: requirementPriority,
          status: requirementStatus,
        }),
      });
      setRequirementTitle("");
      setRequirementDescription("");
      setRequirementPriority("medium");
      setRequirementStatus("draft");
      setShowRequirementForm(false);
      setRequirementOffset(0);
      await loadRequirements(selectedProjectId, 0);
      setSuccess("Requirement created successfully.");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to create requirement.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  if (!accessToken) {
    return (
      <main className="login-layout">
        <section className="intro-panel">
          <div className="brand brand-large">
            <span className="brand-mark">✦</span>
            <span>AI BAP</span>
          </div>
          <div className="intro-content">
            <span className="eyebrow">AI-POWERED BUSINESS ANALYSIS</span>
            <h1>
              Smarter analysis.
              <br />
              Better delivery.
            </h1>
            <p>
              Manage projects, requirements, user stories, tasks, and sprints in
              one intelligent workspace.
            </p>
            <div className="feature-tags">
              <span>Project Management</span>
              <span>AI User Stories</span>
              <span>Agile Workflows</span>
            </div>
          </div>
          <p className="intro-footer">AI BAP · Business Analysis Platform</p>
        </section>
        <section className="form-panel">
          <div className="login-card">
            <span className="eyebrow">WELCOME BACK</span>
            <h2>Sign in to your account</h2>
            <p className="form-description">
              Enter your credentials to access your workspace.
            </p>
            <form onSubmit={handleLogin}>
              <label htmlFor="email">Email address</label>
              <input
                id="email"
                type="email"
                autoComplete="username"
                placeholder="name@company.com"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                placeholder="Enter your password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
              {error && (
                <div className="error-message" role="alert">
                  {error}
                </div>
              )}
              <button
                className="primary-button"
                type="submit"
                disabled={isLoading}
              >
                {isLoading ? "Signing in..." : "Sign In →"}
              </button>
            </form>
            <p className="security-note">
              Protected by JWT-based authentication.
            </p>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark">✦</span>
          <span>AI BAP</span>
        </div>

        <div className="header-actions">
          {currentUser && (
            <span className="user-role">
              {currentUser.full_name} · {currentUser.record_number} ·{" "}
              {currentUser.role === "business_analyst"
                ? "Business Analyst"
                : currentUser.role === "reviewer"
                  ? "Reviewer"
                  : "Admin"}
            </span>
          )}

          <button className="secondary-button" onClick={logout}>
            Sign Out
          </button>
        </div>
      </header>
      <div className="workspace-layout">
        <aside className="sidebar">
          <p className="sidebar-label">WORKSPACE</p>
          <button
            className={`nav-item ${page === "dashboard" ? "active" : ""}`}
            onClick={() => {
              setPage("dashboard");
              setError("");
              setSuccess("");
            }}
          >
            ◫ Dashboard
          </button>
          <button
            className={`nav-item ${page === "projects" ? "active" : ""}`}
            onClick={() => {
              setPage("projects");
              setError("");
              setSuccess("");
            }}
          >
            ▣ Projects
          </button>
          <button
            className={`nav-item ${page === "requirements" ? "active" : ""}`}
            onClick={() => {
              setPage("requirements");
              setError("");
              setSuccess("");
            }}
          >
            ☷ Requirements
          </button>
          <button
            className={`nav-item ${page === "user-stories" ? "active" : ""}`}
            onClick={() => {
              setPage("user-stories");
              setError("");
              setSuccess("");
            }}
          >
            ✦ User Stories
          </button>
          <div className="sidebar-bottom">
            <span className="sidebar-label">AI BAP v1.0</span>
          </div>
        </aside>
        <section className="workspace-content">
          <div className="page-heading">
            <div>
              <span className="eyebrow">AI BAP WORKSPACE</span>
              <h1>
                {page === "dashboard"
                  ? "Dashboard"
                  : page === "projects"
                    ? "Projects"
                    : page === "requirements"
                      ? "Requirements"
                      : "User Stories"}
              </h1>
              <p>
                {page === "dashboard"
                  ? "Overview of your business analysis projects."
                  : page === "projects"
                    ? "Create and manage your projects."
                    : page === "requirements"
                      ? "Manage requirements for a selected project."
                      : "Generate, review, and save user story drafts."}
              </p>
            </div>
            {page === "user-stories" && canCreateContent ? (
              <button
                className="primary-button create-button"
                disabled={!storyRequirementId}
                onClick={() => {
                  clearStoryEditor();
                  setShowStoryForm(true);
                  setSuccess("");
                }}
              >
                + New User Story
              </button>
            ) : page !== "requirements" && canCreateContent ? (
              <button
                className="primary-button create-button"
                onClick={() => {
                  setPage("projects");
                  setShowProjectForm(true);
                  setSuccess("");
                }}
              >
                + New Project
              </button>
            ) : page === "requirements" && canCreateContent ? (
              <button
                className="primary-button create-button"
                disabled={!selectedProjectId}
                onClick={() => {
                  setShowRequirementForm(true);
                  setSuccess("");
                }}
              >
                + New Requirement
              </button>
            ) : null}
          </div>
          {error && (
            <div className="error-message" role="alert">
              {error}
            </div>
          )}
          {success && (
            <div className="success-message" role="status">
              ✓ {success}
            </div>
          )}
          {page === "dashboard" && (
            <>
              <div className="stats-grid">
                <div className="stat-card">
                  <span>Total Projects</span>
                  <strong>{totalProjects}</strong>
                  <small>Projects in your workspace</small>
                </div>
                <div className="stat-card">
                  <span>Projects on This Page</span>
                  <strong>{projects.length}</strong>
                  <small>Current API page</small>
                </div>
                <div className="stat-card">
                  <span>Active on This Page</span>
                  <strong>
                    {
                      projects.filter((project) => project.status === "active")
                        .length
                    }
                  </strong>
                  <small>Current API page only</small>
                </div>
              </div>
              <div className="content-card">
                <h2>Recent Projects</h2>
                {isLoading ? (
                  <p>Loading projects...</p>
                ) : (
                  <ProjectTable projects={projects.slice(0, 5)} />
                )}
              </div>
            </>
          )}
          {page === "projects" && (
            <>
              {canCreateContent && showProjectForm && (
                <div className="content-card">
                  <h2>Create New Project</h2>
                  <form className="project-form" onSubmit={handleCreateProject}>
                    <label htmlFor="project-name">Project Name</label>
                    <input
                      id="project-name"
                      maxLength={120}
                      value={projectName}
                      onChange={(event) => setProjectName(event.target.value)}
                      required
                    />
                    <label htmlFor="project-description">Description</label>
                    <textarea
                      id="project-description"
                      maxLength={2000}
                      rows={4}
                      value={projectDescription}
                      onChange={(event) =>
                        setProjectDescription(event.target.value)
                      }
                    />
                    <label htmlFor="project-status">Status</label>
                    <select
                      id="project-status"
                      value={projectStatus}
                      onChange={(event) =>
                        setProjectStatus(event.target.value as ProjectStatus)
                      }
                    >
                      {Object.entries(PROJECT_STATUS).map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                    <div className="form-actions">
                      <button
                        type="button"
                        className="secondary-light-button"
                        onClick={() => setShowProjectForm(false)}
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="primary-button"
                        disabled={isSaving}
                      >
                        {isSaving ? "Saving..." : "Create Project"}
                      </button>
                    </div>
                  </form>
                </div>
              )}
              <div className="content-card">
                <h2>All Projects</h2>
                {isLoading ? (
                  <p>Loading projects...</p>
                ) : (
                  <ProjectTable projects={projects} />
                )}
                <Pagination
                  offset={projectOffset}
                  total={totalProjects}
                  loading={isLoading}
                  onChange={setProjectOffset}
                />
              </div>
            </>
          )}
          {page === "user-stories" && (
            <>
              <div className="content-card">
                <h2>Select Project & Requirement</h2>
                <div className="project-form">
                  <label htmlFor="story-project">Project</label>
                  <select
                    id="story-project"
                    value={storyProjectId}
                    onChange={(event) => {
                      setStoryProjectId(event.target.value);
                      setStoryRequirementId("");
                      clearAuditHistory();
                      setStories([]);
                      setTotalStories(0);
                      setStoryOffset(0);
                      clearStoryEditor();
                      setShowStoryForm(false);
                      setSuccess("");
                    }}
                  >
                    <option value="">Choose a project</option>
                    {projects.map((project) => (
                      <option key={project.id} value={project.id}>
                        {project.record_number} — {project.name}
                      </option>
                    ))}
                  </select>
                  {totalProjects > projects.length && (
                    <p className="form-description">
                      Project selection currently shows only the loaded project
                      page.
                    </p>
                  )}
                  <label htmlFor="story-requirement">Requirement</label>
                  <select
                    id="story-requirement"
                    disabled={!storyProjectId || isLoading}
                    value={storyRequirementId}
                    onChange={(event) => {
                      setStoryRequirementId(event.target.value);
                      clearAuditHistory();
                      setStories([]);
                      setTotalStories(0);
                      setStoryOffset(0);
                      clearStoryEditor();
                      setShowStoryForm(false);
                      setSuccess("");
                    }}
                  >
                    <option value="">Choose a requirement</option>
                    {storyRequirements.map((requirement) => (
                      <option key={requirement.id} value={requirement.id}>
                        {requirement.record_number} — {requirement.title}
                      </option>
                    ))}
                  </select>
                  {storyRequirements.length === 100 && (
                    <p className="form-description">
                      Only the first 100 requirements are available in this
                      selector.
                    </p>
                  )}
                </div>
              </div>
              {canCreateContent && storyRequirementId && (
                <div className="content-card">
                  <h2>AI-Assisted Draft Generation</h2>
                  <p className="form-description">
                    AI drafts are not saved automatically. Review the content
                    before saving it as Draft.
                  </p>
                  <button
                    className="primary-button"
                    type="button"
                    disabled={isGenerating || isSaving}
                    onClick={() => void handleGenerateStory()}
                  >
                    {isGenerating ? "Generating..." : "✦ Generate AI Draft"}
                  </button>
                </div>
              )}
              {canCreateContent && storyRequirementId && showStoryForm && (
                <div className="content-card">
                  <h2>{aiDraft ? "Review AI Draft" : "Create User Story"}</h2>
                  <form className="project-form" onSubmit={handleCreateStory}>
                    <label htmlFor="story-title">Title</label>
                    <input
                      id="story-title"
                      maxLength={160}
                      required
                      value={storyTitle}
                      onChange={(event) => setStoryTitle(event.target.value)}
                    />
                    <label htmlFor="story-description">Description</label>
                    <textarea
                      id="story-description"
                      rows={5}
                      maxLength={5000}
                      required
                      value={storyDescription}
                      onChange={(event) =>
                        setStoryDescription(event.target.value)
                      }
                    />
                    <label htmlFor="story-criteria">
                      Acceptance Criteria (one per line)
                    </label>
                    <textarea
                      id="story-criteria"
                      rows={6}
                      value={criteriaText}
                      onChange={(event) => setCriteriaText(event.target.value)}
                      placeholder="Given ... When ... Then ..."
                    />
                    {aiDraft && (
                      <label
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 10,
                          marginBottom: 18,
                        }}
                      >
                        <input
                          type="checkbox"
                          style={{ width: "auto", margin: 0 }}
                          checked={reviewed}
                          onChange={(event) =>
                            setReviewed(event.target.checked)
                          }
                        />
                        I have reviewed the AI-generated content and accept
                        responsibility for saving this draft.
                      </label>
                    )}
                    <div className="form-actions">
                      <button
                        type="button"
                        className="secondary-light-button"
                        onClick={() => {
                          setShowStoryForm(false);
                          clearStoryEditor();
                        }}
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="primary-button"
                        disabled={isSaving || (aiDraft !== null && !reviewed)}
                      >
                        {isSaving ? "Saving..." : "Save as Draft"}
                      </button>
                    </div>
                  </form>
                </div>
              )}
              {storyRequirementId && (
                <div className="content-card">
                  <h2>Saved User Stories</h2>
                  {isLoading ? (
                    <p>Loading user stories...</p>
                  ) : (
                    <UserStoryTable
                      stories={stories}
                      currentUser={currentUser}
                      isSaving={isSaving}
                      selectedAuditStoryId={selectedAuditStoryId}
                      isLoadingAudit={isLoadingAudit}
                      onSubmitForReview={handleSubmitStoryForReview}
                      onReview={handleReviewStory}
                      onViewAuditHistory={handleViewAuditHistory}
                    />
                  )}
                  <Pagination
                    offset={storyOffset}
                    total={totalStories}
                    loading={isLoading}
                    onChange={setStoryOffset}
                  />
                </div>
              )}
              {selectedAuditStoryId && (
                <div className="content-card">
                  <h2>User Story Audit History</h2>
                  {isLoadingAudit ? (
                    <p>Loading audit history...</p>
                  ) : auditError ? (
                    <div className="error-message" role="alert">
                      {auditError}
                    </div>
                  ) : auditEvents.length === 0 ? (
                    <p className="empty-state">
                      No approval or rejection history is available for this user
                      story.
                    </p>
                  ) : (
                    <div className="table-wrapper">
                      <table className="projects-table">
                        <thead>
                          <tr>
                            <th>Action</th>
                            <th>Previous Status</th>
                            <th>New Status</th>
                            <th>Recorded</th>
                          </tr>
                        </thead>
                        <tbody>
                          {auditEvents.map((event) => (
                            <tr key={event.id}>
                              <td>{event.action}</td>
                              <td>{event.previous_status}</td>
                              <td>{event.new_status}</td>
                              <td>
                                {new Date(event.created_at).toLocaleString()}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
          {page === "requirements" && (
            <>
              <div className="content-card">
                <h2>Select Project</h2>
                <label htmlFor="requirement-project">Project</label>
                <select
                  id="requirement-project"
                  value={selectedProjectId}
                  onChange={(event) => {
                    setSelectedProjectId(event.target.value);
                    clearAuditHistory();
                    setRequirementOffset(0);
                    setRequirements([]);
                    setTotalRequirements(0);
                    setShowRequirementForm(false);
                    setSuccess("");
                  }}
                >
                  <option value="">Choose a project</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.record_number} — {project.name}
                    </option>
                  ))}
                </select>
                {totalProjects > projects.length && (
                  <p className="form-description">
                    Only projects from the current page are available here. Use
                    Projects pagination to select another page.
                  </p>
                )}
              </div>
              {canCreateContent && selectedProjectId && showRequirementForm && (
                <div className="content-card">
                  <h2>Create New Requirement</h2>
                  <form
                    className="project-form"
                    onSubmit={handleCreateRequirement}
                  >
                    <label htmlFor="requirement-title">Title</label>
                    <input
                      id="requirement-title"
                      maxLength={160}
                      value={requirementTitle}
                      onChange={(event) =>
                        setRequirementTitle(event.target.value)
                      }
                      required
                    />
                    <label htmlFor="requirement-description">Description</label>
                    <textarea
                      id="requirement-description"
                      maxLength={5000}
                      rows={5}
                      value={requirementDescription}
                      onChange={(event) =>
                        setRequirementDescription(event.target.value)
                      }
                      required
                    />
                    <label htmlFor="requirement-priority">Priority</label>
                    <select
                      id="requirement-priority"
                      value={requirementPriority}
                      onChange={(event) =>
                        setRequirementPriority(
                          event.target.value as RequirementPriority,
                        )
                      }
                    >
                      {Object.entries(PRIORITY).map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                    <label htmlFor="requirement-status">Status</label>
                    <select
                      id="requirement-status"
                      value={requirementStatus}
                      onChange={(event) =>
                        setRequirementStatus(
                          event.target.value as RequirementStatus,
                        )
                      }
                    >
                      {Object.entries(REQUIREMENT_STATUS).map(
                        ([value, label]) => (
                          <option key={value} value={value}>
                            {label}
                          </option>
                        ),
                      )}
                    </select>
                    <div className="form-actions">
                      <button
                        type="button"
                        className="secondary-light-button"
                        onClick={() => setShowRequirementForm(false)}
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="primary-button"
                        disabled={isSaving}
                      >
                        {isSaving ? "Saving..." : "Create Requirement"}
                      </button>
                    </div>
                  </form>
                </div>
              )}
              {selectedProjectId && (
                <div className="content-card">
                  <h2>Project Requirements</h2>
                  {isLoading ? (
                    <p>Loading requirements...</p>
                  ) : (
                    <RequirementTable requirements={requirements} />
                  )}
                  <Pagination
                    offset={requirementOffset}
                    total={totalRequirements}
                    loading={isLoading}
                    onChange={setRequirementOffset}
                  />
                </div>
              )}
            </>
          )}
        </section>
      </div>
    </main>
  );
}

function Pagination({
  offset,
  total,
  loading,
  onChange,
}: {
  offset: number;
  total: number;
  loading: boolean;
  onChange: (offset: number) => void;
}) {
  return (
    <div className="pagination">
      <span>
        {total === 0 ? 0 : offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of{" "}
        {total}
      </span>
      <div>
        <button
          className="secondary-light-button"
          disabled={offset === 0 || loading}
          onClick={() => onChange(Math.max(0, offset - PAGE_SIZE))}
        >
          Previous
        </button>
        <button
          className="secondary-light-button"
          disabled={offset + PAGE_SIZE >= total || loading}
          onClick={() => onChange(offset + PAGE_SIZE)}
        >
          Next
        </button>
      </div>
    </div>
  );
}

function ProjectTable({ projects }: { projects: Project[] }) {
  if (!projects.length)
    return (
      <p className="empty-state">
        No projects found. Create your first project to get started.
      </p>
    );
  return (
    <div className="table-wrapper">
      <table className="projects-table">
        <thead>
          <tr>
            <th>Project ID</th>
            <th>Project Name</th>
            <th>Status</th>
            <th>Created By</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {projects.map((project) => (
            <tr key={project.id}>
              <td>{project.record_number}</td>
              <td>
                <strong>{project.name}</strong>
                <small>{project.description || "No description"}</small>
              </td>
              <td>
                <span className={`status-badge status-${project.status}`}>
                  {PROJECT_STATUS[project.status]}
                </span>
              </td>
              <td>
                {project.created_by
                  ? `${project.created_by.full_name} (${project.created_by.record_number})`
                  : "—"}
              </td>
              <td>{new Date(project.created_at).toLocaleDateString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RequirementTable({ requirements }: { requirements: Requirement[] }) {
  if (!requirements.length)
    return (
      <p className="empty-state">
        No requirements yet. Create the first requirement for this project.
      </p>
    );
  return (
    <div className="table-wrapper">
      <table className="projects-table">
        <thead>
          <tr>
            <th>Requirement ID</th>
            <th>Requirement</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Created By</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {requirements.map((requirement) => (
            <tr key={requirement.id}>
              <td>{requirement.record_number}</td>
              <td>
                <strong>{requirement.title}</strong>
                <small>{requirement.description}</small>
              </td>
              <td>{PRIORITY[requirement.priority]}</td>
              <td>
                <span className="status-badge status-planned">
                  {REQUIREMENT_STATUS[requirement.status]}
                </span>
              </td>
              <td>
                {requirement.created_by
                  ? `${requirement.created_by.full_name} (${requirement.created_by.record_number})`
                  : "—"}
              </td>
              <td>{new Date(requirement.created_at).toLocaleDateString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function UserStoryTable({
  stories,
  currentUser,
  isSaving,
  selectedAuditStoryId,
  isLoadingAudit,
  onSubmitForReview,
  onReview,
  onViewAuditHistory,
}: {
  stories: UserStory[];
  currentUser: CurrentUser | null;
  isSaving: boolean;
  selectedAuditStoryId: string | null;
  isLoadingAudit: boolean;
  onSubmitForReview: (storyId: string) => void;
  onReview: (storyId: string, decision: "approve" | "reject") => void;
  onViewAuditHistory: (storyId: string) => void;
}) {
  if (!stories.length) {
    return (
      <p className="empty-state">No user stories yet for this requirement.</p>
    );
  }

  const canSubmit =
    currentUser?.role === "business_analyst" || currentUser?.role === "admin";

  const canReview =
    currentUser?.role === "reviewer" || currentUser?.role === "admin";

  return (
    <div className="table-wrapper">
      <table className="projects-table">
        <thead>
          <tr>
            <th>Story ID</th>
            <th>User Story</th>
            <th>Status</th>
            <th>Created By</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>

        <tbody>
          {stories.map((story) => (
            <tr key={story.id}>
              <td>{story.record_number}</td>
              <td>
                <strong>{story.title}</strong>
                <small>{story.description}</small>

                {story.acceptance_criteria.length > 0 && (
                  <ul>
                    {story.acceptance_criteria.map((criterion, index) => (
                      <li key={index}>{criterion}</li>
                    ))}
                  </ul>
                )}
              </td>

              <td>
                <span className={`status-badge status-${story.status}`}>
                  {REQUIREMENT_STATUS[story.status]}
                </span>
              </td>

              <td>
                {story.created_by
                  ? `${story.created_by.full_name} (${story.created_by.record_number})`
                  : "—"}
              </td>

              <td>{new Date(story.created_at).toLocaleDateString()}</td>

              <td>
                {canSubmit && story.status === "draft" && (
                  <button
                    type="button"
                    className="secondary-button"
                    style={{
                      color: "#172554",
                      backgroundColor: "#ffffff",
                      border: "1px solid #a5b4fc",
                      fontWeight: 600,
                      whiteSpace: "nowrap",
                      padding: "10px 14px",
                    }}
                    disabled={isSaving}
                    onClick={() => onSubmitForReview(story.id)}
                  >
                    Submit for Review
                  </button>
                )}
                {canReview && story.status === "in_review" && (
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "8px",
                      alignItems: "flex-start",
                    }}
                  >
                    <button
                      type="button"
                      className="secondary-button"
                      style={{
                        color: "#166534",
                        backgroundColor: "#ffffff",
                        border: "1px solid #86efac",
                        fontWeight: 600,
                        padding: "8px 12px",
                      }}
                      disabled={isSaving}
                      onClick={() => onReview(story.id, "approve")}
                    >
                      Approve
                    </button>

                    <button
                      type="button"
                      className="secondary-button"
                      style={{
                        color: "#991b1b",
                        backgroundColor: "#ffffff",
                        border: "1px solid #fca5a5",
                        fontWeight: 600,
                        padding: "8px 12px",
                      }}
                      disabled={isSaving}
                      onClick={() => onReview(story.id, "reject")}
                    >
                      Reject
                    </button>
                  </div>
                )}
                {canReview && (
                  <button
                    type="button"
                    className="secondary-button"
                    style={{
                      color: "#172554",
                      backgroundColor: "#ffffff",
                      border: "1px solid #a5b4fc",
                      fontWeight: 600,
                      marginTop: "8px",
                      padding: "8px 12px",
                    }}
                    disabled={
                      isLoadingAudit && selectedAuditStoryId === story.id
                    }
                    onClick={() => onViewAuditHistory(story.id)}
                  >
                    {isLoadingAudit && selectedAuditStoryId === story.id
                      ? "Loading Audit..."
                      : "View Audit History"}
                  </button>
                )}
                {!canReview && !(canSubmit && story.status === "draft") && (
                  <span>—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;
