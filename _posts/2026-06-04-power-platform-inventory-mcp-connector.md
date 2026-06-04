---
layout: post
title: "Power Platform inventory MCP connector for tenant-wide resource queries"
date: 2026-06-04 13:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Power Platform, MCP, Custom Connectors, Copilot Studio, Power Automate, Inventory, Admin, Governance]
description: "Dual-mode Power Platform custom connector that wraps the Power Platform inventory API as both an MCP server for Copilot Studio and 15 typed Power Automate operations covering resource counts, recent items, connector usage, and a RunQuery escape hatch."
---

Admins have been asking Power Platform for a tenant-wide inventory for years. The new Power Platform inventory API quietly answered that ask. It exposes every canvas app, model-driven app, cloud flow, agent flow, workflow agent flow, and Copilot Studio agent across every environment as a single queryable `PowerPlatformResources` table in Azure Resource Graph.

This MCP connector wraps that API as both an MCP server for Copilot Studio and 15 typed Power Automate operations, so makers and admins can ask "how many cloud flows do we have in production?" without writing KQL.

You can find the complete code in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Power%20Platform%20Inventory).

## What it does

The connector is dual-mode: a single `POST /mcp` endpoint for Copilot Studio agents, plus typed Power Automate operations with full schemas and dynamic dropdowns. Every operation maps one-to-one to a sample query from the [Microsoft Learn documentation](https://learn.microsoft.com/power-platform/admin/inventory-sample-queries), so end users get the same answers without authoring the KQL by hand.

All operations call the same endpoint:

```
POST https://api.powerplatform.com/resourcequery/resources/query?api-version=2024-10-01
```

## Counts and distribution

| Operation | MCP tool | KQL behind it |
|-----------|----------|---------------|
| `CountAllResources` | `inventory_count_all` | `PowerPlatformResources \| count` |
| `CountByType` | `inventory_count_by_type` | `summarize count() by type` |
| `CountByEnvironment` | `inventory_count_by_environment` | `summarize count() by environmentId` |
| `CountByRegion` | `inventory_count_by_region` | `summarize count() by location` |
| `TopOwners` | `inventory_top_owners` | `summarize count() by ownerId \| order by desc` |

These are the questions every admin gets first: how many resources do we have, of what kind, in which environments and regions, and who owns the most.

## Resource lookups

| Operation | MCP tool | What it returns |
|-----------|----------|-----------------|
| `FindResource` | `inventory_find_resource` | A single resource by ID (optionally scoped by type) |
| `RecentResources` | `inventory_recent_resources` | Items created in the past N hours (default 24) |
| `ListResourcesByType` | `inventory_list_resources_by_type` | Paged list of resources of a given type |
| `ListEnvironments` | `inventory_list_environments` | Every environment in the tenant |
| `ListEnvironmentGroups` | `inventory_list_environment_groups` | Every environment group |

`RecentResources` is the one to wire into a scheduled flow. Run it every morning, post the new canvas apps and cloud flows to a Teams channel, and you have a zero-cost CoE-style activity feed.

## Connector queries (preview)

| Operation | MCP tool | What it answers |
|-----------|----------|-----------------|
| `TopConnectors` | `inventory_top_connectors` | Most-used connectors by distinct resources |
| `ConnectorCountDistribution` | `inventory_connector_count_distribution` | Resources grouped by number of connectors used |
| `ResourcesUsingConnector` | `inventory_resources_using_connector` | Every resource using a given connector |
| `ConnectorUsageByEnvironment` | `inventory_connector_usage_by_environment` | Connector adoption per environment |

The third one — `ResourcesUsingConnector` — is the impact-analysis query you reach for when a connector is being deprecated, a publisher has a breach, or you're rolling out a new DLP policy. Drop in the connector ID and you get every canvas app, flow, and agent that depends on it, across every environment, in seconds.

Connector queries are still preview on the Microsoft side and only cover canvas apps, model-driven apps, cloud flows, agent flows, workflow agent flows, and Copilot Studio agents. Tabular data sources (SharePoint, Dataverse, SQL, Excel Online) currently report empty `operations` arrays.

## The escape hatch

| Operation | MCP tool | What it accepts |
|-----------|----------|-----------------|
| `RunQuery` | `inventory_run_query` | Raw `TableName` + `Clauses` + `Options` payload |

For anything the typed operations don't cover, `RunQuery` accepts a raw clause body using the documented clause syntax:

```
$type: where | project | take | orderby | distinct | count | summarize | extend | join
```

The 14 typed operations cover the common cases; `RunQuery` handles the long tail without forcing you to fork the connector.

## Example Copilot Studio prompts

With the MCP server attached as an action, an agent can answer admin questions directly:

**User:** "How many canvas apps do we have across the tenant?"
**Agent:** Calls `inventory_count_by_type`, filters the result to `Microsoft.PowerApps/apps`.

**User:** "Which environments use the SharePoint connector the most?"
**Agent:** Calls `inventory_connector_usage_by_environment` with the SharePoint connector ID.

**User:** "Show me every cloud flow created in the last 24 hours"
**Agent:** Calls `inventory_recent_resources` with `type = Microsoft.Flow/flows` and `hours = 24`.

The agent picks the typed operation when one fits and falls back to `inventory_run_query` when it doesn't — no hand-written KQL required.

## Setup

The connector needs an Entra ID app registration with delegated access to the Power Platform inventory API. The flow is the standard `pac connector` deploy, with a small twist: you grab the per-connector redirect URL after the first deploy and paste it back into the Entra app.

### 1. Create the Entra ID app registration

1. Create a Microsoft Entra ID app registration in your tenant.
2. Add `https://api.powerplatform.com/.default` as a delegated API permission and grant admin consent.

### 2. Wire the connector

1. Replace `[INSERT_YOUR_CLIENT_ID]` in `apiProperties.json` with the application (client) ID.
2. Optionally replace `[INSERT_YOUR_APP_INSIGHTS_CONNECTION_STRING]` in `script.csx` to enable telemetry.
3. Deploy with the Power Platform CLI:

   ```powershell
   pac connector create `
     --environment <ENVIRONMENT_ID> `
     --api-definition-file .\apiDefinition.swagger.json `
     --api-properties-file .\apiProperties.json `
     --script-file .\script.csx
   ```

   `pac connector create` prints the new connector ID — save it for redeploys.

### 3. Finish the OAuth wiring

1. Open the connector in the Power Platform maker portal → **Security** tab. Enter the client secret (the client ID is already baked in from step 2) and select **Update connector**.
2. Copy the per-connector redirect URL shown on the Security tab. It looks like `https://global.consent.azure-apim.net/redirect/<connector-internal-name>`.
3. In the Entra app registration → **Authentication → Web platform**, paste that URL as a redirect URI and save.

### 4. Create a connection

Sign in as a Power Platform administrator or Dynamics 365 administrator — inventory access rules require one of those roles.

### Redeploy

For subsequent deploys, swap `create` for `update`:

```powershell
pac connector update `
  --connector-id <CONNECTOR_ID> `
  --environment <ENVIRONMENT_ID> `
  --api-definition-file .\apiDefinition.swagger.json `
  --api-properties-file .\apiProperties.json `
  --script-file .\script.csx
```

## MFA and conditional access

If your tenant requires MFA for Azure Resource Manager, the inventory API can fail with a token acquisition error. To work around it, include client ID `00b46ad5-e4ae-43ac-a878-281fc03d0839` and the Microsoft Azure Management resource in your conditional access policy. Otherwise queries fall through to a permission error that doesn't make the cause obvious.

## Why a custom connector instead of direct API calls

The inventory API itself is just an HTTP endpoint. So why wrap it?

- **Typed operations.** Every sample query becomes a Power Automate action with named parameters and a typed response. No KQL in the flow designer.
- **MCP surface.** The same OpenAPI definition exposes a `POST /mcp` endpoint for Copilot Studio agents. Add it as an action and the agent discovers all 15 tools automatically.
- **One OAuth connection.** The Entra app registration covers both surfaces. Permissions follow the user, so the connector inherits the caller's admin scope.
- **Cross-environment by default.** The API is tenant-scoped, so a single connection answers questions across every environment in your tenant without per-environment configuration.

## Try it yourself

The complete connector code is in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Power%20Platform%20Inventory):

- [apiDefinition.swagger.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Power%20Platform%20Inventory/apiDefinition.swagger.json) — OpenAPI specification
- [apiProperties.json](https://github.com/troystaylor/SharingIsCaring/blob/main/Power%20Platform%20Inventory/apiProperties.json) — Connector metadata
- [script.csx](https://github.com/troystaylor/SharingIsCaring/blob/main/Power%20Platform%20Inventory/script.csx) — Connector script with MCP tools and optional telemetry
- [readme.md](https://github.com/troystaylor/SharingIsCaring/blob/main/Power%20Platform%20Inventory/readme.md) — Full documentation

## Resources

- [Power Platform inventory overview](https://learn.microsoft.com/power-platform/admin/power-platform-inventory)
- [Power Platform inventory API](https://learn.microsoft.com/power-platform/admin/inventory-api)
- [Power Platform inventory schema reference](https://learn.microsoft.com/power-platform/admin/inventory-schema)
- [Power Platform inventory sample queries](https://learn.microsoft.com/power-platform/admin/inventory-sample-queries)
- [Application Insights telemetry for connectors](https://troystaylor.com/power%20platform/2026-01-07-power-platform-custom-connectors-application-insights.html)
- [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring)
