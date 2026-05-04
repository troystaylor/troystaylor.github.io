---
layout: post
title: "Azure Resource Graph MCP connector for Copilot Studio"
date: 2026-05-04 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Copilot Studio, MCP, Azure Resource Graph, KQL, Power Platform, Governance, Azure]
description: "Query Azure resources at scale from Copilot Studio and Power Automate using a dual-mode MCP connector for Azure Resource Graph with 21 MCP tools and 8 REST operations."
---

Azure Resource Graph lets you query resources across subscriptions using KQL, but there's no built-in way to bring that capability into Copilot Studio or Power Automate. Standard Azure Management connectors cover individual resource operations—they don't give you cross-subscription inventory, policy compliance, or change tracking in a single query.

I built this custom MCP connector to expose the full Azure Resource Graph API as both MCP tools for Copilot Studio agents and REST operations for Power Automate and Power Apps. Your agents can query resources, check policy compliance, track changes, manage saved queries, and summarize infrastructure—all scoped to the authenticated user's permissions.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Azure%20Resource%20Graph)

## What this connector does

The connector provides 21 MCP tools organized into six categories, plus 8 REST operations for traditional flows.

### Core query tools

| Tool | Purpose |
|------|---------|
| `query_resources` | Execute arbitrary KQL queries with subscription/management group scoping and pagination |
| `list_tables` | List all ~40 Resource Graph tables with descriptions |
| `list_resource_types` | List distinct resource types, optionally filtered by prefix |

### Infrastructure discovery tools

| Tool | Purpose |
|------|---------|
| `list_subscriptions` | List accessible Azure subscriptions |
| `list_resource_groups` | List resource groups, optionally scoped by subscription |
| `list_management_groups` | List management groups |
| `get_resource_by_id` | Look up a resource by its full ARM resource ID |

### Change tracking tools

| Tool | Purpose |
|------|---------|
| `query_resource_changes` | Query resource config changes (last 14 days) |

### Governance tools

| Tool | Purpose |
|------|---------|
| `query_policy_compliance` | Query Azure Policy compliance state |
| `query_advisor_recommendations` | Query Advisor recommendations by category |
| `query_security_assessments` | Query Defender for Cloud security assessments |
| `query_health_status` | Query resource health and availability |
| `query_service_health` | Query active service health events |
| `query_role_assignments` | Query role assignments (RBAC) |

### Convenience aggregation tools

| Tool | Purpose |
|------|---------|
| `summarize_resources` | Summarize resources by type, location, subscription, or resource group |
| `count_resources` | Count resources with optional filters |

### Saved query tools

| Tool | Purpose |
|------|---------|
| `list_saved_queries` | List saved Resource Graph queries |
| `get_saved_query` | Get a saved query by name |
| `create_saved_query` | Create or update a saved query |
| `delete_saved_query` | Delete a saved query |
| `run_saved_query` | Get and execute a saved query in one step |

### REST operations (Power Automate and Power Apps)

| Operation | Method | Purpose |
|-----------|--------|---------|
| Query Resources | POST | Execute a KQL query against Azure Resource Graph |
| List Operations | GET | List available Resource Graph API operations |
| List Saved Queries by Subscription | GET | List saved queries in a subscription |
| List Saved Queries | GET | List saved queries in a resource group |
| Get Saved Query | GET | Get a saved query by name |
| Create or Update Saved Query | PUT | Create or replace a saved query |
| Update Saved Query | PATCH | Partially update a saved query |
| Delete Saved Query | DELETE | Delete a saved query |

## Why an MCP connector for Resource Graph

The Azure Management connector in Power Platform covers individual resource CRUD. Azure Resource Graph is different—it's a query engine that indexes resources across your entire tenant. That distinction matters for agent scenarios:

- **Cross-subscription visibility.** A single KQL query returns resources across every subscription the user can access. No looping, no pagination logic in flows.
- **Governance in one place.** Policy compliance, Advisor recommendations, Defender assessments, resource health, and RBAC are all queryable from the same connector.
- **Change tracking.** The `resourcechanges` table captures config changes over the last 14 days. Agents can answer "what changed?" without scanning audit logs.
- **Saved queries.** Teams can share and reuse KQL queries through the saved query API. The `run_saved_query` tool fetches and executes a saved query in one step.
- **Natural language to KQL.** Copilot Studio's orchestrator maps prompts like "show me all non-compliant resources" to the right MCP tool and KQL query. The agent handles the translation.

## Architecture

```
Copilot Studio Agent / Power Automate
    │
    │  MCP tools (21) / REST operations (8)
    ▼
Power Platform Connector (script.csx)
    │
    │  OAuth 2.0 (user_impersonation)
    ▼
management.azure.com
/providers/Microsoft.ResourceGraph/resources
```

The connector uses `script.csx` to transform MCP tool calls into Resource Graph API requests. Authentication flows through Azure AD with the `user_impersonation` scope, so agents only see resources the signed-in user has access to.

