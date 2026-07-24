---
layout: post
title: "GraphQL Bridge: a REST-to-GraphQL template for custom connectors"
date: 2026-07-24 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [GraphQL, Custom Connectors, Power Platform, Power Automate, Copilot Studio, script.csx, Integration]
description: "A reusable script.csx template that turns REST-style Power Platform custom connector operations into a JSON to GraphQL to JSON bridge, so callers never touch GraphQL syntax."
---

GraphQL and Power Platform's Swagger model don't agree on much. GraphQL sends one `POST` with a `{ query, variables }` envelope to a single endpoint. Power Platform models operations per path and verb, expects clean request and response schemas, and treats HTTP 200 as success. Point a custom connector straight at a GraphQL API and you get raw query strings in your flows, false successes on failed queries, and response data buried under a `data` root.

GraphQL Bridge is a reusable `script.csx` template that reconciles all three. Callers send flat JSON, the script builds the GraphQL envelope, posts it, and returns clean JSON. No GraphQL knowledge is needed in the connector operations, Power Automate, or Copilot Studio.

You can find the complete code in my [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/GraphQL%20Bridge).

## Why this is needed

Three mismatches between GraphQL and Power Platform's Swagger model drive the whole script:

| GraphQL behavior | Power Platform problem | What the bridge does |
|------------------|------------------------|----------------------|
| Single endpoint, `POST { query, variables }` | Operations are modeled per path and verb | Builds the envelope from a flat body and retargets the request at the GraphQL path |
| Returns HTTP 200 even on failure (`errors` array) | Power Automate sees a false success | Inspects `errors` and returns a real HTTP 400 with the messages |
| Nests results under `data` (and deeper) | Response schemas map poorly to `data.brand.assets` | Unwraps `data` and an optional per-operation sub-path |

## How it works

The bridge chooses one of two modes per `OperationId`.

### Mode A — server-defined document (recommended)

Register the GraphQL document in `GraphQlDocuments`, keyed by `OperationId`. The connector body passes straight through as GraphQL variables, so the operation looks like a normal typed REST call:

```csharp
private static readonly Dictionary<string, string> GraphQlDocuments =
    new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
{
    ["GetAssetById"] = @"query GetAssetById($id: ID!) {
        asset(id: $id) { id title status createdAt }
    }",
};

// Optional: return exactly the nested object the Swagger schema expects
private static readonly Dictionary<string, string> ResponseRootPaths =
    new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
{
    ["GetAssetById"] = "asset",   // returns data.asset instead of the whole data object
};
```

The caller sends a flat body:

```json
{ "id": "abc123" }
```

The script wraps it as variables, posts the registered document, and returns `data.asset`. The maker never sees GraphQL.

### Mode B — passthrough

If no document is registered for the `OperationId`, the body must carry the query itself. Wire this to a generic `RunQuery` operation for ad-hoc queries:

```json
{
  "query": "query ($id: ID!) { asset(id: $id) { id title } }",
  "variables": { "id": "abc123" }
}
```

Reserved body keys (`query`, `variables`, `operationName`) are always honored. In Mode A, everything else in the body becomes variables.

## Configuration

Four settings control the bridge, all at the top of `script.csx`:

| Setting | Purpose |
|---------|---------|
| `GraphQlPath` | Path appended to the connector host (for example, `/graphql`) |
| `GraphQlDocuments` | `OperationId` to GraphQL document (Mode A) |
| `ResponseRootPaths` | `OperationId` to dot-path into `data` to unwrap (for example, `customer.orders`) |
| `PassthroughOperationId` | `OperationId` reserved for the generic query runner (informational) |

Auth is untouched. The incoming request already carries the connector's `Authorization` header. The script only changes the method, URI path, and content, so credentials flow through automatically.

## Error shapes returned

The bridge turns silent GraphQL failures into real HTTP errors your flows can catch:

- Invalid request JSON returns `400 INVALID_JSON`
- No query available returns `400 NO_QUERY`
- A GraphQL `errors` array returns `400 GRAPHQL_ERROR`, with `errors` and any `partialData`
- A non-2xx from the GraphQL server returns the original status, wrapped as `HTTP_<code>`
- A non-JSON GraphQL response returns `502 INVALID_GRAPHQL_RESPONSE`

## Using it for a real API

Most GraphQL APIs expose a single endpoint and use a bearer token:

- **Host**: the API's host, such as `api.example.com`
- **Path**: `/graphql` (the default `GraphQlPath`; change it if the API differs)
- **Auth**: OAuth 2.0 or an API or personal access token, configured as the connector's security definition

Steps to adapt it:

1. Point the connector host at the API and set `GraphQlPath` to its GraphQL endpoint path.
2. Add one entry to `GraphQlDocuments` per typed operation you want to expose, for queries and mutations.
3. Optionally set `ResponseRootPaths` so each operation returns the exact nested object.
4. Add a generic `RunQuery` operation for anything not yet modeled (Mode B).

Because the bridge exposes schema-shaped typed operations rather than a raw passthrough, pair each build with full Swagger response schemas so you keep IntelliSense and dynamic value support in Power Automate.

For per-tenant hosts, where the GraphQL host varies per customer (for example, `{tenant}.example.com`), Power Platform's Swagger host is static. Bake the host as a replaceable constant in the script and set the request URI there instead of relying on `GraphQlPath` alone.

## Conventions

- Uses `this.Context.SendAsync(...)`, never `new HttpClient()`, which the runtime blocks
- Fully qualifies `Newtonsoft.Json.Formatting` to avoid the `System.Xml` ambiguity
- Requires no connection parameters; the endpoint path is a compile-time constant

## Resources

- Template repo: [SharingIsCaring/Connector-Code/GraphQL Bridge](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/GraphQL%20Bridge)
- GraphQL specification: [spec.graphql.org](https://spec.graphql.org/)
- Custom connector C# code reference: [Write code in a custom connector](https://learn.microsoft.com/en-us/connectors/custom-connectors/write-code)
