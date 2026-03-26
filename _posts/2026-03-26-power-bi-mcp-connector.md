---
layout: post
title: "Power BI MCP connector with progressive discovery for Copilot Studio"
date: 2026-03-26 10:00:00 -0600
categories: [Power Platform, Custom Connectors]
tags: [Power BI, Copilot Studio, MCP, Power Mission Control, DAX, reports, dashboards]
---

Power BI has a deep REST API—workspaces, reports, dashboards, datasets, apps, DAX queries, and async report export. Wrapping each operation as a typed MCP tool would flood the orchestrator's context window before it even starts working. This connector uses [Power Mission Control](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20Mission%20Control%20Template) to expose 35 operations across 6 domains through three tools, plus 16 REST operations for Power Automate and Power Apps.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Power%20BI)

## Tools

### Orchestration tools (scan, launch, sequence)

| Tool | Description |
|------|-------------|
| `scan_powerbi` | Discover available Power BI operations by intent or domain |
| `launch_powerbi` | Execute any Power BI API endpoint |
| `sequence_powerbi` | Execute multiple Power BI operations in one call |

### How it works

```
User: "What reports do I have?"

1. Orchestrator calls scan_powerbi({query: "list reports"})
   → Returns: list_reports (GET /reports), list_workspace_reports (GET /groups/{groupId}/reports)

2. Orchestrator calls launch_powerbi({
     endpoint: "/reports",
     method: "GET"
   })
   → Returns: list of reports with IDs, names, and URLs
```

### Capability index domains

The index covers 35 operations across 6 domains:

| Domain | Operations | Examples |
|--------|-----------|----------|
| workspaces | 3 | List workspaces, get workspace, list workspace users |
| reports | 7 | List/get reports, get pages, clone report |
| dashboards | 6 | List/get dashboards, list tiles |
| datasets | 11 | List/get datasets, refresh, refresh history, datasources, execute DAX queries |
| apps | 6 | List/get installed apps, app reports, app dashboards |
| export | 2 | Trigger report export, poll export status |

## DAX query execution

Run DAX queries directly against datasets through the orchestrator:

```
User: "Run a DAX query against dataset cfafbeb1-8037-4d0c-896e-a46fb27ff229
        to get all rows from the Sales table"

1. Orchestrator calls scan_powerbi({query: "execute DAX query"})
   → Returns: execute_queries (POST /datasets/{datasetId}/executeQueries)

2. Orchestrator calls launch_powerbi({
     endpoint: "/datasets/cfafbeb1-8037-4d0c-896e-a46fb27ff229/executeQueries",
     method: "POST",
     body: {
       "queries": [{ "query": "EVALUATE VALUES(Sales)" }],
       "serializerSettings": { "includeNulls": true }
     }
   })
   → Returns: query results with rows and columns
```

DAX queries are limited to 100,000 rows or 1,000,000 values per query, whichever is hit first. Power BI throttles at 120 query requests per minute per user—the connector handles HTTP 429 responses with automatic retry using the `Retry-After` header.

The `Dataset Execute Queries REST API` tenant setting must be enabled in the Power BI admin portal under **Integration settings** for this to work.

## Report export workflow

Export uses an async flow. The connector's capability index includes orchestration hints so the orchestrator chains the steps automatically:

1. `scan_powerbi` → find `export_report`
2. `launch_powerbi` → trigger `POST /reports/{reportId}/ExportTo` with format (PDF, PPTX, PNG)
3. `scan_powerbi` → find `get_export_status`
4. `launch_powerbi` → poll `GET /reports/{reportId}/exports/{exportId}` until `status: Succeeded`
5. Share the `resourceLocation` download URL with the user

The `export_report` capability description explicitly tells the orchestrator to poll with `get_export_status` after triggering, so it chains correctly without additional prompting.

## Sequence operations

Use `sequence_powerbi` to combine multiple API calls:

```json
{
  "requests": [
    { "id": "1", "endpoint": "/reports", "method": "GET" },
    { "id": "2", "endpoint": "/datasets", "method": "GET" }
  ]
}
```

This returns reports and datasets in a single response, reducing round trips. Maximum 20 requests per sequence.

## REST operations for Power Automate and Power Apps

The same connector exposes 16 typed Swagger operations for use in flows and apps:

| Operation | Operation ID | Description |
|-----------|-------------|-------------|
| List Workspaces | `ListWorkspaces` | List all workspaces the user has access to |
| List Reports | `ListReports` | List reports from My workspace |
| List Workspace Reports | `ListWorkspaceReports` | List reports from a specific workspace |
| Get Report | `GetReport` | Get details of a specific report |
| Get Report Pages | `GetReportPages` | List pages within a report |
| List Dashboards | `ListDashboards` | List dashboards from My workspace |
| List Workspace Dashboards | `ListWorkspaceDashboards` | List dashboards from a specific workspace |
| List Dashboard Tiles | `ListDashboardTiles` | List tiles within a dashboard |
| List Datasets | `ListDatasets` | List datasets from My workspace |
| List Workspace Datasets | `ListWorkspaceDatasets` | List datasets from a specific workspace |
| Execute DAX Query | `ExecuteQueries` | Run DAX queries against a dataset |
| Get Refresh History | `GetRefreshHistory` | Get refresh history for a dataset |
| Refresh Dataset | `RefreshDataset` | Trigger a dataset refresh |
| List Apps | `ListApps` | List installed Power BI apps |
| Export Report | `ExportReport` | Trigger a report export to PDF/PPTX/PNG |
| Get Export Status | `GetExportStatus` | Check the status of an export job |

