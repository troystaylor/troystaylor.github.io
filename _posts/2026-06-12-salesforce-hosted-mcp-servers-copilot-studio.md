---
layout: post
title: "Connect Copilot Studio to Salesforce Hosted MCP Servers"
date: 2026-06-12 09:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Salesforce, MCP, Copilot Studio, Custom Connectors, Power Platform, Hosted MCP Servers, SOQL, Data Cloud, Tableau]
description: "Salesforce showed how to connect Claude to their Hosted MCP Servers. Here's how to connect Copilot Studio using a Power Platform custom connector with SalesforceV2 as the identity provider."
---

Salesforce recently published a guide for [connecting Claude to Salesforce Hosted MCP Servers](https://developer.salesforce.com/blogs/2026/05/connect-claude-with-salesforce-hosted-mcp-servers). Claude isn't the only agent that can talk to these servers. Copilot Studio connects the same way, and the MCP connector pattern makes deployment repeatable across your entire Salesforce Hosted MCP server catalog.

This post covers connecting Copilot Studio to every standard Salesforce Hosted MCP Server — SObject All, SObject Reads, SObject Mutations, SObject Deletes, Data 360, and Tableau Next — plus custom servers built from Apex Actions and Flows. One connector pattern, six standard servers, and unlimited custom servers.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Salesforce%20Hosted%20MCP)

## What Salesforce Hosted MCP Servers provide

Salesforce hosts MCP servers inside your org that expose platform capabilities as MCP tools. The servers are pre-configured by Salesforce — you activate them in Setup, create an External Client App for OAuth, and point your MCP client at the server URL.

### Standard servers

| Server | API name | What it does |
|--------|----------|--------------|
| SObject All | `sobject-all` | Full CRUD, SOQL, SOSL, schema discovery, relationship traversal |
| SObject Reads | `sobject-reads` | Read-only queries and search — governance-safe |
| SObject Mutations | `sobject-mutations` | Create and update only, no delete |
| SObject Deletes | `sobject-deletes` | Delete operations only |
| Data 360 | `data-cloud-queries` | Data Cloud SQL queries against unified customer profiles |
| Tableau Next | `tableau-next` | Semantic models, KPIs, and analytics queries |

All servers enforce per-user authentication with field-level security, object permissions, and sharing rules.

### Custom servers

If the standard servers don't fit, build custom hosted MCP servers that expose:

- **Apex Actions** — `@InvocableMethod` annotated methods
- **Autolaunched Flows** — Lightning Flows exposed as MCP tools
- **Apex REST** — Custom REST endpoints
- **AuraEnabled** — `@AuraEnabled` annotated methods
- **Named Query API** — Parametrized SOQL queries
- **Flex prompt templates** — Prompt Builder templates exposed as MCP prompts

Custom servers give you granular control over what tools and prompts your agents can invoke.

## How the connection works

The Salesforce blog describes a three-step process: activate servers, create an External Client App, and configure the MCP client. The first two steps are identical for Copilot Studio. The third step — the MCP client configuration — is where the approaches diverge.

Claude uses CLI commands or JSON config files. Copilot Studio uses a Power Platform custom connector with `SalesforceV2` as the identity provider. The connector is a passthrough: it forwards MCP traffic directly to Salesforce's hosted MCP server. No `script.csx`, no middleware, no custom code.

```
Copilot Studio Agent
    │
    │  MCP Streamable HTTP 1.0
    ▼
Power Platform Connector (passthrough)
    │
    │  OAuth 2.0 + mcp_api scope
    ▼
Salesforce Hosted MCP Server
(api.salesforce.com/platform/mcp/v1/...)
```

## The scope difference: `api` vs `mcp_api`

