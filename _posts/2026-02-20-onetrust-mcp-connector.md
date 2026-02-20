---
layout: post
title: "OneTrust MCP connector for Power Platform"
date: 2026-02-20 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [OneTrust, MCP, Custom Connectors, Power Platform, Copilot Studio, Risk Management, Incident Management, Compliance]
description: "Power Platform custom connector for OneTrust risk and incident management with 14 MCP tools and direct REST endpoints for Power Automate flows."
---

OneTrust is a privacy, security, and governance platform. Its APIs cover risk registers, incident management, and organizational hierarchies. This connector wraps those APIs into a Power Platform custom connector with both direct REST endpoints for Power Automate flows and MCP tools for Copilot Studio agents.

You can find the complete code in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/OneTrust).

The connector exposes 14 MCP tools that a Copilot Studio agent discovers automatically. Create and manage risks, log incidents, move items through workflow stages, link incidents to inventory, and query organizations—all through natural language.

## What's included

### Direct REST operations

These endpoints work with Power Automate flows, Power Apps, and other Power Platform consumers:

| Operation | Method | Description |
|-----------|--------|-------------|
| Create Risk | POST | Create a new risk in the Risk Register |
| Create Incident | POST | Create a new incident in the Incident Register |
| Get Incident | GET | Retrieve details of a specific incident by ID |
| Search Incidents | POST | Search incidents with filters and full-text search |
| Update Incident | PUT | Update an existing incident |
| Update Incident Stage | POST | Move an incident to a different workflow stage |
| Link Incident to Inventory | POST | Link an incident to assets, processing activities, vendors, or entities |
| Get Organizations | GET | Retrieve the hierarchical list of organizations |
| Upsert Risk | PUT | Create or update a risk based on matching attributes |
| Update Risk | PUT | Fully update an existing risk |
| Delete Risk | DELETE | Delete a risk from the Risk Register |
| Modify Risk | PATCH | Partially update specific fields of a risk |
| Update Risk Stage | POST | Move a risk to a different workflow stage |
| Get Risk Template | GET | Retrieve details of a risk template by ID |

### MCP tools (14 tools)

The `InvokeMCP` operation exposes these tools via MCP for Copilot Studio agents:

| Tool | Description |
|------|-------------|
| `createRisk` | Create a new risk in the Risk Register |
| `createIncident` | Create a new incident in the Incident Register |
| `getIncident` | Get details of a specific incident |
| `searchIncidents` | Search incidents with filters and full-text |
| `getOrganizations` | List all organizations in hierarchy |
| `upsertRisk` | Create or update a risk based on match attributes |
| `updateIncident` | Update an existing incident |
| `updateIncidentStage` | Move an incident to the next workflow stage |
| `updateRisk` | Fully update an existing risk |
| `deleteRisk` | Delete a risk |
| `updateRiskStage` | Move a risk to a different workflow stage |
| `linkIncidentToInventory` | Link an incident to inventory items |
| `getRiskTemplate` | Get risk template details |
| `modifyRisk` | Partially update specific fields of a risk |

## Setup

### 1. Create an OAuth application in OneTrust

1. Log in to your OneTrust admin portal
2. Navigate to Integration > Credentials
3. Create a new OAuth application
4. Note the Client ID and Client Secret
5. Set the redirect URI to: `https://global.consent.azure-apim.net/redirect`
6. Assign the required scopes: `RISK`, `RISK_READ`, `INCIDENT`, `INCIDENT_CREATE`, `INCIDENT_READ`, `INTEGRATION`, `ORGANIZATION`, `USER`

### 2. Deploy the connector

Import the connector into your Power Platform environment using PAC CLI or the maker portal. When creating a connection, provide the Client ID and Client Secret from your OneTrust OAuth application.

### 3. Add to Copilot Studio

1. Open your agent in Copilot Studio
2. Go to Actions > Add action
3. Search for "OneTrust" and add it

## Host configuration

The connector defaults to `app.onetrust.com`. If your OneTrust instance uses a different hostname (for example, `app-eu.onetrust.com` or `app-de.onetrust.com`), update the `host` field in `apiDefinition.swagger.json` and the `BASE_URL` constant in `script.csx`.

## Required scopes

- `RISK` — Risk management
- `RISK_READ` — Read risk data
- `INCIDENT` — Incident management
- `INCIDENT_CREATE` — Incident creation
- `INCIDENT_READ` — Read incident data
- `INTEGRATION` — Integration scope for risk upsert and update
- `ORGANIZATION` — Organization data access
- `USER` — User data access

## Application Insights (optional)

Set the `APP_INSIGHTS_CONNECTION_STRING` constant in `script.csx` to enable telemetry. Events tracked:

| Event | Description |
|-------|-------------|
| `RequestReceived` | Incoming request with operation ID and path |
| `RequestCompleted` | Request duration and operation ID |
| `RequestError` | Error details with correlation ID |
| `MCPMethodInvoked` | MCP JSON-RPC method name |
| `MCPError` | MCP protocol errors |
| `ToolCallStarted` | Tool execution begin |
| `ToolCallCompleted` | Successful tool execution |
| `ToolCallFailed` | Tool execution errors |
| `PassthroughCompleted` | Direct REST call status |

## Files

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | OpenAPI definition with REST endpoints and MCP operation |
| `apiProperties.json` | Connector properties with OAuth config and `routeRequestToCode` |
| `script.csx` | MCP server with 14 tools + REST passthrough |
| `readme.md` | Setup guide and operation reference |

## Resources

- Connector repo: [SharingIsCaring/OneTrust](https://github.com/troystaylor/SharingIsCaring/tree/main/OneTrust)
- OneTrust developer docs: [developer.onetrust.com](https://developer.onetrust.com/)
- Power MCP Template: [Power MCP Template v2](https://troystaylor.com/power%20platform/custom%20connectors/2026-02-18-power-mcp-template-v2.html)