## Prerequisites

1. An Azure AD app registration with delegated permissions for Power BI
2. A Power Platform environment with a custom connector license
3. The `Dataset Execute Queries REST API` tenant setting enabled in the Power BI admin portal (under **Integration settings**) for DAX query execution

## Setting up the connector

### 1. Register an Azure AD application

1. Go to [Azure portal](https://portal.azure.com/) > **Microsoft Entra ID** > **App registrations**
2. Select **New registration**
   - **Name:** `Power BI Connector`
   - **Supported account types:** Accounts in any organizational directory (Multitenant)
   - **Redirect URI:** Web > `https://global.consent.azure-apim.net/redirect`
3. Note the **Application (client) ID**
4. Go to **Certificates & secrets** > **New client secret** > note the secret value
5. Go to **API permissions** > **Add a permission** > **Power BI Service** > **Delegated permissions**:
   - `Dashboard.Read.All`
   - `Dataset.Read.All`
   - `Dataset.ReadWrite.All`
   - `Report.Read.All`
   - `Workspace.Read.All`
   - `App.Read.All`
6. Select **Grant admin consent** (or have a tenant admin do this)

### 2. Update apiProperties.json

Replace `[YOUR_CLIENT_ID]` with your Application (client) ID.

### 3. Create the custom connector

1. Go to [Power Platform Maker Portal](https://make.powerapps.com/)
2. Navigate to **Custom connectors** > **+ New custom connector** > **Import an OpenAPI file**
3. Upload `apiDefinition.swagger.json`
4. On the **Security** tab:
   - **Authentication type:** OAuth 2.0
   - **Identity Provider:** Azure Active Directory
   - **Client ID:** Your Application ID
   - **Client Secret:** Your secret
   - **Resource URL:** `https://analysis.windows.net/powerbi/api`
5. On the **Code** tab:
   - Enable **Code**
   - Upload `script.csx`
6. Select **Create connector**

### 4. Test the connection

1. Select the **Test** tab > **+ New connection**
2. Sign in with your Microsoft account
3. Test the `InvokeMCP` operation with:

```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "id": "1",
  "params": {
    "protocolVersion": "2025-11-25",
    "clientInfo": { "name": "test" }
  }
}
```

### 5. Add to Copilot Studio

1. In Copilot Studio, open your agent
2. Add this connector as an action—Copilot Studio detects the MCP endpoint via `x-ms-agentic-protocol`
3. Test with prompts like "What workspaces do I have?" or "List my reports"

## Required permissions

| Permission | Type | Purpose |
|------------|------|---------|
| `Dashboard.Read.All` | Delegated | Read dashboards and tiles |
| `Dataset.Read.All` | Delegated | Read datasets, execute DAX queries |
| `Dataset.ReadWrite.All` | Delegated | Trigger dataset refreshes |
| `Report.Read.All` | Delegated | Read reports, export reports |
| `Workspace.Read.All` | Delegated | Read workspaces and workspace users |
| `App.Read.All` | Delegated | Read installed apps |

## Authentication

| Setting | Value |
|---------|-------|
| Identity provider | Azure Active Directory |
| Authorization URL | `https://login.microsoftonline.com/common/oauth2/v2.0/authorize` |
| Token URL | `https://login.microsoftonline.com/common/oauth2/v2.0/token` |
| Resource URL | `https://analysis.windows.net/powerbi/api` |
| On-behalf-of login | Enabled |

## Power BI API notes

- All Power BI REST API endpoints use base URL `https://api.powerbi.com/v1.0/myorg`
- Workspaces are called "groups" in the API (for example, `/groups/{groupId}`)
- DAX queries are limited to 100,000 rows or 1,000,000 values per query, whichever is hit first
- Power BI throttles at 120 query requests per minute per user (HTTP 429 with `Retry-After` header, handled automatically)
- Report export is asynchronous—trigger with `ExportTo`, poll status, then download via `resourceLocation` URL
- Export supports PDF, PPTX, and PNG for Power BI reports; paginated reports additionally support XLSX, DOCX, CSV, XML, and MHTML

## Files

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | OpenAPI 2.0 definition with MCP endpoint and 16 REST operations |
| `apiProperties.json` | OAuth config with Power BI scopes and script operation bindings |
| `script.csx` | Power Mission Control v3 framework with 35-entry capability index across 6 domains |
| `readme.md` | Setup and usage documentation |

## Resources

- [Power BI connector source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Power%20BI)
- [Power Mission Control template](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20Mission%20Control%20Template)
- [Power BI REST API reference](https://learn.microsoft.com/rest/api/power-bi/)
