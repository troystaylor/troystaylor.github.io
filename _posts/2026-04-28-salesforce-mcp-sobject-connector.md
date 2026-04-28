---
layout: post
title: "Salesforce MCP SObject connector for Copilot Studio"
date: 2026-04-28 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Copilot Studio, MCP, Salesforce, Power Platform, SOQL, SOSL, SObject]
description: "Connect Copilot Studio to Salesforce's hosted MCP server for full SObject CRUD, SOQL, SOSL, and schema discovery using SalesforceV2 as an identity provider in a custom connector."
---

Most Power Platform users connect to Salesforce through the official Salesforce connector, and Copilot Studio has its own pair of Copilot connectors for Salesforce knowledge. Those work well for standard use cases.

I built this custom connector to connect directly to Salesforce's `sobject-all` hosted MCP server. Your Copilot Studio agents get full SObject CRUD operations, SOQL queries, SOSL search, relationship traversal, and schema discovery. No `script.csx` runs in the connector—Salesforce handles all tool definitions and execution.

The key discovery that makes this work: `SalesforceV2` works as an identity provider in `apiProperties.json`. That's not officially documented, but it means you can use the Power Platform CLI to deploy the custom connector that authenticates against Salesforce's OAuth flow and won't break when a refresh token is needed.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Salesforce%20MCP%20SObject)

## Tools provided by Salesforce

The hosted MCP server exposes these tools automatically:

| Tool | Purpose |
|------|---------|
| `getObjectSchema` | Schema info optimized for LLM consumption. Call with no parameters for an index of all queryable objects; call with object name(s) for field-level details |
| `soqlQuery` | Execute SOQL queries with relationship queries, subqueries, filtering, sorting, and aggregation |
| `find` | Text search (SOSL) across multiple objects simultaneously with relevance-ranked results. Max 2,000 records |
| `getUserInfo` | Current user's identity, role, profile, manager, local time, timezone, and admin-configured preferences |
| `listRecentSobjectRecords` | Records of a specific type the user recently viewed or modified. Up to 2,000 records |
| `getRelatedRecords` | Child records via relationship traversal. Supports multi-level traversal (for example, Account to Contacts to Cases) |
| `createSobjectRecord` | Create a new record. Returns the new record's ID on success |
| `updateSobjectRecord` | Update an existing record by ID. Only include fields you want to change |
| `updateRelatedRecord` | Update a child record by navigating from a parent record through a relationship |

All operations respect the authenticated user's field-level security, object permissions, and sharing rules. No elevated access, no separate service account—just the current user's permissions.

## Why a custom MCP connector instead of the official one

The official Salesforce connector and the Copilot connectors map specific REST operations to Salesforce API endpoints. They cover common scenarios, but the tool surface is fixed by what the connector exposes.

This connector takes a different approach: it proxies MCP traffic directly to Salesforce's hosted MCP server using the `mcp-streamable-1.0` protocol. Salesforce defines the tools, not the connector.

That means:

- **More tools than the official connector.** SOQL, SOSL, schema discovery, relationship traversal, and full CRUD are all available as MCP tools that Copilot Studio discovers automatically.
- **No custom code to maintain.** Salesforce owns the tool definitions and execution logic. When they add new capabilities to the `sobject-all` server, your connector picks them up without changes.
- **Security stays with Salesforce.** Field-level security, sharing rules, and object permissions are enforced server-side, not in a connector script.
- **No schema drift.** The connector doesn't hardcode any SObject shapes or field names. The `getObjectSchema` tool returns live metadata.

## The SalesforceV2 identity provider discovery

Power Platform connectors use identity providers defined in `apiProperties.json` for OAuth flows. `SalesforceV2` isn't listed in the official documentation for custom connector identity providers, but it works. Setting `"identityProvider": "SalesforceV2"` in the connection parameters gives you the standard Salesforce OAuth 2.0 authorization code flow with the Power Platform redirect URI.

This is what makes the whole approach viable. Without it, you'd need to handle Salesforce OAuth manually or build a middleware proxy. With it, the connector authenticates just like any other Power Platform connector with OAuth.

## Architecture

```
Copilot Studio Agent
    │
    │  MCP Streamable HTTP 1.0
    ▼
Power Platform Connector (passthrough)
    │
    │  OAuth 2.0 + mcp_api scope
    ▼
api.salesforce.com
/platform/mcp/v1/platform/sobject-all
```

The connector has a single operation (`InvokeMCP`) marked with `x-ms-agentic-protocol: "mcp-streamable-1.0"`. Copilot Studio handles the MCP protocol framing, and Salesforce handles everything else.

