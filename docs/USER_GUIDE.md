# AI BAP User Guide

AI BAP is a shared workspace for connecting projects, requirements, User Stories, review decisions, sprints, and delivery tasks. This guide describes the interface and permissions implemented in the repository. Production availability can differ until the corresponding revision is deployed and verified.

## Contents

- [Access and roles](#access-and-roles)
- [Sign In and Sign Out](#sign-in-and-sign-out)
- [Dashboard](#dashboard)
- [Projects](#projects)
- [Requirements](#requirements)
- [User Stories](#user-stories)
- [Traceability](#traceability)
- [Delivery](#delivery)
- [Pagination, loading, empty, and error states](#pagination-loading-empty-and-error-states)
- [Public demo and data safety](#public-demo-and-data-safety)
- [Known hosting limitations](#known-hosting-limitations)
- [Screenshot plan](#screenshot-plan)

## Access and roles

The application has three roles: **Admin**, **Business Analyst**, and **Reviewer**. The UI displays actions based on role, and the backend enforces the corresponding permissions. The workspace is shared: role permissions do not create a private project area for each account.

| Capability | Admin | Business Analyst | Reviewer |
|---|---:|---:|---:|
| View projects, requirements, stories, traceability, sprints, and tasks | Yes | Yes | Yes |
| Projects: create/edit active projects in the UI | Yes | Yes | No |
| Projects: archive/restore in the UI | Yes | No | No |
| Requirements: create in the UI | Yes | Yes | No |
| Requirements: update through backend API (no edit control in current UI) | Yes | Yes | No |
| User Stories: create and submit drafts in the UI | Yes | Yes | No |
| User Stories: update saved story content through backend API (no general content-edit control in current UI) | Yes | Yes | No |
| Approve or reject stories and view approval audit history | Yes | No | Yes |
| Sprints: create in the UI | Yes | Yes | No |
| Sprints: update through backend API (no edit control in current UI) | Yes | Yes | No |
| Tasks: create in the UI and update status/sprint assignment in the UI | Yes | Yes | No |
| Tasks: update other task fields through backend API (not exposed in current UI) | Yes | Yes | No |
| Use live AI story generation | Yes, except a designated demo identity | Yes, except a designated demo identity | No |

The current React interface has no account registration or user-administration screen. Public self-registration is documented as disabled for the Render Free demo. Account access must be supplied by the project owner; this guide does not publish passwords. Backend API permissions do not necessarily correspond to a visible UI control; the table identifies API-only update capabilities where relevant.

## Sign In and Sign Out

**Purpose:** Sign in to an existing account and end the current application session.

**Required role:** Any active account can sign in. The pages and actions available after sign-in depend on the account role.

**How to open:** Visit the application. When not authenticated, the sign-in form is displayed.

**Fields and controls:**

- **Email address** — the account email/login identifier.
- **Password** — the account password; it is masked by the browser input.
- **Sign In** — submits the credentials. The application then verifies the profile and loads the workspace.
- **Sign Out** — available from the authenticated header. It clears the client-side session and protected workspace state and returns the user to sign-in.

**Workflow:** Enter the credentials provided through the authorized private channel and select **Sign In**. Wait for the profile and project data to load. To leave the session, select **Sign Out**.

**Expected result and errors:** Successful authentication opens the Dashboard. Invalid credentials, inactive accounts, expired sessions, or an unavailable API result in an error; a session-expiry response returns the user to sign-in. No registration action is shown on this screen.

**Related screens:** Dashboard and all authenticated sections.

> Screenshot placeholder — `docs/images/user-guide/user-guide-01-sign-in.png` (capture after a real, authorized UI session).

## Dashboard

**Purpose:** Show recent projects and project-level delivery summary metrics.

**Required role:** Admin, Business Analyst, and Reviewer can view it. Project creation is available only to Admin and Business Analyst.

**How to open:** Select **Dashboard** in the main navigation.

**Fields and controls:**

- **Show** — filter the project selector between **Active** and **Archived** projects.
- **Project** — select a project to load its dashboard metrics.
- **Previous** / **Next** — page through the project list where more results exist.
- **Retry projects** / **Retry dashboard** — retry the corresponding failed load.
- **+ New Project** — opens the project creation form for Admin or Business Analyst.
- **Edit** — shown on eligible active project rows to Admin and Business Analyst; opens the project form.

Recent Projects shows the currently loaded page of projects. After selecting a project, the dashboard shows project-scoped totals such as requirements, approved User Stories, tasks and task statuses, and active sprints. The cards are summaries, not editing controls.

**Workflow:** Choose an archive filter, select a project, and review the resulting metrics. Use pagination to reach other projects. If loading fails, select the displayed retry control.

**Expected result and errors:** A selected project displays its available summary. Until a project is selected, the project-specific panel prompts for selection. Empty project lists and load errors are shown in place; the retry action repeats the affected request.

**Related screens:** Projects, Requirements, User Stories, Delivery, and Traceability.

> Screenshot placeholder — `docs/images/user-guide/user-guide-02-dashboard.png`.

## Projects

**Purpose:** Browse the shared project workspace and, for eligible roles, create or update projects and manage their archive state.

**Required role:** All roles can browse. Admin and Business Analyst can create and edit active projects. Only Admin can archive and restore projects.

**How to open:** Select **Projects** in the main navigation, or select **+ New Project** from a screen where it is offered.

### Project list controls

- **Show** — switches between **Active** and **Archived** projects.
- **Previous** / **Next** — page through results.
- **Edit** — opens the selected active project's form; Admin and Business Analyst only.
- **Archive** — archives an active project; Admin only. A browser confirmation is required.
- **Restore** — returns an archived project to the active list; Admin only.

Archived projects are read-only until restored. The list displays archive information when available. There is no hard-delete button in the UI.

### Create or edit a project

The form contains:

- **Project Name** — required; 1–120 characters.
- **Description** — optional; up to 2,000 characters.
- **Status** — **Planned**, **Active**, **On Hold**, or **Completed**.
- **Cancel** — closes the form without submitting the current changes.
- **Create Project** or **Save Changes** — submits the form.

**Workflow:** Select **+ New Project** to create, or **Edit** on an active row to update. Enter the fields, select a status, and submit. The list reloads to show the result. If the project becomes archived while editing, the application reports the conflict and refreshes the project view; restore it before making changes.

**Related screens:** Projects appear in Dashboard, Requirements, User Stories, Traceability, and Delivery selectors.

> Screenshot placeholders — `docs/images/user-guide/user-guide-03-project-list.png` and `docs/images/user-guide/user-guide-04-project-form.png`.

## Requirements

**Purpose:** Record project needs that can be connected to User Stories.

**Required role:** All roles can view. Admin and Business Analyst can create requirements in the UI and have update permission through the authenticated backend API. The current interface exposes requirement creation but no requirement-edit control.

**How to open:** Select **Requirements**, then choose a project.

**Fields and controls:**

- **Project** — selects the project whose requirements are displayed. The selector uses the currently loaded project page; to reach a project on another page, open **Projects**, use **Previous** / **Next** to load that page, then return to **Requirements**.
- **+ New Requirement** — opens the creation form for Admin and Business Analyst.
- **Title** — required; 1–160 characters.
- **Description** — required; 1–5,000 characters.
- **Priority** — **Low**, **Medium**, **High**, or **Critical**.
- **Status** — **Draft**, **In Review**, **Approved**, or **Rejected**.
- **Cancel** — closes the form without submitting.
- **Create Requirement** — saves the new requirement.
- **Previous** / **Next** — page through requirements when needed.

**Workflow:** Select a project, choose **+ New Requirement**, complete the fields, and select **Create Requirement**. The new item appears in the Project Requirements table and can be selected in the User Stories or Delivery workflows.

**Validation and errors:** The backend enforces the title and description limits and allowed priority/status values. A failed request is shown as an error; correct the input or retry after the service issue is resolved.

**Related screens:** User Stories, Delivery, Dashboard, and Traceability.

> Screenshot placeholder — `docs/images/user-guide/user-guide-05-requirements.png`.

## User Stories

**Purpose:** Create draft stories linked to requirements, submit them for review, and review workflow history.

**Required role:** All roles can view saved stories. Admin and Business Analyst can create stories and submit drafts. Admin and Reviewer can approve or reject stories that are in review. Live AI generation has additional restrictions described below.

**How to open:** Select **User Stories**. Choose a project and then a requirement to display the related stories and available drafting actions.

### Select a project and requirement

- **Project** — chooses the project context.
- **Requirement** — chooses the requirement for the story. The options depend on the selected project.
- The project selector displays projects from the currently loaded project page. To reach a project on another page, open **Projects**, use its **Previous** / **Next** controls to load that page, then return to **User Stories** and select the project.
- The requirement selector displays at most the first 100 requirements returned by the current implementation. It has no pagination, search, or filter control; if the needed requirement is not in the displayed options, this selector cannot navigate to it.

### Create a manual story

Select **+ New User Story** or the story creation action. The form contains:

- **Title** — required; 1–160 characters.
- **Description** — required; 1–5,000 characters.
- **Acceptance Criteria (one per line)** — optional; enter each criterion on a separate line. Up to 30 nonblank criteria are accepted, each up to 1,000 characters.
- **Save as Draft** — saves the story with draft status.
- **Cancel** — clears/closes the editor without saving.

**Workflow:** Select the project and requirement, open the story form, enter a concise title and description, and add acceptance criteria on separate lines. Select **Save as Draft**. The saved story appears in the related list. Newly created stories cannot be created directly as approved.

### Submit a story for review

For an eligible draft, select **Submit for Review** and confirm the browser prompt. The status changes to **In Review** if accepted by the backend. This action is not available to Reviewers, and archived-project stories are not writable.

### Approve or reject a story

Admin and Reviewer can decide on an **In Review** story:

- **Approve** — records an approval decision after confirmation.
- **Reject** — records a rejection decision after confirmation.
- **View Audit History** — loads the decision history where permitted.

Only stories in the reviewable state can be decided; invalid state transitions return an error. The audit view includes recorded status transitions and reviewer information as provided by the API. Use synthetic content in a shared demo workspace.

### Story list and errors

The saved list shows story identity/title, description, acceptance criteria, status, creator, and date information where returned. Use the paging controls for additional results. Empty lists explain that no matching stories are available. Errors display a retry action when implemented.

**Related screens:** Requirements, Traceability, Delivery (tasks require an approved story), and approval audit history.

> Screenshot placeholders — `docs/images/user-guide/user-guide-06-story-list-and-review.png`, `docs/images/user-guide/user-guide-07-manual-story-form.png`, `docs/images/user-guide/user-guide-09-approval-audit.png`.

## Traceability

**Purpose:** Explore the relationship from a project requirement to its User Stories and associated tasks.

**Required role:** Admin, Business Analyst, and Reviewer can view. This screen does not expose editing controls.

**How to open:** Select **Traceability**.

**Fields and controls:**

- **Show** — choose **Active** or **Archived** projects.
- **Project** — choose the project to inspect.
- **Previous** / **Next** — page through projects or traceability records when controls are shown.
- **Retry projects** / **Retry traceability** — retry a failed load.
- Disclosure controls — expand or collapse requirement/story hierarchy details; nested tasks are displayed when available.

**Workflow:** Choose the project, then follow each requirement's nested story entries and their tasks. Use the disclosure details to focus the view and pagination to browse beyond the current page.

**Expected result:** The hierarchy presents linked records returned by the traceability endpoint. Empty states indicate that there are no matching relationships on the selected page; an error does not imply that data was deleted.

**Related screens:** Requirements, User Stories, Delivery, and Dashboard.

> Screenshot placeholder — `docs/images/user-guide/user-guide-12-traceability.png`.

## Delivery

**Purpose:** Plan sprints and track implementation tasks linked to approved User Stories.

**Required role:** All roles can view. Admin and Business Analyst can create sprints/tasks and update task status or sprint assignment. Reviewers have read-only delivery controls.

**How to open:** Select **Delivery**, then choose a project.

### Project and story selectors

- **Project** — selects the project for sprint planning and tasks.
- **Requirement** — selects the requirement used to find a story.
- **User Story** — selects the story for task creation/listing.
- The Project selector displays projects from the currently loaded project page. To select a project on another page, open **Projects**, use **Previous** / **Next** to load that page, then return to **Delivery**.
- **Retry requirements** — retries loading the selected project's requirements after a request error.
- **Retry user stories** — retries loading stories for the selected requirement after a request error.
- **Retry sprints** — retries loading the Project Sprints list.
- **Retry sprint options** — appears for Admin or Business Analyst when loading sprint choices for task assignment fails; retries those assignment options.
- **Retry tasks** — appears when loading tasks for the selected story fails; retries that task-list request.

### Create a sprint

When the project is writable, **Create New Sprint** contains:

- **Sprint Name** — required; 1–160 characters.
- **Start Date** and **End Date** — end date cannot precede start date.
- **Status** — **Planned**, **Active**, **Completed**, or **Cancelled**.
- **Cancel** — closes the form.
- **Create Sprint** — saves the sprint.

The Project Sprints table displays sprint name, dates, status, and creation date. The current UI does not expose sprint edit/delete row buttons. Admin and Business Analyst have sprint update permission through the authenticated backend API, but sprint editing is not available as a UI workflow.

### Create and update tasks

The **+ New Task** button appears in **User Story Tasks** only when a writable project and an approved story are selected and the account has the Admin or Business Analyst role. If the story is not approved, the UI displays “Tasks can only be created for approved user stories.” The creation form contains **Task Title** (required, 1–160 characters), **Description (optional)** (up to 5,000 characters), and **Status** (**To Do**, **In Progress**, **In Review**, **Done**). Select **Create Task** to save, or **Cancel** to close without submitting. On success, the task list refreshes and includes the new task.

For Admin and Business Analyst, the task table provides **Change status for [task title]** and **Change sprint assignment for [task title]** selectors. Assignment can be **Unassigned** or a sprint in the same project. Reviewers see the values without edit selectors. These are the task update controls exposed in the current UI; task title and description are not editable there, although broader update operations are supported by the backend API.

**Errors and empty states:** Requirements, story, sprint, and task lists have loading, empty, and error states. Use the relevant retry button after a transient failure. Archived projects are read-only.

**Related screens:** User Stories, Requirements, Dashboard, and Traceability.

> Screenshot placeholders — `docs/images/user-guide/user-guide-10-delivery-sprints.png` and `docs/images/user-guide/user-guide-11-task-management.png`.

## Pagination, loading, empty, and error states

Project, requirement, story, and traceability collections may be paginated. Use **Previous** and **Next** where displayed; the interface disables navigation when loading or when there is no page in that direction. Dashboard and Traceability project selectors have paging controls. Requirements, User Stories, and Delivery project selectors use the currently loaded project page; go to **Projects** and use its pagination to load a different page, then return to the desired section. The User Stories requirement selector is an exception: it shows only the first 100 requirements and provides no paging control.

During a request, the relevant button or section may show a loading label or disabled state. Empty-state messages mean the current selection/filter has no items to display; they are not an indication that another user's data is private. Error messages appear near the affected panel and may provide **Retry projects**, **Retry dashboard**, **Retry traceability**, **Retry requirements**, **Retry user stories**, **Retry sprints**, **Retry sprint options**, or **Retry tasks**. Retry only the failed read unless the UI explicitly indicates that a write failed; after an ambiguous write result, inspect the list before submitting again to avoid duplicates.

Some actions use a browser confirmation prompt (project archive/restore and story review transitions). Read the prompt before confirming.

> Screenshot placeholder — `docs/images/user-guide/user-guide-13-validation-and-empty-states.png`.

## Public demo and data safety

The planned demo identities are:

- `banlyst@example.com` — Business Analyst
- `reviwer@example.com` — Reviewer

Their current active status and usability in production are **not verified by this guide**. Do not assume a password or anonymous access. The project owner must provide any authorized credentials through a private channel. Do not place credentials in public documentation, screenshots, issues, or logs.

All accounts use a shared workspace rather than isolated per-user projects. Reviewers and Business Analysts may encounter or change the same synthetic records according to their permissions. Avoid editing or archiving another participant's project; label new demo content clearly and use synthetic data only. Public demo data should not contain personal, confidential, or production information.

## AI-assisted User Story generation

For an authorized account where the provider is configured and available, the implemented flow is:

1. Select a project and requirement.
2. Select **Generate AI Draft**.
3. Review and edit the returned title, description, and acceptance criteria.
4. Select the human-review confirmation checkbox.
5. Select **Save as Draft** to save the reviewed draft.
6. When ready, submit the saved draft for human review using **Submit for Review**.

Generation returns an unsaved draft; it is not automatically persisted or approved. Human review is required before saving an AI-generated draft. AI content remains a draft subject to the normal review workflow.

In the inspected local implementation, live generation is disabled for the exact designated demo identities `banlyst@example.com` and `reviwer@example.com`. The frontend disables the action and the backend rejects direct requests. This restriction has **not yet been verified in production**. Public demo Business Analysts can create stories manually, and Reviewers can review, approve, or reject stories. Authorized non-demo Business Analysts and Admins may generate drafts when the provider is configured and reachable.

The current data model does not establish reliable provenance for saved stories. Do not describe a saved story as AI-generated unless that fact has been independently verified. BYOK (bring your own key) is not supported or planned for this demo.

## Known hosting limitations

The repository's Render Free deployment guide describes the demo as short-lived and non-production. It documents Free services as subject to cold starts and the Free PostgreSQL database as limited in size and lifecycle, with no managed backups; the guide advises treating demonstration data as disposable and checking the provider's current limits. These are configuration/documentation caveats, not a live status check. Allow time for a sleeping API service to wake, and do not rely on the demo database as durable storage.

## Screenshot plan

The following are placeholders for future genuine screenshots. No image files are included or implied. Save approved, redacted captures under `docs/images/user-guide/`; use synthetic data and omit credentials, personal information, tokens, and secrets.

| Screen/state | Future screenshot filename |
|---|---|
| Sign In | `docs/images/user-guide/user-guide-01-sign-in.png` |
| Dashboard | `docs/images/user-guide/user-guide-02-dashboard.png` |
| Project list | `docs/images/user-guide/user-guide-03-project-list.png` |
| Project form | `docs/images/user-guide/user-guide-04-project-form.png` |
| Requirements | `docs/images/user-guide/user-guide-05-requirements.png` |
| User Story list and review | `docs/images/user-guide/user-guide-06-story-list-and-review.png` |
| Manual User Story form | `docs/images/user-guide/user-guide-07-manual-story-form.png` |
| Disabled AI Generate | `docs/images/user-guide/user-guide-08-ai-demo-disabled.png` |
| Approval audit history | `docs/images/user-guide/user-guide-09-approval-audit.png` |
| Delivery and sprints | `docs/images/user-guide/user-guide-10-delivery-sprints.png` |
| Task management | `docs/images/user-guide/user-guide-11-task-management.png` |
| Traceability | `docs/images/user-guide/user-guide-12-traceability.png` |
| Validation and empty states | `docs/images/user-guide/user-guide-13-validation-and-empty-states.png` |
| Admin project archive/restore | `docs/images/user-guide/user-guide-14-admin-project-archive.png` |

The Admin-only capture requires an authorized Admin session. The disabled-AI capture requires a designated demo identity after its availability is verified. Do not use fabricated UI images or imply production verification through screenshots.
