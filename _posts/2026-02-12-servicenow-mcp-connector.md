---
layout: post
title: "ServiceNow MCP connector for Power Platform"
date: 2026-02-12 09:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [ServiceNow, MCP, Custom Connectors, Power Platform, Copilot Studio, ITSM, CMDB, Change Management, Service Catalog]
description: "Comprehensive Power Platform custom connector for ServiceNow with 93+ operations across 13 REST APIs, dynamic table schema, MCP tools for Copilot Studio, and Application Insights telemetry."
---

ServiceNow has a massive REST API surface. Table API, Attachment API, CMDB, Service Catalog, Change Management, Knowledge Management, Event Management, Performance Analytics, and more—each with its own endpoints, parameters, and quirks. This connector wraps 93+ operations across 13 ServiceNow APIs into a single Power Platform custom connector with dynamic table schema, MCP tools for Copilot Studio agents, and Application Insights telemetry.

You can find the complete code in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/ServiceNow%20MCP).

## What's included

### Table API (7 operations)

List, get, create, update (PATCH), replace (PUT), and delete records from any ServiceNow table. The connector includes **dynamic table schema**—when you select a table in Power Automate or Power Apps, the body fields auto-populate with the actual fields from that table by querying ServiceNow's `sys_dictionary`. System fields prefixed with `sys_` are excluded to reduce clutter.

### Attachment API (5 operations)

List, get metadata, download, upload, and delete file attachments on any record.

### Aggregate API (1 operation)

Run count, sum, avg, min, and max queries with grouping on any table. Useful for dashboards and reporting without pulling full record sets.

### Import Set API (3 operations)

Import single or multiple records with transform map execution, and check import/transform status. Supports async bulk imports.

### CMDB Instance API (7 operations)

List, get, create, update, and patch Configuration Items. Add and remove CI relationships for dependency mapping.

### Service Catalog API (25+ operations)

Full catalog lifecycle: browse catalogs and categories, list and get items, order now, add to cart, submit producer records, manage cart items, checkout, handle wishlists, check delegation rights, and get variable display values.

### Knowledge Management API (9 operations)

Search articles, get article details, record views, submit ratings, mark helpful/not helpful, flag for review, list categories, and list knowledge bases.

### Change Management API (14 operations)

Create normal, standard (from template), and emergency changes. List standard templates. Get risk assessments, calculate risk, check schedule conflicts, get approvals and tasks, and create change tasks.

### Additional APIs

| API | Operations | What it does |
|-----|-----------|-------------|
| Batch API | 1 | Execute multiple API calls in one request |
| Email Outbound API | 1 | Send outbound email |
| Performance Analytics API | 6 | Scorecards, indicators, indicator scores, breakdown sources |
| User Administration API | 4 | Identify/reconcile users, manage group membership |
| Event Management API | 8 | Push events, list/get/acknowledge/close/reopen alerts, add comments |

## Dynamic table schema

One of the most useful features. When you use CreateRecord, UpdateRecord, or ReplaceRecord in Power Automate:

1. Select a table (for example, `incident` or `change_request`).
2. The connector queries ServiceNow's `sys_dictionary` for that table's field definitions.
3. Body parameters show table-specific fields with proper labels and types.

No more guessing field names or checking ServiceNow documentation mid-flow.

## MCP tools for Copilot Studio

The connector exposes 18 MCP tools via JSON-RPC 2.0:

| Tool | Description |
|------|-------------|
| `list_records` | Query any ServiceNow table |
| `get_record` | Get record by sys_id |
| `create_record` | Create record in any table |
| `update_record` | Update record fields |
| `create_incident` | Quick incident creation |
| `search_knowledge` | Search KB articles |
| `list_changes` | List change requests |
| `create_normal_change` | Create change request |
| `create_event` | Push event to Event Management |
| `list_alerts` | List EM alerts |
| `acknowledge_alert` | Acknowledge alert |
| `close_alert` | Close alert |
| `list_cis` | Query CMDB |
| `list_catalog_items` | Browse catalog |
| `order_catalog_item` | Order from catalog |
| `send_email` | Send email |
| `get_table_stats` | Aggregate queries |
| `batch_requests` | Multiple API calls |

Add the connector as an action in Copilot Studio, and the agent discovers the tools automatically. Users can then interact with ServiceNow through natural conversation:

**User:** "Create a P2 incident for VPN connectivity issues affecting the Seattle office"
**Agent:** *Calls `create_incident` with the details*

**User:** "Search the knowledge base for password reset instructions"
**Agent:** *Calls `search_knowledge` and returns matching articles*

**User:** "Show me all open change requests assigned to the infrastructure team"
**Agent:** *Calls `list_changes` with the appropriate query filter*

## Setup

### ServiceNow prerequisites

- **ServiceNow Zurich** instance or later
- **OAuth plugins activated:** `com.snc.platform.security.oauth`, `com.glide.rest`, `com.glide.auth.scope`, `com.glide.rest.auth.scope`
- **System property** `glide.oauth.inbound.client.credential.grant_type.enabled` set to `true`
- If you get "Access to unscoped api is not allowed," set `glide.security.oauth_allow_unscoped_clients` to `true` in `sys_properties.list`

