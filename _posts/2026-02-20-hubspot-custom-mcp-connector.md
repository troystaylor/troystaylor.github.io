---
layout: post
title: "HubSpot Custom MCP connector for Power Platform"
date: 2026-02-20 09:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [HubSpot, MCP, Custom Connectors, Power Platform, Copilot Studio, CRM, OAuth, Sales]
description: "Power Platform custom connector for HubSpot CRM with 36 MCP tools covering companies, deals, emails, sequences, tasks, and custom objects."
---

HubSpot has a [remote MCP server](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/integrate-with-the-remote-hubspot-mcp-server) in beta. It connects AI assistants to your CRM data through OAuth 2.1 with PKCE. The problem: Power Platform custom connectors don't support OAuth 2.1 with PKCE. The authorization code flow works, but the PKCE challenge/verifier exchange that HubSpot's MCP server requires isn't available in the connector security. So instead of waiting for that support, this connector calls the HubSpot APIs directly. Standard OAuth 2.0 authorization code flow, no PKCE dependency, and full CRUD across the CRM objects you actually need—not just the read-only access that HubSpot's remote MCP server currently provides. Yeah, that's a strike against the HubSpot-hosted MCP, too.

You can find the complete code in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/HubSpot%20Custom%20MCP).

The result is 36 MCP tools that a Copilot Studio agent discovers automatically. Create companies, enroll contacts in sequences, log emails, manage deals through pipeline stages, and work with custom objects—all through natural language.

## Why not the HubSpot-hosted MCP server?

Two reasons:

1. **OAuth 2.1 with PKCE**: HubSpot's remote MCP server at `https://mcp.hubspot.com` requires PKCE for authentication. Power Platform custom connectors support OAuth 2.0 authorization code flow but don't handle the PKCE code challenge and verifier exchange.
2. **Read-only access**: The HubSpot MCP server currently supports read-only access to CRM objects. This connector provides full CRUD—create, read, update, and delete—for companies, deals, emails, tasks, and custom objects, plus sequence enrollment.

## What's included

### Companies (6 tools)

| Tool | Description |
|------|-------------|
| `list_companies` | List companies with pagination and property selection |
| `get_company` | Get a single company by ID |
| `create_company` | Create a company with properties like name, domain, industry |
| `update_company` | Update company properties |
| `delete_company` | Delete a company (moves to recycling bin) |
| `search_companies` | Search companies with filters, sorting, and query text |

### Sales reps / owners (2 tools)

| Tool | Description |
|------|-------------|
| `list_owners` | List all owners (sales reps) with optional email filter |
| `get_owner` | Get a single owner by ID |

### Emails (6 tools)

| Tool | Description |
|------|-------------|
| `list_emails` | List email engagements |
| `get_email` | Get a single email engagement by ID |
| `create_email` | Log a new email with subject, body, and direction |
| `update_email` | Update email engagement properties |
| `delete_email` | Delete an email engagement |
| `search_emails` | Search emails with filters |

### Sequences (3 tools)

| Tool | Description |
|------|-------------|
| `list_sequences` | List available sales sequences |
| `get_sequence` | Get sequence details by ID |
| `enroll_in_sequence` | Enroll a contact in a sequence |

### Tasks / reminders (6 tools)

| Tool | Description |
|------|-------------|
| `list_tasks` | List tasks (reminders/to-dos) |
| `get_task` | Get a single task by ID |
| `create_task` | Create a task with subject, body, status, priority, and owner |
| `update_task` | Update task properties |
| `delete_task` | Delete a task |
| `search_tasks` | Search tasks with filters |

### Deals / contract lifecycles (6 tools)

| Tool | Description |
|------|-------------|
| `list_deals` | List deals with pipeline stage tracking |
| `get_deal` | Get a single deal by ID |
| `create_deal` | Create a deal with name, stage, pipeline, amount, close date |
| `update_deal` | Update deal properties (move through pipeline stages) |
| `delete_deal` | Delete a deal |
| `search_deals` | Search deals with filters |

### Custom objects (8 tools)

| Tool | Description |
|------|-------------|
| `list_custom_object_schemas` | List all custom object schemas defined in HubSpot |
| `get_custom_object_schema` | Get full schema definition for a custom object type |
| `list_custom_objects` | List records of any custom object type |
| `get_custom_object` | Get a single custom object record by ID |
| `create_custom_object` | Create a new custom object record |
| `update_custom_object` | Update a custom object record |
| `delete_custom_object` | Delete a custom object record |
| `search_custom_objects` | Search custom object records with filters |

## Search operators

All search tools support these filter operators:

- `EQ` — Equal to
- `NEQ` — Not equal to
- `LT` / `LTE` — Less than / less than or equal
- `GT` / `GTE` — Greater than / greater than or equal
- `CONTAINS_TOKEN` — Contains token
- `NOT_CONTAINS_TOKEN` — Does not contain token

## Key properties by object

**Companies**: `name`, `domain`, `industry`, `phone`, `city`, `state`, `country`, `numberofemployees`, `annualrevenue`, `hubspot_owner_id`

