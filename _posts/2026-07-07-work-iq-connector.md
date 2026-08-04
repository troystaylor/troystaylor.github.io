---
layout: post
title: "Work IQ connector: Microsoft 365 workplace intelligence in Power Platform"
date: 2026-07-07 16:00:00 -0500
categories: [Power Platform, MCP]
tags: [Work IQ, MCP, Copilot Studio, Custom Connectors, A2A, Microsoft 365, Power Automate]
description: "A dual-mode Power Platform custom connector for Microsoft Work IQ — an MCP endpoint for Copilot Studio and a typed A2A action for Power Automate. Ask natural language questions about workplace data and get structured answers with permission-trimmed, policy-enforced access."
---

"What meetings do I have today?" "What did Dana share about the Q3 budget?" "Who's working on the Contoso proposal?"

These are the kinds of questions your agents and flows should be able to answer without you wiring up separate connectors for Mail, Calendar, Teams, SharePoint, and People. The [Work IQ A2A API](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/work-iq/api-overview) reasons across all M365 data automatically — you ask a question in plain English and get a structured answer back. This connector puts that capability into Power Platform.

## What it does

The connector exposes two paths:

| Path | Protocol | Purpose |
|------|----------|---------|
| `/mcp` | MCP (streamable 1.0) | Copilot Studio agents invoke Work IQ via natural language |
| `/a2a/` | A2A (JSON-RPC 2.0) | Power Automate flows call "Ask Work IQ" as a typed action |

Both hit the same Work IQ backend at `workiq.svc.cloud.microsoft`. The MCP endpoint is a passthrough proxy — Copilot Studio detects it and handles tool invocation automatically. The A2A endpoint wraps the JSON-RPC `SendMessage` method with a typed schema so Power Automate can use it with full IntelliSense.

## How it differs from Agent 365 MCP

| Connector | Approach | Best for |
|-----------|----------|----------|
| Work IQ (this) | Conversational — ask a question, get an answer | Agents and flows that need workplace context without picking a workload |
| [Agent 365 MCP](/power%20platform/mcp/2026-07-07-agent-365-mcp-connector.html) | Tool-based — individual MCP servers per workload | Agents that need granular, programmatic control over Mail, Calendar, Teams, etc. |

Work IQ is simpler. You don't choose which server to call — Work IQ routes to the right data automatically. Agent 365 MCP gives you 11 individual servers with full tool schemas when you need that precision.

## Multi-turn conversations

Work IQ supports conversational context via `contextId`. The first response includes a context ID; pass it back on subsequent requests to ask follow-ups:

```
1. AskWorkIQ → "What meetings do I have today?"
   → response includes contextId: "ctx-abc123"

2. AskWorkIQ → "Tell me more about the 2 PM call"
   → contextId: "ctx-abc123"
   → Work IQ uses conversation history to resolve "the 2 PM call"
```

This means a Power Automate flow can have a multi-step conversation with Work IQ — asking progressively more specific questions about the same topic.

## Supported data

Work IQ reasons over:

- Email messages
- Meetings and calendar data
- Documents in OneDrive and SharePoint
- Teams messages
- People and organizational context
- Planner plans
- Enterprise search results

All responses are permission-trimmed and policy-enforced. Work IQ only returns data the signed-in user has access to, and it respects sensitivity labels and compliance policies.

## The A2A request format

The typed operation wraps the A2A protocol's JSON-RPC format:

```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-guid",
  "method": "SendMessage",
  "params": {
    "message": {
      "role": "ROLE_USER",
      "messageId": "unique-message-guid",
      "contextId": "optional-context-from-previous-response",
      "parts": [
        { "text": "What did Dana share about the Q3 budget?" }
      ],
      "metadata": {
        "Location": {
          "timeZoneOffset": -300,
          "timeZone": "America/Chicago"
        }
      }
    }
  }
}
```

Include `timeZone` and `timeZoneOffset` for time-sensitive queries — Work IQ uses them to interpret "today," "this week," and similar relative references correctly.

## Authentication

The connector uses OAuth 2.0 with the `https://workiq.svc.cloud.microsoft/.default` scope. Delegated only — Work IQ runs in the context of the signed-in user. App-only authentication is not supported.

For multitenant organizations (parent/child tenants), register the app as `AzureADMultipleOrgs`. The token issuer must match the user's home tenant.

## Deployment

1. Import via Maker portal (Custom connectors > Import OpenAPI) or deploy with PAC CLI:

```powershell
pac connector create `
    -df apiDefinition.swagger.json `
    -env <environment-id>
```

2. Configure OAuth in the Security tab with your app registration client ID and the `https://workiq.svc.cloud.microsoft/.default` scope
3. Create a connection and test with a simple question

## Billing

Work IQ API access is independent of Microsoft 365 Copilot licensing, and you pay for it through a [usage-based model that uses Copilot Credits](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/work-iq/api-overview#licensing-requirements). Each query consumes credits based on the complexity of reasoning required, so cost tracks volume rather than seats.

A Copilot license doesn't exempt you. Licensed users get Work IQ across every Microsoft 365 Copilot experience and agent, but [custom and third-party agents are subject to usage-based billing](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/work-iq/#access-and-pricing)—which is what this connector is. Users without a Copilot license are billed on usage as well.

Sort this out before you schedule a flow against it. An admin enables usage-based billing in the [Microsoft 365 admin center](https://learn.microsoft.com/en-us/microsoft-365/copilot/usage-based-billing-overview-copilot-credits) and sets the spending policies, budgets, and caps that decide who can consume and how much. The Cost Management dashboard reports consumption by user, group, service, or agent, which is where a flow that asks Work IQ a question every five minutes shows up.

## Use cases

**Meeting prep agent** — Before a customer meeting, ask Work IQ "What have we discussed with Zava in the last 30 days?" and get a summary spanning email, Teams, and shared documents — all from one call.

**Automated context injection** — A Power Automate flow triggers before weekly standups, asks Work IQ "What did my team accomplish this week?", and posts the summary to a Teams channel.

**Help desk triage** — When a support ticket arrives, ask Work IQ "What do we know about this topic?" to surface relevant internal documentation and prior conversations before routing to an agent.

The full source is available in the [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Work%20IQ).
