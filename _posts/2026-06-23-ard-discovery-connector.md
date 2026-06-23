---
layout: post
title: "Building an ARD Discovery connector for Power Platform and Copilot Studio"
date: 2026-06-23 10:00:00 -0500
categories: [Power Platform, MCP]
tags: [ARD, MCP, Copilot Studio, Custom Connectors, Azure Functions, A2A, Discovery]
description: "A dual-mode Power Platform custom connector that implements the Agentic Resource Discovery (ARD) protocol — crawling registries, verifying trust, and proxying MCP calls with three-tier authentication. The first ARD implementation targeting Azure and Power Platform."
---

The agentic ecosystem has a discovery problem. MCP servers, A2A agents, and AI skills are multiplying, but there's no standard way for an AI client to ask "what's available for this task?" and get a trustworthy answer. The [Agentic Resource Discovery (ARD)](https://agenticresourcediscovery.org/) specification — developed by a working group with participants from Microsoft, Google, Hugging Face, Nvidia, Salesforce, and others — defines that discovery layer.

## What ARD actually is

ARD is a discovery protocol that sits entirely before invocation. It doesn't replace MCP, A2A, or any execution runtime. It answers one question: given a natural language description of a capability, which agentic resources match, and how trustworthy are they?

The core primitives:

- **AI Catalog** (`/.well-known/ai-catalog.json`) — a structured manifest of agentic resources a domain publishes, with URN identifiers, media types, capability descriptions, and optional JWS signatures
- **Search** — semantic + keyword search across indexed catalog entries with structured filters (type, tags, publisher) and federation modes
- **Explore** — faceted aggregation to understand what's available before searching (how many MCP servers vs. A2A agents, which publishers, which tags)
- **Trust verification** — multi-signal scoring (HTTPS, DNS TXT, .well-known file, JWS signature) that produces a 0-100 trust score per domain

ARD doesn't prescribe how you implement the index, the crawl, or the auth. It prescribes the wire format and the trust model.

## Architecture

The connector is dual-mode: typed operations with full schemas for Power Automate, plus an MCP endpoint for Copilot Studio.

```text
┌─────────────────────────────────────────────────────────┐
│  Power Platform Custom Connector (script.csx)           │
│  - Typed operations: /search, /explore, /agents, /proxy │
│  - MCP endpoint: /mcp (JSON-RPC 2.0)                    │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTPS + x-api-key + Auth headers
┌──────────────────────────▼──────────────────────────────┐
│  Azure Functions Backend (.NET 8 Isolated)              │
│  ┌────────────┐ ┌─────────────┐ ┌────────────────────┐  │
│  │ Search     │ │ Explore     │ │ Proxy (3-tier auth)│  │
│  │ List       │ │ Catalog     │ │ OBO → Org → User   │  │
│  │ Health     │ │ Crawl       │ │ + Rate Limiter     │  │
│  └────────────┘ └─────────────┘ └────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ ISearchIndex                                     │   │
│  │  ├─ TableStorageIndex (default, <100K entries)   │   │
│  │  └─ AiSearchIndex (vector + keyword, scalable)   │   │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌────────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │ TrustVerifier  │ │ CrawlState   │ │ TokenStore   │   │
│  │ DNS/JWS/.wk    │ │ Table Storage│ │ Table Storage│   │
│  └────────────────┘ └──────────────┘ └──────────────┘   │
└─────────────────────────────────────────────────────────┘
```

The connector layer (script.csx) handles MCP JSON-RPC dispatch and payload construction. The backend (Azure Functions) owns the index, crawl, trust verification, and proxy auth resolution. They communicate over HTTPS with an API key shared secret.

## The search index: two implementations, one interface

The `ISearchIndex` interface abstracts the catalog index behind four operations:

```csharp
public interface ISearchIndex
{
    Task IndexEntryAsync(IndexedEntry entry);
    Task IndexBatchAsync(IEnumerable<IndexedEntry> entries);
    Task RemoveEntryAsync(string identifier);
    Task<List<ScoredEntry>> SearchAsync(string text,
        Dictionary<string, string[]>? filters = null, int pageSize = 10);
    Task<Dictionary<string, Dictionary<string, int>>> ExploreAsync(
        string[] facetFields, string? text = null, int limit = 20);
    Task<List<IndexedEntry>> ListAsync(string? filter = null,
        int pageSize = 20, int offset = 0);
    Task<int> GetCountAsync();
}
```

**TableStorageIndex** persists entries to Azure Table Storage and queries in-memory. It's sufficient for catalogs under 100K entries and requires zero additional Azure resources beyond the storage account the Functions app already uses.

**AiSearchIndex** persists to Azure AI Search with HNSW vector embeddings from Azure OpenAI's `text-embedding-3-small` model. It enables hybrid vector + keyword search and scales to production workloads. The backend selects the implementation at startup based on whether `AiSearchEndpoint` is configured:

```csharp
if (!string.IsNullOrEmpty(Environment.GetEnvironmentVariable("AiSearchEndpoint")))
    services.AddSingleton<ISearchIndex, AiSearchIndex>();
else
    services.AddSingleton<ISearchIndex, TableStorageIndex>();
```

No code changes, no redeployment. Set the environment variable and the backend switches to vector search.

## Trust verification

This is the part of ARD I find most interesting technically. The spec defines a multi-signal trust model, and the implementation (`TrustVerifier.cs`) checks four signals for each crawled domain:

| Signal | Points | How it works |
|--------|--------|-------------|
| HTTPS origin | +10 | All crawled domains use HTTPS (baseline) |
| DNS TXT record | +20 | Queries `_ard-verify.{domain}` via Cloudflare DoH, checks for `ard-verify=...` value |
| .well-known file | +15 | Fetches `/.well-known/ard-verify.json`, validates the `domain` field matches |
| JWS catalog signature | +30 | Parses JWS Compact Serialization from the catalog's `signature` field, verifies RS256/ES256 header |

The DNS verification uses DNS-over-HTTPS (DoH) via Cloudflare rather than raw DNS queries:

```csharp
var url = $"https://cloudflare-dns.com/dns-query?name=_ard-verify.{domain}&type=TXT";
var request = new HttpRequestMessage(HttpMethod.Get, url);
request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/dns-json"));
```

This avoids firewall issues in Azure Functions (no UDP port 53 needed) and works in consumption plan without any networking configuration.

Trust scores map to four levels: **none** (0-9), **basic** (10-39), **verified** (40-69), **high** (70-100). A domain with HTTPS + DNS TXT + .well-known file scores 45 (verified). Add a JWS-signed catalog and it reaches 75 (high).

### Domain-URN mismatch protection

The crawl pipeline rejects catalog entries where the URN publisher doesn't match the crawled domain. If `good.com` serves a catalog containing `urn:air:evil.com:tools:stealer`, that entry is dropped. This prevents a compromised catalog from injecting entries that appear to come from a different publisher.

## Three-tier proxy authentication

The proxy endpoint (`/proxy`) is where discovery meets invocation. When a user asks Copilot Studio to invoke a discovered capability, the proxy resolves authentication automatically through three tiers:

**Tier 1 — On-Behalf-Of (OBO)**: If the target is a same-tenant Entra ID resource, the proxy extracts the user's access token from App Service auth headers (`x-ms-token-aad-access-token`) and exchanges it via the OBO flow. The user never sees an auth prompt.

```csharp
var userToken = ExtractUserToken(req);
if (!string.IsNullOrEmpty(userToken))
{
    var oboToken = await _obo.TryExchangeAsync(userToken, config.OboScope);
    if (!string.IsNullOrEmpty(oboToken))
    {
        var result = await _registry.ProxyMcpCallAsync(targetUrl, mcpRequest, oboToken);
        if (!string.IsNullOrEmpty(result))
            return await CreateJsonResponse(req, result);
    }
}
```

**Tier 2 — Org token**: If an admin pre-connected the domain via `/connect`, the proxy uses the stored org-level token from Azure Table Storage. The token is refreshed automatically when near expiry.

**Tier 3 — Per-user token or elicitation**: If no OBO or org token is available, the proxy checks for a stored per-user token. If none exists and `EnableElicitation` is `true`, it returns an MCP elicitation response — a structured sign-in prompt that Copilot Studio can present to the user:

```csharp
var inputRequest = new JObject
{
    ["method"] = "elicitation/create",
    ["params"] = new JObject
    {
        ["mode"] = "url",
        ["url"] = connectUrl,
        ["message"] = $"The service at {targetDomain} requires authentication."
    }
};
```

If elicitation is disabled, the proxy returns an actionable error with specific instructions for the admin to connect the domain.

The entire tier cascade is wrapped in a rate limiter — 60 requests per minute per user on the proxy endpoint, enforced with HTTP 429 and `Retry-After` headers.

## The MCP endpoint

The connector exposes an MCP endpoint at `/mcp` for Copilot Studio via `x-ms-agentic-protocol: mcp-streamable-1.0`. The script.csx dispatches JSON-RPC methods to three tools:

| Tool | Purpose |
|------|---------|
| `search_capabilities` | Semantic search with type, tag, and federation filters |
| `explore_registry` | Faceted aggregation over type, publisher, or tag fields |
| `invoke_capability` | Proxy MCP calls to discovered endpoints with automatic auth |

The `invoke_capability` tool is where the real power is. A user in Copilot Studio can say "find me a weather forecast tool" and then "use it to get the forecast for Seattle" — the first call hits `search_capabilities`, the second hits `invoke_capability` which proxies the actual `tools/call` to the discovered MCP server, handling authentication transparently.

The `initialize` response advertises the `elicitation` capability so Copilot Studio knows it can present sign-in prompts when the proxy needs user credentials:

```csharp
["capabilities"] = new JObject
{
    ["tools"] = new JObject { ["listChanged"] = false },
    ["elicitation"] = new JObject {}
}
```

## Web crawling

The crawl function runs every 6 hours via a timer trigger and processes domains from the `CrawlDomains` app setting. Per ARD spec section 6.2, web ingestion of `ai-catalog.json` files is a required capability for all ARD implementations.

```csharp
[Function("Crawl")]
public async Task Run([TimerTrigger("0 0 */6 * * *")] TimerInfo timer)
```

The crawl pipeline:

1. Skip domains crawled within the last 5 hours (prevents duplicate work if the timer fires slightly early)
2. Verify trust signals for the domain before indexing
3. Fetch and parse `/.well-known/ai-catalog.json`
4. Follow nested catalog references (catalogs can reference other catalogs)
5. Index valid entries with trust scores attached
6. Record crawl state (success/failure, entry count, timestamp) in Table Storage

A manual crawl endpoint (`POST /api/crawl-now?domains=a.com,b.com`) lets operators trigger on-demand indexing with API key authentication.

## The connector layer

The script.csx handles the boundary between Power Platform and the Azure Functions backend. For the MCP endpoint, it implements a full JSON-RPC 2.0 dispatcher:

```csharp
switch (method)
{
    case "initialize":
        return HandleInitialize(requestId);
    case "tools/list":
        return HandleToolsList(requestId);
    case "tools/call":
        return await HandleToolsCallAsync(@params, requestId);
    case "resources/list":
    case "prompts/list":
        return CreateJsonRpcSuccessResponse(requestId, new JObject { ... });
    case "ping":
        return CreateJsonRpcSuccessResponse(requestId, new JObject());
    default:
        return CreateJsonRpcErrorResponse(requestId, -32601, "Method not found");
}
```

For typed operations (Power Automate), the connector constructs the correct payload shape. The search tool, for example, maps the MCP tool's simple `type_filter` parameter to the ARD spec's media type strings:

```csharp
var typeMap = new Dictionary<string, string>
{
    { "mcp", "application/mcp-server-card+json" },
    { "a2a", "application/a2a-agent-card+json" },
    { "skill", "application/ai-skill" }
};
```

This lets a Copilot Studio user say "find MCP servers for weather" while the wire format carries `application/mcp-server-card+json` — the actual ARD media type.

## Operational endpoints

The backend exposes several endpoints for operations teams:

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `GET /api/health` | None | Liveness probe returning index stats |
| `POST /api/crawl-now` | API key | Manual crawl trigger |
| `GET /api/robots.txt` | None | Agentmap directive for ARD crawlers |
| `GET /api/.well-known/ai-catalog.json` | None | This instance's published catalog |

The catalog endpoint makes this instance a participant in the ARD network. Other discovery services can crawl it, creating a federated mesh of registries.

## Federation

The search endpoint supports three federation modes:

- **auto** (default) — queries the local index and any configured upstream registry, merges results by relevance score
- **referrals** — returns local results plus links to other registries the client can query directly
- **none** — local index only

The `DefaultRegistryUrl` setting points to an upstream registry. When a search comes in with `federation: auto`, the backend queries both its local index and the upstream, deduplicates by URN identifier, and returns merged results ranked by relevance.

## Deployment

The backend deploys with Azure Developer CLI:

```bash
cd backend
azd init
azd up
```

The connector deploys with PAC CLI:

```bash
pac connector create --api-definition-file apiDefinition.swagger.json \
  --api-properties-file apiProperties.json \
  --script-file script.csx \
  --environment c4f149b0-9f42-e8c4-97d8-bc69b59f971c
```

Required configuration is minimal — a `BackendApiKey` shared secret, a storage account (managed identity), and optionally the `CrawlDomains` list.

## Why this matters for Power Platform

Power Platform and Copilot Studio currently have no native discovery mechanism for external agentic resources. If you want Copilot Studio to find and invoke an MCP server, you need to know the server exists, know its URL, and build a connector for it. ARD eliminates the first two steps.

With this connector, a Copilot Studio agent can:

1. Search across all known ARD registries for a capability matching a natural language description
2. Evaluate trust scores to decide whether to invoke the result
3. Invoke the discovered MCP server through the proxy, with authentication handled automatically
4. All from a single conversation turn

The combination of ARD discovery + MCP invocation + three-tier auth creates a pattern where Copilot Studio agents can dynamically discover and use capabilities they weren't explicitly configured for — while maintaining trust boundaries and audit trails.

## Resources

- [ARD specification](https://agenticresourcediscovery.org/)
- [AI Catalog standard](https://agenticresourcediscovery.org/ai_catalog_spec/)
- [MCP specification](https://modelcontextprotocol.io/specification/)
- [Source code](https://github.com/troystaylor/SharingIsCaring/tree/main/ARD%20Discovery)
