---
layout: post
title: "Jira MCP connector v1.3 with agile, bulk operations, and attachments"
date: 2026-06-04 09:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Jira, MCP, Custom Connectors, Power Platform, Copilot Studio, Atlassian, Agile]
description: "Power Platform custom connector for Jira Cloud with 91 REST operations, 50 MCP tools for Copilot Studio, Jira Software agile support, bulk issue operations, multipart attachment upload, filter CRUD, and Application Insights telemetry."
---

The v1.1 release of my Jira connector covered the basics: 15 REST operations and 13 MCP tools, mostly issue search and lifecycle. v1.3 turns it into a full Jira surface for Power Platform — 91 REST operations and 50 MCP tools, with Jira Software agile, bulk issue operations, multipart file attachments, watchers, votes, worklogs, filter CRUD, and a lot more.

You can find the complete code in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Jira).

## What's new since v1.1

The v1.2 release added `GetIssueByKey`, filter search, users-by-project, async task get/cancel, and accessible resources list. v1.3 is the bigger jump:

- Jira Software agile — boards, sprints, epics
- Bulk issue operations — `BulkCreateIssues`, `BulkFetchIssues`
- Engagement — watchers, votes, issue links
- Worklogs — full CRUD
- File attachments — multipart upload, metadata, delete
- Filters — full CRUD plus my filters and favourites
- Project versions and components — full CRUD
- Groups and status catalog
- Cross-reference suffixes on dependent MCP tools so agents know which discovery tool to call first

Total: 32 new MCP tools (now 50), and 76 new REST operations (now 91).

## REST operations

The 91 operations are split across the two Jira API surfaces.

### Jira Platform (`/rest/api/3`)

| Group | Operations |
|-------|------------|
| Projects | `ListProjects`, `SearchProjects`, `GetProject`, `GetProjectVersions`, `CreateVersion`, `GetVersion`, `UpdateVersion`, `DeleteVersion`, `GetProjectComponents`, `CreateComponent`, `GetComponent`, `UpdateComponent`, `DeleteComponent`, `GetStatuses`, `GetProjectRoles`, `GetProjectStatuses` |
| Issues | `SearchIssues`, `GetIssue`, `CreateIssue`, `UpdateIssue`, `DeleteIssue`, `AssignIssue`, `GetEditIssueMeta`, `NotifyIssue`, `BulkCreateIssues`, `BulkFetchIssues`, `ArchiveIssues`, `UnarchiveIssues`, `ListIssueTypes` |
| Comments | `ListComments`, `AddComment`, `GetComment`, `UpdateComment`, `DeleteComment` |
| Transitions | `GetTransitions`, `TransitionIssue` |
| Watchers and votes | `GetIssueWatchers`, `AddWatcher`, `RemoveWatcher`, `GetVotes`, `AddVote`, `RemoveVote` |
| Issue links | `LinkIssues`, `GetIssueLink`, `DeleteIssueLink`, `GetIssueLinkTypes` |
| Worklogs | `AddWorklog`, `GetIssueWorklogs`, `UpdateWorklog`, `DeleteWorklog` |
| Attachments | `UploadAttachment`, `GetAttachmentMetadata`, `DeleteAttachment` |
| Filters | `ListFilters`, `GetFilter`, `CreateFilter`, `UpdateFilter`, `DeleteFilter`, `GetMyFilters`, `GetFavouriteFilters`, `SetFilterFavourite`, `DeleteFilterFavourite` |
| Users, groups, fields | `GetUser`, `SearchUsers`, `ListUsersByProject`, `FindGroups`, `GetGroupMembers`, `ListFields` |
| Async tasks | `GetTask`, `CancelTask` |
| OAuth | `ListAccessibleResources` |
| MCP | `InvokeMCP` |

### Jira Agile (`/rest/agile/1.0`)

| Group | Operations |
|-------|------------|
| Boards | `ListBoards`, `GetBoard`, `GetBoardConfiguration`, `GetBoardIssues`, `GetBoardBacklog`, `GetBoardProjects` |
| Sprints | `ListBoardSprints`, `GetSprint`, `CreateSprint`, `UpdateSprint`, `DeleteSprint`, `GetSprintIssues`, `MoveIssuesToSprint`, `MoveIssuesToBacklog` |
| Epics | `ListBoardEpics`, `GetEpic`, `GetEpicIssues`, `MoveIssuesToEpic`, `RemoveIssuesFromEpic` |

