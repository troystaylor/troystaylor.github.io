---
layout: post
title: "Power Mission Control: a progressive discovery template for MCP connectors"
date: 2026-03-23 10:00:00 -0600
categories: [Power Platform, Custom Connectors]
tags: [MCP, Copilot Studio, custom connectors, template, progressive discovery, token optimization]
---

Every MCP connector you've built with my Power MCP v2 template follows the same pattern: one `AddTool()` call per API operation, each with a full JSON Schema. For a five-tool connector, this works great. For an API with 30 operations, the `tools/list` response alone can consume 15,000 tokens of the orchestrator's context window—before the agent even does anything.

Power Mission Control changes this. Instead of registering dozens of typed tools, the template exposes three meta-tools that cover any API surface. The orchestrator discovers operations on demand, so full schemas are never injected upfront.

## The problem with typed tools at scale

When Copilot Studio's orchestrator calls `tools/list`, every registered tool dumps its name, description, and full input schema into the response. A 30-tool connector sends roughly 500 tokens per tool—15,000 tokens total. That's context window budget spent on tool definitions the orchestrator may never use.

Worse, each new API operation you want to cover requires writing another `AddTool()` block with custom schema configuration, error handling, and response processing. The developer cost scales linearly with the API surface.

## Three tools instead of thirty

Power Mission Control replaces the per-operation pattern with three tools:

| Tool | Purpose |
|------|---------|
| `scan_{service}` | Search for available operations by intent |
| `launch_{service}` | Execute any API endpoint with auth forwarding |
| `sequence_{service}` | Execute a sequence of multiple operations in one call |

The `{service}` suffix comes from your `ServiceName` configuration. Set it to `apiservice`, and you get `scan_apiservice`, `launch_apiservice`, and `sequence_apiservice`.

The `tools/list` payload drops from ~15,000 tokens to ~1,500—a 90% reduction on initial load.

## How discovery works

Instead of pre-loading every schema, the orchestrator asks `scan_{service}` what's available:

```
User: "Create a new customer"
Orchestrator → scan_apiservice({query: "create customer"})
              ← Returns: endpoint /customers, method POST, required params [name, email]
Orchestrator → launch_apiservice({endpoint: "/customers", method: "POST", body: {...}})
         ← Returns: created customer record
```

The scan tool searches your **capability index**—a JSON array of operation descriptions embedded in the connector. Each entry includes an endpoint, HTTP method, outcome description, domain tag, and parameter lists. The orchestrator gets just enough context to select the right operation and request schemas only when needed.

## Three discovery modes

The template supports three ways to resolve `scan` queries:

### Static (default)

The capability index lives directly in `script.csx`. You curate the JSON array at build time. No external calls needed. This works with any API.

### Hybrid

Combines the embedded index for operation discovery with live API `describe` or metadata calls for field schemas. Describe results are cached (default 30 minutes). Best for APIs with runtime metadata endpoints like `/describe` or introspection queries.

### McpChain

Routes discovery queries to an external MCP server—for example, the MS Learn MCP for Microsoft Graph documentation. Results are cached (default 10 minutes). Best for APIs backed by searchable documentation services.

## Quick start

### 1. Configure your service

In Section 1 of `script.csx`, set your service name and base URL:

```csharp
private static readonly MissionControlOptions McOptions = new MissionControlOptions
{
    ServiceName = "apiservice",
    BaseApiUrl = "https://api.example.com/v1",
    DiscoveryMode = DiscoveryMode.Static,
    MaxDiscoverResults = 3,
};
```

### 2. Build the capability index

Use the companion `generate-capability-index.prompt.md` to create the index from your API docs:

1. Open `generate-capability-index.prompt.md` in VS Code
2. Paste your API documentation (Swagger, Postman collection, or text)
3. Copilot generates the JSON array
4. Review and paste into the `CAPABILITY_INDEX` constant in `script.csx`

Each entry looks like this:

```json
{
    "cid": "create_customer",
    "endpoint": "/customers",
    "method": "POST",
    "outcome": "Create a new customer record",
    "domain": "crm",
    "requiredParams": ["name", "email"],
    "optionalParams": ["phone", "company"],
    "schemaJson": "{\"type\":\"object\",\"properties\":{\"name\":{\"type\":\"string\"},\"email\":{\"type\":\"string\",\"format\":\"email\"}},\"required\":[\"name\",\"email\"]}"
}
```

### 3. Configure auth

Update `apiDefinition.swagger.json` with your API host and auth scheme:

```json
{
    "host": "your-api-host.com",
    "basePath": "/mcp",
    "securityDefinitions": {
        "oauth2_auth": { }
    }
}
```

Update `apiProperties.json` with connection parameters matching your auth.

### 4. Deploy

Import as a custom connector in Power Platform and add to your Copilot Studio agent.

## Built-in capabilities

The template handles common API patterns so you don't have to code them per-tool:

- **Auth forwarding** - The connector's Authorization header passes through to every API call automatically
- **429 retry** - Up to three retries with `Retry-After` header support
- **Error translation** - 401, 403, and 404 responses become friendly messages with fix suggestions
- **Response summarization** - HTML stripping, whitespace collapsing, and field truncation to keep responses token-efficient
- **Pagination detection** - Identifies `@odata.nextLink`, `nextLink`, and `next_page_url` patterns and tells the orchestrator how to get more results
- **Smart defaults** - Auto-injects `$top` for GET collection endpoints and supports author-defined parameter injection per endpoint pattern
- **Sequence operations** - Sequential execution or native `$batch` endpoint support with configurable size

## Add custom tools alongside mission control

You don't have to go all-in on meta-tools. Register typed tools for high-value operations that need custom logic, and let mission control handle the rest:

```csharp
private void RegisterCustomTools(McpRequestHandler handler)
{
    handler.AddTool("get_limits", "Get current API usage limits.",
        schema: s => { },
        handler: async (args, ct) =>
        {
            return await SendExternalRequestAsync(
                HttpMethod.Get, $"{McOptions.BaseApiUrl}/limits");
        });
}
```

These appear in `tools/list` alongside the three mission control tools.

## Smart defaults

Inject domain-specific parameter defaults that run before every `launch` call:

```csharp
McOptions.SmartDefaults = new Dictionary<string, Action<string, JObject>>
{
    ["/calendar"] = (endpoint, queryParams) =>
    {
        if (queryParams["startDate"] == null)
            queryParams["startDate"] = DateTime.UtcNow.Date.ToString("yyyy-MM-dd");
    },
    ["/events"] = (endpoint, queryParams) =>
    {
        if (queryParams["$orderby"] == null)
            queryParams["$orderby"] = "start/dateTime";
    }
};
```

## When to use mission control vs. typed tools

**Use mission control (v3) when:**

- The API has 10+ operations and token savings matter
- Operations follow standard REST patterns
- You want to cover the entire API surface without registering every endpoint
- The API may evolve—adding operations means updating the index, not writing code

**Use typed tools (v2) when:**

- You have a small, fixed set of operations (five or fewer)
- Each tool has complex, unique logic that doesn't fit a generic proxy pattern
- The API requires different auth or processing per operation

**Mix both when:**

- Most operations are standard REST but a few need custom logic
- You want mission control for discovery and launch but also need specific high-value tools exposed directly

## Template files

| File | Purpose |
|------|---------|
| `script.csx` | Connector logic—Section 1 (your config) + Section 2 (framework) |
| `apiDefinition.swagger.json` | OpenAPI definition with single POST at `/mcp/` |
| `apiProperties.json` | Connector metadata and auth config |
| `generate-capability-index.prompt.md` | Copilot prompt for generating capability indexes |

## Backward compatibility

All v2 constructs work unchanged. Use `handler.AddTool()`, `handler.AddResource()`, and `handler.AddPrompt()` directly—either instead of or alongside mission control mode.

## Resources

- [Full source code on GitHub](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20Mission%20Control%20Template)
- [Power MCP Template v2](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20MCP%20Template)
- [MCP specification](https://spec.modelcontextprotocol.io/2025-11-05/)
- [Copilot Studio custom connector documentation](https://learn.microsoft.com/microsoft-copilot-studio/agent-extend-action-connector)