## Prerequisites

- An Azure subscription with resources to query
- An Entra ID (Azure AD) app registration with `https://management.azure.com/.default` scope
- Power Platform environment with custom connector support

## Setup

### 1. Create an app registration

1. Go to [Azure Portal > App Registrations](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)
2. Click **New registration**
3. Name: `Azure Resource Graph Connector`
4. Supported account types: **Accounts in any organizational directory**
5. Redirect URI: `https://global.consent.azure-apim.net/redirect`
6. After creation, note the **Application (client) ID**
7. Under **Certificates & secrets**, create a new client secret
8. Under **API permissions**, add:
   - `https://management.azure.com/user_impersonation` (delegated)
9. Grant admin consent

### 2. Deploy the connector

1. Install [Power Platform CLI](https://learn.microsoft.com/power-platform/developer/cli/introduction)
2. Create a deploy copy and replace the client ID:
   - Copy `apiProperties.json` to `apiProperties.deploy.json`
   - Replace `[[REPLACE_WITH_CLIENT_ID]]` with your app registration client ID
3. Deploy:

```powershell
pac connector create `
  --api-definition-file apiDefinition.swagger.json `
  --api-properties-file apiProperties.deploy.json `
  --script-file script.csx
```

### 3. Create a connection

1. In Power Automate or Copilot Studio, add the **Azure Resource Graph** connector
2. Sign in with your Azure AD credentials
3. The connection uses your identity to query resources—you'll only see resources you have read access to

## Example prompts

Try these in a Copilot Studio agent with the connector enabled:

- "How many virtual machines do we have across all subscriptions?"
- "Show me all non-compliant policy resources"
- "What resources changed in the last 24 hours?"
- "List all resources tagged as production"
- "Summarize our resources by location"
- "Are there any unhealthy resources right now?"
- "What Advisor recommendations do we have for cost?"
- "Show me all role assignments for the engineering subscription"

## Example KQL queries

For the REST operations in Power Automate, pass KQL directly to the Query Resources action.

### Count all virtual machines

```kql
Resources
| where type =~ 'microsoft.compute/virtualmachines'
| summarize count()
```

### List resources by location

```kql
Resources
| summarize count() by location
| order by count_ desc
```

### Find resources with a specific tag

```kql
Resources
| where tags['environment'] =~ 'production'
| project name, type, resourceGroup, location
```

### Non-compliant policy resources

```kql
policyresources
| where type == 'microsoft.policyinsights/policystates'
| where properties.complianceState == 'NonCompliant'
| summarize count() by tostring(properties.policyDefinitionName)
```

### Recent resource changes

```kql
resourcechanges
| where properties.changeAttributes.timestamp > ago(24h)
| project properties.targetResourceId, properties.changeType,
  properties.changeAttributes.timestamp
| order by properties_changeAttributes_timestamp desc
```

## Application Insights logging

The connector supports optional Application Insights telemetry. Edit `script.csx` and replace the placeholder instrumentation key:

```csharp
private const string APP_INSIGHTS_KEY = "[INSERT_YOUR_APP_INSIGHTS_INSTRUMENTATION_KEY]";
```

Replace with your Application Insights instrumentation key:

```csharp
private const string APP_INSIGHTS_KEY = "00000000-0000-0000-0000-000000000000";
```

If the key isn't configured, all logging is silently skipped.

## Files in this project

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | Swagger with MCP tools and REST operations |
| `apiProperties.json` | OAuth configuration with Azure AD identity provider |
| `script.csx` | C# script for MCP tool execution and Application Insights telemetry |
| `readme.md` | Setup and usage guidance |

## When to use this connector

Use this connector when you want Copilot Studio agents or Power Automate flows to query Azure infrastructure at scale. It's a good fit for:

- **Cloud governance teams** that need policy compliance and security assessment visibility in Copilot
- **Platform engineering teams** that want cross-subscription resource inventory without switching to the Azure portal
- **FinOps teams** that need resource counts, summaries, and Advisor cost recommendations surfaced in workflows
- **Incident responders** who want to check resource health and recent changes from a single agent

## Resources

- [Azure Resource Graph connector source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Azure%20Resource%20Graph)
- [Azure Resource Graph overview](https://learn.microsoft.com/azure/governance/resource-graph/overview)
- [Supported tables and resource types](https://learn.microsoft.com/azure/governance/resource-graph/reference/supported-tables-resources)
- [KQL query language reference](https://learn.microsoft.com/azure/governance/resource-graph/concepts/query-language)
- [Starter queries](https://learn.microsoft.com/azure/governance/resource-graph/samples/starter)
- [Advanced queries](https://learn.microsoft.com/azure/governance/resource-graph/samples/advanced)
- [Copilot Studio documentation](https://learn.microsoft.com/microsoft-copilot-studio/)
