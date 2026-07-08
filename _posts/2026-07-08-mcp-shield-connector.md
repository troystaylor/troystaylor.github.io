---
layout: post
title: "Building MCP Shield — supply chain integrity monitoring for MCP tool descriptions"
date: 2026-07-08 14:00:00 -0500
categories: [Power Platform, MCP]
tags: [MCP Shield, Security, Custom Connectors, MCP, Copilot Studio, Power Automate, Tool Poisoning]
description: "A Power Platform custom connector that detects MCP tool description poisoning, silent re-trust attacks, and data exfiltration patterns. Pure script.csx with no Azure infrastructure required — hash descriptions, detect drift, scan outbound payloads, and flag imperative language hidden in tool metadata."
---

Microsoft Incident Response published a [detailed analysis](https://www.microsoft.com/en-us/security/blog/2026/06/30/securing-ai-agents-ai-tools-move-from-reading-acting/) of a real-world MCP tool poisoning attack: a threat actor silently modified an invoice enrichment tool's description to instruct the agent to exfiltrate financial data. The agent followed the poisoned instructions because it trusted the tool description at face value.

MCP Shield is a Power Platform custom connector that counters this attack pattern. It monitors the supply chain integrity of MCP tool descriptions — hashing them, detecting drift, scanning outbound payloads for sensitive data, and flagging imperative language that doesn't belong in documentation.

## Attack phases and defenses

The connector maps directly to the four phases of the tool poisoning attack:

| Phase | Attack | MCP Shield defense |
|-------|--------|-------------------|
| 1 | Tool description poisoning | **Detect Imperative Language** — flags command-like instructions hidden in descriptions |
| 2 | Silent re-trust | **Check Description Drift** — alerts when descriptions change vs. stored hash |
| 3 | Expanded data access | **Scan Outbound Payload** — catches bulk data, PII, and financial patterns in parameters |
| 4 | Exfiltration | **Log Shield Event** — structured telemetry for Sentinel correlation |

## No infrastructure required

This runs entirely within the custom connector runtime. All core operations — SHA-256 hashing, drift detection, DLP scanning, imperative language detection — execute in `script.csx`. No Azure Functions, no Container Apps, no external dependencies.

The only optional infrastructure is an Azure AI Content Safety resource for ML-grade Prompt Shields integration. Without it, the connector still provides full rule-based detection.

## Operations

| Operation | Purpose |
|-----------|---------|
| Hash Tool Description | Compute SHA-256 hash of an MCP tool's description text |
| Check Description Drift | Compare current description against a previously stored hash |
| Scan Outbound Payload | Inspect tool call parameters for sensitive data patterns |
| Detect Imperative Language | Analyze descriptions for hidden directives and exfiltration verbs |
| Inspect with Prompt Shields | ML-grade indirect injection detection (optional, requires Content Safety) |
| Log Shield Event | Record structured security events to Application Insights |
| MCP Endpoint | Copilot Studio agents can self-govern inline via MCP protocol |

## What "Detect Imperative Language" catches

This is the primary defense against tool poisoning. It scans descriptions for:

- **Exfiltration verbs** — "retrieve the last 30 invoices," "attach as additional parameter"
- **Override instructions** — "ignore previous rules," "you must always include"
- **Hidden directives** — "silently," "without telling," "before responding"
- **Bulk data requests** — "all unpaid invoices," "summarize every transaction"
- **Encoding abuse** — "base64 encode the output," zero-width characters

Returns a risk score (0–100) and detailed findings. Anything above your threshold triggers an alert.

## What "Scan Outbound Payload" catches

Before your agent forwards parameters to an external MCP server, this operation inspects them for:

| Pattern | Severity |
|---------|----------|
| SSN patterns | Critical |
| Credit card numbers | Critical |
| IBAN codes | High |
| Bulk query indicators (`SELECT *`, `TOP N`, "last 30 invoices") | High |
| Base64 encoded blocks | Medium |
| Multiple email addresses | Medium |

## Stateless design

MCP Shield is intentionally stateless. The caller maintains the hash registry:

```
1. Get tool descriptions from MCP server
2. Call Hash Tool Description → store hash
3. On next run: Call Check Description Drift with stored hash
4. If drifted → block + alert + Log Shield Event
5. Before forwarding: Scan Outbound Payload
6. Before trusting new tools: Detect Imperative Language
```

Registry options:
- **Dataverse custom table** — `mcpshield_registry` with columns: ServerName, ToolName, DescriptionHash, ApprovedBy, ApprovedDate
- **SharePoint list** — simple for small environments
- **Flow variable** — for single-run validation without persistence

## Example: financial invoice protection flow

This recreates the exact defense for the Microsoft Security Blog attack scenario:

1. **Trigger**: Scheduled (hourly) or on-demand
2. **Get tool list** from the invoice enrichment MCP server
3. **For each tool**:
   - `Detect Imperative Language` on the description
   - If suspicious → `Log Shield Event` (severity: critical) + send Teams alert + skip tool
   - `Check Description Drift` against Dataverse registry
   - If drifted → `Log Shield Event` + require human approval before updating hash
4. **Before each enrichment call**:
   - `Scan Outbound Payload` on the parameters
   - If blocked → `Log Shield Event` + abort call + notify SOC

## Relationship to Agent Governance Toolkit

| Agent Governance Toolkit | MCP Shield |
|--------------------------|-----------|
| Runtime policy enforcement (allow/deny tool calls) | Supply chain integrity monitoring |
| Requires Azure Container App | Pure script.csx — no infrastructure |
| Per-tool policy rules | Per-description content analysis |
| Trust scoring + circuit breakers | Hash registry + drift detection |

They compose: MCP Shield verifies the supply chain is clean; AGT enforces policy on what gets executed.

## Deployment

```powershell
pac connector create `
  -df "apiDefinition.swagger.json" `
  -pf "apiProperties.json" `
  -sf "script.csx" `
  -env <environment-id>
```

No OAuth configuration needed — the connector uses API Key authentication for simplicity (the key protects connector access, not downstream APIs).

The full source is available in the [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/MCP%20Shield).
