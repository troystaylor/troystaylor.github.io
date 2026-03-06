---
title: Managing Azure Arc-enabled SQL Server with a dual-mode Power Platform connector
author: Troy Taylor
date: 2026-03-06
category: Power Platform
layout: post
---

Managing hybrid SQL Server infrastructure across on-premises, multi-cloud, and Azure environments presents unique challenges. Today, I'm sharing a Power Platform custom connector that provides 25 REST operations and MCP tools for managing Azure Arc-enabled SQL Server instances, databases, availability groups, licenses, and more through both traditional automation and conversational AI.

## What Azure Arc Data Services offers

[Azure Arc-enabled SQL Server](https://learn.microsoft.com/en-us/azure/architecture/hybrid/azure-arc-sql-server) extends Azure management capabilities to SQL Server instances running anywhere. This connector wraps the Azure Resource Manager APIs to provide:

- **Instance management**: List, get, create, update, and delete Arc-enabled SQL Server registrations
- **Database visibility**: Query databases with details on state, recovery mode, size, and backup status
- **High availability**: Monitor Always On availability groups and failover groups
- **License management**: Create and manage SQL Server licenses and Extended Security Updates (ESU) licenses
- **Data controllers**: Access Azure Arc data controllers and SQL Managed Instances
- **Cross-subscription queries**: Use Azure Resource Graph for KQL-based inventory searches

## Connector capabilities

The connector operates in two modes:

### REST operations for Power Automate

All 25 operations work as standard Power Platform actions. Use them in flows to automate:
- Inventory reporting across subscriptions
- License compliance monitoring
- Backup policy validation
- Tag management and governance

### MCP tools for Copilot Studio

The same 25 operations are exposed as Model Context Protocol (MCP) tools, enabling natural language interactions:

- "List all Arc-enabled SQL Server instances in my subscription"
- "What databases are on the SQL Server instance named SQLPROD01?"
- "Show me the availability group details for AG-Finance"
- "Update the license type of instance SQLPROD01 to PAYG"
- "Find all Arc SQL instances across all subscriptions using Resource Graph"

## API coverage

| Category | Operations | Description |
|----------|------------|-------------|
| SQL Server instances | 6 | Full CRUD plus PATCH for partial updates |
| Databases | 2 | List and get with backup/recovery info |
| Availability groups | 2 | Replica and sync state details |
| Failover groups | 2 | Partner and role information |
| SQL Server licenses | 4 | Billing and activation management |
| ESU licenses | 4 | Extended Security Updates for SQL 2012/2014 |
| Data controllers | 2 | Azure Arc data controller inventory |
| SQL Managed Instances | 2 | Arc-enabled managed instance details |
| Resource Graph | 1 | KQL queries across subscriptions |

## Setting up the connector

### Prerequisites

1. **Azure subscription** with Azure Arc-enabled SQL Server instances
2. **Azure AD app registration** with `user_impersonation` delegated permission for Azure Service Management
3. **RBAC role assignment**: Reader for queries, Contributor for modifications

### App registration

Create a new registration in the Azure Portal:

1. Navigate to **Microsoft Entra ID > App registrations > New registration**
2. Set the redirect URI to `https://global.consent.azure-apim.net/redirect`
3. Add **Azure Service Management > user_impersonation** delegated permission
4. Create a client secret and copy both the client ID and secret value

### Installation with PAC CLI

```powershell
# Authenticate to your environment
pac auth create --environment "https://yourorg.crm.dynamics.com"

# Create the connector
pac connector create --api-definition apiDefinition.swagger.json --api-properties apiProperties.json --script script.csx
```

## How the code handles dual-mode requests

The script routes requests based on the operation ID:

```csharp
public override async Task<HttpResponseMessage> ExecuteAsync()
{
    switch (Context.OperationId)
    {
        case "InvokeMCP":
            response = await HandleMcpAsync(correlationId);
            break;
        default:
            response = await HandleRestAsync();
            break;
    }
}
```

REST operations pass through to Azure Resource Manager with the appropriate API version. MCP requests parse the JSON-RPC payload and route to the corresponding ARM endpoint based on the tool name.

## Key properties returned

### SQL Server instance details

- **Version**: SQL Server 2012 through 2025
- **Edition**: Enterprise, Standard, Web, Developer, Express, Evaluation
- **Status**: Connected, Disconnected, Registered
- **License type**: Paid, Free, HADR, PAYG, ServerCAL, LicenseOnly
- **Host type**: Azure VM, physical server, VMware, AWS, GCP
- **Azure Defender status**: Protected or Unprotected
- **Backup policy**: Retention days, full/differential/log intervals

### Database properties

- **State**: Online, Offline, Restoring, Recovering, Suspect, Emergency
- **Recovery mode**: Full, Bulk-logged, Simple
- **Backup info**: Last full, differential, and log backup timestamps
- **Size metrics**: Size in MB and available space

### Availability group configuration

- **Replicas**: Name, role, availability mode, failover mode, sync health
- **Databases**: Name, sync state, suspended status
- **Settings**: Failure condition level, health check timeout, DTC support

## Application Insights integration

Enable request and error telemetry by adding your connection string to the script:

```csharp
private const string APP_INSIGHTS_CONNECTION_STRING = 
    "InstrumentationKey=YOUR-KEY;IngestionEndpoint=https://REGION.in.applicationinsights.azure.com/";
```

The following events are logged:

| Event | Description |
|-------|-------------|
| `RequestReceived` | Every incoming request with operation ID and auth details |
| `RequestCompleted` | Success with status code and duration |
| `RequestError` | Unhandled exceptions with error type and message |
| `MCPRequest` | MCP JSON-RPC method received |
| `MCPToolCall` | MCP tool invocation with tool name |
| `MCPToolError` | MCP tool execution failures |
| `OAuthFailure_Passthrough` | 401/403 responses on REST operations |

## Resource Graph queries

The `QueryResourceGraph` operation accepts KQL queries for cross-subscription inventory:

```kusto
Resources
| where type == "microsoft.azurearcdata/sqlserverinstances"
| project name, resourceGroup, subscriptionId, 
    edition = properties.edition,
    version = properties.version,
    status = properties.status
```

This enables powerful scenarios like compliance dashboards, license audits, and cross-environment reporting without iterating through subscriptions individually.

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| 403 Forbidden | Missing RBAC role | Assign Reader/Contributor on the subscription or resource group |
| 401 Unauthorized | Token expired | Re-authenticate the connection |
| No instances returned | Wrong scope | Verify subscription ID and resource group name |
| MCP tools not appearing | Connector not added | Add the connector as an action in Copilot Studio |

## Get the connector

The complete connector files are available in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Azure%20Arc%20Data%20Services):

- `apiDefinition.swagger.json` - OpenAPI specification with all 25 operations
- `apiProperties.json` - Connection parameters and OAuth configuration
- `script.csx` - C# script for MCP handling and Application Insights integration
- `readme.md` - Detailed documentation

## Resources

- [Azure Arc-enabled SQL Server overview](https://learn.microsoft.com/en-us/azure/architecture/hybrid/azure-arc-sql-server)
- [Azure Arc Data Services REST API](https://learn.microsoft.com/en-us/rest/api/azurearcdata/)