## Prerequisites

- A Salesforce org (Production or Sandbox)
- Admin access to create an External Client App in Salesforce Setup
- Power Platform environment with Copilot Studio

## Salesforce setup

### Create an External Client App

1. In Salesforce Setup, search for **External Client App Manager** and click it
2. Click **New External Client App**
3. Fill out the Basic Information section
4. Expand **API (Enable OAuth Settings)** and check **Enable OAuth**
5. In Callback URL, enter: `https://global.consent.azure-apim.net/redirect`
6. In OAuth Scopes, add:
   - Access Salesforce hosted MCP servers (`mcp_api`)
   - Access the identity URL service (`id`)
   - Access unique user identities (`openid`)
   - Perform requests at any time (`refresh_token`)
7. Under Security, enable **Issue JSON Web Token (JWT)-based access tokens for named users**
8. Click **Create**
9. Click **Settings**, then **Consumer Key and Secret** under OAuth Settings. Copy both values for connector configuration.

The External Client App may take up to 30 minutes to become available worldwide after creation.

### Activate the MCP server

1. In Salesforce Setup, search for **MCP** or **Salesforce MCP Servers**
2. Find the **sobject-all** server and activate it
3. MCP servers are disabled by default and must be explicitly activated before any client can connect

## Connector setup

1. Replace `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET` in `apiProperties.json` with the values from your External Client App
2. Deploy the connector:

```powershell
pac connector create `
  --settings-file apiProperties.json `
  --api-definition apiDefinition.swagger.json
```

3. Create a new connection and sign in with your Salesforce credentials
4. Add the connector to a Copilot Studio agent—the MCP tools are discovered automatically

### Sandbox and scratch orgs

The connector defaults to `https://login.salesforce.com`. For sandbox orgs, update the Login URI to `https://test.salesforce.com` when creating the connection.

The hosted MCP server URL for sandbox/scratch orgs uses a different path: `/platform/mcp/v1/sandbox/platform/sobject-all`. Update the `basePath` in `apiDefinition.swagger.json` accordingly.

## Example prompts

Try these in a Copilot Studio agent with the connector enabled:

- "Show me all open opportunities closing this quarter"
- "Find contacts at Zava who have been involved in support cases"
- "What fields are available on the Opportunity object?"
- "Create a new lead for Jane Smith at Zava"
- "Update the stage on opportunity 006xx000001234 to Closed Won"
- "Show me the cases related to the last account I viewed"

## Related Salesforce MCP servers

Salesforce hosts multiple MCP servers for different use cases. Each one can be exposed through the same passthrough connector pattern:

| Connector | MCP Server | Scope |
|-----------|-----------|-------|
| Salesforce SObject (this one) | sobject-all | Full CRUD, queries, search |
| Salesforce SObject Reads | sobject-reads | Read-only access (governance-safe) |
| Salesforce SObject Mutations | sobject-mutations | Create/update only (no delete) |
| Salesforce Data 360 | data-cloud-queries | Data Cloud SQL queries |
| Salesforce Tableau Next | tableau-next | Analytics, dashboards, semantic models |
| Salesforce Custom MCP | Admin-configured | Flows, Apex Actions, API Catalog |

The read-only `sobject-reads` variant is worth considering for governance-sensitive scenarios where you want agents to query and report but not modify data.

## Files in this project

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | Swagger with MCP passthrough operation |
| `apiProperties.json` | OAuth configuration for Salesforce External Client App |
| `readme.md` | Setup and usage guidance |

No `script.csx` is needed because the connector is a pure passthrough.

## When to use this connector

Use this connector when you want Copilot Studio agents to work directly with Salesforce data using the full power of SOQL, SOSL, and SObject CRUD. It's a good fit for:

- Sales teams that need CRM data surfaced in Copilot without switching apps
- Cross-platform workflows where Power Automate orchestrates around Salesforce records
- Governance scenarios where Salesforce's built-in security model is the right enforcement layer
- Agent builders who want schema discovery so the orchestrator can reason about available objects and fields

## Resources

- [Salesforce MCP SObject source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Salesforce%20MCP%20SObject)
- [Salesforce Hosted MCP Servers overview](https://developer.salesforce.com/docs/platform/hosted-mcp-servers/overview)
- [SObject All server reference](https://developer.salesforce.com/docs/platform/hosted-mcp-servers/references/reference/sobject-all.html)
- [Create an External Client App](https://developer.salesforce.com/docs/platform/hosted-mcp-servers/guide/create-external-client-app.html)
- [Copilot Studio documentation](https://learn.microsoft.com/microsoft-copilot-studio/)
