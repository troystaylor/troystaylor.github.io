---
layout: post
title: "Azure Platform Intelligence MCP connector for Copilot Studio"
date: 2026-05-12 14:00:00 -0500
categories: [Power Platform, Custom Connectors, MCP]
tags: [MCP, Copilot Studio, Azure, Platform Engineering, Custom Connectors, Infrastructure as Code]
---

Platform engineers juggle cost estimation, security assessments, drift detection, policy compliance, and template validation across dozens of subscriptions. Each task means a different blade in the Azure portal or a different CLI command. This connector brings nine of those operations into a Copilot Studio agent as MCP tools—ask a question in natural language, get structured results from the Azure Management APIs.

Inspired by the [Git-Ape](https://azure.github.io/git-ape/) platform engineering framework and the [Platform Engineering for the Agentic AI Era](https://devblogs.microsoft.com/all-things-azure/platform-engineering-for-the-agentic-ai-era/) thesis by Microsoft.

## Architecture

```
Copilot Studio Agent
        |  (MCP / JSON-RPC 2.0)
        v
Power Platform Custom Connector
        |  (OAuth delegated)
        v
Azure Management APIs + Azure Retail Prices API
```

All logic runs in the connector's `script.csx`. No container app or external backend required. The connector forwards the user's OAuth token to Azure Management APIs, so RBAC determines what each user can access.

## The nine tools

| Tool | Description | Azure API | RBAC required |
|------|-------------|-----------|---------------|
| `list_subscriptions` | List subscriptions the user has access to | ARM Subscriptions API | Reader |
| `list_resource_groups` | List resource groups in a subscription | ARM Resource Groups API | Reader |
| `estimate_cost` | Estimate monthly cost by resource type/SKU or from an ARM template | Azure Retail Prices API (public) | None |
| `analyze_security` | Security posture analysis via Defender for Cloud assessments | Microsoft.Security/assessments | Security Reader |
| `detect_drift` | Compare desired ARM template state against live resources | Microsoft.Resources/deployments/whatIf | Contributor |
| `validate_template` | Validate an ARM template without deploying | Microsoft.Resources/deployments/validate | Contributor |
| `visualize_resources` | Generate a Mermaid architecture diagram from a resource group | Microsoft.Resources (list) | Reader |
| `check_policy` | Azure Policy compliance summary for a subscription or resource group | Microsoft.PolicyInsights/policyStates | Reader |
| `import_resources` | Export a resource group as an ARM template | Microsoft.Resources/exportTemplate | Reader |

## How each tool works

### Cost estimation

The `estimate_cost` tool queries the [Azure Retail Prices API](https://learn.microsoft.com/rest/api/cost-management/retail-prices/azure-retail-prices)—a public API that requires no authentication. Two modes:

**Single resource** — provide a resource type, SKU, and region:

```
"Estimate the monthly cost for a Standard_D2s_v3 Virtual Machine in East US"
```

**ARM template** — pass a full template and get estimates for every resource:

```
"Estimate cost for this ARM template: {paste template JSON}"
```

The tool maps ARM resource types (`Microsoft.Compute/virtualMachines`, `Microsoft.Storage/storageAccounts`, etc.) to pricing service names and auto-detects monthly quantities from the pricing API's unit of measure. Hourly resources get multiplied by 730 hours/month, daily by 30, and GB-based storage defaults to 100 GB.

### Security analysis

The `analyze_security` tool pulls Microsoft Defender for Cloud assessments and returns findings sorted by severity (High, Medium, Low) with remediation guidance. Optionally filter by resource group:

```
"Analyze the security posture of subscription abc-123"
```

The response includes a summary with counts by severity plus individual findings with descriptions and remediation steps.

### Drift detection

The `detect_drift` tool runs an ARM What-If operation comparing a desired template against live state. It categorizes every resource as create, modify, delete, or no change:

```
"Check if this ARM template matches what's actually deployed in resource group my-rg"
```

For modified resources, the tool surfaces individual property changes with before/after values—so you can see exactly what drifted.

### Template validation

The `validate_template` tool validates an ARM template without deploying. It catches schema errors, invalid resource types, naming conflicts, and permission issues. If validation passes, it also runs a What-If preview showing what would happen on deployment:

```
"Validate this ARM template before I deploy it to my-rg"
```

### Resource visualization

The `visualize_resources` tool lists all resources in a resource group and generates a [Mermaid](https://mermaid.js.org/) architecture diagram. Resources are grouped by type, and the tool detects cross-references between resources (for example, a web app referencing an App Service Plan) to draw dependency edges:

```
"Show me an architecture diagram of resource group my-rg"
```

### Policy compliance

The `check_policy` tool summarizes Azure Policy compliance—how many resources are compliant vs. non-compliant, which policy assignments have violations, and which specific policy definitions are failing:

```
"Check policy compliance for subscription abc-123"
```

### Infrastructure export

The `import_resources` tool exports a resource group as an ARM template with parameter default values and comments. Useful for bringing click-deployed or legacy infrastructure under IaC management:

```
"Export resource group my-rg as an ARM template"
```

Large templates (over 50,000 characters) are truncated with a resource summary to stay within connector response limits.

## Implementation details

### OAuth delegation

The connector uses OAuth 2.0 with the `https://management.azure.com/user_impersonation` scope. When a user creates a connection, they authenticate with their own identity. The connector forwards that token on every Azure Management API call:

```csharp
if (this.Context.Request.Headers.Authorization != null)
{
    request.Headers.Authorization =
        this.Context.Request.Headers.Authorization;
}
```

This means RBAC governs access—users only see what their Azure roles allow.

### Pagination and throttling

Azure Management APIs return paginated results with `nextLink` tokens. The connector follows pagination automatically (up to 10 pages / 5,000 items):

```csharp
private async Task<JArray> SendAzureRequestPaginated(
    HttpMethod method, string url, int maxPages = 10)
{
    var allItems = new JArray();
    var currentUrl = url;

    for (int page = 0; page < maxPages
        && !string.IsNullOrWhiteSpace(currentUrl); page++)
    {
        var response = await SendAzureRequest(method, currentUrl)
            .ConfigureAwait(false);
        var items = response["value"] as JArray;
        if (items != null)
            foreach (var item in items)
                allItems.Add(item);

        currentUrl = response.Value<string>("nextLink");
    }
    return allItems;
}
```

For throttled requests (429), the connector retries up to 3 times with the `Retry-After` header value.

### Async operations with polling

Some Azure APIs (What-If, template export) return `202 Accepted` with a `Location` or `Azure-AsyncOperation` header. The connector polls at 10-second intervals until the operation completes (max 30 polls / ~5 minutes):

```csharp
if (response.StatusCode == HttpStatusCode.Accepted)
{
    // Extract Location or Azure-AsyncOperation header
    // Poll at 10-second intervals until 200/201
}
```

### MCP tool annotations

Every tool declares `readOnlyHint` and `idempotentHint` annotations so MCP clients know which tools are safe to call without side effects:

```csharp
ToolWithAnnotations("estimate_cost",
    "Estimate monthly cost for Azure resources...",
    Props(...),
    new string[0],
    readOnly: true, idempotent: true)
```

All nine tools are read-only and idempotent. The `validate_template` and `detect_drift` tools use the What-If API, which simulates deployment without making changes.

### Application Insights telemetry

Every MCP request logs correlation ID, method, tool name, duration, and success/failure to Application Insights. Drop in your instrumentation key to enable:

```csharp
private const string APP_INSIGHTS_KEY =
    "[INSERT_YOUR_APP_INSIGHTS_INSTRUMENTATION_KEY]";
```

Leave the placeholder to disable telemetry entirely.

## Deploying the connector

### Prerequisites

- Azure subscription
- Entra ID app registration with `Azure Service Management` > `user_impersonation` (delegated)
- Power Platform environment with custom connector support
- [PAC CLI](https://learn.microsoft.com/power-platform/developer/cli/introduction)

### App registration

1. Create an app registration in [Entra ID](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)
2. Add API permission: `Azure Service Management` > `user_impersonation` (delegated)
3. Add redirect URI: `https://global.consent.azure-apim.net/redirect`
4. Create a client secret
5. Note the Application (client) ID and Directory (tenant) ID

### Deploy

```powershell
cd "Azure Platform Intelligence"
pac connector create `
  --settings-file apiProperties.json `
  --api-definition apiDefinition.swagger.json `
  --script script.csx `
  -e c4f149b0-9f42-e8c4-97d8-bc69b59f971c
```

When creating a connection, enter your app registration's client ID, client secret, and tenant ID.

## RBAC summary

For full functionality, the connecting user needs these Azure RBAC roles:

| Role | Tools |
|------|-------|
| None (public API) | `estimate_cost` |
| Reader | `list_subscriptions`, `list_resource_groups`, `visualize_resources`, `check_policy`, `import_resources` |
| Security Reader | `analyze_security` |
| Contributor | `detect_drift`, `validate_template` |

Start with Reader for most operations. Add Security Reader for Defender assessments and Contributor only if you need drift detection or template validation.

## Resources

- [Source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Azure%20Platform%20Intelligence)
- [Git-Ape platform engineering framework](https://azure.github.io/git-ape/)
- [Platform Engineering for the Agentic AI Era](https://devblogs.microsoft.com/all-things-azure/platform-engineering-for-the-agentic-ai-era/)
- [Azure Retail Prices API](https://learn.microsoft.com/rest/api/cost-management/retail-prices/azure-retail-prices)
- [ARM What-If API](https://learn.microsoft.com/azure/azure-resource-manager/templates/deploy-what-if)
- [Microsoft Defender for Cloud assessments](https://learn.microsoft.com/azure/defender-for-cloud/secure-score-security-controls)
- [Azure Policy compliance](https://learn.microsoft.com/azure/governance/policy/how-to/get-compliance-data)
