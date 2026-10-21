import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import "./App.css";

type ProjectStatus = "planned" | "active" | "on_hold" | "completed";
type ProjectArchiveFilter = "active" | "archived";
type ProjectArchiveAction = "archive" | "restore";
type RequirementPriority = "low" | "medium" | "high" | "critical";
type RequirementStatus = "draft" | "in_review" | "approved" | "rejected";
type Page =
  | "dashboard"
  | "projects"
  | "requirements"
  | "user-stories"
  | "traceability"
  | "delivery";
type StoryStatus = "draft" | "in_review" | "approved" | "rejected";
type SprintStatus = "planned" | "active" | "completed" | "cancelled";
type TaskStatus = "todo" | "in_progress" | "in_review" | "done";

type RecordCreator = {
  record_number: string;
  full_name: string;
};

type Project = {
  id: string;
  record_number: string;
  created_by: RecordCreator | null;
  archived_at: string | null;
  archived_by: RecordCreator | null;
  name: string;
  description: string | null;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
};
type ProjectUpdate = {
  name?: string;
  description?: string | null;
  status?: ProjectStatus;
};
type PendingProjectArchiveAction = {
  projectId: string;
  action: ProjectArchiveAction;
};
type TaskStatusCounts = {
  todo: number;
  in_progress: number;
  in_review: number;
  done: number;
};
type ProjectDashboard = {
  project_id: string;
  total_requirements: number;
  approved_user_stories: number;
  tasks_by_status: TaskStatusCounts;
  active_sprints: number;
};
type TraceabilityTask = {
  id: string;
  title: string;
  status: TaskStatus;
};
type TraceabilityStory = {
  id: string;
  record_number: string;
  title: string;
  status: StoryStatus;
  tasks: TraceabilityTask[];
};
type TraceabilityRequirement = {
  id: string;
  record_number: string;
  title: string;
  status: RequirementStatus;
  priority: RequirementPriority;
  stories: TraceabilityStory[];
};
type ProjectTraceabilityResponse = {
  items: TraceabilityRequirement[];
  total: number;
  limit: number;
  offset: number;
};
type Sprint = {
  id: string;
  project_id: string;
  name: string;
  start_date: string;
  end_date: string;
  status: SprintStatus;
  created_at: string;
  updated_at: string;
};
type Task = {
  id: string;
  story_id: string;
  sprint_id: string | null;
  title: string;
  description: string;
  status: TaskStatus;
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
const SELECTOR_PAGE_SIZE = 20;
const SPRINT_OPTION_PAGE_SIZE = 100;
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
const SPRINT_STATUS: Record<SprintStatus, string> = {
  planned: "Planned",
  active: "Active",
  completed: "Completed",
  cancelled: "Cancelled",
};
const TASK_STATUS: Record<TaskStatus, string> = {
  todo: "To Do",
  in_progress: "In Progress",
  in_review: "In Review",
  done: "Done",
};
const ARCHIVED_PROJECT_READ_ONLY_DETAIL =
  "Archived projects are read-only. Restore the project before making changes.";

class ApiRequestError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
  }
}

function isArchivedProject(project: Project): boolean {
  return project.archived_at !== null;
}

function formatArchiveActor(actor: RecordCreator | null): string {
  if (!actor) return "Unknown user";

  if (actor.full_name && actor.record_number) {
    return `${actor.full_name} (${actor.record_number})`;
  }

  return actor.full_name || actor.record_number || "Unknown user";
}

function formatArchiveTimestamp(archivedAt: string | null): string {
  if (!archivedAt) return "Unknown time";

  const timestamp = new Date(archivedAt);
  return Number.isNaN(timestamp.getTime())
    ? "Unknown time"
    : timestamp.toLocaleString();
}

