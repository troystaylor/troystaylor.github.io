---
layout: post
title: "Jira MCP connector for Power Platform with enhanced search and auto-pagination"
date: 2026-06-02 09:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Jira, MCP, Custom Connectors, Power Platform, Copilot Studio, Atlassian, JQL]
description: "Power Platform custom connector for Jira Cloud with 15 REST operations, 13 MCP tools for Copilot Studio, cursor-based enhanced search, opt-in server-side auto-pagination, and Application Insights telemetry."
---

Atlassian is retiring the legacy `/rest/api/3/search` endpoint. Anything still calling it stops working soon. My Jira connector v1.1 moves to the enhanced cursor-based endpoint and adds opt-in server-side auto-pagination so Power Automate flows and Copilot Studio agents can pull more than 100 issues without hand-rolling cursor loops.

You can find the complete code in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Jira).

## What's in v1.1

The key changes in v1.1:

- `SearchIssues` now uses `POST /rest/api/3/search/jql` (cursor-based)
- Opt-in `limit` parameter for server-side auto-pagination on `SearchIssues` and `jira_list_comments`
- Backward-compatible defaults so existing flows keep working
- Plain text to Atlassian Document Format (ADF) conversion for MCP write tools
- Optional Application Insights telemetry

## REST operations

The connector exposes 15 REST operations:

| Operation | Description |
|-----------|-------------|
| `ListProjects` | List projects |
| `SearchIssues` | Search issues using JQL (enhanced search, cursor-based) |
| `GetIssue` | Get an issue by ID or key |
| `CreateIssue` | Create a new issue |
| `UpdateIssue` | Update an issue |
| `ListIssueTypes` | List issue types |
| `GetProjectRoles` | Get roles for a project |
| `GetProjectStatuses` | Get statuses for a project |
| `ListComments` | List comments for an issue |
| `AddComment` | Add a comment to an issue |
| `GetTransitions` | List available transitions |
| `TransitionIssue` | Transition an issue |
| `ListFields` | List issue fields |
| `GetUser` | Get a user by accountId |
| `SearchUsers` | Search users |

This gives you a clean Power Automate surface for scheduled syncs, triggers, and multi-step automations that chain Jira with Dataverse, SharePoint, and Outlook.

## MCP tools for Copilot Studio

The connector exposes 13 MCP tools through JSON-RPC 2.0:

| Tool | Description |
|------|-------------|
| `jira_list_projects` | List visible projects |
| `jira_list_issue_types` | List issue types |
| `jira_list_project_roles` | List roles for a project |
| `jira_list_project_statuses` | List statuses for a project |
| `jira_search_issues` | Search issues using JQL |
| `jira_get_issue` | Get an issue by ID or key |
| `jira_create_issue` | Create a new issue |
| `jira_create_issue_simple` | Create an issue from common fields |
| `jira_update_issue` | Update an existing issue |
| `jira_list_comments` | List comments for an issue |
| `jira_add_comment` | Add a comment to an issue |
| `jira_get_transitions` | List available transitions |
| `jira_transition_issue` | Transition an issue to a new status |

Add the connector as an action in Copilot Studio and the agent discovers the tools automatically:

**User:** "Show me all open bugs in PROJ assigned to me"
**Agent:** Calls `jira_search_issues` with `project = PROJ AND status = Open AND assignee = currentUser() AND type = Bug`

**User:** "Move PROJ-123 to In Review and add a comment"
**Agent:** Chains `jira_get_transitions`, `jira_transition_issue`, and `jira_add_comment`

The agent handles the JQL, the transition ID lookup, and the ADF conversion for the comment body.

## Why the enhanced search matters

The legacy `POST /rest/api/3/search` endpoint is being removed by Atlassian. The replacement is `POST /rest/api/3/search/jql`, which is cursor-based and does not return a `total` count.

The connector wraps that for you. Request fields:

- `jql` (required) — JQL query string
- `maxResults` (optional) — Records per Jira page (1 to 100)
- `limit` (optional) — Total cap across pages
- `nextPageToken` (optional) — Cursor from a previous response
- `fields` (optional) — Field names to return

Sample response:

```json
{
  "isLast": false,
  "nextPageToken": "CAEaAggB",
  "fetched": 500,
  "issues": [ ... ]
}
```

If you need an issue count, use `POST /rest/api/3/search/approximate-count`. The new endpoint intentionally drops `total` for performance reasons.

## Opt-in auto-pagination

Jira caps results at 100 records per page. To retrieve more, the connector supports opt-in server-side auto-pagination on two operations.

For `SearchIssues` and `jira_search_issues`, set `limit` to the total cap you want across pages. The connector loops through Jira pages until that many records are collected or no more pages remain.

For `jira_list_comments`, the same `limit` parameter auto-pages over the classic `startAt` / `maxResults` model.

When `limit` is omitted, both operations return a single Jira page. That keeps existing Power Automate flows working without any change.

## Atlassian Document Format conversion

Jira Cloud uses Atlassian Document Format (ADF) for rich text fields like descriptions and comments. MCP tools that accept plain text convert the text into a simple ADF document before sending the request, so agents can write natural prose without learning ADF.

## OAuth scopes

The connector requests:

- `read:jira-work`
- `write:jira-work`
- `read:jira-user`

Adjust scopes in `apiProperties.json` if you add or remove operations. Each user authorizes with their own Atlassian account, so permissions follow the user rather than the connector.

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

Create a connection using the OAuth 2.0 popup.

### 4. Add to Copilot Studio

1. In Copilot Studio, open your agent.
2. Add this connector as an action.
3. Test with prompts like "List Jira projects" or "Search Jira issues with JQL".

## Application Insights

To enable telemetry, set the `APP_INSIGHTS_CONNECTION_STRING` constant in `script.csx`.

Events tracked:

- `RequestReceived`
- `RequestCompleted`
- `RequestError`
- `McpRequestReceived`
- `McpToolCallStarted`
- `McpToolCallCompleted`
- `McpToolCallError`

That gives you per-tool latency, error rates, and call volume across both REST and MCP paths.

## Why not Rovo?

Atlassian's Rovo MCP server covers Jira, Confluence, Compass, and JSM, and you can add it directly to Copilot Studio. So why build a Power Platform custom connector?

Two reasons:

- **Power Automate.** MCP tools alone don't give you scheduled flows, triggers, or multi-step automations that chain Jira with Dataverse, SharePoint, and Outlook. This connector ships both surfaces from one OAuth connection.
- **Direct REST.** This connector calls the Jira REST API directly. No Rovo rate limits, no admin domain allowlists, no intermediary between your tenant and Atlassian.

## Try it yourself

The complete connector code is available in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Jira):

- [apiDefinition.swagger.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Jira/apiDefinition.swagger.json) — OpenAPI specification
- [script.csx](https://github.com/troystaylor/SharingIsCaring/blob/main/Jira/script.csx) — Connector script with MCP tools and telemetry
- [apiProperties.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Jira/apiProperties.json) — Connector metadata
- [readme.md](https://github.com/troystaylor/SharingIsCaring/blob/main/Jira/readme.md) — Full documentation

## Resources

- [Jira Cloud REST API reference](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [Jira enhanced search endpoint](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-jql-post)
- [Atlassian Document Format](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/)
- [Atlassian OAuth 2.0 (3LO) apps](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/)
- [Application Insights telemetry for connectors](https://troystaylor.com/power%20platform/2026-01-07-power-platform-custom-connectors-application-insights.html)
- [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring)