**Emails**: `hs_email_subject`, `hs_email_text`, `hs_email_direction` (EMAIL_SENT / EMAIL_RECEIVED), `hs_timestamp`, `hs_email_status`

**Tasks**: `hs_task_subject`, `hs_task_body`, `hs_task_status` (NOT_STARTED / IN_PROGRESS / COMPLETED / DEFERRED), `hs_task_priority` (LOW / MEDIUM / HIGH), `hs_timestamp`, `hubspot_owner_id`

**Deals**: `dealname`, `dealstage`, `pipeline`, `amount`, `closedate`, `hubspot_owner_id`, `description`

## Setup

### 1. Create a HubSpot OAuth app

**Option A — HubSpot CLI:**

The `hubspot-app/` subfolder contains a pre-configured HubSpot project with all scopes and the redirect URL set up. Install the CLI, authenticate, and upload:

```bash
npm install -g @hubspot/cli
cd hubspot-app
hs auth
hs project upload
```

After uploading, go to HubSpot Settings > Integrations > Private Apps > HubSpot Custom MCP to copy the Client ID and Client Secret.

> **Note:** HubSpot CLI v8 uses the Ink library for terminal rendering and doesn't produce output in the VS Code integrated terminal. Run these commands in a standalone PowerShell or Windows Terminal window.

**Option B — Developer portal:**

1. Go to app.hubspot.com > Settings > Account Setup > Integrations > Private Apps
2. Create a new app and select the required scopes
3. Under Auth > Redirect URLs, add your connector's redirect URL (from step 5)
4. Copy the Client ID and Client Secret

### 2. Update the connector files

In `apiProperties.json`, replace `[[REPLACE_WITH_HUBSPOT_CLIENT_ID]]` with your app's Client ID.

### 3. Deploy the connector

```bash
pac connector create \
  --api-definition-file apiDefinition.swagger.json \
  --api-properties-file apiProperties.json \
  --script-file script.csx \
  --environment <your-environment-id>
```

> `pac connector create` doesn't support a `--secret` flag. Set the client secret separately (see step 4).

### 4. Set the OAuth client secret

**Option A — Power Platform portal:**

1. Go to make.powerapps.com > Custom connectors
2. Edit your connector > Security tab
3. Paste the Client Secret and click Update connector

**Option B — paconn CLI:**

```bash
pip install paconn
paconn login
paconn update -e <environment-id> -c <connector-api-id> \
  --api-def apiDefinition.swagger.json \
  --api-prop apiProperties.json \
  --script script.csx \
  --secret "<client-secret>"
```

> **Important:** `paconn` uses a different connector ID format than `pac`. The `pac` connector ID (a GUID) won't work with `paconn`. Find the correct ID in the Power Platform portal URL after `customConnectorId=`.

### 5. Configure the redirect URL in HubSpot

After deploying the connector, copy the per-connector redirect URL from the connector's Security tab:

```
https://global.consent.azure-apim.net/redirect/<connector-api-id>
```

Add this URL to your HubSpot OAuth app's Redirect URLs list.

### 6. Create a connection

1. In Power Platform, go to Connections > New connection
2. Select HubSpot Custom MCP
3. Enter your Client ID and Client Secret when prompted
4. Sign in with your HubSpot account to authorize

### 7. Add to Copilot Studio

1. Open your agent in Copilot Studio
2. Go to Actions > Add action
3. Search for "HubSpot Custom MCP" and add it

## Required scopes

- `crm.objects.companies.read` / `crm.objects.companies.write`
- `crm.objects.owners.read`
- `crm.objects.deals.read` / `crm.objects.deals.write`
- `sales-email-read`
- `crm.objects.contacts.read`
- `crm.schemas.custom.read`
- `crm.objects.custom.read` / `crm.objects.custom.write`
- `automation`

## Application Insights (optional)

Set the `APP_INSIGHTS_CONNECTION_STRING` constant in `script.csx` to enable telemetry. Events tracked:

- `McpRequestReceived` — every incoming MCP request
- `McpRequestCompleted` — successful completions with duration
- `McpRequestError` — unhandled errors
- `ToolCallStarted` / `ToolCallFailed` — individual tool execution

## Files

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | OpenAPI definition with `x-ms-agentic-protocol: mcp-streamable-1.0` |
| `apiProperties.json` | Connector properties with OAuth config and `routeRequestToCode` |
| `script.csx` | MCP server with 36 tools |
| `readme.md` | Setup guide and tool reference |

## Resources

- HubSpot remote MCP server (beta): [developers.hubspot.com/.../integrate-with-the-remote-hubspot-mcp-server](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/integrate-with-the-remote-hubspot-mcp-server)
- HubSpot CRM API: [developers.hubspot.com/docs/api-reference/crm](https://developers.hubspot.com/docs/api-reference/crm)
- Power MCP Template: [Power MCP Template v2](https://troystaylor.com/power%20platform/custom%20connectors/2026-02-18-power-mcp-template-v2.html)
