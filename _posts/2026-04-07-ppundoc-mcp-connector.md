---
layout: post
title: "PP:UNDOC MCP connector for Power Platform"
date: 2026-04-08 15:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Power Platform, Undocumented APIs, MCP, Copilot Studio, Custom Connectors, Administration, Governance, Licensing]
description: "Power Platform custom connector wrapping 119 undocumented API endpoints across 9 collections with 34 MCP tools for admin agents—covering BAP, Flow, Dataverse, Power Apps, licensing, DLP, analytics, and tenant configuration."
---

David Wyatt has extensively watched network traffic from the Power Platform Admin Center, the maker portal, and the Flow portal. He catalogued every undocumented endpoint he found and published them at [ppundoc.com](https://ppundoc.com/) with Postman collections on [GitHub](https://github.com/wyattdave/Power-Platform/tree/main/Power%20Platform%20APIs).

My MCP connector wraps 119 of those endpoints across 9 collections into a single custom connector with 34 MCP tools for Copilot Studio admin agents. Tenant settings, environment management, flow administration, Dataverse operations, DLP policies, licensing, analytics, and more—the endpoints that power the admin center UI, now available in your flows and agent conversations.

**These are undocumented APIs.** They were discovered from browser network traffic and may change or break without notice. Don't use them in production-critical scenarios without fallback handling.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/PPUNDOC)

## The 9 collections

| Collection | Endpoints | What it covers |
|-----------|----------|---------------|
| BAP (Business Application Platform) | 9 | Tenant info, tenant settings, environments, DLP policies, Copilot policies, D365 templates |
| Flow (Power Automate) | 24 | Admin flow listing, flow definitions, run history, sharing, enable/disable, error checking, batch operations |
| Dataverse | 50 | Entity management, organization settings, feature flags, solution components, record sharing, security roles, canvas apps, agents, custom connectors |
| Power Apps | 5 | SPN connections, connection sharing, connection listing |
| PP-Environment | 12 | Connector swagger validation, custom connectors, app inventory, connection management, security settings |
| PP-Tenant | 3 | Governance advisor, gateways, connection sharing audit |
| PP-Licensing | 9 | License reports, add-on allocations, tenant capacity, per-environment licensing, security insights |
| Admin Analytics | 5 | Canvas app inventory, desktop flows, cloud flows, Copilot Studio agents, app diagnostics |
| Admin | 1 | D365 app listing |

## MCP tools (34 tools)

### Discovery and inventory

| Tool | Description |
|------|-------------|
| `list_environments` | All environments with capacity and metadata |
| `who_am_i` | Current user identity |
| `find_user` | Find user by UPN email |
| `list_agents` | All Copilot Studio agents |
| `list_solutions` | All solutions |
| `list_custom_connectors` | All custom connectors |
| `list_gateways` | On-premises data gateways |
| `list_connections` | Connections in an environment |

### Governance and security

| Tool | Description |
|------|-------------|
| `get_tenant_settings` | All admin-level settings |
| `update_tenant_settings` | Toggle admin settings |
| `list_dlp_policies` | DLP policies |
| `list_unblockable_connectors` | DLP-exempt connectors |
| `check_role_permissions` | Security role audit |
| `security_insights` | Security analytics summary |
| `get_tenant_advisor` | Governance recommendations |

### Flow management

| Tool | Description |
|------|-------------|
| `list_flows_admin` | All flows across all makers |
| `get_flow_definition` | Full flow JSON |
| `get_flow_run_history` | Run history |
| `get_flow_owners` | Flow owners |
| `share_flow` | Share with user |
| `turn_on_flow` | Enable a flow |
| `turn_off_flow` | Disable a flow |
| `cancel_all_runs` | Abort running instances |
| `check_flow_errors` | Diagnose errors |

### Licensing and capacity

| Tool | Description |
|------|-------------|
| `get_licenses` | License assignments |
| `get_tenant_capacity` | Storage and capacity info |
| `licenses_by_environment` | Per-environment breakdown |
| `add_on_licenses` | Capacity packs, AI Builder credits |
| `request_license_report` | Generate reports |

### Analytics

| Tool | Description |
|------|-------------|
| `list_canvas_apps_analytics` | App inventory with usage |
| `list_desktop_flows` | RPA inventory |
| `list_cloud_flows_analytics` | Cloud flow usage |
| `app_diagnostics` | Per-app usage analytics |
| `list_copilot_agents_analytics` | Agent inventory with usage |

### How it works

```
Admin: "Which environments are using the most capacity?"

1. Orchestrator calls get_tenant_capacity({})

   → Returns storage breakdown: database, file, log
     across all environments

2. Orchestrator calls licenses_by_environment({})

   → Returns per-environment license allocations
     with usage percentages
```

```
Admin: "Show me all flows that are erroring
        in the Sales environment"

1. Orchestrator calls list_flows_admin({
     environment_id: "abc123..."
   })

   → Returns all flows with status

2. Orchestrator calls check_flow_errors({
     flow_id: "def456..."
   })

   → Returns error details and suggested fixes
```

```
Admin: "What DLP policies do we have
        and are there any unblockable connectors?"

1. Orchestrator calls list_dlp_policies({})
   → Returns all DLP policies with rules

2. Orchestrator calls list_unblockable_connectors({})
   → Returns connectors exempt from DLP enforcement
```

## API hosts

The connector routes to 10 different API hosts depending on the operation:

| Host | Collection |
|------|-----------|
| `api.bap.microsoft.com` | BAP |
| `api.flow.microsoft.com` | Flow |
| `{dataverseUrl}` | Dataverse |
| `api.powerapps.com` | Power Apps |
| `{envId}.environment.api.powerplatform.com` | PP-Environment |
| `{tenantId}.tenant.api.powerplatform.com` | PP-Tenant |
| `licensing.powerplatform.microsoft.com` | PP-Licensing |
| `na.adminanalytics.powerplatform.microsoft.com` | Admin Analytics |
| `api.admin.powerplatform.microsoft.com` | Admin |
| `api.powerplatform.com` | PP-Environment Management, MCP |

The script handles host routing automatically based on operation ID. Connection parameters (Dataverse URL, Tenant ID, Environment ID) populate the dynamic host templates.

## Use cases

**Admin agent for tenant governance**: Build a Copilot Studio agent that Power Platform admins talk to in natural language. "What are our DLP policies?" "Which environments have Copilot enabled?" "Show me the governance advisor recommendations." The agent calls the right MCP tools and summarizes the responses.

**Environment capacity monitoring**: Run a scheduled Power Automate flow that checks tenant capacity and per-environment licensing daily. Alert when storage exceeds thresholds or when AI Builder credits are running low.

**Flow administration at scale**: List all flows across all makers in an environment, check for errors, view run history, and enable or disable flows—all without opening the admin center. The `cancel_all_runs` operation handles runaway flows that are consuming resources.

**License audit and reporting**: Generate license reports, check add-on allocations, and get per-environment breakdowns. Pair with the security insights operation for a combined governance and licensing dashboard.

**Security role auditing**: Use `check_role_permissions` to audit what privileges a security role grants. Use `find_user` to look up specific accounts. Combine with DLP policy listing for a complete security posture review.

**Analytics inventory**: Get full inventory of canvas apps, cloud flows, desktop flows, and Copilot Studio agents with usage data. Identify orphaned resources, unused apps, and flows that haven't run in months.

## Prerequisites

1. Power Platform admin or Global admin role
2. A bearer token obtained from browser developer tools or an OAuth flow

### How to get a bearer token

1. Open [admin.powerplatform.microsoft.com](https://admin.powerplatform.microsoft.com/) or [make.powerapps.com](https://make.powerapps.com/)
2. Press F12 to open Developer Tools
3. Go to the **Network** tab
4. Perform any action in the UI
5. Select a request, go to **Headers**, and copy the `Authorization` header value
6. Remove the `Bearer ` prefix—paste just the token

Tokens expire after approximately 60 minutes. Refresh manually or automate via an OAuth flow.

## Connection parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| Dataverse URL | Your Dataverse environment hostname | `org123.crm.dynamics.com` |
| Tenant ID | Power Platform format tenant ID | `Default-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| Environment ID | Power Platform environment ID | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| Environment ID (PP format) | Environment ID without hyphens, with period | `Defaultxxxxxxxxxxxxxxxxxxxxxxxx.xx` |
| Bearer Token | Authorization token from dev tools or OAuth | (secure string) |

## Known limitations

- **Undocumented APIs** — may break without notice. Not supported by Microsoft. Use fallback handling.
- **Bearer token auth** — tokens expire (~60 minutes). Must be refreshed manually or via OAuth flow.
- **Admin Analytics** — requires Global Admin role. Region prefix (`na.`) may differ for non-US tenants.
- **BAP API** — limited SPN support. May require user-context token from browser.
- **PP-Environment API** — requires a special environment ID format (no hyphens, period before last 2 characters).
- **Per-user UPN usage data** — not available through any of these APIs. Use the Power Platform Admin Center UI or Center of Excellence Starter Kit.

## Files

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | OpenAPI 2.0 definition with MCP endpoint and 119 REST operations |
| `apiProperties.json` | Bearer token auth config, dynamic host URL policies, and script operation bindings |
| `script.csx` | C# script handling MCP protocol, host routing across 10 API hosts, and Application Insights telemetry |
| `readme.md` | Setup and usage documentation |

## Resources

- [ppundoc.com](https://ppundoc.com/) — endpoint catalogue by David Wyatt
- [David Wyatt's Postman collections](https://github.com/wyattdave/Power-Platform/tree/main/Power%20Platform%20APIs)
- [David Wyatt on X](https://x.com/WyattDave)
