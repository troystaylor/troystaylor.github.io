---
layout: post
title: "Federated MCP template: bring real-time data into Microsoft 365 Copilot"
date: 2026-05-05 14:00:00 -0500
categories: [Power Platform, MCP]
tags: [MCP, Microsoft 365 Copilot, Federated Connectors, Azure Container Apps, Copilot Studio, .NET]
description: "A .NET 10 template for building custom federated Copilot connectors that bring real-time data from any API into Microsoft 365 Copilot Chat, Researcher, and Copilot Studio via MCP."
---

Microsoft [announced federated Copilot connectors](https://techcommunity.microsoft.com/blog/microsoft365copilotblog/federated-copilot-connectors---bringing-real-time-enterprise-data-within-microso/4515993) as a new way to bring real-time enterprise data into Microsoft 365 Copilot. Unlike Graph connectors that crawl and copy data into the M365 index on a schedule, federated connectors query source systems at runtime using MCP. Data stays where it lives.

I built a template that handles the infrastructure so you can focus on the tools. Clone it, replace the example tools with your data source logic, deploy to Azure Container Apps, and register in the M365 admin center. The MCP C# SDK handles protocol framing, auth, and tool discovery.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Federated%20Copilot%20Template)

## Federated vs sync connectors

| | Sync (Graph Connectors) | Federated (this template) |
|---|---|---|
| Data freshness | Crawl schedule | Real-time at query time |
| Data location | Copied to M365 tenant | Stays in source system |
| Protocol | Graph External Items API | MCP (JSON-RPC 2.0) |
| Tools | N/A | Read-only tools |
| Surfaces | Copilot, Search, Context IQ | Copilot Chat, Researcher, Excel |

The tradeoff is clear: sync connectors give you search indexing and Context IQ grounding. Federated connectors give you live data with no crawl lag. Choose based on whether your data changes hourly or weekly.

## What the template provides

- **ASP.NET Core host** with the [MCP C# SDK v1.0](https://github.com/modelcontextprotocol/csharp-sdk) wired up
- **JWT authentication** with Entra SSO or OAuth 2.0 token passthrough
- **Tool registration** using `[McpServerTool]` attributes — auto-discovered, type-safe
- **Dockerfile** with multi-stage build for Azure Container Apps
- **Bicep infrastructure** and a `deploy.ps1` script for end-to-end deployment
- **Development mode** that skips auth for local testing with VS Code or MCP Inspector

## Architecture

```
M365 Copilot Chat / Researcher
    │
    │  MCP (JSON-RPC 2.0 over Streamable HTTP)
    │  Auth: Entra SSO or OAuth 2.0 (per-user)
    ▼
┌──────────────────────────────────┐
│  Federated MCP Server            │
│  (Azure Container Apps)          │
│                                  │
│  Program.cs ── MCP SDK + Auth    │
│  Tools/    ── [McpServerTool]    │
│                                  │
│  Token passthrough to upstream   │
└──────────┬───────────────────────┘
           │
           │  REST API (bearer token forwarded)
           ▼
   Upstream Data Source
   (Graph, HubSpot, Gong, Jira, etc.)
```

Each connector deploys as its own container app with its own auth configuration and MCP endpoint. One connector, one container, one Base URL in the M365 admin center.

## Three surfaces, one server

A single MCP server built from this template serves three surfaces:

| Surface | How |
|---|---|
| **M365 Copilot Chat / Researcher** | Register as federated connector in M365 admin center |
| **Copilot Studio** | Wrap with a Power Platform custom connector using `x-ms-agentic-protocol` |
| **Direct MCP clients** | Point VS Code, Claude Desktop, or MCP Inspector at the Base URL |

Build once, surface everywhere.

## Prerequisites

- [.NET 10 SDK](https://get.dot.net/10)
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)
- [Docker](https://docs.docker.com/get-docker/) for container builds
- Azure subscription with permission to create Container Apps and Container Registry
- Microsoft 365 tenant with Copilot license
- Admin access: Global Administrator or AI Administrator in M365 admin center

## Quick start

### 1. Clone and configure

```bash
cp -r "Connector-Code/Federated MCP Template" MyConnector
cd MyConnector
```

Edit `appsettings.json`:

- `McpServer.Name` — unique connector identifier
- `McpServer.Title` — user-facing name in M365 Copilot
- `Auth.Authority` — your Entra ID authority URL
- `Auth.ValidAudiences` — your app registration client ID
- `Upstream.BaseUrl` — the API your connector proxies

### 2. Add your tools

Replace `Tools/ExampleTools.cs` with tools for your data source. Federated connectors are **read-only only** — search, get, list, query. No create, update, or delete.

```csharp
[McpServerToolType]
public class MyTools(
    IHttpClientFactory httpClientFactory,
    IHttpContextAccessor contextAccessor)
{
    [McpServerTool(Title = "Search Deals")]
    [Description("Search for deals matching criteria. Returns deal name, stage, value, and owner.")]
    public async Task<string> SearchDeals(
        [Description("Search query")] string query,
        [Description("Max results (1-50)")] int top = 10,
        CancellationToken ct = default)
    {
        var client = CreateAuthenticatedClient();
        var response = await client.GetAsync(
            $"/api/deals?q={Uri.EscapeDataString(query)}&limit={top}", ct);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadAsStringAsync(ct);
    }
}
```

Register your tools in `Program.cs`:

```csharp
.WithTools<MyTools>();
```

Three rules for federated connector tools:
1. **Read-only only** — search, get, list, query operations
2. **Descriptive** — clear `[Description]` attributes help Copilot select the right tool
3. **Citations** — include source URLs in responses for verification links

### 3. Run locally

```bash
dotnet run
```

Test with any MCP client at `http://localhost:5000`. In Development mode, authentication is skipped so you can test tools without configuring JWT tokens. Auth is always enforced in Production.

### 4. Deploy to Azure

```powershell
cd infra
.\deploy.ps1 `
    -ConnectorName "my-connector" `
    -ResourceGroup "rg-mcp-connectors" `
    -RegistryName "mcpregistry" `
    -TenantId "00000000-0000-0000-0000-000000000000" `
    -AppClientId "11111111-1111-1111-1111-111111111111" `
    -UpstreamBaseUrl "https://api.example.com"
```

The script outputs the **MCP Base URL** needed for registration.

## Register as a federated connector

### Step 1: Set up authentication

**For Entra SSO** (Microsoft APIs):

1. Create or update an Entra ID app registration
2. In [Teams Developer Portal](https://dev.teams.microsoft.com/) > Tools > OAuth Client Registration, create an SSO registration
3. Copy the **SSO registration ID**

**For OAuth 2.0** (third-party APIs like HubSpot, Gong):

1. Register your app with the OAuth provider, using redirect URI: `https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect`
2. In [Teams Developer Portal](https://dev.teams.microsoft.com/) > Tools > OAuth Client Registration, create an OAuth connection with the provider's client ID, secret, and endpoints
3. Copy the **OAuth registration ID**

### Step 2: Create the connector

1. Sign in to [M365 admin center](https://admin.microsoft.com/)
2. Navigate to **Copilot > Connectors > Gallery**
3. Under **Created by your org**, select **Create a new connector > Connect to MCP server**
4. Enter:
   - **Display name**: User-facing connector name
   - **Base URL**: The MCP Base URL from deployment
   - **Registration ID**: The SSO or OAuth ID from Step 1
5. **Save**

### Step 3: Stage rollout

1. Select your connector in **Your Connections**
2. Select **Staged rollout**
3. Add test users or groups
4. When ready, select **Deploy to all users**

## Auth patterns

### Token passthrough (simplest)

The template includes a `CreateAuthenticatedClient()` helper that extracts the bearer token from the incoming MCP request and forwards it to the upstream API. This works when the upstream API accepts the same token — for example, Microsoft Graph with Entra SSO, or a third-party API that accepts its own OAuth token directly.

### On-Behalf-Of (OBO) flow

For calling a downstream API that requires a different audience:

```csharp
var incomingToken = contextAccessor.HttpContext?.Request
    .Headers.Authorization.ToString().Replace("Bearer ", "");
var downstreamToken = await confidentialClient
    .AcquireTokenOnBehalfOf(scopes, new UserAssertion(incomingToken))
    .ExecuteAsync();
```

### Service-to-service (managed identity)

For APIs that use Azure managed identity instead of user tokens:

```csharp
var credential = new DefaultAzureCredential();
var token = await credential.GetTokenAsync(
    new TokenRequestContext(new[] { "https://api.example.com/.default" }));
client.DefaultRequestHeaders.Authorization =
    new AuthenticationHeaderValue("Bearer", token.Token);
```

## Project structure

```
├── Program.cs                   # ASP.NET Core host, auth, MCP server config
├── FederatedMcpTemplate.csproj  # .NET 10 project, MCP SDK references
├── appsettings.json             # Server, auth, and upstream configuration
├── Tools/
│   └── ExampleTools.cs          # MCP tool definitions (replace with yours)
├── Dockerfile                   # Multi-stage build for Azure Container Apps
└── infra/
    ├── main.bicep               # Container App + environment + logging
    └── deploy.ps1               # End-to-end build, push, deploy script
```

## SDK features available

The [MCP C# SDK v1.0](https://devblogs.microsoft.com/dotnet/release-v10-of-the-official-mcp-csharp-sdk/) provides:

| Feature | How | Notes |
|---|---|---|
| Tool registration | `[McpServerTool]` attribute | Auto-discovered, type-safe |
| Auth (PRM + JWT) | Built-in | `.AddMcp()` auto-hosts PRM document |
| Incremental scope consent | Built-in | 401/403 with scopes in WWW-Authenticate |
| Long-running requests | `EnablePollingAsync()` | SSE + client polling |
| Tasks (experimental) | `IMcpTaskStore` | Durable result tracking with TTL |
| Icons | `IconSource` parameter | On tools, resources, prompts |
| Resources | `[McpServerResource]` | Static and template-based |
| Prompts | `[McpServerPrompt]` | Reusable prompt templates |

## Resources

- [Federated MCP Template source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Federated%20Copilot%20Template)
- [Federated Copilot connectors announcement](https://techcommunity.microsoft.com/blog/microsoft365copilotblog/federated-copilot-connectors---bringing-real-time-enterprise-data-within-microso/4515993)
- [Federated connectors overview](https://learn.microsoft.com/en-us/microsoft-365/copilot/connectors/federated-connectors-overview)
- [Set up custom federated connectors](https://learn.microsoft.com/en-us/microsoft-365/copilot/connectors/set-up-custom-federated-connectors)
- [Manage federated connectors](https://learn.microsoft.com/en-us/microsoft-365/copilot/connectors/manage-federated-connectors)
- [MCP C# SDK v1.0 release](https://devblogs.microsoft.com/dotnet/release-v10-of-the-official-mcp-csharp-sdk/)
- [MCP C# SDK repository](https://github.com/modelcontextprotocol/csharp-sdk)
- [MCP specification (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25)
- [Teams Developer Portal](https://dev.teams.microsoft.com/)
