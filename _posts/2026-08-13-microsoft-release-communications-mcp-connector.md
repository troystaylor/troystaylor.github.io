---
layout: post
title: "Microsoft 365 Roadmap and Azure Updates in Copilot Studio"
date: 2026-08-13 14:00:00 -0500
categories: [Power Platform, Custom Connectors, MCP]
tags: [MCP, Copilot Studio, Custom Connectors, Power Automate, Microsoft 365 Roadmap, Azure Updates, OData, Integration]
description: "A hybrid Power Platform custom connector for the Microsoft Release Communications MCP Server. The MCP endpoint serves Copilot Studio agents, and OData plus RSS operations serve Power Automate and Power Apps."
---

Microsoft hosts a public MCP server for release communications at `https://www.microsoft.com/releasecommunications/mcp`. It answers questions about the Microsoft 365 Roadmap and Azure Updates — what's in development, what ships this month, what's being retired — with no API key, no license, and no tenant configuration. Point an IDE-based MCP client at it and it works.

Power Platform is the gap. Copilot Studio can consume an MCP server, but only through a connector, and a naive passthrough to this one fails on the first call. [Microsoft Release Communications MCP](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Release%20Communications%20MCP) is that connector, plus REST operations for the flows and apps that can't speak MCP at all.

## Five operations, two audiences

| Operation | Type | Consumer |
|---|---|---|
| `InvokeMCP` | MCP | Copilot Studio agents |
| `ListM365RoadmapItems` | REST | Power Automate, Power Apps |
| `ListAzureUpdates` | REST | Power Automate, Power Apps |
| `GetM365RoadmapFeed` | RSS | Recurrence-triggered flows |
| `GetAzureUpdatesFeed` | RSS | Recurrence-triggered flows |

The MCP endpoint exposes four tools: `get_recent_m365_roadmaps`, `get_m365_roadmap_by_id`, `get_recent_azure_updates`, and `get_azure_update_by_id`.

The docs name the first one `get_recent_roadmaps`. The live server's `tools/list` says `get_recent_m365_roadmaps`. Write agent instructions against the live name.

## Three upstream behaviors that break a passthrough