That's enough surface for scheduled syncs that sweep issues, sprints, and worklogs into Dataverse, scheduled flows that close out sprints, and triggered automations that link issues across projects.

## MCP tools for Copilot Studio

50 tools across discovery, issues, comments, transitions, engagement, filters, project metadata, async tasks, and agile.

### Discovery

`jira_list_projects`, `jira_search_projects`, `jira_get_project`, `jira_get_project_versions`, `jira_get_project_components`, `jira_list_issue_types`, `jira_list_project_roles`, `jira_list_project_statuses`, `jira_get_issue_link_types`, `jira_search_users`, `jira_list_users_by_project`, `jira_list_filters`, `jira_list_accessible_resources`

### Issues

`jira_search_issues`, `jira_get_issue`, `jira_create_issue`, `jira_create_issue_simple`, `jira_update_issue`, `jira_delete_issue`, `jira_assign_issue`, `jira_bulk_create_issues`, `jira_bulk_fetch_issues`

### Comments and transitions

`jira_list_comments`, `jira_add_comment`, `jira_get_transitions`, `jira_transition_issue`

### Engagement

`jira_get_watchers`, `jira_add_watcher`, `jira_remove_watcher`, `jira_link_issues`, `jira_add_worklog`, `jira_get_issue_worklogs`, `jira_upload_attachment`

### Filters

`jira_get_filter`, `jira_create_filter`, `jira_update_filter`, `jira_delete_filter`

### Project versions and components

`jira_create_version`, `jira_create_component`

### Async tasks

`jira_get_task`, `jira_cancel_task`

### Agile (Jira Software)

`jira_list_boards`, `jira_get_board_issues`, `jira_get_board_backlog`, `jira_list_board_sprints`, `jira_list_board_epics`, `jira_create_sprint`, `jira_update_sprint`, `jira_get_sprint_issues`, `jira_move_issues_to_sprint`

## Cross-reference suffixes for agents

When an agent has 50 tools to choose from, it needs to know which discovery tool to call first. Every dependent tool in v1.3 carries a short cross-reference in its description so the orchestrator can chain calls without guessing.

For example:

- `jira_get_issue` advises calling `jira_search_issues` first
- `jira_transition_issue` advises calling `jira_get_transitions` first
- `jira_update_sprint` advises calling `jira_list_board_sprints` first
- `jira_move_issues_to_sprint` advises calling `jira_search_issues` for the issue keys and `jira_list_board_sprints` for the sprint ID

The result: an agent prompt like "close sprint 42 and move the open issues to the next sprint" resolves into a clean three-step chain without trial and error.

## Bulk issue operations

`jira_bulk_create_issues` and `jira_bulk_fetch_issues` wrap the Jira bulk endpoints so an agent or flow can create or read up to the Atlassian per-request cap in one call.

Sample bulk create payload:

```json
{
  "issueUpdates": [
    {
      "fields": {
        "project": { "key": "PROJ" },
        "summary": "Migrate auth to OAuth 2.1",
        "issuetype": { "name": "Story" }
      }
    },
    {
      "fields": {
        "project": { "key": "PROJ" },
        "summary": "Update connector docs",
        "issuetype": { "name": "Task" }
      }
    }
  ]
}
```

Bulk fetch takes a list of issue IDs or keys and returns them in a single response, so a triggered flow can hydrate a batch of issues without firing one HTTP call per record.

## Multipart attachments

`UploadAttachment` (REST) and `jira_upload_attachment` (MCP) both accept a JSON body with the file as base64:

```json
{
  "filename": "report.pdf",
  "contentBase64": "JVBERi0xLjQK...",
  "contentType": "application/pdf"
}
```

The connector:

1. Validates the base64 payload and enforces a 10 MB cap on the decoded size
2. Builds a `multipart/form-data` request with the file part named `file`
3. Sets `X-Atlassian-Token: no-check` to bypass the Jira XSRF check (required by the attachments API)
4. Forwards the user's OAuth bearer token
5. POSTs to `/rest/api/3/issue/{issueIdOrKey}/attachments`

`contentType` defaults to `application/octet-stream` when omitted. That lets a Power Automate flow that just pulled a file from SharePoint or OneDrive forward it straight into a Jira issue with no extra steps.