function ProjectReadOnlyNotice({
  projectId,
  project,
}: {
  projectId: string;
  project: Project | null;
}) {
  if (!projectId) return null;

  if (project === null) {
    return (
      <p className="project-read-only-notice" role="status">
        Project details are unavailable. Write controls are disabled until the
        selected project can be verified.
      </p>
    );
  }

  if (!isArchivedProject(project)) return null;

  return (
    <p className="project-read-only-notice" role="status">
      This project is archived and read-only. An Admin must restore the project
      before changes can be made.
    </p>
  );
}

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
  const projectRequestGeneration = useRef(0);
  const projectViewGeneration = useRef(0);
  const projectArchiveActionGeneration = useRef(0);
  const pendingProjectArchiveActionRef = useRef<string | null>(null);
  const projectMetadataRequestGeneration = useRef(new Map<string, number>());
  const projectMetadataRequests = useRef(new Map<string, Promise<Project | null>>());
  const projectMetadataSessionGeneration = useRef(0);
  const metadataUserId = useRef<string | null>(null);
  const dashboardProjectRequestGeneration = useRef(0);
  const dashboardRequestGeneration = useRef(0);
  const currentDashboardProjectId = useRef("");
  const isDashboardActive = useRef(false);
  const hasDashboardAccess = useRef(false);
  const traceabilityProjectRequestGeneration = useRef(0);
  const traceabilityRequestGeneration = useRef(0);
  const currentTraceabilityProjectId = useRef("");
  const currentTraceabilityOffset = useRef(0);
  const isTraceabilityActive = useRef(false);
  const hasTraceabilityAccess = useRef(false);
  const sprintRequestGeneration = useRef(0);
  const taskSprintOptionRequestGeneration = useRef(0);
  const taskRequestGeneration = useRef(0);
  const taskFormGeneration = useRef(0);
  const deliveryRequirementRequestGeneration = useRef(0);
  const deliveryStoryRequestGeneration = useRef(0);
  const pendingSprintCreationRefresh = useRef(false);
  const pendingTaskRefreshMessage = useRef<string | null>(null);
  const [page, setPage] = useState<Page>("dashboard");
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectMetadataById, setProjectMetadataById] = useState<
    Record<string, Project>
  >({});
  const [totalProjects, setTotalProjects] = useState(0);
  const [projectOffset, setProjectOffset] = useState(0);
  const [projectArchiveFilter, setProjectArchiveFilter] =
    useState<ProjectArchiveFilter>("active");
  const [pendingProjectArchiveAction, setPendingProjectArchiveAction] =
    useState<PendingProjectArchiveAction | null>(null);
  const [dashboardProjects, setDashboardProjects] = useState<Project[]>([]);
  const [dashboardTotalProjects, setDashboardTotalProjects] = useState(0);
  const [dashboardProjectOffset, setDashboardProjectOffset] = useState(0);
  const [dashboardProjectArchiveFilter, setDashboardProjectArchiveFilter] =
    useState<ProjectArchiveFilter>("active");
  const [isLoadingDashboardProjects, setIsLoadingDashboardProjects] =
    useState(false);
  const [dashboardProjectSelectorError, setDashboardProjectSelectorError] =
    useState("");
  const [selectedDashboardProjectId, setSelectedDashboardProjectId] =
    useState("");
  const [dashboardData, setDashboardData] = useState<ProjectDashboard | null>(
    null,
  );
  const [isLoadingDashboard, setIsLoadingDashboard] = useState(false);
  const [dashboardError, setDashboardError] = useState("");
  const [dashboardReloadVersion, setDashboardReloadVersion] = useState(0);
  const [traceabilityProjects, setTraceabilityProjects] = useState<Project[]>([]);
  const [traceabilityTotalProjects, setTraceabilityTotalProjects] = useState(0);
  const [traceabilityProjectOffset, setTraceabilityProjectOffset] = useState(0);
  const [traceabilityProjectArchiveFilter, setTraceabilityProjectArchiveFilter] =
    useState<ProjectArchiveFilter>("active");
  const [isLoadingTraceabilityProjects, setIsLoadingTraceabilityProjects] =
    useState(false);
  const [traceabilityProjectSelectorError, setTraceabilityProjectSelectorError] =
    useState("");
  const [selectedTraceabilityProjectId, setSelectedTraceabilityProjectId] =
    useState("");
  const [traceabilityData, setTraceabilityData] =
    useState<ProjectTraceabilityResponse | null>(null);
  const [traceabilityTotal, setTraceabilityTotal] = useState(0);
  const [traceabilityOffset, setTraceabilityOffset] = useState(0);
  const [isLoadingTraceability, setIsLoadingTraceability] = useState(false);
  const [traceabilityError, setTraceabilityError] = useState("");
  const [traceabilityReloadVersion, setTraceabilityReloadVersion] = useState(0);
  const [sprints, setSprints] = useState<Sprint[]>([]);
  const [totalSprints, setTotalSprints] = useState(0);
  const [sprintOffset, setSprintOffset] = useState(0);
  const [sprintReloadVersion, setSprintReloadVersion] = useState(0);
  const [selectedSprintProjectId, setSelectedSprintProjectId] = useState("");
  const [isLoadingSprints, setIsLoadingSprints] = useState(false);
  const [sprintListError, setSprintListError] = useState("");
  const [taskSprintOptions, setTaskSprintOptions] = useState<Sprint[]>([]);
  const [isLoadingTaskSprintOptions, setIsLoadingTaskSprintOptions] =
    useState(false);
  const [hasLoadedTaskSprintOptions, setHasLoadedTaskSprintOptions] =
    useState(false);
  const [taskSprintOptionError, setTaskSprintOptionError] = useState("");
  const [deliveryRequirements, setDeliveryRequirements] = useState<Requirement[]>([]);
  const [totalDeliveryRequirements, setTotalDeliveryRequirements] = useState(0);
  const [deliveryRequirementOffset, setDeliveryRequirementOffset] = useState(0);
  const [isLoadingDeliveryRequirements, setIsLoadingDeliveryRequirements] =
    useState(false);
  const [hasLoadedDeliveryRequirements, setHasLoadedDeliveryRequirements] =
    useState(false);
  const [deliveryRequirementsError, setDeliveryRequirementsError] = useState("");
  const [selectedTaskRequirementId, setSelectedTaskRequirementId] = useState("");
  const [deliveryStories, setDeliveryStories] = useState<UserStory[]>([]);
  const [totalDeliveryStories, setTotalDeliveryStories] = useState(0);
  const [deliveryStoryOffset, setDeliveryStoryOffset] = useState(0);
  const [isLoadingDeliveryStories, setIsLoadingDeliveryStories] = useState(false);
  const [hasLoadedDeliveryStories, setHasLoadedDeliveryStories] = useState(false);
  const [deliveryStoriesError, setDeliveryStoriesError] = useState("");
  const [selectedTaskStoryId, setSelectedTaskStoryId] = useState("");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [totalTasks, setTotalTasks] = useState(0);
  const [taskOffset, setTaskOffset] = useState(0);
  const [taskReloadVersion, setTaskReloadVersion] = useState(0);
  const [isLoadingTasks, setIsLoadingTasks] = useState(false);
  const [taskListError, setTaskListError] = useState("");
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [totalRequirements, setTotalRequirements] = useState(0);
  const [requirementOffset, setRequirementOffset] = useState(0);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showProjectForm, setShowProjectForm] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [showRequirementForm, setShowRequirementForm] = useState(false);
  const [showSprintForm, setShowSprintForm] = useState(false);
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [projectName, setProjectName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");
  const [projectStatus, setProjectStatus] = useState<ProjectStatus>("planned");
  const [sprintName, setSprintName] = useState("");
  const [sprintStartDate, setSprintStartDate] = useState("");
  const [sprintEndDate, setSprintEndDate] = useState("");
  const [sprintStatus, setSprintStatus] = useState<SprintStatus>("planned");
  const [taskTitle, setTaskTitle] = useState("");
  const [taskDescription, setTaskDescription] = useState("");
  const [taskStatus, setTaskStatus] = useState<TaskStatus>("todo");
  const [requirementTitle, setRequirementTitle] = useState("");
  const [requirementDescription, setRequirementDescription] = useState("");
  const [requirementPriority, setRequirementPriority] =
    useState<RequirementPriority>("medium");
  const [requirementStatus, setRequirementStatus] =
    useState<RequirementStatus>("draft");
  const canCreateContent =
    currentUser?.role === "admin" || currentUser?.role === "business_analyst";
  const canManageProjectArchive = currentUser?.role === "admin";
  const selectedTaskStory =
    deliveryStories.find((story) => story.id === selectedTaskStoryId) ?? null;
  const selectedRequirementProject =
    projectMetadataById[selectedProjectId] ?? null;
  const selectedStoryProject =
    projectMetadataById[storyProjectId] ?? null;
  const selectedDeliveryProject =
    projectMetadataById[selectedSprintProjectId] ?? null;
  const isRequirementProjectWritable =
    selectedRequirementProject !== null &&
    !isArchivedProject(selectedRequirementProject);
  const isStoryProjectWritable =
    selectedStoryProject !== null && !isArchivedProject(selectedStoryProject);
  const isDeliveryProjectWritable =
    selectedDeliveryProject !== null &&
    !isArchivedProject(selectedDeliveryProject);
  const selectedDashboardProject =
    dashboardProjects.find(
      (project) => project.id === selectedDashboardProjectId,
    ) ?? null;
  const selectedTraceabilityProject =
    traceabilityProjects.find(
      (project) => project.id === selectedTraceabilityProjectId,
    ) ?? null;

  const clearAuditHistory = useCallback(() => {
    auditRequestGeneration.current += 1;
    setSelectedAuditStoryId(null);
    setAuditEvents([]);
    setIsLoadingAudit(false);
    setAuditError("");
  }, []);

  const logout = useCallback(() => {
    // I clear the in-memory token and all protected workspace data.
    dashboardProjectRequestGeneration.current += 1;
    dashboardRequestGeneration.current += 1;
    currentDashboardProjectId.current = "";
    isDashboardActive.current = false;
    hasDashboardAccess.current = false;
    traceabilityProjectRequestGeneration.current += 1;
    traceabilityRequestGeneration.current += 1;
    currentTraceabilityProjectId.current = "";
    currentTraceabilityOffset.current = 0;
    isTraceabilityActive.current = false;
    hasTraceabilityAccess.current = false;
    sprintRequestGeneration.current += 1;
    taskSprintOptionRequestGeneration.current += 1;
    taskRequestGeneration.current += 1;
    taskFormGeneration.current += 1;
    deliveryRequirementRequestGeneration.current += 1;
    deliveryStoryRequestGeneration.current += 1;
    projectArchiveActionGeneration.current += 1;
    pendingTaskRefreshMessage.current = null;
    pendingProjectArchiveActionRef.current = null;
    projectMetadataSessionGeneration.current += 1;
    projectMetadataRequestGeneration.current.clear();
    projectMetadataRequests.current.clear();
    metadataUserId.current = null;
    setAccessToken(null);
    setCurrentUser(null);
    setPassword("");
    setProjects([]);
    setProjectMetadataById({});
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
    setDashboardProjects([]);
    setDashboardTotalProjects(0);
    setDashboardProjectOffset(0);
    setDashboardProjectArchiveFilter("active");
    setIsLoadingDashboardProjects(false);
    setDashboardProjectSelectorError("");
    setSelectedDashboardProjectId("");
    setDashboardData(null);
    setIsLoadingDashboard(false);
    setDashboardError("");
    setDashboardReloadVersion(0);
    setTraceabilityProjects([]);
    setTraceabilityTotalProjects(0);
    setTraceabilityProjectOffset(0);
    setTraceabilityProjectArchiveFilter("active");
    setIsLoadingTraceabilityProjects(false);
    setTraceabilityProjectSelectorError("");
    setSelectedTraceabilityProjectId("");
    setTraceabilityData(null);
    setTraceabilityTotal(0);
    setTraceabilityOffset(0);
    setIsLoadingTraceability(false);
    setTraceabilityError("");
    setTraceabilityReloadVersion(0);
    setSprints([]);
    setTotalSprints(0);
    setSprintOffset(0);
    setSelectedSprintProjectId("");
    setIsLoadingSprints(false);
    setSprintListError("");
    setTaskSprintOptions([]);
    setIsLoadingTaskSprintOptions(false);
    setHasLoadedTaskSprintOptions(false);
    setTaskSprintOptionError("");
    setDeliveryRequirements([]);
    setTotalDeliveryRequirements(0);
    setDeliveryRequirementOffset(0);
    setIsLoadingDeliveryRequirements(false);
    setHasLoadedDeliveryRequirements(false);
    setDeliveryRequirementsError("");
    setSelectedTaskRequirementId("");
    setDeliveryStories([]);
    setTotalDeliveryStories(0);
    setDeliveryStoryOffset(0);
    setIsLoadingDeliveryStories(false);
    setHasLoadedDeliveryStories(false);
    setDeliveryStoriesError("");
    setSelectedTaskStoryId("");
    setTasks([]);
    setTotalTasks(0);
    setTaskOffset(0);
    setIsLoadingTasks(false);
    setTaskListError("");
    setTotalRequirements(0);
    setSelectedProjectId("");
    setProjectOffset(0);
    setProjectArchiveFilter("active");
    setPendingProjectArchiveAction(null);
    setEditingProject(null);
    setShowProjectForm(false);
    setShowSprintForm(false);
    setShowTaskForm(false);
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
        throw new ApiRequestError(401, "Your session has expired. Please sign in again.");
      }
      if (!response.ok) {
        const body: unknown = await response.json().catch(() => null);
        const detail =
          body && typeof body === "object" && "detail" in body
            ? (body as { detail: unknown }).detail
            : null;
        throw new ApiRequestError(
          response.status,
          typeof detail === "string"
            ? detail
            : `Request failed (${response.status}).`,
        );
      }
      return response;
    },
    [accessToken, logout],
  );

  const invalidateProjectMetadata = useCallback((projectId: string) => {
    if (!projectId) return;

    projectMetadataRequestGeneration.current.set(
      projectId,
      (projectMetadataRequestGeneration.current.get(projectId) ?? 0) + 1,
    );
    projectMetadataRequests.current.delete(projectId);
    setProjectMetadataById((current) => {
      const remaining = { ...current };
      delete remaining[projectId];
      return remaining;
    });
  }, []);

  const replaceProjectMetadata = useCallback((project: Project) => {
    projectMetadataRequestGeneration.current.set(
      project.id,
      (projectMetadataRequestGeneration.current.get(project.id) ?? 0) + 1,
    );
    projectMetadataRequests.current.delete(project.id);
    setProjectMetadataById((current) => ({
      ...current,
      [project.id]: project,
    }));
  }, []);

  const loadProjectMetadata = useCallback(
    async (projectId: string): Promise<Project | null> => {
      if (!projectId) return null;

      const cachedProject = projectMetadataById[projectId];
      if (cachedProject) return cachedProject;

      const pendingRequest = projectMetadataRequests.current.get(projectId);
      if (pendingRequest) return pendingRequest;

      const requestGeneration =
        (projectMetadataRequestGeneration.current.get(projectId) ?? 0) + 1;
      const sessionGeneration = projectMetadataSessionGeneration.current;
      projectMetadataRequestGeneration.current.set(projectId, requestGeneration);

      const metadataRequest = (async (): Promise<Project | null> => {
        try {
          const response = await request(`/api/v1/projects/${projectId}`);
          const project: Project = await response.json();

          if (project.id !== projectId) {
            throw new Error("The project metadata response belongs to a different project.");
          }

          if (
            projectMetadataRequestGeneration.current.get(projectId) !==
              requestGeneration ||
            projectMetadataSessionGeneration.current !== sessionGeneration
          ) {
            return null;
          }

          setProjectMetadataById((current) => ({
            ...current,
            [projectId]: project,
          }));
          return project;
        } catch {
          return null;
        }
      })();

      projectMetadataRequests.current.set(projectId, metadataRequest);
      void metadataRequest.finally(() => {
        if (projectMetadataRequests.current.get(projectId) === metadataRequest) {
          projectMetadataRequests.current.delete(projectId);
        }
      });

      return metadataRequest;
    },
    [projectMetadataById, request],
  );

  const loadProjects = useCallback(
    async (
      offset: number,
      archiveFilter: ProjectArchiveFilter,
    ): Promise<boolean> => {
      const requestGeneration = projectRequestGeneration.current + 1;
      projectRequestGeneration.current = requestGeneration;
      setIsLoading(true);
      setError("");
      try {
        const response = await request(
          `/api/v1/projects?archived=${archiveFilter === "archived"}&limit=${PAGE_SIZE}&offset=${offset}`,
        );
        const data: Paginated<Project> = await response.json();
        if (projectRequestGeneration.current !== requestGeneration) return false;

        const normalizedOffset =
          data.total === 0
            ? 0
            : Math.floor((data.total - 1) / PAGE_SIZE) * PAGE_SIZE;
        if (offset > normalizedOffset) {
          setProjects([]);
          setTotalProjects(data.total);
          setProjectOffset(normalizedOffset);
          return true;
        }

        setProjects(data.items);
        setTotalProjects(data.total);
        return true;
      } catch (err) {
        if (projectRequestGeneration.current !== requestGeneration) return false;

        setError(
          err instanceof Error ? err.message : "Unable to load projects.",
        );
        return false;
      } finally {
        if (projectRequestGeneration.current === requestGeneration) {
          setIsLoading(false);
        }
      }
    },
    [request],
  );

  async function reconcileArchivedProjectConflict(
    err: unknown,
    projectId: string,
  ) {
    if (
      !(err instanceof ApiRequestError) ||
      err.status !== 409 ||
      err.message !== ARCHIVED_PROJECT_READ_ONLY_DETAIL
    ) {
      return;
    }

    invalidateProjectMetadata(projectId);
    await loadProjectMetadata(projectId);
    await loadProjects(projectOffset, projectArchiveFilter);
  }

  const loadDashboardProjects = useCallback(
    async (
      offset: number,
      archiveFilter: ProjectArchiveFilter,
    ): Promise<boolean> => {
      const requestGeneration =
        dashboardProjectRequestGeneration.current + 1;
      dashboardProjectRequestGeneration.current = requestGeneration;
      setIsLoadingDashboardProjects(true);
      setDashboardProjectSelectorError("");
      try {
        const response = await request(
          `/api/v1/projects?archived=${archiveFilter === "archived"}&limit=${SELECTOR_PAGE_SIZE}&offset=${offset}`,
        );
        const data: Paginated<Project> = await response.json();
        if (
          dashboardProjectRequestGeneration.current !== requestGeneration
        ) {
          return false;
        }

        const normalizedOffset =
          data.total === 0
            ? 0
            : Math.floor((data.total - 1) / SELECTOR_PAGE_SIZE) *
              SELECTOR_PAGE_SIZE;
        if (offset > normalizedOffset) {
          dashboardRequestGeneration.current += 1;
          currentDashboardProjectId.current = "";
          setDashboardProjects([]);
          setDashboardTotalProjects(data.total);
          setDashboardProjectOffset(normalizedOffset);
          setSelectedDashboardProjectId("");
          setDashboardData(null);
          setIsLoadingDashboard(false);
          setDashboardError("");
          return true;
        }

        setDashboardProjects(data.items);
        setDashboardTotalProjects(data.total);
        return true;
      } catch (err) {
        if (
          dashboardProjectRequestGeneration.current !== requestGeneration
        ) {
          return false;
        }

        setDashboardProjects([]);
        setDashboardTotalProjects(0);
        setDashboardProjectSelectorError(
          err instanceof Error
            ? err.message
            : "Unable to load projects for the project dashboard.",
        );
        return false;
      } finally {
        if (dashboardProjectRequestGeneration.current === requestGeneration) {
          setIsLoadingDashboardProjects(false);
        }
      }
    },
    [request],
  );

  const loadProjectDashboard = useCallback(
    async (projectId: string): Promise<boolean> => {
      const requestedProjectId = projectId;
      const requestGeneration = dashboardRequestGeneration.current + 1;
      dashboardRequestGeneration.current = requestGeneration;

      if (!projectId) {
        setDashboardData(null);
        setIsLoadingDashboard(false);
        setDashboardError("");
        return false;
      }

      setDashboardData(null);
      setIsLoadingDashboard(true);
      setDashboardError("");
      try {
        const response = await request(
          `/api/v1/projects/${requestedProjectId}/dashboard`,
        );
        const data: ProjectDashboard = await response.json();
        if (dashboardRequestGeneration.current !== requestGeneration) {
          return false;
        }

        if (data.project_id !== requestedProjectId) {
          setDashboardData(null);
          setDashboardError(
            "The dashboard response belongs to a different project. Please retry.",
          );
          return false;
        }

        setDashboardData(data);
        return true;
      } catch (err) {
        if (dashboardRequestGeneration.current !== requestGeneration) {
          return false;
        }

        setDashboardData(null);
        setDashboardError(
          err instanceof Error
            ? err.message
            : "Unable to load the project dashboard.",
        );
        return false;
      } finally {
        if (dashboardRequestGeneration.current === requestGeneration) {
          setIsLoadingDashboard(false);
        }
      }
    },
    [request],
  );

  const loadTraceabilityProjects = useCallback(
    async (
      offset: number,
      archiveFilter: ProjectArchiveFilter,
    ): Promise<boolean> => {
      const requestGeneration = traceabilityProjectRequestGeneration.current + 1;
      traceabilityProjectRequestGeneration.current = requestGeneration;
      setIsLoadingTraceabilityProjects(true);
      setTraceabilityProjectSelectorError("");
      try {
        const response = await request(
          `/api/v1/projects?archived=${archiveFilter === "archived"}&limit=${SELECTOR_PAGE_SIZE}&offset=${offset}`,
        );
        const data: Paginated<Project> = await response.json();
        if (
          traceabilityProjectRequestGeneration.current !== requestGeneration ||
          !isTraceabilityActive.current ||
          !hasTraceabilityAccess.current
        ) {
          return false;
        }

        const normalizedOffset =
          data.total === 0
            ? 0
            : Math.floor((data.total - 1) / SELECTOR_PAGE_SIZE) *
              SELECTOR_PAGE_SIZE;
        if (offset > normalizedOffset) {
          traceabilityRequestGeneration.current += 1;
          currentTraceabilityProjectId.current = "";
          currentTraceabilityOffset.current = 0;
          setTraceabilityProjects([]);
          setTraceabilityTotalProjects(data.total);
          setTraceabilityProjectOffset(normalizedOffset);
          setSelectedTraceabilityProjectId("");
          setTraceabilityData(null);
          setTraceabilityTotal(0);
          setTraceabilityOffset(0);
          setIsLoadingTraceability(false);
          setTraceabilityError("");
          return true;
        }

        setTraceabilityProjects(data.items);
        setTraceabilityTotalProjects(data.total);
        return true;
      } catch (err) {
        if (
          traceabilityProjectRequestGeneration.current !== requestGeneration ||
          !isTraceabilityActive.current ||
          !hasTraceabilityAccess.current
        ) {
          return false;
        }

        setTraceabilityProjects([]);
        setTraceabilityTotalProjects(0);
        setTraceabilityProjectSelectorError(
          err instanceof Error
            ? err.message
            : "Unable to load projects for traceability.",
        );
        return false;
      } finally {
        if (traceabilityProjectRequestGeneration.current === requestGeneration) {
          setIsLoadingTraceabilityProjects(false);
        }
      }
    },
    [request],
  );

  const loadProjectTraceability = useCallback(
    async (projectId: string, offset: number): Promise<boolean> => {
      const requestedProjectId = projectId;
      const requestedOffset = offset;
      const requestGeneration = traceabilityRequestGeneration.current + 1;
      traceabilityRequestGeneration.current = requestGeneration;

      if (!projectId) {
        setTraceabilityData(null);
        setTraceabilityTotal(0);
        setIsLoadingTraceability(false);
        setTraceabilityError("");
        return false;
      }

      setTraceabilityData(null);
      setIsLoadingTraceability(true);
      setTraceabilityError("");
      try {
        const params = new URLSearchParams({
          limit: String(SELECTOR_PAGE_SIZE),
          offset: String(requestedOffset),
        });
        const response = await request(
          `/api/v1/projects/${requestedProjectId}/traceability?${params}`,
        );
        const data: ProjectTraceabilityResponse = await response.json();
        if (
          traceabilityRequestGeneration.current !== requestGeneration ||
          !isTraceabilityActive.current ||
          !hasTraceabilityAccess.current ||
          currentTraceabilityProjectId.current !== requestedProjectId ||
          currentTraceabilityOffset.current !== requestedOffset
        ) {
          return false;
        }

        const normalizedOffset =
          data.total === 0
            ? 0
            : Math.floor((data.total - 1) / SELECTOR_PAGE_SIZE) *
              SELECTOR_PAGE_SIZE;
        if (requestedOffset > normalizedOffset) {
          setTraceabilityData(null);
          setTraceabilityTotal(data.total);
          currentTraceabilityOffset.current = normalizedOffset;
          setTraceabilityOffset(normalizedOffset);
          return true;
        }

        setTraceabilityData(data);
        setTraceabilityTotal(data.total);
        return true;
      } catch (err) {
        if (
          traceabilityRequestGeneration.current !== requestGeneration ||
          !isTraceabilityActive.current ||
          !hasTraceabilityAccess.current ||
          currentTraceabilityProjectId.current !== requestedProjectId ||
          currentTraceabilityOffset.current !== requestedOffset
        ) {
          return false;
        }

        setTraceabilityData(null);
        setTraceabilityTotal(0);
        setTraceabilityError(
          err instanceof Error
            ? err.message
            : "Unable to load project traceability.",
        );
        return false;
      } finally {
        if (traceabilityRequestGeneration.current === requestGeneration) {
          setIsLoadingTraceability(false);
        }
      }
    },
    [request],
  );

  const loadSprints = useCallback(
    async (projectId: string, offset: number): Promise<boolean> => {
      const requestGeneration = sprintRequestGeneration.current + 1;
      sprintRequestGeneration.current = requestGeneration;

      if (!projectId) {
        setSprints([]);
        setTotalSprints(0);
        setIsLoadingSprints(false);
        setSprintListError("");
        return false;
      }

      setIsLoadingSprints(true);
      setSprintListError("");
      try {
        const params = new URLSearchParams({
          project_id: projectId,
          limit: String(PAGE_SIZE),
          offset: String(offset),
        });
        const response = await request(`/api/v1/sprints?${params}`);
        const data: Paginated<Sprint> = await response.json();

        if (sprintRequestGeneration.current !== requestGeneration) return false;

        const normalizedOffset =
          data.total === 0
            ? 0
            : Math.floor((data.total - 1) / PAGE_SIZE) * PAGE_SIZE;
        if (offset > normalizedOffset) {
          setSprints([]);
          setTotalSprints(data.total);
          setSprintOffset(normalizedOffset);
          return true;
        }

        setSprints(data.items);
        setTotalSprints(data.total);
        return true;
      } catch (err) {
        if (sprintRequestGeneration.current !== requestGeneration) return false;

        setSprintListError(
          err instanceof Error ? err.message : "Unable to load sprints.",
        );
        return false;
      } finally {
        if (sprintRequestGeneration.current === requestGeneration) {
          setIsLoadingSprints(false);
        }
      }
    },
    [request],
  );

  const loadTaskSprintOptions = useCallback(
    async (projectId: string) => {
      const requestGeneration = taskSprintOptionRequestGeneration.current + 1;
      taskSprintOptionRequestGeneration.current = requestGeneration;

      if (!projectId) {
        setTaskSprintOptions([]);
        setIsLoadingTaskSprintOptions(false);
        setHasLoadedTaskSprintOptions(false);
        setTaskSprintOptionError("");
        return;
      }

      setIsLoadingTaskSprintOptions(true);
      setTaskSprintOptions([]);
      setHasLoadedTaskSprintOptions(false);
      setTaskSprintOptionError("");
      try {
        const allSprints: Sprint[] = [];
        let offset = 0;
        let total = 0;

        do {
          const params = new URLSearchParams({
            project_id: projectId,
            limit: String(SPRINT_OPTION_PAGE_SIZE),
            offset: String(offset),
          });
          const response = await request(`/api/v1/sprints?${params}`);
          const data: Paginated<Sprint> = await response.json();

          if (taskSprintOptionRequestGeneration.current !== requestGeneration) {
            return;
          }

          allSprints.push(...data.items);
          total = data.total;
          offset += data.items.length;
        } while (offset < total && offset > 0);

        if (taskSprintOptionRequestGeneration.current !== requestGeneration) {
          return;
        }
        setTaskSprintOptions(allSprints);
        setHasLoadedTaskSprintOptions(true);
      } catch (err) {
        if (taskSprintOptionRequestGeneration.current !== requestGeneration) {
          return;
        }
        setTaskSprintOptions([]);
        setHasLoadedTaskSprintOptions(false);
        setTaskSprintOptionError(
          err instanceof Error
            ? err.message
            : "Unable to load sprint assignment options.",
        );
      } finally {
        if (taskSprintOptionRequestGeneration.current === requestGeneration) {
          setIsLoadingTaskSprintOptions(false);
        }
      }
    },
    [request],
  );

  const loadDeliveryRequirements = useCallback(
    async (projectId: string, offset: number) => {
      const requestGeneration = deliveryRequirementRequestGeneration.current + 1;
      deliveryRequirementRequestGeneration.current = requestGeneration;

      if (!projectId) {
        setDeliveryRequirements([]);
        setTotalDeliveryRequirements(0);
        setIsLoadingDeliveryRequirements(false);
        setHasLoadedDeliveryRequirements(false);
        setDeliveryRequirementsError("");
        return;
      }

      setIsLoadingDeliveryRequirements(true);
      setHasLoadedDeliveryRequirements(false);
      setDeliveryRequirementsError("");
      try {
        const params = new URLSearchParams({
          project_id: projectId,
          limit: String(SELECTOR_PAGE_SIZE),
          offset: String(offset),
        });
        const response = await request(`/api/v1/requirements?${params}`);
        const data: Paginated<Requirement> = await response.json();

        if (deliveryRequirementRequestGeneration.current !== requestGeneration) {
          return;
        }
        const normalizedOffset =
          data.total === 0
            ? 0
            : Math.floor((data.total - 1) / SELECTOR_PAGE_SIZE) *
              SELECTOR_PAGE_SIZE;
        if (offset > normalizedOffset) {
          setDeliveryRequirements([]);
          setTotalDeliveryRequirements(data.total);
          setDeliveryRequirementOffset(normalizedOffset);
          return;
        }
        setDeliveryRequirements(data.items);
        setTotalDeliveryRequirements(data.total);
        setHasLoadedDeliveryRequirements(true);
      } catch (err) {
        if (deliveryRequirementRequestGeneration.current !== requestGeneration) {
          return;
        }
        setDeliveryRequirements([]);
        setTotalDeliveryRequirements(0);
        setDeliveryRequirementsError(
          err instanceof Error
            ? err.message
            : "Unable to load requirements for task selection.",
        );
      } finally {
        if (deliveryRequirementRequestGeneration.current === requestGeneration) {
          setIsLoadingDeliveryRequirements(false);
        }
      }
    },
    [request],
  );

  const loadDeliveryStories = useCallback(
    async (requirementId: string, offset: number) => {
      const requestGeneration = deliveryStoryRequestGeneration.current + 1;
      deliveryStoryRequestGeneration.current = requestGeneration;

      if (!requirementId) {
        setDeliveryStories([]);
        setTotalDeliveryStories(0);
        setIsLoadingDeliveryStories(false);
        setHasLoadedDeliveryStories(false);
        setDeliveryStoriesError("");
        return;
      }

      setIsLoadingDeliveryStories(true);
      setHasLoadedDeliveryStories(false);
      setDeliveryStoriesError("");
      try {
        const params = new URLSearchParams({
          requirement_id: requirementId,
          limit: String(SELECTOR_PAGE_SIZE),
          offset: String(offset),
        });
        const response = await request(`/api/v1/user-stories?${params}`);
        const data: Paginated<UserStory> = await response.json();

        if (deliveryStoryRequestGeneration.current !== requestGeneration) return;
        const normalizedOffset =
          data.total === 0
            ? 0
            : Math.floor((data.total - 1) / SELECTOR_PAGE_SIZE) *
              SELECTOR_PAGE_SIZE;
        if (offset > normalizedOffset) {
          setDeliveryStories([]);
          setTotalDeliveryStories(data.total);
          setDeliveryStoryOffset(normalizedOffset);
          return;
        }
        setDeliveryStories(data.items);
        setTotalDeliveryStories(data.total);
        setHasLoadedDeliveryStories(true);
      } catch (err) {
        if (deliveryStoryRequestGeneration.current !== requestGeneration) return;
        setDeliveryStories([]);
        setTotalDeliveryStories(0);
        setDeliveryStoriesError(
          err instanceof Error
            ? err.message
            : "Unable to load user stories for task selection.",
        );
      } finally {
        if (deliveryStoryRequestGeneration.current === requestGeneration) {
          setIsLoadingDeliveryStories(false);
        }
      }
    },
    [request],
  );

  const loadTasks = useCallback(
    async (storyId: string, offset: number): Promise<boolean> => {
      const requestGeneration = taskRequestGeneration.current + 1;
      taskRequestGeneration.current = requestGeneration;

      if (!storyId) {
        setTasks([]);
        setTotalTasks(0);
        setIsLoadingTasks(false);
        setTaskListError("");
        return false;
      }

      setIsLoadingTasks(true);
      setTaskListError("");
      try {
        const params = new URLSearchParams({
          story_id: storyId,
          limit: String(PAGE_SIZE),
          offset: String(offset),
        });
        const response = await request(`/api/v1/tasks?${params}`);
        const data: Paginated<Task> = await response.json();

        if (taskRequestGeneration.current !== requestGeneration) return false;
        const normalizedOffset =
          data.total === 0
            ? 0
            : Math.floor((data.total - 1) / PAGE_SIZE) * PAGE_SIZE;
        if (offset > normalizedOffset) {
          setTasks([]);
          setTotalTasks(data.total);
          setTaskOffset(normalizedOffset);
          return true;
        }
        setTasks(data.items);
        setTotalTasks(data.total);
        return true;
      } catch (err) {
        if (taskRequestGeneration.current !== requestGeneration) return false;
        setTaskListError(
          err instanceof Error ? err.message : "Unable to load tasks.",
        );
        return false;
      } finally {
        if (taskRequestGeneration.current === requestGeneration) {
          setIsLoadingTasks(false);
        }
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
    if (!storyRequirementId || !isStoryProjectWritable) return;
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
      await reconcileArchivedProjectConflict(err, storyProjectId);
      setError(err instanceof Error ? err.message : "AI generation failed.");
    } finally {
      setIsGenerating(false);
    }
  }

  async function handleCreateStory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!storyRequirementId || !isStoryProjectWritable) return;
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
      refreshTraceabilityForProject(storyProjectId);
      setSuccess("User story saved as Draft.");
    } catch (err) {
      await reconcileArchivedProjectConflict(err, storyProjectId);
      setError(
        err instanceof Error ? err.message : "Unable to save user story.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function handleSubmitStoryForReview(storyId: string) {
    if (!isStoryProjectWritable) return;

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
      refreshTraceabilityForProject(storyProjectId);
      setSuccess("User story submitted for review successfully.");
    } catch (err) {
      await reconcileArchivedProjectConflict(err, storyProjectId);
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
    if (!isStoryProjectWritable) return;

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

      refreshDashboardForProject(storyProjectId);
      refreshTraceabilityForProject(storyProjectId);
      await loadStories(storyRequirementId, storyOffset);

      setSuccess(
        decision === "approve"
          ? "User story approved successfully."
          : "User story rejected successfully.",
      );
    } catch (err) {
      await reconcileArchivedProjectConflict(err, storyProjectId);
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
    if (accessToken) void loadProjects(projectOffset, projectArchiveFilter);
  }, [accessToken, projectOffset, projectArchiveFilter, loadProjects]);

  useEffect(() => {
    const currentUserId = currentUser?.id ?? null;
    if (metadataUserId.current === currentUserId) return;

    metadataUserId.current = currentUserId;
    projectMetadataSessionGeneration.current += 1;
    projectMetadataRequestGeneration.current.clear();
    projectMetadataRequests.current.clear();
    setProjectMetadataById({});
  }, [currentUser?.id]);

  useEffect(() => {
    if (!accessToken || page !== "requirements" || !selectedProjectId) return;

    void loadProjectMetadata(selectedProjectId);
  }, [accessToken, page, selectedProjectId, loadProjectMetadata]);

  useEffect(() => {
    if (!accessToken || page !== "user-stories" || !storyProjectId) return;

    void loadProjectMetadata(storyProjectId);
  }, [accessToken, page, storyProjectId, loadProjectMetadata]);

  useEffect(() => {
    if (!accessToken || page !== "delivery" || !selectedSprintProjectId) return;

    void loadProjectMetadata(selectedSprintProjectId);
  }, [
    accessToken,
    page,
    selectedSprintProjectId,
    loadProjectMetadata,
  ]);

  useEffect(() => {
    hasDashboardAccess.current = Boolean(accessToken);
    isDashboardActive.current =
      page === "dashboard" && hasDashboardAccess.current;
    currentDashboardProjectId.current =
      page === "dashboard" && accessToken ? selectedDashboardProjectId : "";
  }, [accessToken, page, selectedDashboardProjectId]);

  useEffect(() => {
    if (page !== "dashboard") {
      dashboardProjectRequestGeneration.current += 1;
      dashboardRequestGeneration.current += 1;
      currentDashboardProjectId.current = "";
      isDashboardActive.current = false;
      setDashboardProjects([]);
      setIsLoadingDashboardProjects(false);
      setDashboardProjectSelectorError("");
      setDashboardData(null);
      setIsLoadingDashboard(false);
      setDashboardError("");
    }
  }, [page]);

  useEffect(() => {
    if (!accessToken || page !== "dashboard") return;

    void loadDashboardProjects(
      dashboardProjectOffset,
      dashboardProjectArchiveFilter,
    );

    return () => {
      dashboardProjectRequestGeneration.current += 1;
    };
  }, [
    accessToken,
    page,
    dashboardProjectOffset,
    dashboardProjectArchiveFilter,
    loadDashboardProjects,
  ]);

  useEffect(() => {
    if (
      !accessToken ||
      page !== "dashboard" ||
      !selectedDashboardProjectId
    ) {
      return;
    }

    void loadProjectDashboard(selectedDashboardProjectId);

    return () => {
      dashboardRequestGeneration.current += 1;
    };
  }, [
    accessToken,
    page,
    selectedDashboardProjectId,
    dashboardReloadVersion,
    loadProjectDashboard,
  ]);

  useEffect(() => {
    hasTraceabilityAccess.current = Boolean(accessToken);
    isTraceabilityActive.current =
      page === "traceability" && hasTraceabilityAccess.current;
    currentTraceabilityProjectId.current =
      page === "traceability" && accessToken
        ? selectedTraceabilityProjectId
        : "";
    currentTraceabilityOffset.current =
      page === "traceability" && accessToken ? traceabilityOffset : 0;
  }, [
    accessToken,
    page,
    selectedTraceabilityProjectId,
    traceabilityOffset,
  ]);

  useEffect(() => {
    if (page !== "traceability") {
      traceabilityProjectRequestGeneration.current += 1;
      traceabilityRequestGeneration.current += 1;
      currentTraceabilityProjectId.current = "";
      currentTraceabilityOffset.current = 0;
      isTraceabilityActive.current = false;
      setTraceabilityProjects([]);
      setIsLoadingTraceabilityProjects(false);
      setTraceabilityProjectSelectorError("");
      setTraceabilityData(null);
      setTraceabilityTotal(0);
      setIsLoadingTraceability(false);
      setTraceabilityError("");
    }
  }, [page]);

  useEffect(() => {
    if (!accessToken || page !== "traceability") return;

    void loadTraceabilityProjects(
      traceabilityProjectOffset,
      traceabilityProjectArchiveFilter,
    );

    return () => {
      traceabilityProjectRequestGeneration.current += 1;
    };
  }, [
    accessToken,
    page,
    traceabilityProjectOffset,
    traceabilityProjectArchiveFilter,
    loadTraceabilityProjects,
  ]);

  useEffect(() => {
    if (
      !accessToken ||
      page !== "traceability" ||
      !selectedTraceabilityProjectId
    ) {
      return;
    }

    void loadProjectTraceability(
      selectedTraceabilityProjectId,
      traceabilityOffset,
    );

    return () => {
      traceabilityRequestGeneration.current += 1;
    };
  }, [
    accessToken,
    page,
    selectedTraceabilityProjectId,
    traceabilityOffset,
    traceabilityReloadVersion,
    loadProjectTraceability,
  ]);

  useEffect(() => {
    if (page !== "delivery") {
      pendingSprintCreationRefresh.current = false;
      sprintRequestGeneration.current += 1;
      taskSprintOptionRequestGeneration.current += 1;
      setIsLoadingSprints(false);
      setSprintListError("");
      setTaskSprintOptions([]);
      setIsLoadingTaskSprintOptions(false);
      setHasLoadedTaskSprintOptions(false);
      setTaskSprintOptionError("");
      pendingTaskRefreshMessage.current = null;
      taskRequestGeneration.current += 1;
      deliveryRequirementRequestGeneration.current += 1;
      deliveryStoryRequestGeneration.current += 1;
      setIsLoadingTasks(false);
      setTaskListError("");
      setIsLoadingDeliveryRequirements(false);
      setDeliveryRequirementsError("");
      setIsLoadingDeliveryStories(false);
      setDeliveryStoriesError("");
    }
  }, [page]);

  useEffect(() => {
    if (!accessToken || page !== "delivery") return;

    let isActive = true;
    void loadSprints(selectedSprintProjectId, sprintOffset).then(
      (refreshed) => {
        if (!isActive || !pendingSprintCreationRefresh.current) return;

        pendingSprintCreationRefresh.current = false;
        setSuccess(
          refreshed
            ? "Sprint created successfully."
            : "Sprint was created, but the sprint list could not be refreshed.",
        );
      },
    );

    return () => {
      isActive = false;
      sprintRequestGeneration.current += 1;
    };
  }, [
    accessToken,
    page,
    selectedSprintProjectId,
    sprintOffset,
    sprintReloadVersion,
    loadSprints,
  ]);

  useEffect(() => {
    if (!accessToken || page !== "delivery") return;
    void loadTaskSprintOptions(selectedSprintProjectId);
  }, [
    accessToken,
    page,
    selectedSprintProjectId,
    sprintReloadVersion,
    loadTaskSprintOptions,
  ]);

  useEffect(() => {
    if (!accessToken || page !== "delivery") return;
    void loadDeliveryRequirements(
      selectedSprintProjectId,
      deliveryRequirementOffset,
    );
  }, [
    accessToken,
    page,
    selectedSprintProjectId,
    deliveryRequirementOffset,
    loadDeliveryRequirements,
  ]);

  useEffect(() => {
    if (!accessToken || page !== "delivery") return;
    void loadDeliveryStories(selectedTaskRequirementId, deliveryStoryOffset);
  }, [
    accessToken,
    page,
    selectedTaskRequirementId,
    deliveryStoryOffset,
    loadDeliveryStories,
  ]);

  useEffect(() => {
    if (!accessToken || page !== "delivery") return;

    let isActive = true;
    void loadTasks(selectedTaskStoryId, taskOffset).then((refreshed) => {
      if (!isActive || !pendingTaskRefreshMessage.current) return;

      const message = pendingTaskRefreshMessage.current;
      pendingTaskRefreshMessage.current = null;
      setSuccess(
        refreshed
          ? message
          : "Task was saved, but the task list could not be refreshed.",
      );
    });

    return () => {
      isActive = false;
      taskRequestGeneration.current += 1;
    };
  }, [
    accessToken,
    page,
    selectedTaskStoryId,
    taskOffset,
    taskReloadVersion,
    loadTasks,
  ]);

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
      hasDashboardAccess.current = true;
      isDashboardActive.current = true;
      currentDashboardProjectId.current = "";
      hasTraceabilityAccess.current = true;
      isTraceabilityActive.current = false;
      currentTraceabilityProjectId.current = "";
      currentTraceabilityOffset.current = 0;
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
      setEditingProject(null);
      setShowProjectForm(false);
      setProjectOffset(0);
      await loadProjects(0, projectArchiveFilter);
      setSuccess("Project created successfully.");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to create project.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  function resetProjectForm(force = false) {
    if (isSaving && editingProject && !force) return;

    setEditingProject(null);
    setProjectName("");
    setProjectDescription("");
    setProjectStatus("planned");
    setShowProjectForm(false);
  }

  function startProjectEdit(project: Project) {
    if (!canCreateContent || isSaving) return;

    setEditingProject(project);
    setProjectName(project.name);
    setProjectDescription(project.description ?? "");
    setProjectStatus(project.status);
    navigateToPage("projects");
    setShowProjectForm(true);
    setError("");
    setSuccess("");
  }

  async function handleUpdateProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editingProject) return;

    const name = projectName.trim();
    const description = projectDescription.trim() || null;
    const update: ProjectUpdate = {};

    if (!name) {
      setError("Project name is required.");
      return;
    }
    if (name !== editingProject.name) update.name = name;
    if (description !== (editingProject.description ?? null)) {
      update.description = description;
    }
    if (projectStatus !== editingProject.status) update.status = projectStatus;

    if (Object.keys(update).length === 0) {
      setError("Make at least one change before saving this project.");
      return;
    }

    setIsSaving(true);
    setError("");
    setSuccess("");
    try {
      await request(`/api/v1/projects/${editingProject.id}`, {
        method: "PATCH",
        body: JSON.stringify(update),
      });
      resetProjectForm(true);
      const refreshed = await loadProjects(projectOffset, projectArchiveFilter);
      setSuccess(
        refreshed
          ? "Project updated successfully."
          : "Project was updated, but the project list could not be refreshed.",
      );
    } catch (err) {
      await reconcileArchivedProjectConflict(err, editingProject.id);
      setError(
        err instanceof Error ? err.message : "Unable to update project.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function handleProjectArchiveAction(
    project: Project,
    action: ProjectArchiveAction,
  ) {
    if (currentUser?.role !== "admin") return;
    if (
      (action === "archive" && isArchivedProject(project)) ||
      (action === "restore" && !isArchivedProject(project))
    ) {
      return;
    }

    if (pendingProjectArchiveActionRef.current !== null) return;

    const actionLabel = action === "archive" ? "archive" : "restore";
    if (!window.confirm(`Are you sure you want to ${actionLabel} ${project.name}?`)) {
      return;
    }

    const actionKey = `${project.id}:${action}`;
    if (pendingProjectArchiveActionRef.current !== null) return;

    pendingProjectArchiveActionRef.current = actionKey;
    setPendingProjectArchiveAction({ projectId: project.id, action });
    setError("");
    setSuccess("");

    const viewGeneration = projectViewGeneration.current;
    const actionGeneration = projectArchiveActionGeneration.current;
    const archivePath =
      action === "archive"
        ? `/api/v1/projects/${project.id}/archive`
        : `/api/v1/projects/${project.id}/restore`;

    try {
      const response = await request(archivePath, { method: "POST" });
      const updatedProject: Project = await response.json();
      if (projectArchiveActionGeneration.current !== actionGeneration) return;
      if (updatedProject.id !== project.id) {
        throw new Error("Unexpected project response. Please refresh and try again.");
      }
      replaceProjectMetadata(updatedProject);

      if (action === "archive" && editingProject?.id === project.id) {
        resetProjectForm(true);
      }

      if (projectViewGeneration.current === viewGeneration) {
        await loadProjects(projectOffset, projectArchiveFilter);
      }

      setSuccess(
        action === "archive"
          ? "Project archived successfully."
          : "Project restored successfully.",
      );
    } catch (err) {
      if (projectArchiveActionGeneration.current !== actionGeneration) return;

      if (
        err instanceof ApiRequestError &&
        err.status === 409 &&
        projectViewGeneration.current === viewGeneration
      ) {
        await loadProjects(projectOffset, projectArchiveFilter);
      }

      setError(
        err instanceof Error
          ? err.message
          : `Unable to ${actionLabel} project.`,
      );
    } finally {
      if (pendingProjectArchiveActionRef.current === actionKey) {
        pendingProjectArchiveActionRef.current = null;
        setPendingProjectArchiveAction(null);
      }
    }
  }

  function handleProjectArchiveFilterChange(
    archiveFilter: ProjectArchiveFilter,
  ) {
    if (archiveFilter === projectArchiveFilter) return;

    // I invalidate the previous filter's response before requesting the new one.
    projectRequestGeneration.current += 1;
    projectViewGeneration.current += 1;
    setProjectArchiveFilter(archiveFilter);
    setProjectOffset(0);
    setError("");
  }

  function handleProjectPageChange(offset: number) {
    if (offset === projectOffset) return;

    projectViewGeneration.current += 1;
    setProjectOffset(offset);
  }

  function resetSprintForm() {
    setSprintName("");
    setSprintStartDate("");
    setSprintEndDate("");
    setSprintStatus("planned");
    setShowSprintForm(false);
  }

  async function handleCreateSprint(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isDeliveryProjectWritable) return;
    const name = sprintName.trim();

    if (!selectedSprintProjectId || !name || !sprintStartDate || !sprintEndDate) {
      setError("Project, sprint name, start date, and end date are required.");
      return;
    }
    if (sprintEndDate < sprintStartDate) {
      setError("Sprint end date must be on or after the start date.");
      return;
    }

    setIsSaving(true);
    setError("");
    setSuccess("");
    const creationGeneration = sprintRequestGeneration.current;
    try {
      await request("/api/v1/sprints", {
        method: "POST",
        body: JSON.stringify({
          project_id: selectedSprintProjectId,
          name,
          start_date: sprintStartDate,
          end_date: sprintEndDate,
          status: sprintStatus,
        }),
      });
      if (sprintRequestGeneration.current !== creationGeneration) return;

      refreshDashboardForProject(selectedSprintProjectId);

      resetSprintForm();
      setSprintOffset(0);
      pendingSprintCreationRefresh.current = true;
      setSprintReloadVersion((version) => version + 1);
    } catch (err) {
      await reconcileArchivedProjectConflict(err, selectedSprintProjectId);
      setError(err instanceof Error ? err.message : "Unable to create sprint.");
    } finally {
      setIsSaving(false);
    }
  }

  function handleSprintProjectChange(projectId: string) {
    if (isSaving) return;
    sprintRequestGeneration.current += 1;
    taskSprintOptionRequestGeneration.current += 1;
    taskRequestGeneration.current += 1;
    deliveryRequirementRequestGeneration.current += 1;
    deliveryStoryRequestGeneration.current += 1;
    pendingTaskRefreshMessage.current = null;
    setSelectedSprintProjectId(projectId);
    setSprintOffset(0);
    setSprints([]);
    setTotalSprints(0);
    setIsLoadingSprints(false);
    setSprintListError("");
    setTaskSprintOptions([]);
    setIsLoadingTaskSprintOptions(false);
    setHasLoadedTaskSprintOptions(false);
    setTaskSprintOptionError("");
    setDeliveryRequirements([]);
    setTotalDeliveryRequirements(0);
    setDeliveryRequirementOffset(0);
    setIsLoadingDeliveryRequirements(false);
    setHasLoadedDeliveryRequirements(false);
    setDeliveryRequirementsError("");
    setSelectedTaskRequirementId("");
    setDeliveryStories([]);
    setTotalDeliveryStories(0);
    setDeliveryStoryOffset(0);
    setIsLoadingDeliveryStories(false);
    setHasLoadedDeliveryStories(false);
    setDeliveryStoriesError("");
    setSelectedTaskStoryId("");
    setTasks([]);
    setTotalTasks(0);
    setTaskOffset(0);
    setIsLoadingTasks(false);
    setTaskListError("");
    resetSprintForm();
    resetTaskForm();
    setError("");
    setSuccess("");
  }

  function handleDashboardProjectChange(projectId: string) {
    if (isLoadingDashboardProjects) return;

    dashboardRequestGeneration.current += 1;
    currentDashboardProjectId.current = projectId;
    setSelectedDashboardProjectId(projectId);
    setDashboardData(null);
    setIsLoadingDashboard(false);
    setDashboardError("");
  }

  function handleDashboardProjectArchiveFilterChange(
    archiveFilter: ProjectArchiveFilter,
  ) {
    if (archiveFilter === dashboardProjectArchiveFilter) return;

    // I invalidate only the prior selector request and retain valid KPI data.
    dashboardProjectRequestGeneration.current += 1;
    setDashboardProjectArchiveFilter(archiveFilter);
    setDashboardProjectOffset(0);
    setDashboardProjectSelectorError("");
  }

  function handleTraceabilityProjectChange(projectId: string) {
    if (isLoadingTraceabilityProjects) return;

    traceabilityProjectRequestGeneration.current += 1;
    traceabilityRequestGeneration.current += 1;
    currentTraceabilityProjectId.current = projectId;
    currentTraceabilityOffset.current = 0;
    setSelectedTraceabilityProjectId(projectId);
    setTraceabilityOffset(0);
    setTraceabilityData(null);
    setTraceabilityTotal(0);
    setIsLoadingTraceability(false);
    setTraceabilityError("");
  }

  function handleTraceabilityProjectArchiveFilterChange(
    archiveFilter: ProjectArchiveFilter,
  ) {
    if (archiveFilter === traceabilityProjectArchiveFilter) return;

    // I invalidate only the prior selector request and retain valid traceability data.
    traceabilityProjectRequestGeneration.current += 1;
    setTraceabilityProjectArchiveFilter(archiveFilter);
    setTraceabilityProjectOffset(0);
    setTraceabilityProjectSelectorError("");
  }

  function handleTraceabilityProjectPageChange(offset: number) {
    if (
      isLoadingTraceabilityProjects ||
      offset === traceabilityProjectOffset
    ) {
      return;
    }

    traceabilityProjectRequestGeneration.current += 1;
    traceabilityRequestGeneration.current += 1;
    currentTraceabilityProjectId.current = "";
    currentTraceabilityOffset.current = 0;
    setTraceabilityProjectOffset(offset);
    setTraceabilityProjects([]);
    setTraceabilityProjectSelectorError("");
    setSelectedTraceabilityProjectId("");
    setTraceabilityData(null);
    setTraceabilityTotal(0);
    setTraceabilityOffset(0);
    setIsLoadingTraceability(false);
    setTraceabilityError("");
  }

  function handleTraceabilityPageChange(offset: number) {
    if (
      isLoadingTraceability ||
      !selectedTraceabilityProjectId ||
      offset === traceabilityOffset
    ) {
      return;
    }

    traceabilityRequestGeneration.current += 1;
    currentTraceabilityOffset.current = offset;
    setTraceabilityOffset(offset);
    setTraceabilityData(null);
    setTraceabilityError("");
  }

  function retryTraceabilityProjectSelector() {
    if (isLoadingTraceabilityProjects) return;

    void loadTraceabilityProjects(
      traceabilityProjectOffset,
      traceabilityProjectArchiveFilter,
    );
  }

  function retryProjectTraceability() {
    if (!selectedTraceabilityProjectId || isLoadingTraceability) return;

    void loadProjectTraceability(
      selectedTraceabilityProjectId,
      traceabilityOffset,
    );
  }

  function handleDashboardProjectPageChange(offset: number) {
    if (
      isLoadingDashboardProjects ||
      offset === dashboardProjectOffset
    ) {
      return;
    }

    dashboardProjectRequestGeneration.current += 1;
    dashboardRequestGeneration.current += 1;
    currentDashboardProjectId.current = "";
    setDashboardProjectOffset(offset);
    setDashboardProjects([]);
    setDashboardProjectSelectorError("");
    setSelectedDashboardProjectId("");
    setDashboardData(null);
    setIsLoadingDashboard(false);
    setDashboardError("");
  }

  function retryDashboardProjectSelector() {
    if (isLoadingDashboardProjects) return;

    void loadDashboardProjects(
      dashboardProjectOffset,
      dashboardProjectArchiveFilter,
    );
  }

  function retryProjectDashboard() {
    if (!selectedDashboardProjectId || isLoadingDashboard) return;

    void loadProjectDashboard(selectedDashboardProjectId);
  }

  function refreshDashboardForProject(projectId: string) {
    if (
      hasDashboardAccess.current &&
      isDashboardActive.current &&
      projectId === currentDashboardProjectId.current
    ) {
      setDashboardReloadVersion((version) => version + 1);
    }
  }

  function refreshTraceabilityForProject(projectId: string) {
    if (
      hasTraceabilityAccess.current &&
      isTraceabilityActive.current &&
      projectId === currentTraceabilityProjectId.current
    ) {
      setTraceabilityReloadVersion((version) => version + 1);
    }
  }

  function navigateToPage(nextPage: Page) {
    isDashboardActive.current = nextPage === "dashboard";
    currentDashboardProjectId.current =
      nextPage === "dashboard" && hasDashboardAccess.current
        ? selectedDashboardProjectId
        : "";
    isTraceabilityActive.current = nextPage === "traceability";
    currentTraceabilityProjectId.current =
      nextPage === "traceability" && hasTraceabilityAccess.current
        ? selectedTraceabilityProjectId
        : "";
    currentTraceabilityOffset.current = nextPage === "traceability" ? traceabilityOffset : 0;
    setPage(nextPage);
  }

  function resetTaskForm(force = false) {
    if (isSaving && !force) return;
    taskFormGeneration.current += 1;
    setTaskTitle("");
    setTaskDescription("");
    setTaskStatus("todo");
    setShowTaskForm(false);
  }

  function handleTaskRequirementChange(requirementId: string) {
    if (isSaving) return;
    taskRequestGeneration.current += 1;
    deliveryStoryRequestGeneration.current += 1;
    pendingTaskRefreshMessage.current = null;
    setSelectedTaskRequirementId(requirementId);
    setDeliveryStories([]);
    setTotalDeliveryStories(0);
    setDeliveryStoryOffset(0);
    setIsLoadingDeliveryStories(false);
    setHasLoadedDeliveryStories(false);
    setDeliveryStoriesError("");
    setSelectedTaskStoryId("");
    setTasks([]);
    setTotalTasks(0);
    setTaskOffset(0);
    setIsLoadingTasks(false);
    setTaskListError("");
    resetTaskForm();
    setError("");
    setSuccess("");
  }

  function handleTaskStoryChange(storyId: string) {
    if (isSaving) return;
    taskRequestGeneration.current += 1;
    pendingTaskRefreshMessage.current = null;
    setSelectedTaskStoryId(storyId);
    setTasks([]);
    setTotalTasks(0);
    setTaskOffset(0);
    setIsLoadingTasks(false);
    setTaskListError("");
    resetTaskForm();
    setError("");
    setSuccess("");
  }

  function retryTaskSprintOptions() {
    if (
      !selectedSprintProjectId ||
      isSaving ||
      isLoadingTaskSprintOptions
    ) {
      return;
    }

    void loadTaskSprintOptions(selectedSprintProjectId);
  }

  function retrySprintList() {
    if (!selectedSprintProjectId || isSaving || isLoadingSprints) return;

    void loadSprints(selectedSprintProjectId, sprintOffset);
  }

  function retryDeliveryRequirements() {
    if (
      !selectedSprintProjectId ||
      isSaving ||
      isLoadingDeliveryRequirements
    ) {
      return;
    }

    void loadDeliveryRequirements(
      selectedSprintProjectId,
      deliveryRequirementOffset,
    );
  }

  function retryDeliveryStories() {
    if (
      !selectedTaskRequirementId ||
      isSaving ||
      isLoadingDeliveryStories
    ) {
      return;
    }

    void loadDeliveryStories(selectedTaskRequirementId, deliveryStoryOffset);
  }

  function retryTaskList() {
    if (!selectedTaskStoryId || isSaving || isLoadingTasks) return;

    void loadTasks(selectedTaskStoryId, taskOffset);
  }

  function handleDeliveryRequirementPageChange(offset: number) {
    if (isSaving || offset === deliveryRequirementOffset) return;
    deliveryRequirementRequestGeneration.current += 1;
    deliveryStoryRequestGeneration.current += 1;
    taskRequestGeneration.current += 1;
    pendingTaskRefreshMessage.current = null;
    setDeliveryRequirementOffset(offset);
    setDeliveryRequirements([]);
    setHasLoadedDeliveryRequirements(false);
    setDeliveryRequirementsError("");
    setSelectedTaskRequirementId("");
    setDeliveryStories([]);
    setTotalDeliveryStories(0);
    setDeliveryStoryOffset(0);
    setIsLoadingDeliveryStories(false);
    setHasLoadedDeliveryStories(false);
    setDeliveryStoriesError("");
    setSelectedTaskStoryId("");
    setTasks([]);
    setTotalTasks(0);
    setTaskOffset(0);
    setIsLoadingTasks(false);
    setTaskListError("");
    resetTaskForm();
    setError("");
    setSuccess("");
  }

  function handleDeliveryStoryPageChange(offset: number) {
    if (isSaving || offset === deliveryStoryOffset) return;
    deliveryStoryRequestGeneration.current += 1;
    taskRequestGeneration.current += 1;
    pendingTaskRefreshMessage.current = null;
    setDeliveryStoryOffset(offset);
    setDeliveryStories([]);
    setHasLoadedDeliveryStories(false);
    setDeliveryStoriesError("");
    setSelectedTaskStoryId("");
    setTasks([]);
    setTotalTasks(0);
    setTaskOffset(0);
    setIsLoadingTasks(false);
    setTaskListError("");
    resetTaskForm();
    setError("");
    setSuccess("");
  }

  async function handleCreateTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSaving || !isDeliveryProjectWritable) return;
    const title = taskTitle.trim();

    if (!selectedTaskStory || selectedTaskStory.status !== "approved") {
      setError("Tasks can only be created for an approved user story.");
      return;
    }
    if (!title) {
      setError("Task title is required.");
      return;
    }

    setIsSaving(true);
    setError("");
    setSuccess("");
    taskRequestGeneration.current += 1;
    setIsLoadingTasks(false);
    const creationGeneration = taskRequestGeneration.current;
    const submittedFormGeneration = taskFormGeneration.current;
    try {
      await request("/api/v1/tasks", {
        method: "POST",
        body: JSON.stringify({
          story_id: selectedTaskStory.id,
          title,
          description: taskDescription.trim(),
          status: taskStatus,
        }),
      });
      if (taskFormGeneration.current !== submittedFormGeneration) return;

      resetTaskForm(true);
      setTaskOffset(0);
      setTaskReloadVersion((version) => version + 1);

      if (taskRequestGeneration.current !== creationGeneration) return;
      refreshDashboardForProject(selectedSprintProjectId);
      refreshTraceabilityForProject(selectedSprintProjectId);
      pendingTaskRefreshMessage.current = "Task created successfully.";
    } catch (err) {
      if (taskRequestGeneration.current !== creationGeneration) return;
      await reconcileArchivedProjectConflict(err, selectedSprintProjectId);
      setError(err instanceof Error ? err.message : "Unable to create task.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleUpdateTaskStatus(task: Task, status: TaskStatus) {
    if (!isDeliveryProjectWritable) return;

    if (!canCreateContent || isSaving || status === task.status) return;

    setIsSaving(true);
    setError("");
    setSuccess("");
    taskRequestGeneration.current += 1;
    setIsLoadingTasks(false);
    const updateGeneration = taskRequestGeneration.current;
    try {
      await request(`/api/v1/tasks/${task.id}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      if (taskRequestGeneration.current !== updateGeneration) return;

      refreshDashboardForProject(selectedSprintProjectId);
      refreshTraceabilityForProject(selectedSprintProjectId);
      pendingTaskRefreshMessage.current = "Task status updated successfully.";
      setTaskReloadVersion((version) => version + 1);
    } catch (err) {
      if (taskRequestGeneration.current !== updateGeneration) return;
      await reconcileArchivedProjectConflict(err, selectedSprintProjectId);
      setError(
        err instanceof Error ? err.message : "Unable to update task status.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function handleUpdateTaskSprint(
    task: Task,
    sprintId: string | null,
  ) {
    if (
      !isDeliveryProjectWritable ||
      !canCreateContent ||
      isSaving ||
      isLoadingTaskSprintOptions ||
      !hasLoadedTaskSprintOptions ||
      Boolean(taskSprintOptionError) ||
      sprintId === task.sprint_id
    ) {
      return;
    }
    if (
      sprintId !== null &&
      !taskSprintOptions.some((sprint) => sprint.id === sprintId)
    ) {
      setError("The selected sprint is no longer available for this project.");
      return;
    }

    setIsSaving(true);
    setError("");
    setSuccess("");
    taskRequestGeneration.current += 1;
    setIsLoadingTasks(false);
    const updateGeneration = taskRequestGeneration.current;
    try {
      await request(`/api/v1/tasks/${task.id}`, {
        method: "PATCH",
        body: JSON.stringify({ sprint_id: sprintId }),
      });
      if (taskRequestGeneration.current !== updateGeneration) return;

      pendingTaskRefreshMessage.current =
        "Task sprint assignment updated successfully.";
      setTaskReloadVersion((version) => version + 1);
    } catch (err) {
      if (taskRequestGeneration.current !== updateGeneration) return;
      await reconcileArchivedProjectConflict(err, selectedSprintProjectId);
      setError(
        err instanceof Error
          ? err.message
          : "Unable to update task sprint assignment.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function handleCreateRequirement(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedProjectId || !isRequirementProjectWritable) return;
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
      refreshDashboardForProject(selectedProjectId);
      refreshTraceabilityForProject(selectedProjectId);
      setRequirementTitle("");
      setRequirementDescription("");
      setRequirementPriority("medium");
      setRequirementStatus("draft");
      setShowRequirementForm(false);
      setRequirementOffset(0);
      await loadRequirements(selectedProjectId, 0);
      setSuccess("Requirement created successfully.");
    } catch (err) {
      await reconcileArchivedProjectConflict(err, selectedProjectId);
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
              navigateToPage("dashboard");
              setError("");
              setSuccess("");
            }}
          >
            ◫ Dashboard
          </button>
          <button
            className={`nav-item ${page === "projects" ? "active" : ""}`}
            onClick={() => {
              navigateToPage("projects");
              setError("");
              setSuccess("");
            }}
          >
            ▣ Projects
          </button>
          <button
            className={`nav-item ${page === "requirements" ? "active" : ""}`}
            onClick={() => {
              navigateToPage("requirements");
              setError("");
              setSuccess("");
            }}
          >
            ☷ Requirements
          </button>
          <button
            className={`nav-item ${page === "user-stories" ? "active" : ""}`}
            onClick={() => {
              navigateToPage("user-stories");
              setError("");
              setSuccess("");
            }}
          >
            ✦ User Stories
          </button>
          <button
            className={`nav-item ${page === "traceability" ? "active" : ""}`}
            onClick={() => {
              navigateToPage("traceability");
              setError("");
              setSuccess("");
            }}
          >
            ⤳ Traceability
          </button>
          <button
            className={`nav-item ${page === "delivery" ? "active" : ""}`}
            onClick={() => {
              navigateToPage("delivery");
              setError("");
              setSuccess("");
            }}
          >
            ✓ Delivery
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
                      : page === "user-stories"
                        ? "User Stories"
                        : page === "traceability"
                          ? "Traceability"
                          : "Delivery"}
              </h1>
              <p>
                {page === "dashboard"
                  ? "Overview of your business analysis projects."
                  : page === "projects"
                    ? "Create and manage your projects."
                    : page === "requirements"
                      ? "Manage requirements for a selected project."
                      : page === "user-stories"
                        ? "Generate, review, and save user story drafts."
                        : page === "traceability"
                          ? "View requirement, user story, and task relationships for a selected project."
                          : "Manage project sprints and task delivery planning."}
              </p>
            </div>
            {page === "delivery" && canCreateContent ? (
              <button
                className="primary-button create-button"
                disabled={
                  !selectedSprintProjectId ||
                  !isDeliveryProjectWritable ||
                  isSaving
                }
                onClick={() => {
                  resetSprintForm();
                  setShowSprintForm(true);
                  setSuccess("");
                }}
              >
                + New Sprint
              </button>
            ) : page === "user-stories" && canCreateContent ? (
              <button
                className="primary-button create-button"
                disabled={!storyRequirementId || !isStoryProjectWritable}
                onClick={() => {
                  clearStoryEditor();
                  setShowStoryForm(true);
                  setSuccess("");
                }}
              >
                + New User Story
              </button>
            ) : (page === "dashboard" || page === "projects") &&
              canCreateContent ? (
              <button
                className="primary-button create-button"
                disabled={isSaving && editingProject !== null}
                onClick={() => {
                  resetProjectForm();
                  navigateToPage("projects");
                  setShowProjectForm(true);
                  setSuccess("");
                }}
              >
                + New Project
              </button>
            ) : page === "requirements" && canCreateContent ? (
              <button
                className="primary-button create-button"
                disabled={!selectedProjectId || !isRequirementProjectWritable}
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
                  <ProjectTable
                    projects={projects.slice(0, 5)}
                    onEdit={canCreateContent ? startProjectEdit : undefined}
                    isSaving={isSaving}
                  />
                )}
              </div>
              <div className="content-card">
                <h2>Project Dashboard</h2>
                <p className="form-description">
                  Select a project to view counts derived from its stored
                  requirements, user stories, tasks, and sprints.
                </p>
                <div className="project-form">
                  <div className="selector-filter">
                    <label htmlFor="dashboard-project-archive-filter">Show</label>
                    <select
                      id="dashboard-project-archive-filter"
                      value={dashboardProjectArchiveFilter}
                      disabled={isLoadingDashboardProjects}
                      onChange={(event) =>
                        handleDashboardProjectArchiveFilterChange(
                          event.target.value as ProjectArchiveFilter,
                        )
                      }
                    >
                      <option value="active">Active</option>
                      <option value="archived">Archived</option>
                    </select>
                  </div>
                  <label htmlFor="dashboard-project">Project</label>
                  <select
                    id="dashboard-project"
                    value={selectedDashboardProjectId}
                    disabled={isLoadingDashboardProjects}
                    onChange={(event) =>
                      handleDashboardProjectChange(event.target.value)
                    }
                  >
                    <option value="">Choose a project</option>
                    {dashboardProjects.map((project) => (
                      <option key={project.id} value={project.id}>
                        {project.record_number} — {project.name}
                        {isArchivedProject(project) ? " (Archived)" : ""}
                      </option>
                    ))}
                  </select>
                  {isLoadingDashboardProjects ? (
                    <p className="form-description">Loading projects...</p>
                  ) : dashboardProjectSelectorError ? (
                    <div className="error-message" role="alert">
                      <p>{dashboardProjectSelectorError}</p>
                      <button
                        type="button"
                        className="secondary-button"
                        disabled={isLoadingDashboardProjects}
                        onClick={retryDashboardProjectSelector}
                      >
                        Retry project selector
                      </button>
                    </div>
                  ) : dashboardTotalProjects === 0 ? (
                    <p className="empty-state">
                      No projects are available for a project dashboard.
                    </p>
                  ) : null}
                </div>
                <Pagination
                  offset={dashboardProjectOffset}
                  total={dashboardTotalProjects}
                  loading={isLoadingDashboardProjects}
                  pageSize={SELECTOR_PAGE_SIZE}
                  onChange={handleDashboardProjectPageChange}
                />
              </div>
              {selectedDashboardProjectId && (
                <div className="content-card">
                  <h2>
                    Project KPIs —{" "}
                    {selectedDashboardProject?.name ?? selectedDashboardProjectId}
                  </h2>
                  {isLoadingDashboard ? (
                    <p>Loading project dashboard...</p>
                  ) : dashboardError ? (
                    <div className="error-message" role="alert">
                      <p>{dashboardError}</p>
                      <button
                        type="button"
                        className="secondary-button"
                        disabled={
                          isLoadingDashboard || !selectedDashboardProjectId
                        }
                        onClick={retryProjectDashboard}
                      >
                        Retry project dashboard
                      </button>
                    </div>
                  ) : dashboardData ? (
                    <>
                      <p className="form-description">
                        Counts for the selected project.
                      </p>
                      <div className="stats-grid">
                        <div className="stat-card">
                          <span>Total Requirements</span>
                          <strong>{dashboardData.total_requirements}</strong>
                          <small>Stored requirements</small>
                        </div>
                        <div className="stat-card">
                          <span>Approved User Stories</span>
                          <strong>
                            {dashboardData.approved_user_stories}
                          </strong>
                          <small>Stories with Approved status</small>
                        </div>
                        <div className="stat-card">
                          <span>Total Tasks</span>
                          <strong>
                            {dashboardData.tasks_by_status.todo +
                              dashboardData.tasks_by_status.in_progress +
                              dashboardData.tasks_by_status.in_review +
                              dashboardData.tasks_by_status.done}
                          </strong>
                          <small>Across all task statuses</small>
                        </div>
                        <div className="stat-card">
                          <span>Active Sprints</span>
                          <strong>{dashboardData.active_sprints}</strong>
                          <small>Sprints with Active status</small>
                        </div>
                        <div className="stat-card">
                          <span>To Do Tasks</span>
                          <strong>{dashboardData.tasks_by_status.todo}</strong>
                          <small>To Do</small>
                        </div>
                        <div className="stat-card">
                          <span>In Progress Tasks</span>
                          <strong>
                            {dashboardData.tasks_by_status.in_progress}
                          </strong>
                          <small>In Progress</small>
                        </div>
                        <div className="stat-card">
                          <span>In Review Tasks</span>
                          <strong>
                            {dashboardData.tasks_by_status.in_review}
                          </strong>
                          <small>In Review</small>
                        </div>
                        <div className="stat-card">
                          <span>Done Tasks</span>
                          <strong>{dashboardData.tasks_by_status.done}</strong>
                          <small>Done</small>
                        </div>
                      </div>
                    </>
                  ) : null}
                </div>
              )}
            </>
          )}
          {page === "traceability" && (
            <>
              <div className="content-card">
                <h2>Select Project</h2>
                <p className="form-description">
                  Select a project to view its complete requirement, user story,
                  and task hierarchy for the current requirement page.
                </p>
                <div className="project-form">
                  <div className="selector-filter">
                    <label htmlFor="traceability-project-archive-filter">
                      Show
                    </label>
                    <select
                      id="traceability-project-archive-filter"
                      value={traceabilityProjectArchiveFilter}
                      disabled={isLoadingTraceabilityProjects}
                      onChange={(event) =>
                        handleTraceabilityProjectArchiveFilterChange(
                          event.target.value as ProjectArchiveFilter,
                        )
                      }
                    >
                      <option value="active">Active</option>
                      <option value="archived">Archived</option>
                    </select>
                  </div>
                  <label htmlFor="traceability-project">Project</label>
                  <select
                    id="traceability-project"
                    value={selectedTraceabilityProjectId}
                    disabled={isLoadingTraceabilityProjects}
                    onChange={(event) =>
                      handleTraceabilityProjectChange(event.target.value)
                    }
                  >
                    <option value="">Choose a project</option>
                    {traceabilityProjects.map((project) => (
                      <option key={project.id} value={project.id}>
                        {project.record_number} — {project.name}
                        {isArchivedProject(project) ? " (Archived)" : ""}
                      </option>
                    ))}
                  </select>
                  {isLoadingTraceabilityProjects ? (
                    <p className="form-description">Loading projects...</p>
                  ) : traceabilityProjectSelectorError ? (
                    <div className="error-message" role="alert">
                      <p>{traceabilityProjectSelectorError}</p>
                      <button
                        type="button"
                        className="secondary-button"
                        disabled={isLoadingTraceabilityProjects}
                        onClick={retryTraceabilityProjectSelector}
                      >
                        Retry project selector
                      </button>
                    </div>
                  ) : traceabilityTotalProjects === 0 ? (
                    <p className="empty-state">
                      No projects are available for traceability.
                    </p>
                  ) : null}
                </div>
                <Pagination
                  offset={traceabilityProjectOffset}
                  total={traceabilityTotalProjects}
                  loading={isLoadingTraceabilityProjects}
                  pageSize={SELECTOR_PAGE_SIZE}
                  onChange={handleTraceabilityProjectPageChange}
                />
              </div>
              {selectedTraceabilityProjectId && (
                <div className="content-card">
                  <h2>
                    Requirements Traceability — {" "}
                    {selectedTraceabilityProject?.name ??
                      selectedTraceabilityProjectId}
                  </h2>
                  {isLoadingTraceability ? (
                    <p>Loading traceability...</p>
                  ) : traceabilityError ? (
                    <div className="error-message" role="alert">
                      <p>{traceabilityError}</p>
                      <button
                        type="button"
                        className="secondary-button"
                        disabled={
                          isLoadingTraceability ||
                          !selectedTraceabilityProjectId
                        }
                        onClick={retryProjectTraceability}
                      >
                        Retry traceability
                      </button>
                    </div>
                  ) : traceabilityData && traceabilityData.items.length === 0 ? (
                    <p className="empty-state">
                      No requirements are available for this project.
                    </p>
                  ) : traceabilityData ? (
                    <div aria-label="Requirements traceability hierarchy">
                      {traceabilityData.items.map((requirement) => (
                        <details key={requirement.id} open>
                          <summary>
                            <strong>
                              {requirement.record_number} — {requirement.title}
                            </strong>{" "}
                            <span
                              className={`status-badge status-${requirement.status}`}
                            >
                              {REQUIREMENT_STATUS[requirement.status]}
                            </span>{" "}
                            <span>Priority: {PRIORITY[requirement.priority]}</span>
                          </summary>
                          {requirement.stories.length === 0 ? (
                            <p className="empty-state">
                              No user stories linked to this requirement.
                            </p>
                          ) : (
                            requirement.stories.map((story) => (
                              <details key={story.id}>
                                <summary>
                                  <strong>
                                    {story.record_number} — {story.title}
                                  </strong>{" "}
                                  <span
                                    className={`status-badge status-${story.status}`}
                                  >
                                    {REQUIREMENT_STATUS[story.status]}
                                  </span>
                                </summary>
                                {story.tasks.length === 0 ? (
                                  <p className="empty-state">
                                    No tasks linked to this user story.
                                  </p>
                                ) : (
                                  <ul aria-label={`Tasks for ${story.record_number}`}>
                                    {story.tasks.map((task) => (
                                      <li key={task.id}>
                                        <strong>{task.title}</strong>{" "}
                                        <span
                                          className={`status-badge status-${task.status}`}
                                        >
                                          {TASK_STATUS[task.status]}
                                        </span>
                                      </li>
                                    ))}
                                  </ul>
                                )}
                              </details>
                            ))
                          )}
                        </details>
                      ))}
                    </div>
                  ) : null}
                  <Pagination
                    offset={traceabilityOffset}
                    total={traceabilityTotal}
                    loading={isLoadingTraceability}
                    pageSize={SELECTOR_PAGE_SIZE}
                    onChange={handleTraceabilityPageChange}
                  />
                </div>
              )}
            </>
          )}
          {page === "delivery" && (
            <>
              <div className="content-card">
                <h2>Select Project</h2>
                <div className="project-form">
                  <label htmlFor="sprint-project">Project</label>
                  <select
                    id="sprint-project"
                    value={selectedSprintProjectId}
                    disabled={isSaving}
                    onChange={(event) =>
                      handleSprintProjectChange(event.target.value)
                    }
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
                  <ProjectReadOnlyNotice
                    projectId={selectedSprintProjectId}
                    project={selectedDeliveryProject}
                  />
                </div>
              </div>
              {selectedSprintProjectId && (
                <div className="content-card">
                  <h2>Select Requirement and User Story</h2>
                  <div className="project-form">
                    <label htmlFor="task-requirement">Requirement</label>
                    <select
                      id="task-requirement"
                      value={selectedTaskRequirementId}
                      disabled={isSaving || isLoadingDeliveryRequirements}
                      onChange={(event) =>
                        handleTaskRequirementChange(event.target.value)
                      }
                    >
                      <option value="">Choose a requirement</option>
                      {deliveryRequirements.map((requirement) => (
                        <option key={requirement.id} value={requirement.id}>
                          {requirement.record_number} — {requirement.title}
                        </option>
                      ))}
                    </select>
                    {isLoadingDeliveryRequirements ? (
                      <p className="form-description">Loading requirements...</p>
                    ) : hasLoadedDeliveryRequirements && !deliveryRequirements.length ? (
                      <p className="form-description">
                        No requirements are available for this project.
                      </p>
                    ) : null}
                    {deliveryRequirementsError && (
                      <div className="error-message" role="alert">
                        <p>{deliveryRequirementsError}</p>
                        <button
                          type="button"
                          className="secondary-button"
                          disabled={isSaving || isLoadingDeliveryRequirements}
                          onClick={retryDeliveryRequirements}
                        >
                          Retry requirements
                        </button>
                      </div>
                    )}
                    <Pagination
                      offset={deliveryRequirementOffset}
                      total={totalDeliveryRequirements}
                      loading={isLoadingDeliveryRequirements || isSaving}
                      pageSize={SELECTOR_PAGE_SIZE}
                      onChange={handleDeliveryRequirementPageChange}
                    />
                    <label htmlFor="task-story">User Story</label>
                    <select
                      id="task-story"
                      value={selectedTaskStoryId}
                      disabled={
                        !selectedTaskRequirementId ||
                        isSaving ||
                        isLoadingDeliveryStories
                      }
                      onChange={(event) =>
                        handleTaskStoryChange(event.target.value)
                      }
                    >
                      <option value="">Choose a user story</option>
                      {deliveryStories.map((story) => (
                        <option key={story.id} value={story.id}>
                          {story.record_number} — {story.title}
                        </option>
                      ))}
                    </select>
                    {selectedTaskRequirementId && isLoadingDeliveryStories ? (
                      <p className="form-description">Loading user stories...</p>
                    ) : selectedTaskRequirementId &&
                      hasLoadedDeliveryStories &&
                      !deliveryStories.length ? (
                      <p className="form-description">
                        No user stories are available for this requirement.
                      </p>
                    ) : null}
                    {deliveryStoriesError && (
                      <div className="error-message" role="alert">
                        <p>{deliveryStoriesError}</p>
                        <button
                          type="button"
                          className="secondary-button"
                          disabled={isSaving || isLoadingDeliveryStories}
                          onClick={retryDeliveryStories}
                        >
                          Retry user stories
                        </button>
                      </div>
                    )}
                    {selectedTaskRequirementId && (
                      <Pagination
                        offset={deliveryStoryOffset}
                        total={totalDeliveryStories}
                        loading={isLoadingDeliveryStories || isSaving}
                        pageSize={SELECTOR_PAGE_SIZE}
                        onChange={handleDeliveryStoryPageChange}
                      />
                    )}
                  </div>
                </div>
              )}
              {canCreateContent &&
                isDeliveryProjectWritable &&
                selectedSprintProjectId &&
                showSprintForm && (
                <div className="content-card">
                  <h2>Create New Sprint</h2>
                  <form
                    className="project-form"
                    onSubmit={handleCreateSprint}
                    aria-busy={isSaving}
                  >
                    <label htmlFor="sprint-name">Sprint Name</label>
                    <input
                      id="sprint-name"
                      maxLength={160}
                      value={sprintName}
                      onChange={(event) => setSprintName(event.target.value)}
                      disabled={isSaving}
                      required
                    />
                    <label htmlFor="sprint-start-date">Start Date</label>
                    <input
                      id="sprint-start-date"
                      type="date"
                      value={sprintStartDate}
                      onChange={(event) => setSprintStartDate(event.target.value)}
                      disabled={isSaving}
                      required
                    />
                    <label htmlFor="sprint-end-date">End Date</label>
                    <input
                      id="sprint-end-date"
                      type="date"
                      min={sprintStartDate || undefined}
                      value={sprintEndDate}
                      onChange={(event) => setSprintEndDate(event.target.value)}
                      disabled={isSaving}
                      required
                    />
                    <label htmlFor="sprint-status">Status</label>
                    <select
                      id="sprint-status"
                      value={sprintStatus}
                      onChange={(event) =>
                        setSprintStatus(event.target.value as SprintStatus)
                      }
                      disabled={isSaving}
                    >
                      {Object.entries(SPRINT_STATUS).map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                    <div className="form-actions">
                      <button
                        type="button"
                        className="secondary-light-button"
                        disabled={isSaving}
                        onClick={resetSprintForm}
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="primary-button"
                        disabled={isSaving}
                      >
                        {isSaving ? "Saving..." : "Create Sprint"}
                      </button>
                    </div>
                  </form>
                </div>
              )}
              {selectedSprintProjectId && (
                <div className="content-card">
                  <h2>Project Sprints</h2>
                  {isLoadingSprints ? (
                    <p>Loading sprints...</p>
                  ) : (
                    <SprintTable sprints={sprints} />
                  )}
                  {sprintListError && (
                    <div className="error-message" role="alert">
                      <p>{sprintListError}</p>
                      <button
                        type="button"
                        className="secondary-button"
                        disabled={isSaving || isLoadingSprints}
                        onClick={retrySprintList}
                      >
                        Retry sprints
                      </button>
                    </div>
                  )}
                  <Pagination
                    offset={sprintOffset}
                    total={totalSprints}
                    loading={isLoadingSprints || isSaving}
                    onChange={setSprintOffset}
                  />
                </div>
              )}
              {canCreateContent &&
                isDeliveryProjectWritable &&
                selectedTaskStory?.status === "approved" &&
                showTaskForm && (
                  <div className="content-card">
                    <h2>Create New Task</h2>
                    <form
                      className="project-form"
                      onSubmit={handleCreateTask}
                      aria-busy={isSaving}
                    >
                      <label htmlFor="task-title">Task Title</label>
                      <input
                        id="task-title"
                        maxLength={160}
                        value={taskTitle}
                        onChange={(event) => setTaskTitle(event.target.value)}
                        disabled={isSaving}
                        required
                      />
                      <label htmlFor="task-description">Description (optional)</label>
                      <textarea
                        id="task-description"
                        maxLength={5000}
                        value={taskDescription}
                        onChange={(event) =>
                          setTaskDescription(event.target.value)
                        }
                        disabled={isSaving}
                      />
                      <label htmlFor="task-status">Status</label>
                      <select
                        id="task-status"
                        value={taskStatus}
                        onChange={(event) =>
                          setTaskStatus(event.target.value as TaskStatus)
                        }
                        disabled={isSaving}
                      >
                        {Object.entries(TASK_STATUS).map(([value, label]) => (
                          <option key={value} value={value}>
                            {label}
                          </option>
                        ))}
                      </select>
                      <div className="form-actions">
                        <button
                          type="button"
                          className="secondary-light-button"
                          disabled={isSaving}
                          onClick={resetTaskForm}
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          className="primary-button"
                          disabled={isSaving}
                        >
                          {isSaving ? "Saving..." : "Create Task"}
                        </button>
                      </div>
                    </form>
                  </div>
                )}
              {selectedTaskStory && (
                <div className="content-card" aria-busy={isSaving}>
                  <div className="section-heading">
                    <div>
                      <h2>User Story Tasks</h2>
                      <p className="form-description">
                        {selectedTaskStory.record_number} — {selectedTaskStory.title}
                      </p>
                    </div>
                    {canCreateContent &&
                      isDeliveryProjectWritable &&
                      selectedTaskStory.status === "approved" && (
                      <button
                        type="button"
                        className="primary-button"
                        disabled={isSaving}
                        onClick={() => {
                          resetTaskForm();
                          setShowTaskForm(true);
                          setSuccess("");
                        }}
                      >
                        + New Task
                      </button>
                    )}
                  </div>
                  {selectedTaskStory.status !== "approved" && canCreateContent && (
                    <p className="form-description">
                      Tasks can only be created for approved user stories.
                    </p>
                  )}
                  {canCreateContent && taskSprintOptionError && (
                    <div className="error-message" role="alert">
                      <p>{taskSprintOptionError}</p>
                      <button
                        type="button"
                        className="secondary-button"
                        disabled={isSaving || isLoadingTaskSprintOptions}
                        onClick={retryTaskSprintOptions}
                      >
                        Retry sprint options
                      </button>
                    </div>
                  )}
                  {taskListError && (
                    <div className="error-message" role="alert">
                      <p>{taskListError}</p>
                      <button
                        type="button"
                        className="secondary-button"
                        disabled={isSaving || isLoadingTasks}
                        onClick={retryTaskList}
                      >
                        Retry tasks
                      </button>
                    </div>
                  )}
                  {isLoadingTasks ? (
                    <p>Loading tasks...</p>
                  ) : (
                    <TaskTable
                      tasks={tasks}
                      sprints={taskSprintOptions}
                      canEdit={canCreateContent && isDeliveryProjectWritable}
                      isSaving={isSaving}
                      isLoadingSprints={isLoadingTaskSprintOptions}
                      hasLoadedSprints={hasLoadedTaskSprintOptions}
                      onStatusChange={handleUpdateTaskStatus}
                      onSprintChange={handleUpdateTaskSprint}
                    />
                  )}
                  <Pagination
                    offset={taskOffset}
                    total={totalTasks}
                    loading={isLoadingTasks || isSaving}
                    onChange={setTaskOffset}
                  />
                </div>
              )}
            </>
          )}
          {page === "projects" && (
            <>
              {canCreateContent && showProjectForm && (
                <div className="content-card">
                  <h2>{editingProject ? "Edit Project" : "Create New Project"}</h2>
                  <form
                    className="project-form"
                    onSubmit={editingProject ? handleUpdateProject : handleCreateProject}
                    aria-busy={isSaving}
                  >
                    <label htmlFor="project-name">Project Name</label>
                    <input
                      id="project-name"
                      maxLength={120}
                      value={projectName}
                      onChange={(event) => setProjectName(event.target.value)}
                      disabled={isSaving}
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
                      disabled={isSaving}
                    />
                    <label htmlFor="project-status">Status</label>
                    <select
                      id="project-status"
                      value={projectStatus}
                      onChange={(event) =>
                        setProjectStatus(event.target.value as ProjectStatus)
                      }
                      disabled={isSaving}
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
                        disabled={isSaving}
                        onClick={resetProjectForm}
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="primary-button"
                        disabled={isSaving}
                      >
                        {isSaving
                          ? "Saving..."
                          : editingProject
                            ? "Save Changes"
                            : "Create Project"}
                      </button>
                    </div>
                  </form>
                </div>
              )}
              <div className="content-card">
                <div className="section-heading-row">
                  <h2>All Projects</h2>
                  <div className="project-filter">
                    <label htmlFor="project-archive-filter">Show</label>
                    <select
                      id="project-archive-filter"
                      value={projectArchiveFilter}
                      onChange={(event) =>
                        handleProjectArchiveFilterChange(
                          event.target.value as ProjectArchiveFilter,
                        )
                      }
                    >
                      <option value="active">Active</option>
                      <option value="archived">Archived</option>
                    </select>
                  </div>
                </div>
                {isLoading ? (
                  <p>Loading projects...</p>
                ) : (
                  <ProjectTable
                    projects={projects}
                    onEdit={canCreateContent ? startProjectEdit : undefined}
                    onArchive={
                      canManageProjectArchive
                        ? (project) => void handleProjectArchiveAction(project, "archive")
                        : undefined
                    }
                    onRestore={
                      canManageProjectArchive
                        ? (project) => void handleProjectArchiveAction(project, "restore")
                        : undefined
                    }
                    pendingProjectArchiveAction={pendingProjectArchiveAction}
                    isSaving={isSaving}
                  />
                )}
                <Pagination
                  offset={projectOffset}
                  total={totalProjects}
                  loading={isLoading}
                  onChange={handleProjectPageChange}
                />
                {projectArchiveFilter === "archived" && (
                  <p className="form-description project-filter-guidance">
                    New projects are unarchived. Select Active to find a project
                    created while viewing this list.
                  </p>
                )}
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
                <ProjectReadOnlyNotice
                  projectId={storyProjectId}
                  project={selectedStoryProject}
                />
              </div>
              {canCreateContent && isStoryProjectWritable && storyRequirementId && (
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
              {canCreateContent &&
                isStoryProjectWritable &&
                storyRequirementId &&
                showStoryForm && (
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
                      isProjectWritable={isStoryProjectWritable}
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
                <ProjectReadOnlyNotice
                  projectId={selectedProjectId}
                  project={selectedRequirementProject}
                />
              </div>
              {canCreateContent &&
                isRequirementProjectWritable &&
                selectedProjectId &&
                showRequirementForm && (
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
  pageSize = PAGE_SIZE,
  onChange,
}: {
  offset: number;
  total: number;
  loading: boolean;
  pageSize?: number;
  onChange: (offset: number) => void;
}) {
  const displayOffset =
    total === 0
      ? 0
      : Math.min(
          offset,
          Math.floor((total - 1) / pageSize) * pageSize,
        );

  return (
    <div className="pagination">
      <span>
        {total === 0 ? 0 : displayOffset + 1}–
        {Math.min(displayOffset + pageSize, total)} of{" "}
        {total}
      </span>
      <div>
        <button
          className="secondary-light-button"
          disabled={displayOffset === 0 || loading}
          onClick={() => onChange(Math.max(0, displayOffset - pageSize))}
        >
          Previous
        </button>
        <button
          className="secondary-light-button"
          disabled={displayOffset + pageSize >= total || loading}
          onClick={() => onChange(displayOffset + pageSize)}
        >
          Next
        </button>
      </div>
    </div>
  );
}

function ProjectTable({
  projects,
  onEdit,
  onArchive,
  onRestore,
  pendingProjectArchiveAction = null,
  isSaving = false,
}: {
  projects: Project[];
  onEdit?: (project: Project) => void;
  onArchive?: (project: Project) => void;
  onRestore?: (project: Project) => void;
  pendingProjectArchiveAction?: PendingProjectArchiveAction | null;
  isSaving?: boolean;
}) {
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
            {(onEdit || onArchive || onRestore) && <th>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {projects.map((project) => (
            <tr key={project.id}>
              <td>{project.record_number}</td>
              <td>
                <strong>{project.name}</strong>
                <small>{project.description || "No description"}</small>
                {isArchivedProject(project) && (
                  <small className="archive-metadata">
                    <span className="archive-badge">Archived</span>
                    <span>
                      Archived {formatArchiveTimestamp(project.archived_at)} by{" "}
                      {formatArchiveActor(project.archived_by)}
                    </span>
                  </small>
                )}
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
              {(onEdit || onArchive || onRestore) && (
                <td>
                  <div className="project-actions">
                    {!isArchivedProject(project) && onEdit && (
                      <button
                        type="button"
                        className="secondary-light-button"
                        disabled={isSaving}
                        aria-label={`Edit ${project.name}`}
                        onClick={() => onEdit(project)}
                      >
                        Edit
                      </button>
                    )}
                    {!isArchivedProject(project) && onArchive && (
                      <button
                        type="button"
                        className="secondary-light-button archive-action-button"
                        disabled={pendingProjectArchiveAction !== null}
                        aria-label={`Archive ${project.name}`}
                        onClick={() => onArchive(project)}
                      >
                        {pendingProjectArchiveAction?.projectId === project.id &&
                        pendingProjectArchiveAction.action === "archive"
                          ? "Archiving..."
                          : "Archive"}
                      </button>
                    )}
                    {isArchivedProject(project) && onRestore && (
                      <button
                        type="button"
                        className="secondary-light-button"
                        disabled={pendingProjectArchiveAction !== null}
                        aria-label={`Restore ${project.name}`}
                        onClick={() => onRestore(project)}
                      >
                        {pendingProjectArchiveAction?.projectId === project.id &&
                        pendingProjectArchiveAction.action === "restore"
                          ? "Restoring..."
                          : "Restore"}
                      </button>
                    )}
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SprintTable({ sprints }: { sprints: Sprint[] }) {
  if (!sprints.length)
    return (
      <p className="empty-state">
        No sprints found for this project. Create a sprint to begin planning
        delivery.
      </p>
    );
  return (
    <div className="table-wrapper">
      <table className="projects-table">
        <thead>
          <tr>
            <th>Sprint</th>
            <th>Start Date</th>
            <th>End Date</th>
            <th>Status</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {sprints.map((sprint) => (
            <tr key={sprint.id}>
              <td>
                <strong>{sprint.name}</strong>
              </td>
              <td>{sprint.start_date}</td>
              <td>{sprint.end_date}</td>
              <td>
                <span className={`status-badge status-${sprint.status}`}>
                  {SPRINT_STATUS[sprint.status]}
                </span>
              </td>
              <td>{new Date(sprint.created_at).toLocaleDateString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TaskTable({
  tasks,
  sprints,
  canEdit,
  isSaving,
  isLoadingSprints,
  hasLoadedSprints,
  onStatusChange,
  onSprintChange,
}: {
  tasks: Task[];
  sprints: Sprint[];
  canEdit: boolean;
  isSaving: boolean;
  isLoadingSprints: boolean;
  hasLoadedSprints: boolean;
  onStatusChange: (task: Task, status: TaskStatus) => void;
  onSprintChange: (task: Task, sprintId: string | null) => void;
}) {
  if (!tasks.length)
    return (
      <p className="empty-state">
        No tasks found for this user story. Create a task to begin delivery
        tracking.
      </p>
    );

  const sprintsById = new Map(sprints.map((sprint) => [sprint.id, sprint]));

  return (
    <div className="table-wrapper">
      <table className="projects-table">
        <thead>
          <tr>
            <th>Task</th>
            <th>Description</th>
            <th>Status</th>
            <th>Sprint Assignment</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => (
            <tr key={task.id}>
              <td>
                <strong>{task.title}</strong>
              </td>
              <td>{task.description || "—"}</td>
              <td>
                {canEdit ? (
                  <select
                    aria-label={`Change status for ${task.title}`}
                    value={task.status}
                    disabled={isSaving}
                    onChange={(event) =>
                      onStatusChange(
                        task,
                        event.target.value as TaskStatus,
                      )
                    }
                  >
                    {Object.entries(TASK_STATUS).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                ) : (
                  <span className={`status-badge status-${task.status}`}>
                    {TASK_STATUS[task.status]}
                  </span>
                )}
              </td>
              <td>
                {canEdit ? (
                  !hasLoadedSprints ? (
                    <select
                      aria-label={`${
                        isLoadingSprints ? "Loading" : "Unavailable"
                      } sprint assignment for ${task.title}`}
                      value={task.sprint_id ?? ""}
                      disabled
                    >
                      <option value={task.sprint_id ?? ""}>
                        {isLoadingSprints
                          ? task.sprint_id
                            ? "Loading current assignment..."
                            : "Unassigned"
                          : "Sprint options unavailable"}
                      </option>
                    </select>
                  ) : (
                    <select
                      aria-label={`Change sprint assignment for ${task.title}`}
                      value={task.sprint_id ?? ""}
                      disabled={isSaving}
                      onChange={(event) =>
                        onSprintChange(task, event.target.value || null)
                      }
                    >
                      <option value="">Unassigned</option>
                      {task.sprint_id && !sprintsById.has(task.sprint_id) && (
                        <option value={task.sprint_id} disabled>
                          Unavailable sprint (current assignment)
                        </option>
                      )}
                      {sprints.map((sprint) => (
                        <option key={sprint.id} value={sprint.id}>
                          {sprint.name} ({SPRINT_STATUS[sprint.status]})
                        </option>
                      ))}
                    </select>
                  )
                ) : task.sprint_id ? (
                  !hasLoadedSprints ? (
                    isLoadingSprints
                      ? "Loading current assignment..."
                      : "Sprint options unavailable"
                  ) : sprintsById.has(task.sprint_id) ? (
                    sprintsById.get(task.sprint_id)?.name
                  ) : (
                    "Unavailable sprint"
                  )
                ) : (
                  "Unassigned"
                )}
              </td>
              <td>{new Date(task.created_at).toLocaleDateString()}</td>
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
  isProjectWritable,
  isSaving,
  selectedAuditStoryId,
  isLoadingAudit,
  onSubmitForReview,
  onReview,
  onViewAuditHistory,
}: {
  stories: UserStory[];
  currentUser: CurrentUser | null;
  isProjectWritable: boolean;
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
    isProjectWritable &&
    (currentUser?.role === "business_analyst" || currentUser?.role === "admin");

  const canReview =
    currentUser?.role === "reviewer" || currentUser?.role === "admin";
  const canDecide = isProjectWritable && canReview;

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
                {canDecide && story.status === "in_review" && (
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