The server is spec-compliant. That's the problem — Power Platform's MCP handling expects a narrower shape than the spec allows. [script.csx](https://github.com/troystaylor/SharingIsCaring/blob/main/Microsoft%20Release%20Communications%20MCP/script.csx) handles each one.

**406 on an `Accept` header of `application/json`.** Streamable HTTP requires the client to accept both content types, and the server enforces it. Every call fails until you send both:

```csharp
// The MRC MCP Server returns 406 unless the caller accepts both JSON and SSE.
forward.Headers.Accept.Clear();
forward.Headers.Accept.ParseAdd("application/json");
forward.Headers.Accept.ParseAdd("text/event-stream");
```

**Responses framed as SSE.** The body comes back as `event: message` / `data: {...}` lines, which isn't parseable JSON-RPC. The script unwraps the frames and returns the message as `application/json`. It scans every frame and prefers the one carrying `result` or `error`, since a single response can include progress events ahead of the real answer:

```csharp
lastPayload = payload;
if (parsed["result"] != null || parsed["error"] != null)
    bestPayload = payload;
```

**202 with an empty body on notifications.** Correct per spec, and Copilot Studio reports it as an invalid JSON-RPC response. Empty successes get a valid envelope instead:

```csharp
if (string.IsNullOrWhiteSpace(responseBody))
{
    if (response.IsSuccessStatusCode)
        return CreateJsonRpcSuccessResponse(requestId, new JObject());
    ...
}
```

## Schema normalization on tools/list

The tool schemas are valid JSON Schema that Power Platform won't take. `NormalizeToolsList` rewrites four things:

- Nullable union types (`"type": ["integer","null"]` on `skip`) collapse to a single scalar type
- `"default": null` entries are dropped
- The non-standard `execution` vendor key is removed from each tool object
- Non-boolean `exclusiveMinimum` and `exclusiveMaximum` values are coerced

Descriptions pass through untouched. The upstream OData filter guidance in those descriptions is what lets an agent build a working filter, so rewriting it would cost more than the schema fixes save.

If parsing fails at any point, the original content is returned rather than a broken rewrite:

```csharp
catch
{
    return content;
}
```

## The REST operations exist because MCP has a ceiling

The MCP tools cap at 50 items and truncate descriptions to fit a context window. That's right for an agent and wrong for a flow that needs to page 1,000 Azure retirements into a table.

The MCP tools wrap a public OData v4 API on the same host. Its service container is named `ReleaseCommunicationsApi` — the same string the MCP server reports as `serverInfo.name`. The connector exposes the entity sets directly:

```http
GET /releasecommunications/api/v2/M365?$filter=products/any(p: p eq 'Microsoft Teams')&$top=50
GET /releasecommunications/api/v2/Azure?$filter=tags/any(t: t eq 'Retirements')&$count=true
GET /releasecommunications/api/v2/Azure?$filter=availabilities/any(a: a/ring eq 'Retirement' and a/year eq 2026)
```

`$filter`, `$search`, `$orderby`, `$select`, `$top`, `$skip`, and `$count` all work, including `any()` lambdas over collections and the nested `availabilities` complex type.

Entity key access such as `M365(569217)` returns 404. Fetch one post with `$filter=id eq 569217`, or the v1 path `/api/v1/m365/569217`.

The OData endpoints aren't on Microsoft Learn. They're public, anonymous, and back the published roadmap and updates sites, but they carry no compatibility guarantee. The MCP endpoint is the documented surface — prefer it for agents and treat REST as convenience for flows.

## In a flow

Enter OData expressions unescaped. The connector handles URL encoding.

| Goal | Filter |
|---|---|
| Teams features still in development | `products/any(p: p eq 'Microsoft Teams') and status eq 'In development'` |
| Features reaching GA in a month | `generalAvailabilityDate eq '2026-02'` |
| Posts published on or after a date | `created ge 2026-02-01T00:00:00Z` |
| GCC High launched features | `cloudInstances/any(ci: ci eq 'GCC High') and status eq 'Launched'` |

Set **Include Count** to `true` and read `@odata.count` to size a paging loop, then step **Skip** by your **Top** value. Use **Select** — descriptions are full HTML and will bloat a flow run.

For change detection, run a **Recurrence** trigger against an RSS operation, or query with `created ge` using the previous run's timestamp.

## In Copilot Studio

Add the connector under **Tools** > **Add a tool** > **Model Context Protocol**, pick the connection, and add the tools.

The server covers two catalogs, so name the source in the prompt:

```
Which Microsoft Teams features on the Microsoft 365 Roadmap are releasing in June?
What is the status of Feature ID 526798 on the Microsoft 365 Roadmap?
Show all Azure retirements scheduled for this year.
Which Azure Databricks features reached general availability in February?
```

Roadmap and update data is the kind of thing a model will answer from memory, confidently and a year out of date. If that happens, name the tools in the agent instructions:

```markdown
When the user asks about Microsoft 365 Roadmap features, Azure service updates, release
timing, or retirements, call get_recent_m365_roadmaps, get_m365_roadmap_by_id,
get_recent_azure_updates, or get_azure_update_by_id before answering.
```

Set `include_facets` to `true` on either list tool to discover valid filter values before filtering.

## Setup

No connection parameters. No app registration.

```powershell
paconn login
paconn create --api-def apiDefinition.swagger.json --api-prop apiProperties.json --script script.csx
```

Test `InvokeMCP` with an initialize payload. A successful response reports `serverInfo.name` as `ReleaseCommunicationsApi`.

The connector is anonymous by design, and the caller's `Authorization` header is deliberately not forwarded to the public endpoint.

Application Insights logging is in the script and off until you replace the placeholder instrumentation key. It emits `McpRequestCompleted` and `RequestError` with the MCP method, tool name, correlation ID, status code, and duration. Telemetry failures are swallowed so they never affect a call.

If you're not on Power Platform, skip the connector and point your client at the server:

```json
{
  "servers": {
    "MRC-MCP-Server": {
      "type": "http",
      "url": "https://www.microsoft.com/releasecommunications/mcp"
    }
  }
}
```

## Resources

- [Source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Release%20Communications%20MCP)
- [Get started with the Microsoft Release Communications MCP Server](https://learn.microsoft.com/microsoft-365/admin/manage/mrc-mcp)
- [Microsoft 365 Roadmap](https://www.microsoft.com/microsoft-365/roadmap)
- [Azure Updates](https://azure.microsoft.com/updates)
- [Microsoft API Terms of Use](https://learn.microsoft.com/legal/microsoft-apis/terms-of-use)
