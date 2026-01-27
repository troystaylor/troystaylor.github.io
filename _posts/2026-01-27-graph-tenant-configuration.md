---
layout: post
title: "Graph Tenant Configuration Connector for Power Platform"
date: 2026-01-27 14:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [Graph Tenant Configuration, Microsoft Graph, UTCM, Configuration Monitoring, Baselines, Snapshots, Copilot Studio, MCP, Custom Connectors, Power Platform, Preview]
description: "Microsoft Graph UTCM connector for Power Platform with MCP support to monitor tenant drift, baselines, and snapshots."
---

> Preview: Uses Microsoft Graph UTCM API (graph-rest-beta). Behavior may change.

Microsoft Graph **Unified Tenant Configuration Management (UTCM)** API connector for Power Platform. Use it to monitor tenant configuration drift, keep baselines healthy, and capture snapshots for backup or migration.

Define baselines, run monitors, and track drift across 300+ resource types spanning Microsoft Entra, Defender, Exchange Online, Intune, Purview, and Teams. Review run history and drift details to understand what changed.

Use it as a Power Platform custom connector or as an MCP action in Copilot Studio. The MCP endpoint exposes tools and prompts so agents can check drift, create monitors, and export configurations inside your Power Platform guardrails.

## Why this matters
- Detect tenant configuration drift against baselines
- Capture snapshots for backup or migration
- Track monitoring runs and drift counts across 300+ resource types
- Use as a Power Platform connector and as an MCP action in Copilot Studio

## What’s included
- Power Platform custom connector (Swagger + `apiProperties.json` + `script.csx`)
- MCP endpoint with tools and prompts for Copilot Studio
- Application Insights telemetry hooks (optional)

## Supported workloads
- **Microsoft Defender**
- **Microsoft Entra** (38 resource types, e.g., `microsoft.entra.conditionalAccessPolicy`)
- **Exchange Online** (58 resource types)
- **Intune** (65+ resource types)
- **Purview** (28 resource types)
- **Teams** (60 resource types)

## API operations
**Monitors**
- List, create, get, update, delete monitors
- Get monitor baseline

**Drifts**
- List drifts, get drift

**Snapshots**
- List snapshot jobs (max 12 visible)
- Get snapshot job, delete snapshot job
- Create snapshot from baseline

**Monitoring results**
- List monitoring run results, get run result

**Baselines**
- Get baseline

## MCP integration (Copilot Studio)
**Tools**
- `list_monitors`, `create_monitor`, `get_monitor`, `delete_monitor`
- `list_drifts`, `get_drift`
- `list_snapshots`, `get_snapshot`, `create_snapshot`, `delete_snapshot`
- `list_results`, `get_baseline`

**Prompts**
- `check_drift_status` — summarize current drift
- `create_security_monitor` — create security-focused monitor
- `export_configuration` — snapshot for export

**Copilot Studio usage**
1. Import connector
2. Create OAuth connection
3. Add **InvokeMCP** action (tools appear automatically)

## Example scenarios
**Monitor security configuration**
1. Create monitor → security resources
2. Check results → `ListConfigurationMonitoringResults`
3. Check drifts → `ListConfigurationDrifts`
4. Drill into drift → `GetConfigurationDrift`

**Export tenant configuration**
1. Get baseline ID → `GetMonitorBaseline`
2. Create snapshot → `CreateSnapshotFromBaseline`
3. Poll → `GetConfigurationSnapshotJob`
4. Download → use `resourceLocation`

**Clean up snapshots**
1. List snapshots → `ListConfigurationSnapshotJobs`
2. Delete old → `DeleteConfigurationSnapshotJob`

> Reference: [Supported workloads and resource types](https://learn.microsoft.com/graph/utcm-supported-resourcetypes) · [JSON schema](https://json.schemastore.org/utcm-monitor.json)

## Prerequisites
> Preview: API is beta (`graph-rest-beta`). Expect changes; requires admin consent.

1. **Azure AD app registration** with delegated permissions:
   - `ConfigurationMonitoring.Read.All`
   - `ConfigurationMonitoring.ReadWrite.All`
   - `User.Read`
2. **Admin consent** for the permissions
3. **Privileged role** for managing monitors
4. **UTCM service principal** in your tenant (`03b07b79-c5bc-4b5e-9bfa-13acf4a99998`)

### Set up UTCM service principal
```powershell
Install-Module Microsoft.Graph.Authentication
Install-Module Microsoft.Graph.Applications
Connect-MgGraph -Scopes 'Application.ReadWrite.All'
New-MgServicePrincipal -AppId '03b07b79-c5bc-4b5e-9bfa-13acf4a99998'
```

Grant Graph app roles to UTCM SP (example):
```powershell
$permissions = @('User.ReadWrite.All','Policy.Read.All')
$Graph = Get-MgServicePrincipal -Filter "AppId eq '00000003-0000-0000-c000-000000000000'"
$UTCM = Get-MgServicePrincipal -Filter "AppId eq '03b07b79-c5bc-4b5e-9bfa-13acf4a99998'"
foreach ($p in $permissions) {
  $AppRole = $Graph.AppRoles | Where-Object { $_.Value -eq $p }
  $body = @{ AppRoleId = $AppRole.Id; ResourceId = $Graph.Id; PrincipalId = $UTCM.Id }
  New-MgServicePrincipalAppRoleAssignment -ServicePrincipalId $UTCM.Id -BodyParameter $body
}
```

## Connector setup
1. **Register app** → redirect URI: `https://global.consent.azure-apim.net/redirect`
2. **Add permissions** → grant admin consent
3. **Create client secret** → copy **Value**
4. **Update** `apiProperties.json` with your `clientId`
5. **Deploy**
   ```powershell
   pac connector create \
     --environment <ENV_ID> \
     --api-definition-file "apiDefinition.swagger.json" \
     --api-properties-file "apiProperties.json" \
     --script-file "script.csx"
   ```
   or update:
   ```powershell
   pac connector update \
     --environment <ENV_ID> \
     --connector-id <CONNECTOR_ID> \
     --api-definition-file "apiDefinition.swagger.json" \
     --api-properties-file "apiProperties.json" \
     --script-file "script.csx"
   ```

## Application Insights (optional)
```csharp
private const string APP_INSIGHTS_CONNECTION_STRING = "InstrumentationKey=...;IngestionEndpoint=https://...";
```
Events: `OperationStarted`, `OperationCompleted`, `OperationError`, `McpRequest`, `ToolCall*`, `GraphApiError`

## Limitations
- Snapshot jobs: max 12 visible
- Monitor frequency: 6 hours
- API version: Preview (`graph-rest-beta`)
- Permissions: Admin consent required

## Resources
- Repo: https://github.com/troystaylor/SharingIsCaring/tree/main/Graph%20Tenant%20Configuration
- UTCM API overview: https://learn.microsoft.com/graph/api/resources/unified-tenant-configuration-management-api-overview?view=graph-rest-beta
- Resource types: https://learn.microsoft.com/graph/utcm-supported-resourcetypes