---
layout: post
title: "Power Platform Admin MCP connector for Copilot Studio"
date: 2026-05-13 14:00:00 -0500
categories: [Power Platform, Custom Connectors, MCP]
tags: [MCP, Copilot Studio, Power Platform Admin, Custom Connectors, Governance, PPAC]
---

Administering Power Platform environments means jumping between the admin center, PowerShell modules, and the Power Platform Admin API. Each environment has its own settings, Copilot governance configuration, connectors, and apps to track. When you're responsible for dozens of environments, checking whether a single setting is consistent across all of them turns into a repetitive manual exercise.

With the [CoE Starter Kit transitioning to the Power Platform admin center](https://learn.microsoft.com/power-platform/guidance/coe/starter-kit) and no longer receiving feature updates, organizations need new approaches to platform governance. The admin center covers inventory, usage, monitoring, and actions through its UI—but it doesn't expose those capabilities to agents. This connector fills that gap.

This connector wraps 12 Power Platform Admin API operations as MCP tools, letting a Copilot Studio agent handle cross-environment administration from a single conversation.

## Architecture

```
Copilot Studio Agent
        |  (MCP / JSON-RPC 2.0)
        v
Power Platform Admin Connector
        |  (OAuth2 delegated)
        v
api.powerplatform.com
Power Platform Admin API
```

All logic runs in the connector's `script.csx`. No external backend required. The connector forwards the signed-in user's OAuth token to the Power Platform Admin API, so access follows existing admin role assignments.

This is the fourth connector in the Dataverse family:

| Connector | Target API | Purpose |
|-----------|-----------|---------|
| **Power Platform Admin** (this) | `api.powerplatform.com` | Cross-environment platform administration |
| Dataverse Power Agent | `org.crm.dynamics.com` | Data operations (CRUD, bulk, relationships) |
| Dataverse Power Orchestration Tools | `org.crm.dynamics.com` | Dynamic tool discovery with orchestration |
| Dataverse Custom API | `org.crm.dynamics.com` | Custom API lifecycle management |

## The 12 tools

### Environment management

| Tool | Description |
|------|-------------|
| `admin_list_environments` | List all environments with capacity metrics, types, states, and Dataverse URLs |
| `admin_get_environment` | Full details of a specific environment including runtime endpoints and protection status |
| `admin_get_settings` | Get PPAC management settings (SAS IP rules, audit logging, etc.) |
| `admin_update_setting` | Update management settings on an environment |
| `admin_compare_settings` | Compare a setting value across all environments |

### Governance and security

| Tool | Description |
|------|-------------|
| `admin_get_copilot_governance` | Get Copilot governance features and settings (tenant or environment scope) |
| `admin_update_copilot_governance` | Update Copilot governance settings |
| `admin_get_security_recommendations` | Get security recommendations from Power Platform Advisor |
| `admin_get_cross_tenant_connections` | Cross-tenant connection reports for compliance auditing |

### Resource inventory

| Tool | Description |
|------|-------------|
| `admin_list_connectors` | List connectors in an environment (certified, custom, virtual, MCP) |
| `admin_list_apps` | List Power Apps in an environment with owner and sharing status |

### Application lifecycle

| Tool | Description |
|------|-------------|
| `admin_install_package` | Install a Microsoft application package in an environment |

## How each tool works

### List and inspect environments

The `admin_list_environments` tool returns every environment the user can administer—name, type (Production, Sandbox, Developer, Trial, Default), management state, Azure region, Dataverse URL, update cadence, and capacity metrics broken down by Database, File, and Log in MB.

```
"List all my Power Platform environments"
```

Use `admin_get_environment` for full details on a specific environment including runtime endpoints, protection status, retention configuration, and virtual network settings:

```
"Show me the full details of my production environment"
```

### Read and update PPAC settings

The `admin_get_settings` tool returns management settings for an environment—toggles like `EnableIpBasedStorageAccessSignatureRule`, `LoggingEnabledForIpBasedStorageAccessSignature`, and other PPAC controls. Use the optional `$select` parameter to filter specific settings:

```
"What are the PPAC settings on my production environment?"
```

The `admin_update_setting` tool updates one or more settings. The tool description warns the agent this is a destructive operation, prompting user confirmation before execution:

```csharp
["description"] = "Update one or more PPAC management settings on an " +
    "environment. ... This is a destructive operation — confirm with the " +
    "user before executing."
```

```
"Enable SAS IP restrictions on environment abc-123"
```

### Compare settings across environments

The `admin_compare_settings` tool is the most useful environment management tool. It takes a setting name, iterates through every environment, and returns a comparison table showing the value in each one:

```
"Compare EnableIpBasedStorageAccessSignatureRule across all environments"
```

The implementation lists all environments first, then queries the setting for each one individually, handling errors per environment so a single failure doesn't break the full comparison:

```csharp
foreach (var env in environments)
{
    try
    {
        var settingsResponse = await CallAdminApi(
            HttpMethod.Get,
            $"/environmentmanagement/environments/{envId}/settings" +
            $"?api-version={SETTINGS_API_VERSION}" +
            $"&$select={Uri.EscapeDataString(settingName)}"
        ).ConfigureAwait(false);

        comparison.Add(new JObject
        {
            ["environmentId"] = envId,
            ["environmentName"] = envName,
            ["settingName"] = settingName,
            ["value"] = settingsData[settingName],
            ["status"] = "retrieved"
        });
    }
    catch (Exception ex)
    {
        comparison.Add(new JObject
        {
            ["environmentId"] = envId,
            ["environmentName"] = envName,
            ["settingName"] = settingName,
            ["value"] = null,
            ["status"] = $"error: {ex.Message}"
        });
    }
}
```

### Copilot governance

The `admin_get_copilot_governance` tool retrieves both Copilot governance settings and feature flags in a single call. Pass an environment ID for environment-scoped settings, or omit it for tenant-level:

```
"What Copilot governance settings are configured for my tenant?"
```

The tool fetches settings and features in sequence, catching errors on each so a partial result still returns:

```csharp
var settingsUrl = string.IsNullOrEmpty(envId)
    ? $"/copilotgovernance/settings?api-version={SETTINGS_API_VERSION}"
    : $"/copilotgovernance/environments/{envId}/settings" +
      $"?api-version={SETTINGS_API_VERSION}";
```

The `admin_update_copilot_governance` tool updates Copilot governance settings at the tenant or environment level. Like the settings update tool, it includes a destructive operation warning in the tool description.

### Security recommendations

The `admin_get_security_recommendations` tool pulls recommendations from Power Platform Advisor. It first tries the security recommendations endpoint and falls back to the analytics advisor endpoint if the first returns an error:

```
"Show me security recommendations for my environments"
```

### Cross-tenant connections

The `admin_get_cross_tenant_connections` tool returns connection reports that span tenant boundaries—useful for compliance teams identifying data flow risks:

```
"Are there any cross-tenant connections I should review?"
```

### Resource inventory

The `admin_list_connectors` tool lists connectors in an environment with type classification (certified, custom, virtual, MCP), publisher, and tier. The `admin_list_apps` tool lists Power Apps with owner and sharing status:

```
"What connectors are available in my dev environment?"
"List all Power Apps in my production environment"
```

### Application lifecycle

The `admin_install_package` tool initiates installation of a Microsoft application package in an environment. The operation is asynchronous—the tool returns an operation ID for tracking progress:

```
"Install the Customer Service package in my sandbox environment"
```

## Dual-mode design

The connector exposes both MCP and typed REST operations. Copilot Studio agents call the `/mcp` endpoint through JSON-RPC 2.0. Power Automate flows use the typed operations directly—`ListEnvironments`, `GetEnvironment`, `GetSettings`, `UpdateSettings`—with dynamic dropdowns for environment selection:

```json
"x-ms-dynamic-values": {
    "operationId": "GetEnvironmentDropdown",
    "value-path": "id",
    "value-title": "name"
}
```

The typed operations reuse the same handler functions as MCP tools, keeping logic in one place:

```csharp
private async Task<HttpResponseMessage> HandleTypedListEnvironments()
{
    var result = await HandleListEnvironments(new JObject())
        .ConfigureAwait(false);
    return CreateTypedResponse(result);
}
```

## Implementation details

### OAuth delegation

The connector authenticates against `https://api.powerplatform.com` using OAuth 2.0 with the `aad` identity provider. When a user creates a connection, they sign in with their admin account. The connector forwards that token on every API call:

```csharp
if (this.Context.Request.Headers.Authorization != null)
{
    request.Headers.Authorization =
        this.Context.Request.Headers.Authorization;
}
```

### API versioning

The connector uses two API versions for different endpoint families:

```csharp
private const string ENV_API_VERSION = "2024-10-01";
private const string SETTINGS_API_VERSION = "2022-03-01-preview";
```

Environment management endpoints use the newer `2024-10-01` version. Settings, governance, security, connectors, apps, and application lifecycle endpoints use `2022-03-01-preview`.

### Destructive operation safety

Tools that modify state (`admin_update_setting`, `admin_update_copilot_governance`, `admin_install_package`) include explicit "This is a destructive operation — confirm with the user before executing" in their descriptions. This signals MCP clients and agents to ask for user confirmation before calling these tools.

### Application Insights telemetry

Every MCP request and tool call logs to Application Insights. Drop in your connection string to enable:

```csharp
private const string APP_INSIGHTS_CONNECTION_STRING =
    "[INSERT_YOUR_APP_INSIGHTS_CONNECTION_STRING]";
```

Leave the placeholder to disable telemetry entirely.

## Why not the CoE Starter Kit

The [CoE Starter Kit](https://learn.microsoft.com/power-platform/guidance/coe/starter-kit) is no longer actively maintained. Its core scenarios—inventory, usage tracking, monitoring, and governance actions—have moved into the Power Platform admin center as built-in experiences.

Microsoft's transition guidance points to the admin center UI, the PAC CLI, the Power Platform Admin API, and the Power Platform for Admins V2 connector. This MCP connector takes a different approach: instead of building flows or scripts against those tools, you ask an agent a question and get a structured answer.

The CoE Starter Kit required deploying and maintaining a set of Power Apps, flows, and Dataverse tables. This connector is a single `script.csx` that calls the same Power Platform Admin API the admin center uses—no solution packages to install, no sync jobs to monitor, no Dataverse storage consumption.

| Capability | CoE Starter Kit | Admin center | This connector |
|-----------|----------------|--------------|----------------|
| Environment inventory | Sync job + Dataverse | Built-in UI | `admin_list_environments` |
| Settings management | Manual / PowerShell | Built-in UI | `admin_get_settings`, `admin_update_setting` |
| Cross-environment comparison | Custom reporting | Not available | `admin_compare_settings` |
| Copilot governance | Not available | Built-in UI | `admin_get_copilot_governance` |
| Security recommendations | Not available | Actions tab | `admin_get_security_recommendations` |
| Cross-tenant audit | Not available | Built-in UI | `admin_get_cross_tenant_connections` |
| Connector/app inventory | Sync job + Dataverse | Built-in UI | `admin_list_connectors`, `admin_list_apps` |
| Natural language queries | Not available | Not available | All 12 tools via MCP |

## Deploying the connector

### Prerequisites

- Entra ID app registration with `Power Platform API` permissions (see the [full permissions list](https://github.com/troystaylor/SharingIsCaring/tree/main/Power%20Platform%20Admin#prerequisites))
- Power Platform admin role (System Administrator, Power Platform Administrator, or Dynamics 365 Administrator)
- Copilot Studio license for MCP integration
- [PAC CLI](https://learn.microsoft.com/power-platform/developer/cli/introduction)

### App registration

1. Create an app registration in [Entra ID](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)
2. Add API permissions for `Power Platform API` (resource ID `8578e004-a5c6-46e7-913e-12f58912df43`):
   - `EnvironmentManagement.Environments.Read`
   - `EnvironmentManagement.Settings.Read`
   - `EnvironmentManagement.Settings.ReadWrite`
   - `CopilotGovernance.Features.Read`
   - `CopilotGovernance.Settings.Read`
   - `CopilotGovernance.Settings.Write`
   - `Security.Recommendations.Read`
   - `Analytics.AdvisorRecommendations.Read`
   - `Governance.CrossTenantConnectionReports.Read`
   - `Connectivity.Connectors.Read`
   - `PowerApps.Apps.Read`
   - `AppManagement.ApplicationPackages.Install`
   - `AppManagement.ApplicationPackages.Read`
3. Add redirect URI: `https://global.consent.azure-apim.net/redirect`
4. Create a client secret
5. Note the Application (client) ID

### Deploy

```powershell
cd "Power Platform Admin"
pac connector create `
  --settings-file apiProperties.json `
  --api-definition apiDefinition.swagger.json `
  --script script.csx `
  -e c4f149b0-9f42-e8c4-97d8-bc69b59f971c
```

Update the `clientId` in `apiProperties.json` with your app registration's Application (client) ID before deploying.

## Resources

- [Source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Power%20Platform%20Admin)
- [Power Platform API reference](https://learn.microsoft.com/power-platform/admin/programmability-and-extensibility/powerplatform-api-reference)
- [Permissions reference](https://learn.microsoft.com/power-platform/admin/programmability-permission-reference)
- [Environment management settings tutorial](https://learn.microsoft.com/power-platform/admin/programmability-tutorial-environmentmanagement-settings)
