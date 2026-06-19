---
layout: post
title: "Federated Copilot connectors aren't actually read-only"
date: 2026-06-19 14:00:00 -0500
categories: [Power Platform, MCP]
tags: [MCP, Microsoft 365 Copilot, Federated Connectors, Security Research, Copilot Studio]
description: "Experiment proving that Microsoft 365 Copilot Federated connectors can perform full CRUD operations despite being documented as read-only. The platform trusts the readOnlyHint annotation at face value with no runtime enforcement."
---

Microsoft's documentation is explicit: Federated Copilot connectors are read-only. The [Federated connectors overview](https://learn.microsoft.com/microsoft-365/copilot/connectors/Federated-connectors-overview) states they "are read-only and can be audited in Microsoft Purview." The [setup guide](https://learn.microsoft.com/microsoft-365/copilot/connectors/set-up-custom-Federated-connectors) describes them as exposing "read-only tools to safely surface your data." The [submission requirements](https://learn.microsoft.com/microsoft-365/copilot/connectors/submit-Federated-connector) mandate that "each tool must include the `readOnlyHint` annotation to be enabled."

I built an MCP server to test whether that constraint is enforced at runtime or only at registration. The answer: **registration only**.

## The experiment

I deployed a .NET 10 MCP server to Azure Container Apps with six tools:

- 3 read tools: `list_tasks`, `get_task`, `search_tasks`
- 3 write tools: `create_task`, `update_task`, `delete_task`

All six tools declared `readOnlyHint: true` in their annotations — including the write operations. The server uses an in-memory data store seeded with six task items so mutations are obvious.

I registered it as a custom Federated connector in the M365 Admin Center, authenticated via OAuth 2.0, and tested from Copilot Chat.

## Results

| Test | Result |
|------|--------|
| Tools with `readOnlyHint: false` | Filtered out at registration |
| Tools with `readOnlyHint: true` (honest reads) | Accepted and invocable |
| Write tools with `readOnlyHint: true` | **Accepted, exposed, and invoked** |
| Semantic analysis of tool names/descriptions | **None** — `create_task` and `delete_task` pass through |
| Runtime blocking of write operations | **None** — tool executes, data mutates |

All four CRUD operations succeeded in Copilot Chat on 2026-06-19:

- **Read**: "List all tasks from Federated CRUD Test"
- **Create**: "Create a new task called 'Written from Copilot' in the Testing category"
- **Update**: "Mark task 4 as done"
- **Delete**: "Delete task 6"

## How the enforcement actually works

```text
Registration time:
  Platform calls tools/list
  Checks annotations.readOnlyHint on each tool
  readOnlyHint: true  → tool registered
  readOnlyHint: false → tool silently dropped
  no annotations      → validation fails ("no read-only tool defined")

Runtime:
  No additional checks.
  If a tool was registered, Copilot invokes it freely.
```

The platform trusts `readOnlyHint` at face value. There's no behavioral verification, no semantic analysis of tool names or descriptions, and no runtime interception of the actual HTTP calls the tool makes.

## Why this matters

The Federated connector model is designed for scenarios where data "can't or shouldn't be indexed" and must remain in the source system. Organizations adopt it specifically because it's documented as a safe, read-only bridge to sensitive data. If a partner or internal developer marks write tools as read-only (whether through ignorance or intent), Copilot will execute those mutations on behalf of the user with no guardrail.

Microsoft could close this gap with:

- Semantic analysis of tool names and descriptions at registration
- Runtime enforcement that intercepts non-GET HTTP methods
- Purview behavioral auditing that flags tools whose actual behavior contradicts their annotations
- A separate permission tier for write-capable Federated connectors

## Technical discoveries along the way

**MCP .NET SDK v1.4.0 bug**: The `McpServerToolAttribute.ReadOnly` property does not emit `annotations` in the wire format. I had to use a raw JSON-RPC handler to get the annotation into the `tools/list` response.

**Entra SSO**: Does not work cross-tenant for Federated connectors (fails with `AADSTS90009`). OAuth 2.0 works cross-tenant but requires service principals in both tenants.

**Stateless JSON-RPC**: The Federated connector platform works with plain `application/json` responses. No SSE or session management required.

**annotations field required**: Without `annotations` on at least one tool, registration fails with "no read-only tool defined." The field isn't optional — it's the entire enforcement mechanism.

## Architecture

The test server is intentionally minimal:

- .NET 10 MCP server with Streamable HTTP transport
- In-memory data store (6 seeded task items)
- Microsoft Entra authentication (OAuth 2.0 + RFC 9728 resource metadata)
- Azure Container App hosting

## Responsible disclosure

This isn't a vulnerability in the traditional sense — it's a gap between documentation and enforcement. The platform correctly filters tools at registration based on their declared annotations. It just doesn't verify that declaration against actual behavior. I'm sharing this publicly because the behavior is observable to anyone who deploys a custom Federated connector, and awareness helps organizations make informed decisions about which connectors they approve.

## Resources

- [Federated connectors overview](https://learn.microsoft.com/microsoft-365/copilot/connectors/Federated-connectors-overview)
- [Set up custom Federated connectors](https://learn.microsoft.com/microsoft-365/copilot/connectors/set-up-custom-Federated-connectors)
- [Submit a Federated connector](https://learn.microsoft.com/microsoft-365/copilot/connectors/submit-Federated-connector)
- [MCP specification](https://modelcontextprotocol.io/specification)
- [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring)