This is the critical configuration detail. My earlier [Salesforce MCP connector](https://github.com/troystaylor/SharingIsCaring/tree/main/Salesforce%20MCP) uses the `api` scope because it calls Salesforce REST API endpoints directly through `script.csx`. Hosted MCP Servers require a different scope.

In the `apiProperties.json` for a hosted MCP server connector, the scopes must include:

```json
"scopes": [
  "mcp_api",
  "refresh_token"
]
```

Compare that to the original REST API connector:

```json
"scopes": [
  "api",
  "openid",
  "refresh_token"
]
```

The `api` scope grants access to Salesforce REST APIs. The `mcp_api` scope grants access to Salesforce Hosted MCP Servers. They're separate permission boundaries. If you use `api` when connecting to a hosted MCP server, the request fails with a 403.

The `openid` and `id` scopes are optional for hosted MCP servers. They're useful if your connector needs to identify the authenticated user, but the hosted MCP server doesn't require them for tool execution.

## Salesforce setup

### Activate hosted MCP servers

1. In Salesforce Setup, search for **MCP Servers**
2. Click the **Salesforce Servers** tab
3. Click on each server you want to expose, then click **Activate**
4. Copy the server's **API Name** (without the `platform.` prefix) and **Server URL**

Servers are disabled by default. You must explicitly activate each one.

### Create an External Client App

The Salesforce blog covers this step in detail. The key differences for a Power Platform connector:

1. In Setup, search for **External Client App Manager** and click **New External Client App**
2. Fill out Basic Information
3. Under **API (Enable OAuth Settings)**, check **Enable OAuth**
4. In **Callback URL**, enter: `https://global.consent.azure-apim.net/redirect`
5. In **OAuth Scopes**, add:
   - Access Salesforce hosted MCP servers (`mcp_api`)
   - Perform requests at any time (`refresh_token`)
6. Under **Security**:
   - Check **Issue JSON Web Token (JWT)-based access tokens for named users**
   - Check **Require Proof Key for Code Exchange (PKCE) extension for Supported Authorization Flows**
   - Uncheck **Require secret for Web Server Flow** and **Require secret for Refresh Token Flow**
7. Click **Create**
8. Navigate to **Settings** > **OAuth Settings** > **Consumer Key and Secret**. Copy both values.

The callback URL is the only configuration that differs from the Claude setup. Claude Desktop uses `https://claude.ai/api/mcp/auth_callback`. Claude Code uses `http://localhost:38000/callback`. Power Platform uses the global consent redirect.

The External Client App can take up to 30 minutes to become available after creation.

## Connector configuration

### Both files

You can find both connector files in the [Salesforce Hosted MCP folder](https://github.com/troystaylor/SharingIsCaring/tree/main/Salesforce%20Hosted%20MCP) of my SharingIsCaring repository:

- [apiProperties.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Salesforce%20Hosted%20MCP/apiProperties.json) — OAuth configuration with `SalesforceV2` identity provider
- [apiDefinition.swagger.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Salesforce%20Hosted%20MCP/apiDefinition.swagger.json) — Swagger with MCP passthrough operation

### apiProperties.json

Key differences from my [REST API connector's apiProperties.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Salesforce%20MCP/apiProperties.json):

- **Scopes** — `mcp_api` and `refresh_token` instead of `api`, `openid`, and `refresh_token`
- **No policies** — The Accept header for MCP Streamable HTTP is set via `produces` in the Swagger instead of a `setheader` policy
- **Capabilities** — Includes `actions` since the connector exposes an MCP operation

`SalesforceV2` as the identity provider gives you the standard Salesforce OAuth 2.0 authorization code flow through the Power Platform redirect URI. This isn't documented in the official identity provider list, but it works and handles token refresh correctly.

**Important:** `SalesforceV2` can only be set through the Power Platform CLI — the Copilot Studio connector UI doesn't expose it as an identity provider option (yet). You can't create this connector entirely from the UI.

### apiDefinition.swagger.json

The Swagger is a single-operation passthrough. The important pieces:

- **`basePath`** — `/platform/mcp/v1/platform/sobject-all` targets the SObject All server. Change this value to target a different server.
- **`path: "/"`** — The basePath already includes the server path, so the operation sits at the root.
- **`x-ms-agentic-protocol: "mcp-streamable-1.0"`** — Tells Copilot Studio this operation speaks MCP. Copilot Studio handles `tools/list`, `tools/call`, and response parsing automatically.
- **`securityDefinitions`** — Declares `mcp_api` as the OAuth scope. Update the `authorizationUrl` and `tokenUrl` if connecting to a sandbox (`test.salesforce.com` instead of `login.salesforce.com`).
- **No `parameters` or `schema`** — The connector doesn't define request/response shapes. MCP protocol framing is handled by Copilot Studio.

### Deploy

Because `SalesforceV2` isn't available in the Copilot Studio connector UI, deployment is a two-step process:

**Step 1: Add the connector through Copilot Studio** to generate the environment-specific redirect URI. In Copilot Studio, go to your agent's actions, add a new connector, and import the Swagger file. This registers the connector and creates the redirect URI you'll need for the Salesforce External Client App callback URL.

**Step 2: Update the connector with the CLI** to apply the `apiProperties.json` that sets `SalesforceV2` as the identity provider:

```powershell
pac connector update `
  --connector-id <CONNECTOR_ID> `
  --settings-file apiProperties.json `
  --api-definition apiDefinition.swagger.json
```

If you're creating the connector for the first time outside of Copilot Studio, use `pac connector create` instead:

```powershell
pac connector create `
  --settings-file apiProperties.json `
  --api-definition apiDefinition.swagger.json
```

After the CLI update, create a connection, sign in with your Salesforce credentials, and add the connector to a Copilot Studio agent. Tools are discovered automatically.

## Connecting to other standard servers

The connector pattern is identical for every Salesforce Hosted MCP Server. Change the `basePath` and redeploy.

| Server | basePath (production) |
|--------|----------------------|
| SObject All | `/platform/mcp/v1/platform/sobject-all` |
| SObject Reads | `/platform/mcp/v1/platform/sobject-reads` |
| SObject Mutations | `/platform/mcp/v1/platform/sobject-mutations` |
| SObject Deletes | `/platform/mcp/v1/platform/sobject-deletes` |
| Data 360 | `/platform/mcp/v1/platform/data-cloud-queries` |
| Tableau Next | `/platform/mcp/v1/platform/tableau-next` |

For sandbox and scratch orgs, replace `platform` in the path segment after `v1/` with `sandbox`:

```
/platform/mcp/v1/sandbox/platform/sobject-all
```

### Governance through server selection

The server variants enable governance at the connector level:

- Give sales teams the **SObject All** connector for full CRM access
- Give reporting agents the **SObject Reads** connector so they can query but never modify
- Give data entry agents the **SObject Mutations** connector so they can create and update but never delete
- Restrict delete operations to the **SObject Deletes** connector with tighter access controls

Each connector is a separate custom connector in Power Platform, so you can apply different DLP policies, environment access rules, and connection sharing to each one.

## Connecting to custom hosted MCP servers

Custom servers follow the same pattern with one difference: the basePath uses the custom server's API name instead of a standard server name.

For example, if you created a custom hosted MCP server named `coral-cloud-flows` that exposes a Cancel Booking flow (as shown in the Salesforce blog), the basePath would be:

```
/platform/mcp/v1/platform/coral-cloud-flows
```

Everything else — the `apiProperties.json`, the `SalesforceV2` identity provider, the `mcp_api` scope, the deployment command — stays the same.

Custom servers can expose:

- Invocable Apex methods as tools — great for complex business logic that doesn't fit a simple CRUD pattern
- Autolaunched flows as tools — expose existing automation as agent-callable tools without writing code
- Flex prompt templates as MCP prompts — your Prompt Builder templates become commands that Copilot Studio can invoke

## Example prompts

With the SObject All connector in a Copilot Studio agent:

- "Show me all open opportunities closing this quarter with amounts over $100K"
- "What fields are available on the Opportunity object?"
- "Find all contacts at Zava who are decision makers"
- "Create a new task assigned to me for the Zava account review"
- "Show me the cases related to account 001xx000003abcDEF"

With a Data 360 connector:

- "Run a SQL query against the unified contact profile to find customers in the Pacific Northwest"
- "What data streams are available in my Data Cloud instance?"

With a custom server connector exposing Flows:

- "Cancel all bookings for tomorrow morning's Surf Lesson experience"
- "Run the customer onboarding flow for the new Zava contract"

## When to use hosted MCP servers vs the REST API connector

| Approach | When to use it |
|----------|---------------|
| Hosted MCP Server connector | Copilot Studio agents that need Salesforce data and actions, governance through server variants, no custom code to maintain |
| [REST API connector](https://github.com/troystaylor/SharingIsCaring/tree/main/Salesforce%20MCP) (with `api` scope) | Power Automate flows that need typed operations, custom `script.csx` logic, Application Insights telemetry, dynamic sObject schema in the designer |
| [Client Credentials connector](https://github.com/troystaylor/SharingIsCaring/tree/main/Salesforce%20Client%20Credentials) | Unattended automation, service-to-service calls, scenarios where interactive login isn't viable |
| [Cowork plugin](https://github.com/troystaylor/SharingIsCaring/tree/main/Cowork%20Plugins/Salesforce) | Microsoft 365 Copilot users who need CRM data in Cowork with skill-based prompts |

The hosted MCP server approach has one significant advantage: Salesforce owns the tool definitions and execution logic. When Salesforce adds new capabilities to a server, your connector picks them up without any changes.

## Resources

- [Salesforce Hosted MCP connector source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Salesforce%20Hosted%20MCP)
- [Connect Claude with Salesforce Hosted MCP Servers](https://developer.salesforce.com/blogs/2026/05/connect-claude-with-salesforce-hosted-mcp-servers) — the Salesforce blog post that inspired this guide
- [Salesforce Hosted MCP Servers documentation](https://developer.salesforce.com/docs/platform/hosted-mcp-servers/overview)
- [Standard MCP Servers reference](https://developer.salesforce.com/docs/platform/hosted-mcp-servers/references/reference/servers-reference.html)
- [Create an External Client App](https://developer.salesforce.com/docs/platform/hosted-mcp-servers/guide/create-external-client-app.html)
- [Copilot Studio documentation](https://learn.microsoft.com/microsoft-copilot-studio/)