## Agile workflows in Copilot Studio

With boards, sprints, and epics in scope, an agent can run scrum master patterns end to end:

**User:** "Show me the active sprint for board 1 and list any issues still open"
**Agent:** Calls `jira_list_board_sprints` filtered to active state, then `jira_get_sprint_issues` and filters by status.

**User:** "Move all unfinished issues from sprint 42 to sprint 43"
**Agent:** Chains `jira_get_sprint_issues`, `jira_move_issues_to_sprint`.

**User:** "Create a new sprint called Hardening for board 1"
**Agent:** Calls `jira_create_sprint` with the board ID it remembered from earlier in the conversation.

## Auto-pagination and enhanced search

The v1.1 enhanced search behavior carries forward unchanged. `SearchIssues` and `jira_search_issues` use the cursor-based `POST /rest/api/3/search/jql` endpoint. Set the optional `limit` parameter to trigger server-side auto-pagination across Jira pages, or omit it for a single page (backward-compatible default).

`jira_list_comments` uses the same opt-in `limit` pattern over the classic `startAt` / `maxResults` model.

If you need an issue count from the new search endpoint, call `POST /rest/api/3/search/approximate-count`. The cursor-based endpoint intentionally drops `total` for performance.

## OAuth scopes

The connector still requests three scopes:

- `read:jira-work`
- `write:jira-work`
- `read:jira-user`

Jira Software (agile) operations are gated by the same `read:jira-work` and `write:jira-work` scopes, so the agile additions need no new permissions. If your Atlassian app uses finer-grained agile scopes (`read:sprint:jira-software`, for example), add them in the developer console and update `apiProperties.json` to match.

## Setup

### 1. Create an Atlassian OAuth 2.0 (3LO) app

1. Go to the Atlassian developer console.
2. Create a new OAuth 2.0 (3LO) app.
3. Add this redirect URL: `https://global.consent.azure-apim.net/redirect`
4. Copy the Client ID and Client Secret.

### 2. Import the connector

1. In the Power Platform Maker portal, go to **Custom connectors > Import an OpenAPI file**.
2. Import `apiDefinition.swagger.json`.
3. On the **Code** tab, paste the contents of `script.csx` and toggle the code on.
4. Save the connector.

### 3. Create a connection

Create a connection using the OAuth 2.0 popup with the Client ID and Client Secret from your Atlassian app.

### 4. Add to Copilot Studio

1. In Copilot Studio, open your agent.
2. Add this connector as an action (MCP server).
3. Test with prompts like "List Jira projects", "Search Jira issues with JQL", or "Show me board 1's active sprint".

## Application Insights

To enable telemetry, set the `APP_INSIGHTS_INSTRUMENTATION_KEY` constant in `script.csx`. Telemetry is silently skipped when the placeholder value is unchanged.

Events tracked:

- `RequestReceived`
- `RequestCompleted`
- `RequestError`
- `McpRequestReceived`
- `McpToolCallStarted`
- `McpToolCallCompleted`
- `McpToolCallError`

That gives you per-tool latency, error rates, and call volume across all 91 REST operations and 50 MCP tools.

## Try it yourself

The complete connector code is in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Jira):

- [apiDefinition.swagger.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Jira/apiDefinition.swagger.json) — OpenAPI specification
- [script.csx](https://github.com/troystaylor/SharingIsCaring/blob/main/Jira/script.csx) — Connector script with MCP tools and telemetry
- [apiProperties.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Jira/apiProperties.json) — Connector metadata
- [readme.md](https://github.com/troystaylor/SharingIsCaring/blob/main/Jira/readme.md) — Full documentation

## Resources

- [v1.1 release post: enhanced search and auto-pagination](https://troystaylor.com/power%20platform/custom%20connectors/2026-06-02-jira-mcp-connector-v1-1.html)
- [Jira Cloud REST API reference](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [Jira Software (Agile) REST API reference](https://developer.atlassian.com/cloud/jira/software/rest/intro/)
- [Jira enhanced search endpoint](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-jql-post)
- [Atlassian Document Format](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/)
- [Atlassian OAuth 2.0 (3LO) apps](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/)
- [Application Insights telemetry for connectors](https://troystaylor.com/power%20platform/2026-01-07-power-platform-custom-connectors-application-insights.html)
- [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring)