### Create OAuth application

1. Navigate to **System OAuth → Application Registry**.
2. Click **New** → **Create an OAuth API endpoint for external clients**.
3. Configure:
   - **Name:** Power Platform Connector
   - **Client ID:** (auto-generated—copy this)
   - **Client Secret:** Generate and copy
   - **Redirect URL:** `https://global.consent.azure-apim.net/redirect`
4. Save.

### Import the connector

1. Go to [Power Automate](https://make.powerautomate.com/) or [Power Apps](https://make.powerapps.com/) → Custom connectors.
2. Import from OpenAPI file: upload `apiDefinition.swagger.json`.
3. Create a connection using your ServiceNow instance name and OAuth credentials.

Or use PAC CLI:

```bash
pac connector create --api-definition apiDefinition.swagger.json --api-properties apiProperties.json
```

## Query syntax reference

ServiceNow uses encoded query syntax for filtering:

| Operator | Syntax | Example |
|----------|--------|---------|
| Equals | `field=value` | `active=true` |
| Not Equals | `field!=value` | `state!=7` |
| Contains | `fieldLIKEvalue` | `short_descriptionLIKEvpn` |
| Starts With | `fieldSTARTSWITHvalue` | `numberSTARTSWITHINC` |
| In List | `fieldINlist` | `stateIN1,2,3` |
| AND | `^` | `active=true^priority=1` |
| OR | `^OR` | `priority=1^ORpriority=2` |
| Order By | `^ORDERBY` | `^ORDERBYsys_created_on` |
| Order Desc | `^ORDERBYDESC` | `^ORDERBYDESCpriority` |

## Examples

### Create an incident

```json
{
  "short_description": "VPN connection issue",
  "description": "User unable to connect to VPN from home office",
  "urgency": "2",
  "impact": "2",
  "caller_id": "<user_sys_id>"
}
```

### Create a normal change request

```json
{
  "short_description": "Server patch deployment",
  "description": "Apply latest security patches to production servers",
  "justification": "Critical security vulnerabilities need to be addressed",
  "implementation_plan": "1. Backup servers\n2. Apply patches\n3. Reboot\n4. Verify services",
  "backout_plan": "Restore from backup if issues arise",
  "assignment_group": "<group_sys_id>",
  "start_date": "2026-02-15 02:00:00",
  "end_date": "2026-02-15 04:00:00"
}
```

### Batch multiple requests

```json
{
  "batch_request_id": "my-batch-001",
  "rest_requests": [
    { "id": "1", "method": "GET", "url": "/api/now/table/incident?sysparm_limit=5" },
    { "id": "2", "method": "GET", "url": "/api/now/table/sys_user?sysparm_limit=5" }
  ]
}
```

## Application Insights (optional)

Update the connection string in `script.csx`:

```csharp
private const string APP_INSIGHTS_CONNECTION_STRING = "InstrumentationKey=xxx;IngestionEndpoint=https://xxx.in.applicationinsights.azure.com/";
```

Events logged: `RequestReceived`, `RequestCompleted`, `RequestError`, `MCPRequest`, `MCPToolCall`, `MCPToolError`.

## Common tables

| Table | Description |
|-------|-------------|
| `incident` | Incident Management |
| `change_request` | Change Management |
| `problem` | Problem Management |
| `sc_request` | Service Catalog Requests |
| `sc_req_item` | Requested Items |
| `sys_user` | Users |
| `sys_user_group` | Groups |
| `cmdb_ci` | Configuration Items (base) |
| `cmdb_ci_server` | Servers |
| `kb_knowledge` | Knowledge Articles |

## Try it yourself

The complete connector code is available in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/ServiceNow%20MCP):

- [apiDefinition.swagger.json](https://github.com/troystaylor/SharingIsCaring/blob/main/ServiceNow%20MCP/apiDefinition.swagger.json) — OpenAPI specification
- [script.csx](https://github.com/troystaylor/SharingIsCaring/blob/main/ServiceNow%20MCP/script.csx) — Connector script with MCP and dynamic schema
- [apiProperties.json](https://github.com/troystaylor/SharingIsCaring/blob/main/ServiceNow%20MCP/apiProperties.json) — Connector metadata
- [readme.md](https://github.com/troystaylor/SharingIsCaring/blob/main/ServiceNow%20MCP/readme.md) — Full documentation

## Resources

- [ServiceNow REST API documentation](https://developer.servicenow.com/dev.do#!/reference/api/zurich/rest/)
- [ServiceNow OAuth setup guide](https://docs.servicenow.com/bundle/zurich-platform-security/page/administer/security/concept/oauth-application-registry.html)
- [Official Power Platform conenctor for ServiceNow](https://learn.microsoft.com/en-us/connectors/service-now/)
- [Application Insights telemetry for connectors](https://troystaylor.github.io/power%20platform/2026/01/07/power-platform-custom-connectors-application-insights.html)
